"""Service to inspect past 30 days application history from Gmail and database to prevent duplicate applications."""
import re
import datetime
import httpx
from typing import Set, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config import settings
from app.models.integration import Integration
from app.models.application import Application
from app.models.job import Job


async def get_valid_gmail_token(db: AsyncSession, user_id: int = 1) -> str | None:
    """Retrieve and refresh Gmail OAuth access token."""
    result = await db.execute(
        select(Integration).where(Integration.user_id == user_id, Integration.provider == "gmail")
    )
    integration = result.scalar_one_or_none()
    if not integration or not integration.is_connected or not integration.access_token:
        return None

    # Check token validity or refresh
    async with httpx.AsyncClient() as client:
        test_res = await client.get(
            "https://www.googleapis.com/gmail/v1/users/me/profile",
            headers={"Authorization": f"Bearer {integration.access_token}"}
        )
        if test_res.status_code == 200:
            return integration.access_token

        # Token expired -> Refresh using refresh_token
        if integration.refresh_token and settings.GMAIL_CLIENT_ID and settings.GMAIL_CLIENT_SECRET:
            refresh_res = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": settings.GMAIL_CLIENT_ID,
                    "client_secret": settings.GMAIL_CLIENT_SECRET,
                    "refresh_token": integration.refresh_token,
                    "grant_type": "refresh_token",
                }
            )
            if refresh_res.status_code == 200:
                new_token = refresh_res.json().get("access_token")
                integration.access_token = new_token
                await db.commit()
                return new_token

    return None


async def get_applied_companies_last_30_days(db: AsyncSession, user_id: int = 1) -> Dict[str, Any]:
    """
    Scans both:
    1. Gmail inbox for the last 30 days for confirmation emails:
       - 'Your application was sent to <Company>'
       - 'Your application to <Role> at <Company>'
       - 'Application: <Role> - <Company>'
    2. Local SQLite database for applications submitted in the last 30 days.
    
    Returns a normalized set of company names and list of recent application records.
    """
    applied_companies: Set[str] = set()
    gmail_records: List[Dict[str, str]] = []

    # 1. Check Gmail
    token = await get_valid_gmail_token(db, user_id)
    if token:
        async with httpx.AsyncClient() as client:
            # Search specifically for application confirmations from LinkedIn and employers in past 30 days
            query = 'from:(jobs-noreply@linkedin.com OR linkedin.com OR mailer-daemon) newer_than:30d'
            res = await client.get(
                "https://www.googleapis.com/gmail/v1/users/me/messages",
                params={"q": query, "maxResults": 30},
                headers={"Authorization": f"Bearer {token}"}
            )
            if res.status_code == 200:
                messages = res.json().get("messages", [])
                for m in messages:
                    try:
                        m_res = await client.get(
                            f"https://www.googleapis.com/gmail/v1/users/me/messages/{m['id']}",
                            params={"format": "metadata", "metadataHeaders": ["Subject", "Date", "From"]},
                            headers={"Authorization": f"Bearer {token}"},
                            timeout=5.0
                        )
                        if m_res.status_code == 200:
                            headers = {h["name"]: h["value"] for h in m_res.json().get("payload", {}).get("headers", [])}
                            subject = headers.get("Subject", "")
                            date = headers.get("Date", "")
                            
                            # Pattern 1: "Your application was sent to <Company>"
                            match1 = re.search(r"application was sent to\s+([^,\.\n\r]+)", subject, re.IGNORECASE)
                            if match1:
                                comp = match1.group(1).strip().lower()
                                applied_companies.add(comp)
                                gmail_records.append({"company": comp, "subject": subject, "date": date, "source": "gmail_linkedin"})

                            # Pattern 2: "Your application to <Role> at <Company>"
                            match2 = re.search(r"application to\s+.+\s+at\s+([^,\.\n\r]+)", subject, re.IGNORECASE)
                            if match2:
                                comp = match2.group(1).strip().lower()
                                applied_companies.add(comp)
                                gmail_records.append({"company": comp, "subject": subject, "date": date, "source": "gmail_confirmation"})
                    except Exception:
                        continue

    # 2. Check local DB applications from the last 30 days
    thirty_days_ago = datetime.datetime.utcnow() - datetime.timedelta(days=30)
    db_apps = await db.execute(
        select(Application, Job)
        .join(Job, Application.job_id == Job.id)
        .where(Application.user_id == user_id, Application.created_at >= thirty_days_ago)
    )
    for app, job in db_apps.all():
        if job and job.company:
            comp = job.company.strip().lower()
            applied_companies.add(comp)

    return {
        "applied_company_names": list(applied_companies),
        "total_recent_applications": len(applied_companies),
        "gmail_history": gmail_records
    }
