"""Resume storage model."""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from app.core.database import Base


class Resume(Base):
    __tablename__ = "resumes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), default=1)
    
    # File info
    filename = Column(String(255), nullable=False)
    filepath = Column(String(1000), nullable=False)
    file_size = Column(Integer)  # bytes
    mime_type = Column(String(100), default="application/pdf")
    
    # Parsed content
    raw_text = Column(Text)
    parsed_data = Column(Text)  # JSON: structured parsed content
    
    # Resume type
    label = Column(String(255), default="Default Resume")  # User-friendly name
    is_default = Column(Boolean, default=False)
    is_tailored = Column(Boolean, default=False)  # AI-generated tailored version
    tailored_for_job_id = Column(Integer, ForeignKey("jobs.id"))
    
    # Version tracking
    version = Column(Integer, default=1)
    parent_resume_id = Column(Integer, ForeignKey("resumes.id"))
    
    # Timestamps
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
