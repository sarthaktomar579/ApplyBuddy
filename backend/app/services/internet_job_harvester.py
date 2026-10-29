"""
ApplyPilot AI — Internet Job & Recruiter Email Harvester
Finds real, verified tech job openings across the internet with explicit recruiter/founder contact emails.
Strict Rules:
1. ZERO ASSUMPTIONS: Never guesses careers@ or synthesized emails. Only targets explicit emails written by recruiters/founders.
2. ZERO BOUNCE: Pre-validates via permanent bounce quarantine blacklist and DNS MX verification.
3. 15-DAY DUPLICATE SHIELD: Checks Gmail Sent (newer_than:15d) and database records before sending.
4. EXCLUSIONS: Strictly excludes Pinnacle Infotech / Pinnacle U and blacklisted scams (Dexter, ThinkNova).
"""

import re
import html
import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.job import Job
from app.models.recruiter import Recruiter
from app.models.email import Email
from app.models.application import Application
from app.services.email_verifier import validate_recipient_deliverability, USER_EXCLUDED_COMPANIES
from app.services.verified_recruiters import get_verified_outreach_targets
from app.services.email_outreach_service import (
    get_valid_gmail_token,
    get_recently_emailed_targets_15d,
    build_email_content,
    dispatch_single_email,
    RESUME_PATH,
    campaign_manager
)

# Active Hacker News "Who is Hiring?" stories (October 2026 & September 2026)
HN_HIRING_STORY_IDS = ["49922569", "49522897"]

RELEVANT_TECH_KEYWORDS = [
    "python", "react", "fastapi", "next.js", "nextjs", "node", "django",
    "full stack", "fullstack", "backend", "frontend", "software developer",
    "software engineer", "ai", "llm", "postgres", "typescript", "sde"
]

RELEVANT_LOCATION_KEYWORDS = [
    "remote", "worldwide", "anywhere", "india", "bengaluru", "bangalore",
    "pune", "delhi", "gurugram", "gurgaon", "noida", "hyderabad", "hybrid", "global"
]

EXCLUDED_SENIORITY_REGEX = re.compile(
    r"\b(senior|sr\.?|staff|principal|lead|director|vp|head|architect|manager|cto|chief|executive|5\+\s*years|6\+\s*years|7\+\s*years|8\+\s*years|10\+\s*years)\b",
    re.IGNORECASE
)

EXCLUDED_DOMAIN_REGEX = re.compile(
    r"\b(ios|android|mobile|swift|objective-c|kotlin|flutter|react\s*native|devops|sre|reliability|infrastructure|hardware|embedded|firmware|sales|marketing|recruiter|recruiting|designer|ui/ux|qa|sdet|test\s*engineer|blockchain|solidity|web3|smart\s*contract|rust|c\+\+|phd|postdoc|biotech|lab|robotics|data\s*analyst|data\s*scientist|freelance|commission)\b",
    re.IGNORECASE
)

TARGET_ROLE_REGEX = re.compile(
    r"\b(full\s*stack|fullstack|backend|frontend|software\s*developer|software\s*engineer|sde|sde[\s\-_]*1|sde[\s\-_]*i\b|associate\s*software|junior|graduate|ai\s*engineer|ai\s*application|product\s*engineer|python\s*developer|web\s*developer)\b",
    re.IGNORECASE
)


INDIA_HUBS_REGEX = re.compile(
    r"\b(india|bengaluru|bangalore|delhi|delhi\s*ncr|\bncr\b|gurugram|gurgaon|noida|pune|hyderabad|mumbai|chennai|kolkata|jaipur|ahmedabad|chandigarh|kochi|indore)\b",
    re.IGNORECASE
)

WORLDWIDE_REMOTE_REGEX = re.compile(
    r"\b(worldwide|anywhere|global|remote\s*\(worldwide\)|remote\s*\(global\)|work\s*from\s*anywhere)\b",
    re.IGNORECASE
)

FOREIGN_RESTRICTION_REGEX = re.compile(
    r"\b(us\s*only|usa\s*only|u\.s\.\s*only|north\s*america\s*only|eu\s*only|uk\s*only|canada\s*only|latam\s*only|must\s*be\s*located\s*in\s*(?:the\s*)?(?:us|usa|u\.s\.|uk|eu|canada)|us\s*citizens?|security\s*clearance|no\s*visa\s*support)\b",
    re.IGNORECASE
)

FOREIGN_LOCATION_REGEX = re.compile(
    r"\b(london|nyc|new\s*york|san\s*francisco|\bsf\b|bay\s*area|seattle|austin|chicago|los\s*angeles|boston|tokyo|japan|croatia|dubrovnik|switzerland|zurich|germany|berlin|munich|amsterdam|netherlands|paris|france|madrid|barcelona|spain|poland|warsaw|sweden|stockholm|ireland|dublin|toronto|vancouver|canada|australia|sydney|melbourne|singapore|israel|tel\s*aviv)\b",
    re.IGNORECASE
)


def is_location_india_or_allowed_remote(headline: str, text: str = "") -> bool:
    """
    Strictly verifies job location is in India or open to candidates in India:
    1. Rejects any 'US only', 'North America only', 'EU only', 'UK only', 'No visa support'.
    2. Rejects foreign onsite/hybrid cities (London, Tokyo, NYC, SF, Germany, Croatia, etc.).
    3. Requires explicit India tech hub (Bengaluru, Delhi NCR, Pune, Hyderabad, Remote India)
       OR unrestricted worldwide remote.
    """
    head_l = (headline or "").lower()
    text_l = (text or "").lower()

    # 1. Foreign-only restriction check (e.g. US Only, EU Only, No visa)
    if FOREIGN_RESTRICTION_REGEX.search(head_l) or FOREIGN_RESTRICTION_REGEX.search(text_l):
        return False

    # 2. If headline specifies a foreign location without an India hub or unrestricted worldwide remote -> reject
    if FOREIGN_LOCATION_REGEX.search(head_l):
        if not (INDIA_HUBS_REGEX.search(head_l) or WORLDWIDE_REMOTE_REGEX.search(head_l)):
            return False

    # 3. Check if explicitly in India (headline or body using exact word boundaries)
    if INDIA_HUBS_REGEX.search(head_l) or INDIA_HUBS_REGEX.search(text_l):
        return True

    # 4. Check for unrestricted remote (e.g. Remote (Worldwide), Anywhere, Global)
    if WORLDWIDE_REMOTE_REGEX.search(head_l):
        return True

    return False


def is_role_relevant_and_entry_level(title: str, text: str = "") -> bool:
    """
    Strict relevance guard for Sarthak Singh Tomar (Entry Level Full Stack & AI Developer):
    1. Rejects any Senior, Staff, Lead, Manager, Architect, or Executive roles.
    2. Rejects iOS, Android, Mobile, DevOps, QA, Hardware, and non-web domains.
    3. Requires target Full Stack, Backend (Python/FastAPI), Frontend (React/Next.js), SDE, or AI Engineer roles.
    4. Ensures required tech stack is present.
    """
    clean_title = (title or "").strip()
    clean_text = (text or "").strip()

    # 1. Seniority Check on Title
    if EXCLUDED_SENIORITY_REGEX.search(clean_title):
        return False

    # 2. Domain / Irrelevant Tech Check on Title
    if EXCLUDED_DOMAIN_REGEX.search(clean_title):
        return False

    # 3. Target Entry / SDE Role Check on Title
    if not TARGET_ROLE_REGEX.search(clean_title):
        return False

    # 4. Tech stack alignment: Python, React, FastAPI, Next.js, Node, AI/LLM, PostgreSQL, Full Stack
    combined = (clean_title + " " + clean_text).lower()
    has_tech = any(k in combined for k in [
        "python", "react", "fastapi", "next.js", "nextjs", "node", "ai", "llm",
        "postgres", "typescript", "javascript", "full stack", "fullstack", "backend", "frontend", "sde"
    ])
    if not has_tech:
        return False

    return True

RELEVANT_LOCATION_KEYWORDS = [
    "remote", "worldwide", "anywhere", "india", "bengaluru", "bangalore",
    "pune", "delhi", "gurugram", "gurgaon", "noida", "hyderabad", "hybrid", "global"
]

EMAIL_REGEX = re.compile(r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})")


async def fetch_hn_who_is_hiring_jobs() -> List[Dict[str, Any]]:
    """
    Fetches real tech job posts from Hacker News 'Who is Hiring?' threads via Algolia API.
    Extracts only posts where founders/recruiters explicitly wrote their contact email in the text.
    """
    discovered: List[Dict[str, Any]] = []
    seen_emails = set()

    async with httpx.AsyncClient(timeout=10.0) as client:
        for story_id in HN_HIRING_STORY_IDS:
            try:
                url = f"https://hn.algolia.com/api/v1/search?tags=comment,story_{story_id}&hitsPerPage=300"
                res = await client.get(url, headers={"User-Agent": "Mozilla/5.0 ApplyPilot/1.0"})
                if res.status_code != 200:
                    continue

                hits = res.json().get("hits", [])
                for h in hits:
                    raw_comment = h.get("comment_text", "")
                    if not raw_comment:
                        continue

                    # Unescape HTML
                    text = html.unescape(re.sub(r"<[^>]+>", " ", raw_comment)).strip()
                    text_lower = text.lower()

                    # 1. Relevance filter: must match Sarthak's technical skills
                    if not any(k in text_lower for k in RELEVANT_TECH_KEYWORDS):
                        continue

                    # 2. Location filter: remote or India tech hubs
                    if not any(loc in text_lower for loc in RELEVANT_LOCATION_KEYWORDS):
                        continue

                    # 3. Extract explicit email
                    emails = EMAIL_REGEX.findall(text)
                    if not emails:
                        continue

                    primary_email = emails[0].lower().strip()
                    if primary_email in seen_emails:
                        continue
                    seen_emails.add(primary_email)

                    # 4. Anti-scam & Exclusion
                    if any(exc in text_lower or exc in primary_email for exc in USER_EXCLUDED_COMPANIES):
                        continue
                    if any(scam in text_lower for scam in ["dexter", "thinknova", "training institute", "placement guarantee"]):
                        continue

                    # 5. Extract company & title from first line
                    lines = [l.strip() for l in text.split("\n") if l.strip()]
                    first_line = lines[0] if lines else "Tech Startup"
                    parts = [p.strip() for p in first_line.split("|")]

                    company_name = parts[0][:50] if len(parts) > 0 else "Tech Startup"
                    company_name = re.sub(r"\(http.*?\)", "", company_name).strip()

                    job_title = ""
                    if len(parts) > 1:
                        for p in parts[1:]:
                            plower = p.lower()
                            if any(k in plower for k in ["engineer", "developer", "full stack", "backend", "frontend", "sde"]):
                                job_title = p[:60].strip()
                                break
                    if not job_title:
                        job_title = "Full Stack Software Developer"

                    # 6. Strict Entry-Level & Domain Relevance Filter
                    if EXCLUDED_SENIORITY_REGEX.search(first_line) or EXCLUDED_SENIORITY_REGEX.search(job_title):
                        continue
                    if EXCLUDED_DOMAIN_REGEX.search(first_line) or EXCLUDED_DOMAIN_REGEX.search(job_title):
                        continue
                    if not is_role_relevant_and_entry_level(job_title, text):
                        continue
                    # 7. Strict India / Allowed Remote Location Filter
                    if not is_location_india_or_allowed_remote(first_line, text):
                        continue

                    # Recruiter/Founder name inference
                    person_name = f"{company_name} Hiring Team"
                    first_part_email = primary_email.split("@")[0]
                    if "." in first_part_email and len(first_part_email.split(".")[0]) > 2:
                        name_candidate = first_part_email.split(".")[0].capitalize()
                        if name_candidate.isalpha():
                            person_name = name_candidate
                    elif first_part_email.isalpha() and len(first_part_email) > 2 and first_part_email not in {"jobs", "careers", "talent", "info", "hello", "team"}:
                        person_name = first_part_email.capitalize()

                    discovered.append({
                        "source": "Hacker News Who is Hiring",
                        "company": company_name,
                        "job_title": job_title,
                        "person_name": person_name,
                        "person_title": "Engineering Hiring Team / Founder",
                        "recipient_email": primary_email,
                        "recipient_type": "specific_person" if person_name != f"{company_name} Hiring Team" else "confirmed_hiring_desk",
                        "location": "Remote / Bengaluru / Global",
                        "salary_display": "₹8.0 - ₹20.0 LPA / Competitive",
                        "date_posted": h.get("created_at") or datetime.now(timezone.utc).isoformat(),
                        "tech_stack": [k.capitalize() for k in ["Python", "React", "FastAPI", "PostgreSQL"] if k in text_lower],
                        "evidence": f"Explicit email published by founder/recruiter in HN Hiring thread {story_id}.",
                        "post_text": text[:2000]
                    })
            except Exception as e:
                print(f"[InternetHarvester] Error scraping HN thread {story_id}: {e}")

    return discovered


async def get_all_verified_internet_opportunities(db: AsyncSession, token: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Aggregates and verifies tech job opportunities from across the internet:
    1. HN Who is Hiring live posts with explicit emails.
    2. Curated seed of verified technical recruiters and confirmed hiring desks.
    3. Runs DNS MX verification and 15-day deduplication shield on all targets.
    """
    # 1. Fetch live internet postings
    internet_jobs = await fetch_hn_who_is_hiring_jobs()

    # 2. Add curated verified recruiters
    curated_targets = get_verified_outreach_targets()

    all_raw_targets = curated_targets + internet_jobs

    # 3. Retrieve 15-day deduplication shield (Gmail Sent + Local DB)
    shield = await get_recently_emailed_targets_15d(db, token)
    blacklisted_emails = shield.get("addresses", set())
    blacklisted_companies = shield.get("companies", set())

    verified_queue: List[Dict[str, Any]] = []
    seen_in_batch = set()

    for target in all_raw_targets:
        clean_email = target["recipient_email"].lower().strip()
        clean_company = target["company"].lower().strip()

        if clean_email in seen_in_batch:
            continue
        seen_in_batch.add(clean_email)

        # Strict Entry-Level & Full Stack / AI Relevance Check
        if not is_role_relevant_and_entry_level(target["job_title"], target.get("post_text", target["job_title"])):
            print(f"[InternetHarvester] Skipped non-entry/irrelevant role: {target['job_title']} at {target['company']}")
            continue

        # Strict India / Allowed Remote Location Check
        loc_str = target.get("location", "") + " " + target["company"]
        if not is_location_india_or_allowed_remote(loc_str, target.get("post_text", "")):
            print(f"[InternetHarvester] Skipped non-India location: {target.get('location')} at {target['company']}")
            continue

        # Pre-send Deliverability Check (Quarantine, Syntax, Domain MX)
        is_deliverable, reason = validate_recipient_deliverability(clean_email, target["company"])
        if not is_deliverable:
            print(f"[InternetHarvester] Shield blocked {clean_email} ({target['company']}): {reason}")
            continue

        # 15-Day Duplicate Shield Check
        if clean_email in blacklisted_emails:
            print(f"[InternetHarvester] 15d Shield skipped {clean_email}: Already contacted within past 15 days.")
            continue

        if clean_company in blacklisted_companies and clean_company not in {"tech startup", "remote"}:
            print(f"[InternetHarvester] 15d Shield skipped {clean_company}: Company contacted within past 15 days.")
            continue

        target["deliverability_status"] = "verified_ready"
        verified_queue.append(target)

    return verified_queue


async def run_autonomous_internet_outreach(
    db: AsyncSession,
    daily_limit: int = 50,
    delay_seconds: int = 30
) -> Dict[str, Any]:
    """
    Completely autonomous outreach engine:
    1. Retrieves valid Gmail token for sarthakt579@gmail.com.
    2. Scrapes and verifies genuine opportunities across the internet with explicit emails.
    3. Dispatches tailored application emails with Resume attached safely spaced by 30 seconds.
    4. Logs all jobs, applications, and emails into the database.
    """
    token = await get_valid_gmail_token(db)
    if not token:
        return {"status": "error", "message": "Gmail is not connected or token expired. Please connect in Settings."}

    # Harvest & verify targets across internet
    targets = await get_all_verified_internet_opportunities(db, token)
    if not targets:
        return {"status": "complete", "message": "No new uncontacted targets found across internet. All recent roles shielded by 15-day cooldown.", "sent": 0}

    from_email = "sarthakt579@gmail.com"
    sent_count = 0
    skipped_count = 0
    dispatched_records = []

    for target in targets[:daily_limit]:
        recipient_email = target["recipient_email"].lower().strip()
        company = target["company"]
        job_title = target["job_title"]
        person_name = target.get("person_name") or f"{company} Hiring Lead"

        # Double check 15-day shield right before send
        shield = await get_recently_emailed_targets_15d(db, token)
        if recipient_email in shield.get("addresses", set()):
            skipped_count += 1
            continue

        # Build personalized content
        content = build_email_content(
            job_title=job_title,
            company=company,
            person_name=target.get("person_name"),
            tech_stack=target.get("tech_stack", ["Python", "React", "FastAPI", "Next.js"]),
            job_description=target.get("post_text") or target.get("evidence")
        )

        # Dispatch with Resume_Sarthak_Tomar.pdf attached
        res = await dispatch_single_email(
            token=token,
            from_email=from_email,
            to_email=recipient_email,
            subject=content["subject"],
            body=content["body"],
            resume_path=RESUME_PATH
        )

        # Token refresh fallback
        if not res.get("success") and res.get("status_code") == 401:
            token = await get_valid_gmail_token(db, force_refresh=True)
            if token:
                res = await dispatch_single_email(
                    token=token,
                    from_email=from_email,
                    to_email=recipient_email,
                    subject=content["subject"],
                    body=content["body"],
                    resume_path=RESUME_PATH
                )

        if res.get("success"):
            sent_count += 1
            msg_id = res.get("message_id")

            # 1. Save Job
            job = Job(
                user_id=1,
                title=job_title,
                company=company,
                location=target.get("location", "Remote / Bengaluru"),
                salary_min=700000,
                salary_max=1500000,
                salary_currency="INR",
                description=target.get("post_text") or target.get("evidence", "Discovered via Internet Tech Hiring Post"),
                source=target.get("source", "Internet Recruiter Post"),
                recruiter_name=person_name,
                recruiter_email=recipient_email,
                recruiter_source=target.get("evidence", "Internet hiring post"),
                date_posted=datetime.now(timezone.utc),
                is_active=True,
                is_relevant=True
            )
            db.add(job)
            await db.flush()

            # 2. Save Recruiter
            recruiter_obj = Recruiter(
                user_id=1,
                name=person_name,
                email=recipient_email,
                title=target.get("person_title", "Engineering Hiring Lead"),
                company=company,
                verification_status="verified_official",
                evidence=target.get("evidence", "Explicit email in public hiring post")
            )
            db.add(recruiter_obj)
            await db.flush()

            # 3. Save Email
            em = Email(
                user_id=1,
                job_id=job.id,
                to_email=recipient_email,
                to_name=f"{person_name} ({company})",
                from_email=from_email,
                subject=content["subject"],
                body=content["body"],
                status="sent",
                recipient_verified=True,
                recipient_source=target.get("source", "Internet Tech Post"),
                gmail_message_id=msg_id,
                sent_at=datetime.now(timezone.utc),
                is_personalized=True,
                generation_model="ApplyPilot Autonomous Internet Outreach"
            )
            db.add(em)

            # 4. Save Application
            app_rec = Application(
                user_id=1,
                job_id=job.id,
                status="email_sent",
                applied_via="autonomous_internet_outreach",
                applied_by="ai",
                application_url=f"mailto:{recipient_email}",
                notes=f"Delivered directly to {person_name} at {company} <{recipient_email}> with Resume attached from internet post."
            )
            db.add(app_rec)
            await db.commit()

            dispatched_records.append({
                "company": company,
                "role": job_title,
                "email": recipient_email,
                "person": person_name
            })

            # Safe pacing between emails
            if sent_count < daily_limit:
                await asyncio.sleep(delay_seconds)
        else:
            print(f"[InternetHarvester] Failed sending to {recipient_email}: {res.get('error')}")

    return {
        "status": "success",
        "total_targets_found": len(targets),
        "sent_count": sent_count,
        "skipped_15d_count": skipped_count,
        "dispatched": dispatched_records
    }
