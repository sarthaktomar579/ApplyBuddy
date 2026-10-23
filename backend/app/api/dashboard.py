"""Dashboard API routes - Real aggregated stats."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.models.job import Job
from app.models.application import Application
from app.models.email import Email
from app.models.recruiter import Recruiter
from app.models.job_match import JobMatch

router = APIRouter()


@router.get("/stats")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """Get real-time dashboard statistics from stored records."""
    
    # Jobs
    total_jobs = (await db.execute(select(func.count(Job.id)).where(Job.user_id == 1))).scalar() or 0
    active_jobs = (await db.execute(select(func.count(Job.id)).where(Job.user_id == 1, Job.is_active == True))).scalar() or 0
    bookmarked_jobs = (await db.execute(select(func.count(Job.id)).where(Job.user_id == 1, Job.is_bookmarked == True))).scalar() or 0
    
    # Matches
    total_matches = (await db.execute(select(func.count(JobMatch.id)).where(JobMatch.user_id == 1))).scalar() or 0
    high_matches = (await db.execute(select(func.count(JobMatch.id)).where(JobMatch.user_id == 1, JobMatch.overall_score >= 70))).scalar() or 0
    
    # Applications by status
    app_statuses = {}
    for status in ["discovered", "shortlisted", "preparing_application", "awaiting_approval",
                   "email_sent", "application_submitted", "follow_up_due", "recruiter_replied",
                   "interview_scheduled", "rejected", "offer_received", "withdrawn"]:
        count = (await db.execute(
            select(func.count(Application.id)).where(Application.user_id == 1, Application.status == status)
        )).scalar() or 0
        app_statuses[status] = count
    total_applications = sum(app_statuses.values())
    
    # Emails by status
    email_statuses = {}
    for status in ["draft", "awaiting_approval", "approved", "sending", "sent", "failed", "cancelled"]:
        count = (await db.execute(
            select(func.count(Email.id)).where(Email.user_id == 1, Email.status == status)
        )).scalar() or 0
        email_statuses[status] = count
    
    # Recruiters
    total_recruiters = (await db.execute(select(func.count(Recruiter.id)).where(Recruiter.user_id == 1))).scalar() or 0
    verified_recruiters = (await db.execute(
        select(func.count(Recruiter.id)).where(Recruiter.user_id == 1, Recruiter.verification_status == "verified_official")
    )).scalar() or 0
    
    return {
        "jobs": {
            "total": total_jobs,
            "active": active_jobs,
            "bookmarked": bookmarked_jobs,
            "matched": total_matches,
            "high_match": high_matches,
        },
        "applications": {
            "total": total_applications,
            "by_status": app_statuses,
        },
        "emails": {
            "total": sum(email_statuses.values()),
            "by_status": email_statuses,
        },
        "recruiters": {
            "total": total_recruiters,
            "verified": verified_recruiters,
        },
        "quick_stats": {
            "jobs_discovered": total_jobs,
            "jobs_matching": high_matches,
            "awaiting_review": app_statuses.get("discovered", 0) + app_statuses.get("shortlisted", 0),
            "emails_drafted": email_statuses.get("draft", 0),
            "emails_approved": email_statuses.get("approved", 0),
            "emails_sent": email_statuses.get("sent", 0),
            "applications_submitted": app_statuses.get("application_submitted", 0),
            "responses_received": app_statuses.get("recruiter_replied", 0),
            "interviews_scheduled": app_statuses.get("interview_scheduled", 0),
            "follow_ups_due": app_statuses.get("follow_up_due", 0),
        },
    }
