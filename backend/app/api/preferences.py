"""Job preferences API routes."""
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from typing import Optional, List
from app.core.database import get_db
from app.models.preferences import JobPreference, PreferredLocation, PreferredRole

router = APIRouter()


class LocationSchema(BaseModel):
    city: str
    state: Optional[str] = None
    country: str = "India"

class RoleSchema(BaseModel):
    title: str
    priority: int = 1

class PreferencesResponse(BaseModel):
    id: int
    experience_level: str
    min_experience_years: int
    max_experience_years: int
    min_salary_lpa: float
    max_salary_lpa: float
    accept_unpaid: bool
    remote_ok: bool
    hybrid_ok: bool
    onsite_ok: bool
    willing_to_relocate: bool
    full_time: bool
    internship: bool
    contract: bool
    weight_skills: int
    weight_experience: int
    weight_location: int
    weight_salary: int
    weight_company: int
    preferred_locations: List[LocationSchema]
    preferred_roles: List[RoleSchema]

class PreferencesUpdateRequest(BaseModel):
    experience_level: Optional[str] = None
    min_experience_years: Optional[int] = None
    max_experience_years: Optional[int] = None
    min_salary_lpa: Optional[float] = None
    max_salary_lpa: Optional[float] = None
    accept_unpaid: Optional[bool] = None
    remote_ok: Optional[bool] = None
    hybrid_ok: Optional[bool] = None
    onsite_ok: Optional[bool] = None
    willing_to_relocate: Optional[bool] = None
    full_time: Optional[bool] = None
    internship: Optional[bool] = None
    contract: Optional[bool] = None
    weight_skills: Optional[int] = None
    weight_experience: Optional[int] = None
    weight_location: Optional[int] = None
    weight_salary: Optional[int] = None
    weight_company: Optional[int] = None
    preferred_locations: Optional[List[LocationSchema]] = None
    preferred_roles: Optional[List[RoleSchema]] = None


def _pref_to_response(pref: JobPreference) -> dict:
    return {
        "id": pref.id,
        "experience_level": pref.experience_level,
        "min_experience_years": pref.min_experience_years,
        "max_experience_years": pref.max_experience_years,
        "min_salary_lpa": pref.min_salary_lpa,
        "max_salary_lpa": pref.max_salary_lpa,
        "accept_unpaid": pref.accept_unpaid,
        "remote_ok": pref.remote_ok,
        "hybrid_ok": pref.hybrid_ok,
        "onsite_ok": pref.onsite_ok,
        "willing_to_relocate": pref.willing_to_relocate,
        "full_time": pref.full_time,
        "internship": pref.internship,
        "contract": pref.contract,
        "weight_skills": pref.weight_skills,
        "weight_experience": pref.weight_experience,
        "weight_location": pref.weight_location,
        "weight_salary": pref.weight_salary,
        "weight_company": pref.weight_company,
        "preferred_locations": [
            {"city": loc.city, "state": loc.state, "country": loc.country}
            for loc in pref.preferred_locations
        ],
        "preferred_roles": [
            {"title": r.title, "priority": r.priority}
            for r in pref.preferred_roles
        ],
    }


@router.get("")
async def get_preferences(db: AsyncSession = Depends(get_db)):
    """Get job preferences."""
    result = await db.execute(
        select(JobPreference)
        .where(JobPreference.user_id == 1)
        .options(
            selectinload(JobPreference.preferred_locations),
            selectinload(JobPreference.preferred_roles),
        )
    )
    pref = result.scalar_one_or_none()
    if not pref:
        raise HTTPException(status_code=404, detail="Preferences not found")
    return _pref_to_response(pref)


@router.put("")
async def update_preferences(request: PreferencesUpdateRequest, db: AsyncSession = Depends(get_db)):
    """Update job preferences."""
    result = await db.execute(
        select(JobPreference)
        .where(JobPreference.user_id == 1)
        .options(
            selectinload(JobPreference.preferred_locations),
            selectinload(JobPreference.preferred_roles),
        )
    )
    pref = result.scalar_one_or_none()
    if not pref:
        raise HTTPException(status_code=404, detail="Preferences not found")
    
    # Update scalar fields
    update_data = request.model_dump(exclude_unset=True, exclude={"preferred_locations", "preferred_roles"})
    for key, value in update_data.items():
        setattr(pref, key, value)
    
    # Update locations if provided
    if request.preferred_locations is not None:
        for loc in pref.preferred_locations:
            await db.delete(loc)
        for loc in request.preferred_locations:
            db.add(PreferredLocation(
                preference_id=pref.id,
                city=loc.city,
                state=loc.state,
                country=loc.country,
            ))
    
    # Update roles if provided
    if request.preferred_roles is not None:
        for r in pref.preferred_roles:
            await db.delete(r)
        for role in request.preferred_roles:
            db.add(PreferredRole(
                preference_id=pref.id,
                title=role.title,
                priority=role.priority,
            ))
    
    await db.flush()
    
    # Reload
    result = await db.execute(
        select(JobPreference)
        .where(JobPreference.user_id == 1)
        .options(
            selectinload(JobPreference.preferred_locations),
            selectinload(JobPreference.preferred_roles),
        )
    )
    pref = result.scalar_one_or_none()
    return _pref_to_response(pref)
