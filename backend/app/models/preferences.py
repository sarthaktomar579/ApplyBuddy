"""Job preference models."""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class JobPreference(Base):
    __tablename__ = "job_preferences"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, default=1)
    
    # Experience level
    experience_level = Column(String(100), default="fresher")  # fresher, entry_level, 0-2_years, internship
    min_experience_years = Column(Integer, default=0)
    max_experience_years = Column(Integer, default=2)
    
    # Compensation
    min_salary_lpa = Column(Float, default=5.0)
    max_salary_lpa = Column(Float, default=6.0)
    accept_unpaid = Column(Boolean, default=False)
    
    # Work arrangement
    remote_ok = Column(Boolean, default=True)
    hybrid_ok = Column(Boolean, default=True)
    onsite_ok = Column(Boolean, default=True)
    willing_to_relocate = Column(Boolean, default=True)
    
    # Employment type
    full_time = Column(Boolean, default=True)
    internship = Column(Boolean, default=True)
    contract = Column(Boolean, default=False)
    
    # Matching weights (0-100)
    weight_skills = Column(Integer, default=35)
    weight_experience = Column(Integer, default=20)
    weight_location = Column(Integer, default=15)
    weight_salary = Column(Integer, default=15)
    weight_company = Column(Integer, default=15)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    preferred_locations = relationship("PreferredLocation", back_populates="preference", cascade="all, delete-orphan")
    preferred_roles = relationship("PreferredRole", back_populates="preference", cascade="all, delete-orphan")


class PreferredLocation(Base):
    __tablename__ = "preferred_locations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    preference_id = Column(Integer, ForeignKey("job_preferences.id"), nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(100))
    country = Column(String(100), default="India")
    
    preference = relationship("JobPreference", back_populates="preferred_locations")


class PreferredRole(Base):
    __tablename__ = "preferred_roles"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    preference_id = Column(Integer, ForeignKey("job_preferences.id"), nullable=False)
    title = Column(String(255), nullable=False)
    priority = Column(Integer, default=1)  # 1 = highest priority
    
    preference = relationship("JobPreference", back_populates="preferred_roles")
