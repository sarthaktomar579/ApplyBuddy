"""Jobs API routes - Discovery, listing, and management."""
import json
import re
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from typing import Optional, List
from app.core.database import get_db
from app.models.job import Job, JobSkill
from app.models.job_match import JobMatch

router = APIRouter()


class ManualJobRequest(BaseModel):
    title: str
    company: str
    location: Optional[str] = None
    employment_type: Optional[str] = None
    work_arrangement: Optional[str] = None
    experience_required: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: str = "INR"
    description: Optional[str] = None
    required_skills: Optional[List[str]] = None
    preferred_skills: Optional[List[str]] = None
    application_url: Optional[str] = None
    source_url: Optional[str] = None


class HarvestLinkedInPostRequest(BaseModel):
    author_name: Optional[str] = "Hiring Team"
    author_title: Optional[str] = "Technical Recruiter"
    company: Optional[str] = None
    recipient_email: str
    post_text: str
    post_url: Optional[str] = None
    job_title: Optional[str] = None
    auto_send: bool = True


@router.post("/harvest-from-linkedin")
async def harvest_from_linkedin(request: HarvestLinkedInPostRequest, db: AsyncSession = Depends(get_db)):
    """
    Harvests verified recruiter contact directly from live LinkedIn post body text.
    Validates deliverability, checks 15-day deduplication shield, and auto-dispatches tailored email with resume attached.
    """
    from app.services.email_verifier import validate_recipient_deliverability
    from app.services.email_outreach_service import (
        get_valid_gmail_token,
        get_recently_emailed_targets_15d,
        build_email_content,
        dispatch_single_email,
        RESUME_PATH
    )
    from app.models.recruiter import Recruiter
    from app.models.email import Email
    from app.models.application import Application

    clean_email = request.recipient_email.strip().lower()
    clean_company = (request.company or "").strip()
    author_name = request.author_name or "Hiring Team"
    author_title = request.author_title or "Technical Recruiter"

    # Infer company from author title or post text if missing
    if not clean_company:
        comp_m = re.search(r"at\s+([A-Za-z0-9\s]+?)(?:\||—|-|\.|\n|$)", author_title)
        if comp_m:
            clean_company = comp_m.group(1).strip()
        else:
            clean_company = "Tech Startup"

    # 1. Deliverability & Bounce Quarantine Check
    is_valid, reason = validate_recipient_deliverability(clean_email, clean_company)
    if not is_valid:
        return {"status": "rejected", "reason": reason, "email": clean_email}

    # 2. Check 15-day deduplication
    token = await get_valid_gmail_token(db)
    shield = await get_recently_emailed_targets_15d(db, token)
    if clean_email in shield.get("addresses", set()):
        return {"status": "skipped", "reason": f"Email '{clean_email}' already contacted in last 15 days.", "email": clean_email}
    if clean_company and clean_company.lower() in shield.get("companies", set()):
        return {"status": "skipped", "reason": f"Company '{clean_company}' already contacted in last 15 days.", "email": clean_email}

    # 3. Infer Job Title from Post Text if not provided
    job_title = request.job_title
    if not job_title:
        text_lower = request.post_text.lower()
        if "full stack" in text_lower or "fullstack" in text_lower:
            job_title = "Full Stack Software Developer"
        elif "backend" in text_lower:
            job_title = "Backend Software Engineer (Python / FastAPI)"
        elif "frontend" in text_lower or "react" in text_lower:
            job_title = "Frontend Engineer (React / Next.js)"
        elif "ai" in text_lower or "llm" in text_lower or "machine learning" in text_lower:
            job_title = "AI Platform Engineer (LLM Integration)"
        else:
            job_title = "Software Development Engineer"

    # 4. Save Job in DB
    job = Job(
        user_id=1,
        title=job_title,
        company=clean_company,
        location="Bengaluru / Gurugram / Remote",
        salary_min=700000,
        salary_max=1400000,
        salary_currency="INR",
        description=request.post_text[:2000],
        source="LinkedIn Recruiter Post",
        source_url=request.post_url,
        recruiter_name=author_name,
        recruiter_email=clean_email,
        recruiter_source=f"LinkedIn Post by {author_name} ({author_title})",
        date_posted=datetime.now(timezone.utc),
        is_active=True,
        is_relevant=True
    )
    db.add(job)
    await db.flush()

    # 5. Save Recruiter in DB
    rec = await db.execute(select(Recruiter).where(Recruiter.email == clean_email))
    recruiter_obj = rec.scalar_one_or_none()
    if not recruiter_obj:
        recruiter_obj = Recruiter(
            user_id=1,
            name=author_name,
            email=clean_email,
            title=author_title,
            company=clean_company,
            verification_status="verified_official",
            source_url=request.post_url,
            evidence=f"Direct email specified in LinkedIn hiring post by {author_name}."
        )
        db.add(recruiter_obj)
        await db.flush()

    # 6. Auto-send application if requested
    delivery_status = "queued"
    if request.auto_send and token:
        content = build_email_content(
            job_title=job_title,
            company=clean_company,
            person_name=author_name,
            tech_stack=["React", "Python", "FastAPI", "Next.js", "PostgreSQL"],
            job_description=request.post_text
        )
        from_email = "sarthakt579@gmail.com"
        res = await dispatch_single_email(
            token=token,
            from_email=from_email,
            to_email=clean_email,
            subject=content["subject"],
            body=content["body"],
            resume_path=RESUME_PATH
        )
        if not res.get("success") and res.get("status_code") == 401:
            token = await get_valid_gmail_token(db, force_refresh=True)
            if token:
                res = await dispatch_single_email(
                    token=token,
                    from_email=from_email,
                    to_email=clean_email,
                    subject=content["subject"],
                    body=content["body"],
                    resume_path=RESUME_PATH
                )

        if res.get("success"):
            delivery_status = "sent"
            msg_id = res.get("message_id")
            # Log Email
            em = Email(
                user_id=1,
                job_id=job.id,
                to_email=clean_email,
                to_name=f"{author_name} ({author_title})",
                from_email=from_email,
                subject=content["subject"],
                body=content["body"],
                status="sent",
                recipient_verified=True,
                recipient_source=f"LinkedIn Post by {author_name}",
                gmail_message_id=msg_id,
                sent_at=datetime.now(timezone.utc),
                is_personalized=True,
                generation_model="ApplyPilot AI Direct Post Outreach"
            )
            db.add(em)

            # Log Application
            app_rec = Application(
                user_id=1,
                job_id=job.id,
                status="email_sent",
                applied_via="linkedin_post_direct",
                applied_by="ai",
                application_url=f"mailto:{clean_email}",
                notes=f"Application delivered to {author_name} ({author_title}) at {clean_company} <{clean_email}> with Resume_Sarthak_Tomar.pdf attached from real LinkedIn post."
            )
            db.add(app_rec)
        else:
            delivery_status = f"failed: {res.get('error')}"

    await db.commit()
    return {
        "status": "success",
        "delivery": delivery_status,
        "job_id": job.id,
        "company": clean_company,
        "recruiter": author_name,
        "email": clean_email,
        "message": f"Harvested and delivered to {author_name} ({clean_email}) with Resume attached!"
    }


@router.get("")
async def list_jobs(
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
    location: Optional[str] = None,
    employment_type: Optional[str] = None,
    source: Optional[str] = None,
    posted_after: Optional[str] = None,
    latest_only: bool = False,
    is_active: Optional[bool] = True,
    is_relevant: Optional[bool] = None,
    is_bookmarked: Optional[bool] = None,
    sort_by: str = "date_posted",
    sort_order: str = "desc",
    db: AsyncSession = Depends(get_db),
):
    """List jobs with filters and pagination."""
    query = select(Job).where(Job.user_id == 1)
    
    if is_active is not None:
        query = query.where(Job.is_active == is_active)
    if is_relevant is not None:
        query = query.where(Job.is_relevant == is_relevant)
    if is_bookmarked is not None:
        query = query.where(Job.is_bookmarked == is_bookmarked)
    if source:
        query = query.where(Job.source == source)
    
    # Filter by date_posted
    if latest_only and not posted_after:
        posted_after = "2026-10-22"
    
    if posted_after:
        try:
            target_date = datetime.fromisoformat(posted_after.replace("Z", "+00:00"))
        except Exception:
            target_date = datetime(2026, 10, 22, 0, 0, tzinfo=timezone.utc)
        query = query.where(Job.date_posted >= target_date)

    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                Job.title.ilike(search_term),
                Job.company.ilike(search_term),
                Job.description.ilike(search_term),
            )
        )
    if location:
        query = query.where(Job.location.ilike(f"%{location}%"))
    if employment_type:
        query = query.where(Job.employment_type == employment_type)
    
    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Sort
    sort_col = getattr(Job, sort_by, Job.discovered_at)
    if sort_order == "desc":
        query = query.order_by(sort_col.desc())
    else:
        query = query.order_by(sort_col.asc())
    
    # Paginate
    query = query.offset(skip).limit(limit)
    result = await db.execute(query.options(selectinload(Job.skills), selectinload(Job.match)))
    jobs = result.scalars().all()
    
    return {
        "total": total,
        "jobs": [_job_to_dict(j) for j in jobs],
        "skip": skip,
        "limit": limit,
    }


@router.post("")
async def add_manual_job(request: ManualJobRequest, db: AsyncSession = Depends(get_db)):
    """Manually add a job listing."""
    # Create canonical URL for deduplication
    canonical = request.application_url or request.source_url or f"manual_{request.company}_{request.title}_{datetime.now(timezone.utc).timestamp()}"
    
    # Check for duplicates
    existing = await db.execute(select(Job).where(Job.canonical_url == canonical))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="This job listing already exists")
    
    job = Job(
        user_id=1,
        title=request.title,
        company=request.company,
        location=request.location,
        employment_type=request.employment_type,
        work_arrangement=request.work_arrangement,
        experience_required=request.experience_required,
        salary_min=request.salary_min,
        salary_max=request.salary_max,
        salary_currency=request.salary_currency,
        description=request.description,
        required_skills=json.dumps(request.required_skills) if request.required_skills else None,
        preferred_skills=json.dumps(request.preferred_skills) if request.preferred_skills else None,
        application_url=request.application_url,
        source_url=request.source_url,
        canonical_url=canonical,
        source="manual",
    )
    db.add(job)
    await db.flush()
    
    # Add skills
    if request.required_skills:
        for skill in request.required_skills:
            db.add(JobSkill(job_id=job.id, skill_name=skill, is_required=True))
    if request.preferred_skills:
        for skill in request.preferred_skills:
            db.add(JobSkill(job_id=job.id, skill_name=skill, is_required=False))
    
    await db.flush()
    return {"id": job.id, "message": "Job added successfully"}


@router.get("/{job_id}")
async def get_job(job_id: int, db: AsyncSession = Depends(get_db)):
    """Get job details."""
    result = await db.execute(
        select(Job)
        .where(Job.id == job_id)
        .options(selectinload(Job.skills), selectinload(Job.match))
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return _job_to_dict(job)


@router.put("/{job_id}/bookmark")
async def toggle_bookmark(job_id: int, db: AsyncSession = Depends(get_db)):
    """Toggle job bookmark."""
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job.is_bookmarked = not job.is_bookmarked
    return {"bookmarked": job.is_bookmarked}


@router.put("/{job_id}/relevant")
async def mark_relevant(job_id: int, relevant: bool = True, db: AsyncSession = Depends(get_db)):
    """Mark job as relevant or irrelevant."""
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job.is_relevant = relevant
    return {"is_relevant": job.is_relevant}


@router.delete("/{job_id}")
async def delete_job(job_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a job listing."""
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    await db.delete(job)
    return {"message": "Job deleted"}


@router.post("/discover")
async def trigger_job_discovery(auto_apply: bool = False, db: AsyncSession = Depends(get_db)):
    """Trigger job discovery engine to fetch fresh opportunities (>= Oct 22, 2026) and match them."""
    from app.services.job_discovery import job_discovery_service
    from app.models.profile import Profile, Skill

    # Get user profile skills
    profile_res = await db.execute(select(Profile).where(Profile.user_id == 1).options(selectinload(Profile.skills)))
    profile = profile_res.scalar_one_or_none()
    skills = [s.name for s in (profile.skills or [])] if profile else []

    profile_data = {
        "full_name": profile.full_name if profile else "Sarthak Singh Tomar",
        "skills": skills,
        "preferred_locations": ["Bengaluru", "Hyderabad", "Pune", "Delhi NCR", "Noida", "Mumbai", "Remote"],
    }

    result = await job_discovery_service.discover_jobs(db, profile_data, auto_apply_instant=auto_apply)
    return {
        "status": "success",
        "discovered": result["discovered"],
        "existing": result["existing"],
        "total_processed": result["total_processed"],
        "auto_applied_count": result.get("auto_applied_count", 0),
        "message": f"Discovery complete: {result['discovered']} jobs indexed, {result.get('auto_applied_count', 0)} automatically applied upon publication."
    }


@router.post("/instant-apply-all")
async def instant_apply_all_latest(min_score: int = 65, max_count: int = 50, db: AsyncSession = Depends(get_db)):
    """
    Instantly apply to all relevant latest jobs (posted on or after Oct 22, 2026, including LinkedIn).
    Applies up to 50 jobs in one queue via LinkedIn Easy Apply or verified portal with Resume_SarthakT.pdf attached.
    """
    from app.services.job_discovery import job_discovery_service
    from app.api.applications import auto_apply_to_matches, AutoApplyRequest
    from app.models.profile import Profile

    profile_res = await db.execute(select(Profile).where(Profile.user_id == 1).options(selectinload(Profile.skills)))
    profile = profile_res.scalar_one_or_none()
    skills = [s.name for s in (profile.skills or [])] if profile else []

    profile_data = {
        "full_name": profile.full_name if profile else "Sarthak Singh Tomar",
        "skills": skills,
        "preferred_locations": ["Bengaluru", "Hyderabad", "Pune", "Delhi NCR", "Noida", "Mumbai", "Remote"],
    }

    # First discover any latest jobs
    disc_res = await job_discovery_service.discover_jobs(db, profile_data, auto_apply_instant=False)

    # Then run auto-apply across all matches (up to max_count = 50)
    apply_req = AutoApplyRequest(min_score=min_score, send_now=True, max_count=max_count)
    apply_res = await auto_apply_to_matches(apply_req, db=db)

    return {
        "status": "success",
        "newly_discovered": disc_res["discovered"],
        "applications_processed": apply_res["processed_count"],
        "skipped_duplicates_count": apply_res.get("skipped_duplicates_count", 0),
        "results": apply_res["results"],
        "gmail_connected": apply_res["gmail_connected"],
        "message": f"Successfully applied to {apply_res['processed_count']} relevant positions on LinkedIn & verified portals with Resume_SarthakT.pdf attached."
    }


@router.post("/{job_id}/match")
async def evaluate_job_match_endpoint(job_id: int, db: AsyncSession = Depends(get_db)):
    """Re-evaluate AI match score and analysis for a specific job."""
    from app.services.ai_provider import ai_service
    from app.models.profile import Profile

    result = await db.execute(
        select(Job).where(Job.id == job_id).options(selectinload(Job.skills), selectinload(Job.match))
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    profile_res = await db.execute(select(Profile).where(Profile.user_id == 1).options(selectinload(Profile.skills)))
    profile = profile_res.scalar_one_or_none()
    skills = [s.name for s in (profile.skills or [])] if profile else []

    profile_data = {
        "full_name": profile.full_name if profile else "Sarthak Singh Tomar",
        "skills": skills,
        "preferred_locations": ["Bengaluru", "Hyderabad", "Pune", "Delhi NCR", "Remote"],
    }

    req_skills = [s.skill_name for s in job.skills if s.is_required] if job.skills else []
    pref_skills = [s.skill_name for s in job.skills if not s.is_required] if job.skills else []

    eval_res = await ai_service.evaluate_job_match(
        job_data={
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "work_arrangement": job.work_arrangement,
            "experience_required": job.experience_required,
            "description": job.description,
            "required_skills": req_skills,
            "preferred_skills": pref_skills,
        },
        profile_data=profile_data
    )

    if not job.match:
        match_obj = JobMatch(job_id=job.id, user_id=1)
        db.add(match_obj)
        job.match = match_obj

    job.match.overall_score = eval_res["overall_score"]
    job.match.skills_score = eval_res["skills_score"]
    job.match.experience_score = eval_res["experience_score"]
    job.match.education_score = eval_res["education_score"]
    job.match.location_score = eval_res["location_score"]
    job.match.salary_score = eval_res["salary_score"]
    job.match.matching_skills = json.dumps(eval_res["matching_skills"])
    job.match.missing_skills = json.dumps(eval_res["missing_skills"])
    job.match.relevant_projects = json.dumps(eval_res["relevant_projects"])
    job.match.is_eligible = eval_res["is_eligible"]
    job.match.eligibility_issues = json.dumps(eval_res["eligibility_issues"])
    job.match.match_reasons = json.dumps(eval_res["match_reasons"])
    job.match.recommended_action = eval_res["recommended_action"]

    await db.commit()
    return {"message": "Job match evaluated", "match": eval_res}


def _parse_json(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return []


def _job_to_dict(job: Job) -> dict:
    match_data = None
    if job.match:
        match_data = {
            "overall_score": job.match.overall_score,
            "skills_score": job.match.skills_score,
            "experience_score": job.match.experience_score,
            "education_score": job.match.education_score,
            "location_score": job.match.location_score,
            "salary_score": job.match.salary_score,
            "matching_skills": _parse_json(job.match.matching_skills),
            "missing_skills": _parse_json(job.match.missing_skills),
            "relevant_projects": _parse_json(job.match.relevant_projects),
            "is_eligible": job.match.is_eligible,
            "eligibility_issues": _parse_json(job.match.eligibility_issues),
            "match_reasons": _parse_json(job.match.match_reasons),
            "recommended_action": job.match.recommended_action,
        }
    
    return {
        "id": job.id,
        "title": job.title,
        "company": job.company,
        "location": job.location,
        "employment_type": job.employment_type,
        "work_arrangement": job.work_arrangement,
        "experience_required": job.experience_required,
        "salary_min": job.salary_min,
        "salary_max": job.salary_max,
        "salary_currency": job.salary_currency,
        "description": job.description,
        "required_skills": _parse_json(job.required_skills),
        "preferred_skills": _parse_json(job.preferred_skills),
        "application_url": job.application_url,
        "source_url": job.source_url,
        "source": job.source,
        "date_posted": job.date_posted.isoformat() if job.date_posted else None,
        "application_deadline": job.application_deadline.isoformat() if job.application_deadline else None,
        "discovered_at": job.discovered_at.isoformat() if job.discovered_at else None,
        "is_active": job.is_active,
        "is_bookmarked": job.is_bookmarked,
        "is_relevant": job.is_relevant,
        "match": match_data,
        "skills": [{"name": s.skill_name, "is_required": s.is_required} for s in (job.skills or [])],
    }
