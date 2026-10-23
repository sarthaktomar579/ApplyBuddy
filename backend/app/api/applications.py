"""Application tracking API routes."""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from typing import Optional
from app.core.database import get_db
from app.models.application import Application, ApplicationStatusHistory
from app.models.job import Job

router = APIRouter()

VALID_STATUSES = [
    "discovered", "shortlisted", "preparing_application", "awaiting_approval",
    "email_sent", "application_submitted", "follow_up_due", "recruiter_replied",
    "interview_scheduled", "rejected", "offer_received", "withdrawn",
]


class CreateApplicationRequest(BaseModel):
    job_id: int
    status: str = "discovered"
    notes: Optional[str] = None

class UpdateStatusRequest(BaseModel):
    status: str
    notes: Optional[str] = None

class UpdateApplicationRequest(BaseModel):
    notes: Optional[str] = None
    follow_up_date: Optional[str] = None
    interview_date: Optional[str] = None
    interview_type: Optional[str] = None
    interview_notes: Optional[str] = None
    response_content: Optional[str] = None
    offer_salary: Optional[str] = None
    offer_details: Optional[str] = None


@router.get("")
async def list_applications(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """List applications with optional status filter."""
    query = select(Application).where(Application.user_id == 1)
    
    if status:
        query = query.where(Application.status == status)
    
    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    query = query.order_by(Application.updated_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query.options(selectinload(Application.job)))
    applications = result.scalars().all()
    
    return {
        "total": total,
        "applications": [_app_to_dict(a) for a in applications],
    }


@router.post("")
async def create_application(request: CreateApplicationRequest, db: AsyncSession = Depends(get_db)):
    """Create a new application entry."""
    if request.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {VALID_STATUSES}")
    
    # Verify job exists
    job_result = await db.execute(select(Job).where(Job.id == request.job_id))
    if not job_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check for existing application for this job
    existing = await db.execute(
        select(Application).where(Application.job_id == request.job_id, Application.user_id == 1)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Application already exists for this job")
    
    app = Application(
        user_id=1,
        job_id=request.job_id,
        status=request.status,
        notes=request.notes,
    )
    db.add(app)
    await db.flush()
    
    # Record initial status
    db.add(ApplicationStatusHistory(
        application_id=app.id,
        new_status=request.status,
        changed_by="user",
    ))
    
    return {"id": app.id, "message": "Application created"}


@router.put("/{app_id}/status")
async def update_status(app_id: int, request: UpdateStatusRequest, db: AsyncSession = Depends(get_db)):
    """Update application status."""
    if request.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {VALID_STATUSES}")
    
    result = await db.execute(select(Application).where(Application.id == app_id))
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    
    old_status = app.status
    app.status = request.status
    
    # Record status change
    db.add(ApplicationStatusHistory(
        application_id=app.id,
        old_status=old_status,
        new_status=request.status,
        changed_by="user",
        notes=request.notes,
    ))
    
    return {"message": f"Status updated from '{old_status}' to '{request.status}'"}


@router.put("/{app_id}")
async def update_application(app_id: int, request: UpdateApplicationRequest, db: AsyncSession = Depends(get_db)):
    """Update application details."""
    result = await db.execute(select(Application).where(Application.id == app_id))
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    
    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key in ("follow_up_date", "interview_date") and value:
            try:
                value = datetime.fromisoformat(value)
            except ValueError:
                pass
        setattr(app, key, value)
    
    return {"message": "Application updated"}


@router.get("/{app_id}")
async def get_application(app_id: int, db: AsyncSession = Depends(get_db)):
    """Get application details with history."""
    result = await db.execute(
        select(Application)
        .where(Application.id == app_id)
        .options(
            selectinload(Application.job),
            selectinload(Application.status_history),
        )
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    
    data = _app_to_dict(app)
    data["status_history"] = [
        {
            "old_status": h.old_status,
            "new_status": h.new_status,
            "changed_by": h.changed_by,
            "notes": h.notes,
            "changed_at": h.changed_at.isoformat() if h.changed_at else None,
        }
        for h in app.status_history
    ]
    return data


@router.delete("/{app_id}")
async def delete_application(app_id: int, db: AsyncSession = Depends(get_db)):
    """Delete an application."""
    result = await db.execute(select(Application).where(Application.id == app_id))
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    await db.delete(app)
    return {"message": "Application deleted"}


def _app_to_dict(app: Application) -> dict:
    return {
        "id": app.id,
        "job_id": app.job_id,
        "status": app.status,
        "applied_via": app.applied_via,
        "notes": app.notes,
        "follow_up_date": app.follow_up_date.isoformat() if app.follow_up_date else None,
        "follow_up_count": app.follow_up_count,
        "interview_date": app.interview_date.isoformat() if app.interview_date else None,
        "interview_type": app.interview_type,
        "interview_notes": app.interview_notes,
        "response_content": app.response_content,
        "offer_salary": app.offer_salary,
        "offer_details": app.offer_details,
        "created_at": app.created_at.isoformat() if app.created_at else None,
        "updated_at": app.updated_at.isoformat() if app.updated_at else None,
        "job": {
            "id": app.job.id,
            "title": app.job.title,
            "company": app.job.company,
            "location": app.job.location,
        } if app.job else None,
    }
