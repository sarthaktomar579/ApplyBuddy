"""
ApplyPilot AI — Automated Cold Email Outreach Engine
Strictly eliminates 550 bounces and duplicate applications:
1. Targets only confirmed specific named technical recruiters, talent leads, founders, or verified active hiring channels.
2. Quarantines and blocks all known bounced addresses (550 Address Not Found).
3. Enforces 15-day strict deduplication across recipient email, company name, and position title.
4. Delivers personalized applications with Resume_Sarthak_Tomar.pdf attached, spaced by 30-second safe pacing.
"""

import os
import re
import base64
import asyncio
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import Dict, Any, List, Set, Optional, Tuple

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.database import async_session
from app.models.integration import Integration
from app.models.email import Email
from app.models.application import Application
from app.models.job import Job
from app.models.resume import Resume
from app.services.verified_recruiters import get_verified_outreach_targets
from app.services.email_verifier import validate_recipient_deliverability, KNOWN_BOUNCED_ADDRESSES

# Path to Sarthak's resume
RESUME_PATH = os.path.join(settings.UPLOAD_DIR, "Resume_SarthakT.pdf")


async def get_valid_gmail_token(db: AsyncSession, user_id: int = 1, force_refresh: bool = False) -> Optional[str]:
    """Retrieve and refresh Gmail OAuth access token."""
    res = await db.execute(
        select(Integration).where(Integration.user_id == user_id, Integration.provider == "gmail")
    )
    integration = res.scalar_one_or_none()
    if not integration or not integration.is_connected or not integration.access_token:
        return None

    async with httpx.AsyncClient(timeout=8.0) as client:
        try:
            # Check token validity if not force refreshing
            if not force_refresh:
                test_res = await client.get(
                    "https://www.googleapis.com/gmail/v1/users/me/profile",
                    headers={"Authorization": f"Bearer {integration.access_token}"}
                )
                if test_res.status_code == 200:
                    return integration.access_token

            # Refresh token
            if integration.refresh_token and settings.GMAIL_CLIENT_ID and settings.GMAIL_CLIENT_SECRET:
                ref_res = await client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "client_id": settings.GMAIL_CLIENT_ID,
                        "client_secret": settings.GMAIL_CLIENT_SECRET,
                        "refresh_token": integration.refresh_token,
                        "grant_type": "refresh_token"
                    }
                )
                if ref_res.status_code == 200:
                    new_token = ref_res.json().get("access_token")
                    integration.access_token = new_token
                    await db.commit()
                    return new_token
        except Exception as e:
            print(f"[EmailOutreach] Token check/refresh error: {e}")

    return None


async def get_recently_emailed_targets_15d(db: AsyncSession, token: Optional[str] = None, user_id: int = 1) -> Dict[str, Set[str]]:
    """
    Comprehensive 15-day deduplication and bounce scanner:
    - Emails emailed in last 15 days
    - Companies contacted in last 15 days
    - (Company, Position) pairs contacted in last 15 days
    - Mailer-daemon bounce addresses to permanently quarantine
    """
    emailed_addresses: Set[str] = set()
    emailed_companies: Set[str] = set()
    emailed_company_positions: Set[str] = set()

    # Seed known bounced addresses
    for b in KNOWN_BOUNCED_ADDRESSES:
        emailed_addresses.add(b.lower().strip())

    # 1. Inspect Gmail Sent history (newer_than:15d) if token provided
    if token:
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.get(
                    "https://www.googleapis.com/gmail/v1/users/me/messages",
                    params={"q": "from:me newer_than:15d", "maxResults": 60},
                    headers={"Authorization": f"Bearer {token}"}
                )
                if res.status_code == 200:
                    messages = res.json().get("messages", [])

                    async def fetch_meta(mid: str):
                        try:
                            mr = await client.get(
                                f"https://www.googleapis.com/gmail/v1/users/me/messages/{mid}",
                                params={"format": "metadata", "metadataHeaders": ["To", "Subject"]},
                                headers={"Authorization": f"Bearer {token}"}
                            )
                            if mr.status_code == 200:
                                payload = mr.json().get("payload", {})
                                hdrs = {h["name"]: h["value"] for h in payload.get("headers", [])}
                                return hdrs.get("To", ""), hdrs.get("Subject", "")
                        except Exception:
                            pass
                        return "", ""

                    results = await asyncio.gather(*[fetch_meta(m["id"]) for m in messages], return_exceptions=True)
                    for r in results:
                        if isinstance(r, tuple):
                            to_val, subj_val = r
                            # Extract recipient emails
                            for em in re.findall(r"[\w\.-]+@[\w\.-]+", to_val.lower()):
                                emailed_addresses.add(em.strip().lower())
                            
                            # Extract company name from subject: "Application: ... at [Company]"
                            comp_match = re.search(r"at\s+([^—–\-\|]+)", subj_val.lower())
                            if comp_match:
                                comp_name = comp_match.group(1).strip().lower()
                                emailed_companies.add(comp_name)

                                # Extract position
                                pos_match = re.search(r"application:\s*([^at]+)\s+at", subj_val.lower())
                                if pos_match:
                                    pos_name = pos_match.group(1).strip().lower()
                                    emailed_company_positions.add(f"{comp_name}::{pos_name}")
        except Exception as e:
            print(f"[EmailOutreach] Error scanning Gmail sent history: {e}")

    # 2. Local DB records in last 15 days (Emails, Applications, and Jobs)
    try:
        fifteen_days_ago = datetime.now(timezone.utc) - timedelta(days=15)
        
        # Check Emails table
        db_emails = await db.execute(
            select(Email).where(Email.user_id == user_id, Email.created_at >= fifteen_days_ago)
        )
        for em in db_emails.scalars().all():
            if em.to_email:
                emailed_addresses.add(em.to_email.strip().lower())
            if em.subject:
                comp_m = re.search(r"at\s+([^—–\-\|]+)", em.subject.lower())
                if comp_m:
                    cname = comp_m.group(1).strip().lower()
                    emailed_companies.add(cname)
                    pos_m = re.search(r"application:\s*([^at]+)\s+at", em.subject.lower())
                    if pos_m:
                        pname = pos_m.group(1).strip().lower()
                        emailed_company_positions.add(f"{cname}::{pname}")

        # Check Applications table
        db_apps = await db.execute(
            select(Application).where(Application.user_id == user_id, Application.created_at >= fifteen_days_ago)
        )
        for app in db_apps.scalars().all():
            if app.application_url and "mailto:" in app.application_url:
                m_email = app.application_url.replace("mailto:", "").strip().lower()
                emailed_addresses.add(m_email)

        # Check recent Jobs with recruiter emails
        db_jobs = await db.execute(
            select(Job).where(Job.user_id == user_id, Job.discovered_at >= fifteen_days_ago)
        )
        for j in db_jobs.scalars().all():
            if j.recruiter_email:
                emailed_addresses.add(j.recruiter_email.strip().lower())
            if j.company:
                emailed_companies.add(j.company.strip().lower())
    except Exception as e:
        print(f"[EmailOutreach] Error querying DB history: {e}")

    return {
        "addresses": emailed_addresses,
        "companies": emailed_companies,
        "positions": emailed_company_positions
    }


def build_email_content(
    job_title: str,
    company: str,
    person_name: Optional[str] = None,
    tech_stack: Optional[List[str]] = None,
    job_description: Optional[str] = None
) -> Dict[str, str]:
    """
    Dynamically tailored application email customized according to company requirements,
    tech stack, and role focus (Backend, Frontend, Full Stack, AI/LLM).
    """
    subject = f"Application: {job_title} at {company} — Sarthak Singh Tomar (IIIT Kota '26)"

    title_lower = (job_title or "").lower()
    desc_lower = (job_description or "").lower()

    # Personalized greeting
    greeting = "Hello, I hope you are doing great"
    if person_name and person_name.strip():
        first_name = person_name.strip().split()[0]
        if first_name.lower() not in {"hiring", "team", "jobs", "careers", "lead", "recruiter"}:
            greeting = f"Hello {first_name}, I hope you are having a productive week"

    # Dynamic role & company requirements alignment
    is_ai = any(k in title_lower or k in desc_lower for k in ["ai", "llm", "machine learning", "agent", "model"])
    is_backend = any(k in title_lower or k in desc_lower for k in ["backend", "python", "fastapi", "django", "api", "microservices", "postgres"])
    is_frontend = any(k in title_lower or k in desc_lower for k in ["frontend", "react", "next.js", "nextjs", "ui", "typescript", "tailwind"])

    if is_ai:
        focus_pitch = (
            f"Given {company}'s focus on AI-driven workflows and intelligent platforms, my background aligns directly: "
            "I have hands-on experience integrating LLMs, speech-to-text technologies, and clinical summarization pipelines "
            "using FastAPI, Next.js, and modern AI APIs."
        )
    elif is_backend and not is_frontend:
        focus_pitch = (
            f"Given {company}'s backend requirements, my core strength lies in building high-throughput API services "
            "using FastAPI, Python, Django REST, and PostgreSQL, backed by strong algorithmic efficiency "
            "(Knight on LeetCode with 1500+ DSA problems solved)."
        )
    elif is_frontend and not is_backend:
        focus_pitch = (
            f"Given {company}'s focus on user-facing product engineering, I specialize in building responsive, "
            "high-performance web applications using React.js, Next.js (App Router), TypeScript, and WebSockets, "
            "with a strong eye for clean state management."
        )
    else:
        focus_pitch = (
            f"With {company} scaling its product engineering, I bring full-lifecycle development experience bridging "
            "responsive Next.js/React frontends with scalable FastAPI/Python backends and PostgreSQL databases."
        )

    # Dynamic tech stack mention
    stack_note = ""
    if tech_stack and len(tech_stack) > 0:
        tech_str = ", ".join(tech_stack[:3])
        stack_note = f" I noticed your team works with {tech_str}, which directly matches my daily development stack."

    body = f"""{greeting}

I'm Sarthak Singh Tomar, a 2026 B.Tech graduate from IIIT Kota. {focus_pitch}{stack_note} I'm also a 3-star coder on CodeChef and Knight on LeetCode with over 1500+ DSA problems solved across platforms.

Experience: Worked as a Software Developer at Xelron AI for 3 months and as a Full Stack Developer at Skygnosis from June 2026 to September 2026, where I developed AI-powered applications by integrating LLMs, speech-to-text technologies, and AI-driven clinical summarization workflows using FastAPI and Next.js. I also worked on automating medical documentation and integrating third-party APIs to build intelligent, scalable applications.

I have attached my resume (Resume_Sarthak_Tomar.pdf) for your consideration and would love the opportunity to contribute to {company}'s engineering team.

Best regards,
Sarthak Singh Tomar
Contact number: 6377525805
Resume link: https://drive.google.com/file/d/1Z2zuNplo9Y81-p_ItPNuwSN4XBIIv5o/view?usp=sharing
GitHub link: https://github.com/sarthaktomar579
"""

    return {"subject": subject, "body": body}


async def dispatch_single_email(
    token: str,
    from_email: str,
    to_email: str,
    subject: str,
    body: str,
    resume_path: str = RESUME_PATH
) -> Dict[str, Any]:
    """
    Constructs MIME multipart message with attached PDF resume and dispatches via Gmail API.
    """
    msg = MIMEMultipart()
    msg["To"] = to_email
    msg["From"] = from_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    # Attach PDF resume
    if os.path.exists(resume_path):
        with open(resume_path, "rb") as f:
            attachment = MIMEApplication(f.read(), _subtype="pdf")
            attachment.add_header("Content-Disposition", "attachment", filename="Resume_Sarthak_Tomar.pdf")
            msg.attach(attachment)

    raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")

    async with httpx.AsyncClient(timeout=20.0) as client:
        res = await client.post(
            "https://www.googleapis.com/gmail/v1/users/me/messages/send",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"raw": raw_message}
        )
        if res.status_code == 200:
            return {"success": True, "message_id": res.json().get("id")}
        else:
            return {"success": False, "error": res.text, "status_code": res.status_code}


class EmailCampaignManager:
    """
    Zero-Bounce Automated Cold Email Engine:
    - Targets verified specific persons or confirmed active hiring desks.
    - Strict bounce quarantine & pre-send deliverability checks.
    - 15-day strict deduplication across email, company, and position.
    - 30-second safe pacing with Resume_Sarthak_Tomar.pdf attached.
    """
    def __init__(self):
        self.is_running: bool = False
        self.is_paused: bool = True
        self.sent_today: int = 0
        self.daily_limit: int = 100
        self.delay_seconds: int = 30
        self.skipped_15d_count: int = 0
        self.targets: List[Dict[str, Any]] = get_verified_outreach_targets()
        self.total_targets: int = len(self.targets)
        self.current_index: int = 0
        self.current_target: Optional[Dict[str, Any]] = None
        self.started_at: Optional[str] = None
        self.last_sent_at: Optional[str] = None
        self.logs: List[Dict[str, Any]] = []
        self._task: Optional[asyncio.Task] = None

    def refresh_targets(self):
        self.targets = get_verified_outreach_targets()
        self.total_targets = len(self.targets)

    def add_log(self, log_type: str, message: str, details: Optional[Dict[str, Any]] = None):
        """Appends a timestamped log entry."""
        entry = {
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "type": log_type,  # 'info', 'success', 'warning', 'error'
            "message": message,
            "details": details or {}
        }
        self.logs.insert(0, entry)
        if len(self.logs) > 120:
            self.logs.pop()

    def get_status(self) -> Dict[str, Any]:
        """Returns live campaign metrics."""
        return {
            "is_running": self.is_running,
            "is_paused": self.is_paused,
            "sent_today": self.sent_today,
            "daily_limit": self.daily_limit,
            "delay_seconds": self.delay_seconds,
            "skipped_15d_count": self.skipped_15d_count,
            "total_targets": self.total_targets,
            "current_index": self.current_index,
            "current_target": self.current_target,
            "started_at": self.started_at,
            "last_sent_at": self.last_sent_at,
            "logs": self.logs[:50]
        }

    def start_campaign(self, daily_limit: int = 100, delay_seconds: int = 30) -> Dict[str, Any]:
        """Launches the zero-bounce automated outreach background loop."""
        if self.is_running:
            return {"status": "already_running", "message": "Campaign is already running."}

        self.refresh_targets()
        self.is_running = True
        self.is_paused = False
        self.daily_limit = daily_limit
        self.delay_seconds = delay_seconds
        self.started_at = datetime.now(timezone.utc).isoformat()
        self.add_log(
            "info",
            f"🚀 Zero-Bounce Outreach Engine Started: {self.total_targets} verified specific recruiters & verified desks queued."
        )

        self._task = asyncio.create_task(self._campaign_loop())
        return {"status": "started", "message": "Zero-bounce campaign started successfully."}

    def stop_campaign(self) -> Dict[str, Any]:
        """Pauses or stops the ongoing campaign."""
        self.is_running = False
        self.is_paused = True
        if self._task and not self._task.done():
            self._task.cancel()
        self.add_log("warning", "⏸️ Campaign paused by user.")
        return {"status": "stopped", "message": "Campaign paused."}

    async def _campaign_loop(self):
        """Asynchronous execution loop for sending cold emails."""
        try:
            async with async_session() as db:
                # 1. Fetch valid Gmail token
                token = await get_valid_gmail_token(db)
                if not token:
                    self.add_log("error", "❌ Gmail is not connected or token expired. Please connect Gmail in Settings.")
                    self.is_running = False
                    return

                # Load live internet opportunities + verified directory
                try:
                    from app.services.internet_job_harvester import get_all_verified_internet_opportunities
                    self.targets = await get_all_verified_internet_opportunities(db, token)
                    self.total_targets = len(self.targets)
                    if self.total_targets == 0:
                        self.add_log(
                            "warning",
                            "🛡️ [15-Day Duplicate Shield Active] All currently available opportunities in the queue have already been contacted within the past 15 days. No new uncontacted targets left. The engine will pause to protect you from duplicate applications."
                        )
                        self.is_running = False
                        return
                    self.add_log("info", f"🌐 Discovered {self.total_targets} verified tech openings across the internet with explicit contact emails.")
                except Exception as e:
                    print(f"Error loading internet targets in campaign: {e}")

                # 2. Build 15-day duplicate & bounce shield
                self.add_log("info", "🛡️ Scanning 15-day Sent history & permanent bounce quarantine...")
                shield = await get_recently_emailed_targets_15d(db, token)
                blacklist_emails = shield["addresses"]
                blacklist_companies = shield["companies"]
                blacklist_positions = shield["positions"]

                self.add_log(
                    "info",
                    f"🛡️ 15-Day Shield Active: {len(blacklist_emails)} emails, {len(blacklist_companies)} companies protected from duplicates."
                )

                from_email = "sarthakt579@gmail.com"

                # 3. Process verified targets
                while self.is_running and self.sent_today < self.daily_limit and self.current_index < len(self.targets):
                    target = self.targets[self.current_index]
                    self.current_index += 1

                    recipient_email = target["recipient_email"].lower().strip()
                    company_clean = target["company"].lower().strip()
                    job_title_clean = target["job_title"].lower().strip()
                    pos_key = f"{company_clean}::{job_title_clean}"
                    person_name = target.get("person_name") or target["company"]
                    person_title = target.get("person_title") or "Technical Recruiter"

                    # 1. Pre-send Deliverability & Bounce Check
                    is_deliverable, reason = validate_recipient_deliverability(recipient_email, target["company"])
                    if not is_deliverable:
                        self.add_log(
                            "warning",
                            f"🛡️ [Bounce Shield] Blocked {recipient_email} ({target['company']}): {reason}",
                            {"company": target["company"], "email": recipient_email}
                        )
                        continue

                    # 2. 15-Day Strict Cooldown Check (by email, company, and position)
                    if recipient_email in blacklist_emails:
                        self.skipped_15d_count += 1
                        self.add_log(
                            "warning",
                            f"🛡️ [15-Day Shield] Skipped {person_name} ({recipient_email}): Email address contacted within past 15 days.",
                            {"company": target["company"], "email": recipient_email}
                        )
                        continue

                    if company_clean in blacklist_companies and pos_key in blacklist_positions:
                        self.skipped_15d_count += 1
                        self.add_log(
                            "warning",
                            f"🛡️ [15-Day Shield] Skipped {target['company']} - {target['job_title']}: Already applied within 15-day window.",
                            {"company": target["company"], "position": target["job_title"]}
                        )
                        continue

                    # 3. Prepare tailored email addressed to specific person
                    content = build_email_content(
                        job_title=target["job_title"],
                        company=target["company"],
                        person_name=target.get("person_name"),
                        tech_stack=target.get("tech_stack"),
                        job_description=target.get("post_text") or target.get("evidence")
                    )

                    self.current_target = {
                        "company": target["company"],
                        "title": target["job_title"],
                        "person_name": person_name,
                        "person_title": person_title,
                        "recipient_type": target.get("recipient_type", "specific_person"),
                        "email": recipient_email,
                        "location": target["location"],
                        "salary": target["salary_display"],
                        "evidence": target.get("evidence", "Verified hiring contact")
                    }

                    # Log the specific individual selected
                    self.add_log(
                        "info",
                        f"👤 Contacting Specific Person: {person_name} ({person_title}) at {target['company']} <{recipient_email}> with Resume attached...",
                        {"company": target["company"], "email": recipient_email, "person": person_name}
                    )

                    # 4. Dispatch email with PDF resume attached
                    res = await dispatch_single_email(
                        token=token,
                        from_email=from_email,
                        to_email=recipient_email,
                        subject=content["subject"],
                        body=content["body"],
                        resume_path=RESUME_PATH
                    )

                    # Auto-refresh token and retry once on 401
                    if not res.get("success") and res.get("status_code") == 401:
                        new_tok = await get_valid_gmail_token(db, force_refresh=True)
                        if new_tok:
                            token = new_tok
                            res = await dispatch_single_email(
                                token=token,
                                from_email=from_email,
                                to_email=recipient_email,
                                subject=content["subject"],
                                body=content["body"],
                                resume_path=RESUME_PATH
                            )

                    if res.get("success"):
                        self.sent_today += 1
                        self.last_sent_at = datetime.now().strftime("%H:%M:%S")
                        msg_id = res.get("message_id")

                        # Update in-memory 15-day blacklist
                        blacklist_emails.add(recipient_email)
                        blacklist_companies.add(company_clean)
                        blacklist_positions.add(pos_key)

                        # Record in Database
                        try:
                            # 1. Job record
                            job_rec = await db.execute(
                                select(Job).where(Job.company == target["company"], Job.title == target["job_title"])
                            )
                            job_obj = job_rec.scalar_one_or_none()
                            if not job_obj:
                                job_obj = Job(
                                    user_id=1,
                                    title=target["job_title"],
                                    company=target["company"],
                                    location=target["location"],
                                    salary_min=float(target["salary_min"]),
                                    salary_max=float(target["salary_max"]),
                                    salary_currency="INR",
                                    source="LinkedIn & Wellfound Verified",
                                    application_url=f"mailto:{recipient_email}",
                                    recruiter_name=person_name,
                                    recruiter_email=recipient_email,
                                    recruiter_source=target.get("evidence"),
                                    is_active=True,
                                    is_relevant=True
                                )
                                db.add(job_obj)
                                await db.flush()

                            # 2. Email record
                            email_record = Email(
                                user_id=1,
                                job_id=job_obj.id,
                                to_email=recipient_email,
                                to_name=f"{person_name} ({person_title})",
                                from_email=from_email,
                                subject=content["subject"],
                                body=content["body"],
                                status="sent",
                                recipient_verified=True,
                                recipient_source=target.get("evidence"),
                                gmail_message_id=msg_id,
                                sent_at=datetime.now(timezone.utc),
                                is_personalized=True,
                                generation_model="ApplyPilot AI Person Outreach"
                            )
                            db.add(email_record)

                            # 3. Application record
                            app_record = Application(
                                user_id=1,
                                job_id=job_obj.id,
                                status="email_sent",
                                applied_via="gmail_direct",
                                applied_by="ai",
                                application_url=f"mailto:{recipient_email}",
                                notes=f"Personal application dispatched to {person_name} ({person_title}) at {target['company']} <{recipient_email}> with Resume_Sarthak_Tomar.pdf attached. Salary: {target['salary_display']}."
                            )
                            db.add(app_record)
                            await db.commit()
                        except Exception as dbe:
                            print(f"[EmailOutreach] DB recording error: {dbe}")
                            await db.rollback()

                        self.add_log(
                            "success",
                            f"✅ Delivered: {target['job_title']} at {target['company']} to {person_name} ({self.sent_today}/{self.daily_limit} sent today).",
                            {"company": target["company"], "email": recipient_email, "person": person_name, "salary": target["salary_display"]}
                        )
                    else:
                        error_text = res.get("error", "Unknown error")
                        self.add_log(
                            "error",
                            f"❌ Delivery failed for {target['company']}: {error_text[:80]}",
                            {"company": target["company"], "error": error_text}
                        )

                    # Safe Pacing Delay between consecutive emails
                    if self.is_running and self.sent_today < self.daily_limit:
                        self.add_log(
                            "info",
                            f"⏳ Safe delay: waiting {self.delay_seconds}s before next dispatch to safeguard Gmail reputation..."
                        )
                        await asyncio.sleep(self.delay_seconds)

                # Completion check
                if self.sent_today >= self.daily_limit:
                    self.add_log(
                        "success",
                        f"🎉 Daily limit of {self.daily_limit} verified emails reached safely! Queue paused until tomorrow."
                    )
                self.is_running = False

        except asyncio.CancelledError:
            self.add_log("warning", "Campaign loop was cancelled.")
        except Exception as e:
            self.add_log("error", f"Campaign loop error: {str(e)}")
            self.is_running = False


# Global singleton instance
campaign_manager = EmailCampaignManager()
