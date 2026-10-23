"""Application tracking model."""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class Application(Base):
    __tablename__ = "applications"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), default=1)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    
    # Status tracking
    status = Column(String(50), default="discovered", nullable=False)
    # Statuses: discovered, shortlisted, preparing_application, awaiting_approval,
    #           email_sent, application_submitted, follow_up_due, recruiter_replied,
    #           interview_scheduled, rejected, offer_received, withdrawn
    
    # Application details
    applied_via = Column(String(100))  # email, portal, referral
    application_url = Column(String(1000))
    cover_letter = Column(Text)
    custom_resume_id = Column(Integer, ForeignKey("resumes.id"))
    answers = Column(Text)  # JSON: application form answers
    
    # Notes
    notes = Column(Text)
    
    # Follow-up tracking
    follow_up_date = Column(DateTime)
    follow_up_count = Column(Integer, default=0)
    
    # Interview
    interview_date = Column(DateTime)
    interview_type = Column(String(100))  # phone, video, onsite, coding
    interview_notes = Column(Text)
    
    # Response
    response_date = Column(DateTime)
    response_content = Column(Text)
    
    # Offer
    offer_salary = Column(String(100))
    offer_details = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    job = relationship("Job", back_populates="applications")
    status_history = relationship("ApplicationStatusHistory", back_populates="application", cascade="all, delete-orphan")


class ApplicationStatusHistory(Base):
    __tablename__ = "application_status_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    application_id = Column(Integer, ForeignKey("applications.id"), nullable=False)
    
    old_status = Column(String(50))
    new_status = Column(String(50), nullable=False)
    changed_by = Column(String(50), default="user")  # user, system, automation
    notes = Column(Text)
    
    changed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    application = relationship("Application", back_populates="status_history")
