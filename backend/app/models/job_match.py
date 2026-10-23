"""Job match score model."""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class JobMatch(Base):
    __tablename__ = "job_matches"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), default=1)
    job_id = Column(Integer, ForeignKey("jobs.id"), unique=True, nullable=False)
    
    # Overall score
    overall_score = Column(Float, nullable=False)  # 0-100
    
    # Component scores
    skills_score = Column(Float, default=0)
    experience_score = Column(Float, default=0)
    education_score = Column(Float, default=0)
    location_score = Column(Float, default=0)
    salary_score = Column(Float, default=0)
    
    # Analysis
    matching_skills = Column(Text)      # JSON array
    missing_skills = Column(Text)       # JSON array
    relevant_projects = Column(Text)    # JSON array of project names
    relevant_experience = Column(Text)  # JSON array
    
    # Eligibility
    is_eligible = Column(Boolean, default=True)
    eligibility_issues = Column(Text)   # JSON array of issues
    
    # Explanation
    match_reasons = Column(Text)        # JSON array of why it matches
    recommended_action = Column(String(255))  # "Apply immediately", "Review requirements"
    
    # AI model used
    scored_by = Column(String(100))     # "gemini-1.5-flash", "manual"
    
    # Timestamps
    scored_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationship
    job = relationship("Job", back_populates="match")
