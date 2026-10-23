"""Profile API routes."""
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from typing import Optional, List
from app.core.database import get_db
from app.models.profile import Profile, Skill, Experience, Project, Education

router = APIRouter()


# ── Pydantic Schemas ──────────────────────────────────────────────────────────

class SkillSchema(BaseModel):
    id: Optional[int] = None
    category: str
    name: str
    proficiency: Optional[str] = None

class ExperienceSchema(BaseModel):
    id: Optional[int] = None
    company: str
    role: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None
    highlights: Optional[List[str]] = None
    technologies: Optional[List[str]] = None

class ProjectSchema(BaseModel):
    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    problem: Optional[str] = None
    solution: Optional[str] = None
    impact: Optional[str] = None
    technologies: Optional[List[str]] = None
    github_url: Optional[str] = None
    live_url: Optional[str] = None
    is_highlight: bool = False

class EducationSchema(BaseModel):
    id: Optional[int] = None
    institution: str
    degree: str
    field_of_study: Optional[str] = None
    graduation_year: Optional[int] = None
    gpa: Optional[str] = None
    achievements: Optional[List[str]] = None

class ProfileResponse(BaseModel):
    id: int
    full_name: str
    email: str
    phone: Optional[str] = None
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    degree: Optional[str] = None
    college: Optional[str] = None
    graduation_year: Optional[int] = None
    summary: Optional[str] = None
    strongest_areas: Optional[List[str]] = None
    dsa_problems_solved: int = 0
    leetcode_rating: Optional[str] = None
    codechef_rating: Optional[str] = None
    skills: List[SkillSchema] = []
    experiences: List[ExperienceSchema] = []
    projects: List[ProjectSchema] = []
    education_entries: List[EducationSchema] = []

class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    degree: Optional[str] = None
    college: Optional[str] = None
    graduation_year: Optional[int] = None
    summary: Optional[str] = None
    strongest_areas: Optional[List[str]] = None
    dsa_problems_solved: Optional[int] = None
    leetcode_rating: Optional[str] = None
    codechef_rating: Optional[str] = None
    skills: Optional[List[SkillSchema]] = None
    experiences: Optional[List[ExperienceSchema]] = None
    projects: Optional[List[ProjectSchema]] = None
    education_entries: Optional[List[EducationSchema]] = None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_json_field(value):
    """Parse a JSON string field to a list."""
    if value is None:
        return None
    if isinstance(value, list):
        return value
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return None


def _profile_to_response(profile: Profile) -> dict:
    """Convert a Profile ORM object to a response dict."""
    return {
        "id": profile.id,
        "full_name": profile.full_name,
        "email": profile.email,
        "phone": profile.phone,
        "github_url": profile.github_url,
        "linkedin_url": profile.linkedin_url,
        "portfolio_url": profile.portfolio_url,
        "degree": profile.degree,
        "college": profile.college,
        "graduation_year": profile.graduation_year,
        "summary": profile.summary,
        "strongest_areas": _parse_json_field(profile.strongest_areas),
        "dsa_problems_solved": profile.dsa_problems_solved or 0,
        "leetcode_rating": profile.leetcode_rating,
        "codechef_rating": profile.codechef_rating,
        "skills": [
            {"id": s.id, "category": s.category, "name": s.name, "proficiency": s.proficiency}
            for s in profile.skills
        ],
        "experiences": [
            {
                "id": e.id, "company": e.company, "role": e.role,
                "start_date": e.start_date, "end_date": e.end_date,
                "description": e.description,
                "highlights": _parse_json_field(e.highlights),
                "technologies": _parse_json_field(e.technologies),
            }
            for e in profile.experiences
        ],
        "projects": [
            {
                "id": p.id, "name": p.name, "description": p.description,
                "problem": p.problem, "solution": p.solution, "impact": p.impact,
                "technologies": _parse_json_field(p.technologies),
                "github_url": p.github_url, "live_url": p.live_url,
                "is_highlight": p.is_highlight,
            }
            for p in profile.projects
        ],
        "education_entries": [
            {
                "id": ed.id, "institution": ed.institution, "degree": ed.degree,
                "field_of_study": ed.field_of_study, "graduation_year": ed.graduation_year,
                "gpa": ed.gpa, "achievements": _parse_json_field(ed.achievements),
            }
            for ed in profile.education_entries
        ],
    }


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("")
async def get_profile(db: AsyncSession = Depends(get_db)):
    """Get the user's profile with all related data."""
    result = await db.execute(
        select(Profile)
        .where(Profile.user_id == 1)
        .options(
            selectinload(Profile.skills),
            selectinload(Profile.experiences),
            selectinload(Profile.projects),
            selectinload(Profile.education_entries),
        )
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    return _profile_to_response(profile)


@router.put("")
async def update_profile(request: ProfileUpdateRequest, db: AsyncSession = Depends(get_db)):
    """Update the user's profile."""
    result = await db.execute(
        select(Profile)
        .where(Profile.user_id == 1)
        .options(
            selectinload(Profile.skills),
            selectinload(Profile.experiences),
            selectinload(Profile.projects),
            selectinload(Profile.education_entries),
        )
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    # Update scalar fields
    update_data = request.model_dump(exclude_unset=True, exclude={"skills", "experiences", "projects", "education_entries"})
    for key, value in update_data.items():
        if key == "strongest_areas" and isinstance(value, list):
            setattr(profile, key, json.dumps(value))
        else:
            setattr(profile, key, value)
    
    # Update skills if provided
    if request.skills is not None:
        # Clear existing
        for s in profile.skills:
            await db.delete(s)
        # Add new
        for skill in request.skills:
            db.add(Skill(
                profile_id=profile.id,
                category=skill.category,
                name=skill.name,
                proficiency=skill.proficiency,
            ))
    
    # Update experiences if provided
    if request.experiences is not None:
        for e in profile.experiences:
            await db.delete(e)
        for exp in request.experiences:
            db.add(Experience(
                profile_id=profile.id,
                company=exp.company,
                role=exp.role,
                start_date=exp.start_date,
                end_date=exp.end_date,
                description=exp.description,
                highlights=json.dumps(exp.highlights) if exp.highlights else None,
                technologies=json.dumps(exp.technologies) if exp.technologies else None,
            ))
    
    # Update projects if provided
    if request.projects is not None:
        for p in profile.projects:
            await db.delete(p)
        for proj in request.projects:
            db.add(Project(
                profile_id=profile.id,
                name=proj.name,
                description=proj.description,
                problem=proj.problem,
                solution=proj.solution,
                impact=proj.impact,
                technologies=json.dumps(proj.technologies) if proj.technologies else None,
                github_url=proj.github_url,
                live_url=proj.live_url,
                is_highlight=proj.is_highlight,
            ))
    
    # Update education if provided
    if request.education_entries is not None:
        for ed in profile.education_entries:
            await db.delete(ed)
        for edu in request.education_entries:
            db.add(Education(
                profile_id=profile.id,
                institution=edu.institution,
                degree=edu.degree,
                field_of_study=edu.field_of_study,
                graduation_year=edu.graduation_year,
                gpa=edu.gpa,
                achievements=json.dumps(edu.achievements) if edu.achievements else None,
            ))
    
    await db.flush()
    
    # Reload profile
    result = await db.execute(
        select(Profile)
        .where(Profile.user_id == 1)
        .options(
            selectinload(Profile.skills),
            selectinload(Profile.experiences),
            selectinload(Profile.projects),
            selectinload(Profile.education_entries),
        )
    )
    profile = result.scalar_one_or_none()
    return _profile_to_response(profile)
