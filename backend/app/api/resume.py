"""Resume upload and management API routes."""
import os
import shutil
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.config import settings
from app.models.resume import Resume

router = APIRouter()


@router.get("")
async def list_resumes(db: AsyncSession = Depends(get_db)):
    """List all uploaded resumes."""
    result = await db.execute(
        select(Resume).where(Resume.user_id == 1).order_by(Resume.uploaded_at.desc())
    )
    resumes = result.scalars().all()
    return [
        {
            "id": r.id,
            "filename": r.filename,
            "label": r.label,
            "is_default": r.is_default,
            "is_tailored": r.is_tailored,
            "file_size": r.file_size,
            "version": r.version,
            "uploaded_at": r.uploaded_at.isoformat() if r.uploaded_at else None,
            "has_parsed_data": r.parsed_data is not None,
        }
        for r in resumes
    ]


@router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...),
    label: str = "Default Resume",
    set_default: bool = True,
    db: AsyncSession = Depends(get_db),
):
    """Upload a resume PDF."""
    # Validate file type
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")
    
    # Validate file size
    content = await file.read()
    if len(content) > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {settings.MAX_FILE_SIZE_MB}MB"
        )
    
    # Save file
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    safe_filename = f"resume_{timestamp}_{file.filename}"
    filepath = os.path.join(settings.UPLOAD_DIR, safe_filename)
    
    with open(filepath, "wb") as f:
        f.write(content)
    
    # Parse PDF text
    raw_text = ""
    try:
        import pdfplumber
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    raw_text += text + "\n"
    except Exception as e:
        print(f"Warning: Could not parse PDF text: {e}")
    
    # If set_default, unset previous defaults
    if set_default:
        result = await db.execute(
            select(Resume).where(Resume.user_id == 1, Resume.is_default == True)
        )
        for r in result.scalars().all():
            r.is_default = False
    
    # Create record
    resume = Resume(
        user_id=1,
        filename=file.filename,
        filepath=filepath,
        file_size=len(content),
        mime_type="application/pdf",
        raw_text=raw_text if raw_text else None,
        label=label,
        is_default=set_default,
    )
    db.add(resume)
    await db.flush()
    
    return {
        "id": resume.id,
        "filename": resume.filename,
        "label": resume.label,
        "is_default": resume.is_default,
        "file_size": resume.file_size,
        "has_parsed_text": bool(raw_text),
        "message": "Resume uploaded successfully",
    }


@router.get("/{resume_id}")
async def get_resume(resume_id: int, db: AsyncSession = Depends(get_db)):
    """Get resume details including parsed text."""
    result = await db.execute(select(Resume).where(Resume.id == resume_id, Resume.user_id == 1))
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    return {
        "id": resume.id,
        "filename": resume.filename,
        "label": resume.label,
        "is_default": resume.is_default,
        "is_tailored": resume.is_tailored,
        "file_size": resume.file_size,
        "raw_text": resume.raw_text,
        "parsed_data": resume.parsed_data,
        "version": resume.version,
        "uploaded_at": resume.uploaded_at.isoformat() if resume.uploaded_at else None,
    }


@router.put("/{resume_id}/set-default")
async def set_default_resume(resume_id: int, db: AsyncSession = Depends(get_db)):
    """Set a resume as the default."""
    result = await db.execute(select(Resume).where(Resume.id == resume_id, Resume.user_id == 1))
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    # Unset all defaults
    all_result = await db.execute(select(Resume).where(Resume.user_id == 1))
    for r in all_result.scalars().all():
        r.is_default = False
    
    resume.is_default = True
    return {"message": f"'{resume.label}' set as default resume"}


    await db.delete(resume)
    return {"message": "Resume deleted"}


class TailorResumeRequest(BaseModel):
    job_id: int
    resume_id: Optional[int] = None


@router.post("/tailor")
async def tailor_resume(request: TailorResumeRequest, db: AsyncSession = Depends(get_db)):
    """Generate tailored resume bullet points and project emphasis for a target job."""
    from app.services.ai_provider import ai_service
    from app.models.job import Job
    from app.models.profile import Profile
    from sqlalchemy.orm import selectinload

    # Fetch job
    job_res = await db.execute(select(Job).where(Job.id == request.job_id).options(selectinload(Job.skills)))
    job = job_res.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Fetch profile
    profile_res = await db.execute(select(Profile).where(Profile.user_id == 1))
    profile = profile_res.scalar_one_or_none()

    req_skills = [s.skill_name for s in job.skills if s.is_required] if job.skills else []

    tailored_data = await ai_service.tailor_resume_suggestions(
        job_data={
            "title": job.title,
            "company": job.company,
            "description": job.description or "",
            "required_skills": req_skills,
        },
        profile_data={
            "full_name": profile.full_name if profile else "Sarthak Singh Tomar",
            "degree": profile.degree if profile else "B.Tech",
            "college": profile.college if profile else "IIIT Kota",
        }
    )

    return {
        "job_id": job.id,
        "job_title": job.title,
        "company": job.company,
        "data": tailored_data,
    }


class AnswerQuestionsRequest(BaseModel):
    job_id: int
    questions: list[str]


@router.post("/answer-questions")
async def answer_application_questions(request: AnswerQuestionsRequest, db: AsyncSession = Depends(get_db)):
    """Generate tailored portal application answers using candidate profile and job details."""
    from app.services.ai_provider import ai_service
    from app.models.job import Job
    from app.models.profile import Profile

    job_res = await db.execute(select(Job).where(Job.id == request.job_id))
    job = job_res.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    profile_res = await db.execute(select(Profile).where(Profile.user_id == 1))
    profile = profile_res.scalar_one_or_none()

    answers = await ai_service.answer_application_questions(
        questions=request.questions,
        job_data={"title": job.title, "company": job.company},
        profile_data={"full_name": profile.full_name if profile else "Sarthak Singh Tomar"}
    )

    return {
        "job_id": job.id,
        "job_title": job.title,
        "company": job.company,
        "answers": answers,
    }
