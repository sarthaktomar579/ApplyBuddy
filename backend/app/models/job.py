"""Job listing model."""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Core info
    title = Column(String(500), nullable=False)
    company = Column(String(255), nullable=False)
    location = Column(String(255))
    employment_type = Column(String(100))  # full-time, internship, contract
    work_arrangement = Column(String(50))  # remote, hybrid, on-site
    experience_required = Column(String(100))  # "0-2 years", "Fresher"
    
    # Compensation
    salary_min = Column(Float)
    salary_max = Column(Float)
    salary_currency = Column(String(10), default="INR")
    salary_period = Column(String(20))  # yearly, monthly, hourly
    stipend = Column(String(100))  # For internships
    
    # Details
    description = Column(Text)
    required_skills = Column(Text)  # JSON array
    preferred_skills = Column(Text)  # JSON array
    qualifications = Column(Text)  # JSON array of required qualifications
    responsibilities = Column(Text)  # JSON array
    benefits = Column(Text)  # JSON array
    
    # URLs and tracking
    application_url = Column(String(1000))
    source_url = Column(String(1000))
    canonical_url = Column(String(1000), unique=True)  # For deduplication
    source = Column(String(100))  # "greenhouse", "lever", "manual", "careers_page"
    
    # Dates
    date_posted = Column(DateTime)
    application_deadline = Column(DateTime)
    discovered_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_checked = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Status
    is_active = Column(Boolean, default=True)
    is_expired = Column(Boolean, default=False)
    is_relevant = Column(Boolean, default=True)  # User can mark as irrelevant
    is_bookmarked = Column(Boolean, default=False)
    
    # Recruiter info
    recruiter_name = Column(String(255))
    recruiter_email = Column(String(255))
    recruiter_source = Column(String(500))
    
    # User reference
    user_id = Column(Integer, ForeignKey("users.id"), default=1)
    
    # Relationships
    skills = relationship("JobSkill", back_populates="job", cascade="all, delete-orphan")
    match = relationship("JobMatch", back_populates="job", uselist=False, cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="job", cascade="all, delete-orphan")
    emails = relationship("Email", back_populates="job", cascade="all, delete-orphan")


class JobSkill(Base):
    __tablename__ = "job_skills"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    skill_name = Column(String(100), nullable=False)
    is_required = Column(Boolean, default=True)
    
    job = relationship("Job", back_populates="skills")
