"""Recruiter and HR contact model."""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime
from app.core.database import Base


class Recruiter(Base):
    __tablename__ = "recruiters"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, default=1)
    
    # Contact info
    name = Column(String(255))
    email = Column(String(255), nullable=False)
    phone = Column(String(50))
    title = Column(String(255))  # e.g., "Technical Recruiter"
    department = Column(String(100))  # e.g., "Talent Acquisition"
    
    # Company
    company = Column(String(255), nullable=False)
    
    # Verification
    verification_status = Column(String(50), default="unverified")
    # Statuses: verified_official, publicly_listed, unverified, not_found
    source_url = Column(String(1000))  # Where we found this contact
    evidence = Column(Text)  # Description of how we verified
    
    # Association
    associated_job_ids = Column(Text)  # JSON array of job IDs
    
    # Tracking
    emails_sent_count = Column(Integer, default=0)
    last_contacted = Column(DateTime)
    last_verified = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
