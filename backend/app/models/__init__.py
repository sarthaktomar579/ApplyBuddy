"""
ApplyPilot AI - Database Models
All SQLAlchemy models for the application.
"""
from app.models.user import User
from app.models.profile import Profile, Skill, Experience, Project, Education
from app.models.job import Job, JobSkill
from app.models.application import Application, ApplicationStatusHistory
from app.models.email import Email, EmailAttachment
from app.models.recruiter import Recruiter
from app.models.resume import Resume
from app.models.preferences import JobPreference, PreferredLocation, PreferredRole
from app.models.integration import Integration
from app.models.job_match import JobMatch

__all__ = [
    "User",
    "Profile", "Skill", "Experience", "Project", "Education",
    "Job", "JobSkill",
    "Application", "ApplicationStatusHistory",
    "Email", "EmailAttachment",
    "Recruiter",
    "Resume",
    "JobPreference", "PreferredLocation", "PreferredRole",
    "Integration",
    "JobMatch",
]
