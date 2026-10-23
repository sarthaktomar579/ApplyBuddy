"""Email management API routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
from typing import Optional
from app.core.database import get_db
from app.models.email import Email

router = APIRouter()


class CreateEmailRequest(BaseModel):
    job_id: Optional[int] = None
    to_email: str
    to_name: Optional[str] = None
    subject: str
    body: str
    resume_id: Optional[int] = None
    recipient_verified: bool = False
    recipient_source: Optional[str] = None

class UpdateEmailRequest(BaseModel):
    to_email: Optional[str] = None
    to_name: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    resume_id: Optional[int] = None


@router.get("")
async def list_emails(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """List emails with optional status filter."""
    query = select(Email).where(Email.user_id == 1)
    
    if status:
        query = query.where(Email.status == status)
    
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()
    
    result = await db.execute(
        query.order_by(Email.created_at.desc()).offset(skip).limit(limit)
    )
    emails = result.scalars().all()
    
    return {
        "total": total,
        "emails": [_email_to_dict(e) for e in emails],
    }


@router.post("")
async def create_email(request: CreateEmailRequest, db: AsyncSession = Depends(get_db)):
    """Create a new email draft."""
    email = Email(
        user_id=1,
        job_id=request.job_id,
        to_email=request.to_email,
        to_name=request.to_name,
        subject=request.subject,
        body=request.body,
        resume_id=request.resume_id,
        status="draft",
        recipient_verified=request.recipient_verified,
        recipient_source=request.recipient_source,
    )
    db.add(email)
    await db.flush()
    return {"id": email.id, "message": "Email draft created"}


class GenerateEmailRequest(BaseModel):
    job_id: int
    recruiter_name: Optional[str] = None
    recruiter_email: Optional[str] = None
    recruiter_verified: bool = False
    recipient_source: Optional[str] = None


@router.post("/generate")
async def generate_cold_email(request: GenerateEmailRequest, db: AsyncSession = Depends(get_db)):
    """Generate an AI-tailored cold application email for a specific job & recruiter."""
    from app.services.ai_provider import ai_service
    from app.models.job import Job
    from app.models.profile import Profile
    from app.models.recruiter import Recruiter
    from app.models.resume import Resume

    # Get job
    job_res = await db.execute(select(Job).where(Job.id == request.job_id))
    job = job_res.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Get profile
    profile_res = await db.execute(select(Profile).where(Profile.user_id == 1))
    profile = profile_res.scalar_one_or_none()

    # Get default resume
    resume_res = await db.execute(select(Resume).where(Resume.user_id == 1, Resume.is_default == True))
    default_resume = resume_res.scalar_one_or_none()

    # If recruiter_email not provided, try to find recruiter from company in DB
    target_recruiter_name = request.recruiter_name
    target_recruiter_email = request.recruiter_email
    is_verified = request.recruiter_verified
    source = request.recipient_source

    if not target_recruiter_email:
        rec_res = await db.execute(
            select(Recruiter).where(Recruiter.company.ilike(f"%{job.company}%")).limit(1)
        )
        rec = rec_res.scalar_one_or_none()
        if rec:
            target_recruiter_name = rec.name
            target_recruiter_email = rec.email
            is_verified = rec.verification_status == "verified_official"
            source = rec.evidence or rec.source_url

    email_data = await ai_service.generate_cold_email(
        job_data={
            "title": job.title,
            "company": job.company,
            "description": job.description or "",
        },
        profile_data={
            "full_name": profile.full_name if profile else "Sarthak Singh Tomar",
            "email": profile.email if profile else "sarthakt579@gmail.com",
            "github_url": profile.github_url if profile else "https://github.com/sarthaktomar579",
        },
        recruiter_name=target_recruiter_name
    )

    return {
        "job_id": job.id,
        "job_title": job.title,
        "company": job.company,
        "to_email": target_recruiter_email or f"careers@{job.company.lower().replace(' ', '')}.com",
        "to_name": target_recruiter_name or f"{job.company} Hiring Team",
        "subject": email_data["subject"],
        "body": email_data["body"],
        "resume_id": default_resume.id if default_resume else None,
        "recipient_verified": is_verified,
        "recipient_source": source,
    }


@router.get("/{email_id}")
async def get_email(email_id: int, db: AsyncSession = Depends(get_db)):
    """Get email details."""
    result = await db.execute(select(Email).where(Email.id == email_id, Email.user_id == 1))
    email = result.scalar_one_or_none()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    return _email_to_dict(email)


@router.put("/{email_id}")
async def update_email(email_id: int, request: UpdateEmailRequest, db: AsyncSession = Depends(get_db)):
    """Update an email draft."""
    result = await db.execute(select(Email).where(Email.id == email_id, Email.user_id == 1))
    email = result.scalar_one_or_none()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    if email.status not in ("draft", "awaiting_approval"):
        raise HTTPException(status_code=400, detail="Can only edit drafts and awaiting approval emails")
    
    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(email, key, value)
    
    return {"message": "Email updated"}


@router.put("/{email_id}/approve")
async def approve_email(email_id: int, db: AsyncSession = Depends(get_db)):
    """Approve an email for sending."""
    result = await db.execute(select(Email).where(Email.id == email_id, Email.user_id == 1))
    email = result.scalar_one_or_none()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    if email.status not in ("draft", "awaiting_approval"):
        raise HTTPException(status_code=400, detail=f"Cannot approve email with status '{email.status}'")
    
    email.status = "approved"
    return {"message": "Email approved for sending"}


@router.put("/{email_id}/cancel")
async def cancel_email(email_id: int, db: AsyncSession = Depends(get_db)):
    """Cancel a pending email."""
    result = await db.execute(select(Email).where(Email.id == email_id, Email.user_id == 1))
    email = result.scalar_one_or_none()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    if email.status in ("sent",):
        raise HTTPException(status_code=400, detail="Cannot cancel an already sent email")
    
    email.status = "cancelled"
    return {"message": "Email cancelled"}


@router.delete("/{email_id}")
async def delete_email(email_id: int, db: AsyncSession = Depends(get_db)):
    """Delete an email."""
    result = await db.execute(select(Email).where(Email.id == email_id, Email.user_id == 1))
    email = result.scalar_one_or_none()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    if email.status == "sent":
        raise HTTPException(status_code=400, detail="Cannot delete a sent email")
    
    await db.delete(email)
    return {"message": "Email deleted"}


def _email_to_dict(email: Email) -> dict:
    return {
        "id": email.id,
        "job_id": email.job_id,
        "idempotency_key": email.idempotency_key,
        "to_email": email.to_email,
        "to_name": email.to_name,
        "from_email": email.from_email,
        "subject": email.subject,
        "body": email.body,
        "status": email.status,
        "recipient_verified": email.recipient_verified,
        "recipient_source": email.recipient_source,
        "resume_id": email.resume_id,
        "gmail_message_id": email.gmail_message_id,
        "sent_at": email.sent_at.isoformat() if email.sent_at else None,
        "error_message": email.error_message,
        "retry_count": email.retry_count,
        "is_personalized": email.is_personalized,
        "generation_model": email.generation_model,
        "created_at": email.created_at.isoformat() if email.created_at else None,
    }
