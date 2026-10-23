"""Recruiter contacts API routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
from app.core.database import get_db
from app.models.recruiter import Recruiter

router = APIRouter()


class CreateRecruiterRequest(BaseModel):
    name: Optional[str] = None
    email: str
    title: Optional[str] = None
    department: Optional[str] = None
    company: str
    verification_status: str = "unverified"
    source_url: Optional[str] = None
    evidence: Optional[str] = None

class UpdateRecruiterRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    title: Optional[str] = None
    department: Optional[str] = None
    company: Optional[str] = None
    verification_status: Optional[str] = None
    source_url: Optional[str] = None
    evidence: Optional[str] = None


@router.get("")
async def list_recruiters(
    company: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List all recruiter contacts."""
    query = select(Recruiter).where(Recruiter.user_id == 1)
    
    if company:
        query = query.where(Recruiter.company.ilike(f"%{company}%"))
    if status:
        query = query.where(Recruiter.verification_status == status)
    
    result = await db.execute(query.order_by(Recruiter.updated_at.desc()))
    recruiters = result.scalars().all()
    
    return [
        {
            "id": r.id,
            "name": r.name,
            "email": r.email,
            "title": r.title,
            "department": r.department,
            "company": r.company,
            "verification_status": r.verification_status,
            "source_url": r.source_url,
            "evidence": r.evidence,
            "emails_sent_count": r.emails_sent_count,
            "last_contacted": r.last_contacted.isoformat() if r.last_contacted else None,
            "last_verified": r.last_verified.isoformat() if r.last_verified else None,
        }
        for r in recruiters
    ]


@router.post("")
async def add_recruiter(request: CreateRecruiterRequest, db: AsyncSession = Depends(get_db)):
    """Add a recruiter contact."""
    recruiter = Recruiter(
        user_id=1,
        name=request.name,
        email=request.email,
        title=request.title,
        department=request.department,
        company=request.company,
        verification_status=request.verification_status,
        source_url=request.source_url,
        evidence=request.evidence,
    )
    db.add(recruiter)
    await db.flush()
    return {"id": recruiter.id, "message": "Recruiter contact added"}


@router.put("/{recruiter_id}")
async def update_recruiter(recruiter_id: int, request: UpdateRecruiterRequest, db: AsyncSession = Depends(get_db)):
    """Update recruiter info."""
    result = await db.execute(select(Recruiter).where(Recruiter.id == recruiter_id))
    recruiter = result.scalar_one_or_none()
    if not recruiter:
        raise HTTPException(status_code=404, detail="Recruiter not found")
    
    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(recruiter, key, value)
    
    return {"message": "Recruiter updated"}


@router.delete("/{recruiter_id}")
async def delete_recruiter(recruiter_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a recruiter contact."""
    result = await db.execute(select(Recruiter).where(Recruiter.id == recruiter_id))
    recruiter = result.scalar_one_or_none()
    if not recruiter:
        raise HTTPException(status_code=404, detail="Recruiter not found")
    await db.delete(recruiter)
    return {"message": "Recruiter deleted"}


@router.post("/discover/{company}")
async def discover_company_recruiters(company: str, db: AsyncSession = Depends(get_db)):
    """Discover recruiter contacts for a specific target company."""
    from app.services.recruiter_finder import recruiter_finder_service
    results = await recruiter_finder_service.discover_recruiters_for_company(company, db)
    return {
        "company": company,
        "count": len(results),
        "recruiters": results,
    }
