"""Profile, skills, experience, projects, and education models."""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base


class Profile(Base):
    __tablename__ = "profiles"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Personal info
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(50))
    github_url = Column(String(500))
    linkedin_url = Column(String(500))
    portfolio_url = Column(String(500))
    
    # Education summary
    degree = Column(String(255))
    college = Column(String(500))
    graduation_year = Column(Integer)
    
    # Professional summary
    summary = Column(Text)
    strongest_areas = Column(Text)  # JSON string of areas
    
    # Competitive programming
    dsa_problems_solved = Column(Integer, default=0)
    leetcode_rating = Column(String(100))
    codechef_rating = Column(String(100))
    other_achievements = Column(Text)  # JSON string
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    skills = relationship("Skill", back_populates="profile", cascade="all, delete-orphan")
    experiences = relationship("Experience", back_populates="profile", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="profile", cascade="all, delete-orphan")
    education_entries = relationship("Education", back_populates="profile", cascade="all, delete-orphan")


class Skill(Base):
    __tablename__ = "skills"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False)
    category = Column(String(100), nullable=False)  # e.g., "Programming Languages", "Frontend"
    name = Column(String(100), nullable=False)
    proficiency = Column(String(50))  # beginner, intermediate, advanced, expert
    
    profile = relationship("Profile", back_populates="skills")


class Experience(Base):
    __tablename__ = "experiences"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False)
    
    company = Column(String(255), nullable=False)
    role = Column(String(255), nullable=False)
    start_date = Column(String(50))  # "June 2026"
    end_date = Column(String(50))    # "September 2026" or "Present"
    description = Column(Text)
    highlights = Column(Text)  # JSON array of key responsibilities
    technologies = Column(Text)  # JSON array of tech used
    
    profile = relationship("Profile", back_populates="experiences")


class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False)
    
    name = Column(String(255), nullable=False)
    description = Column(Text)
    problem = Column(Text)
    solution = Column(Text)
    impact = Column(Text)
    technologies = Column(Text)  # JSON array
    github_url = Column(String(500))
    live_url = Column(String(500))
    is_highlight = Column(Boolean, default=False)  # Featured project
    
    profile = relationship("Profile", back_populates="projects")


class Education(Base):
    __tablename__ = "education"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False)
    
    institution = Column(String(500), nullable=False)
    degree = Column(String(255), nullable=False)
    field_of_study = Column(String(255))
    graduation_year = Column(Integer)
    gpa = Column(String(20))
    achievements = Column(Text)  # JSON array
    
    profile = relationship("Profile", back_populates="education_entries")
