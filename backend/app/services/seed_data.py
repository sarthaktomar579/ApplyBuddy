"""
Seed data service - Prepopulates the database with Sarthak's profile.
"""
import json
from sqlalchemy import select
from app.core.database import async_session
from app.core.security import hash_password
from app.models.user import User
from app.models.profile import Profile, Skill, Experience, Project, Education
from app.models.preferences import JobPreference, PreferredLocation, PreferredRole


async def seed_default_user():
    """Create default user and profile if not exists."""
    async with async_session() as session:
        # Check if default user exists
        result = await session.execute(select(User).where(User.id == 1))
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            # Check if jobs exist
            from app.models.job import Job
            job_check = await session.execute(select(Job).limit(1))
            if not job_check.scalar_one_or_none():
                from app.services.recruiter_finder import recruiter_finder_service
                from app.services.job_discovery import job_discovery_service
                await recruiter_finder_service.seed_initial_recruiters(session)
                profile_data = {
                    "full_name": "Sarthak Singh Tomar",
                    "skills": ["C++", "Python", "JavaScript", "React", "Next.js", "FastAPI", "Node.js", "PostgreSQL", "Docker", "WebSockets"],
                    "preferred_locations": ["Bengaluru", "Hyderabad", "Pune", "Delhi NCR", "Remote"],
                }
                await job_discovery_service.discover_jobs(session, profile_data)
            return
        
        # Create default user
        user = User(
            id=1,
            email="sarthakt579@gmail.com",
            hashed_password=hash_password("applypilot2026"),
            is_active=True,
        )
        session.add(user)
        await session.flush()
        
        # Create profile
        profile = Profile(
            user_id=1,
            full_name="Sarthak Singh Tomar",
            email="sarthakt579@gmail.com",
            phone="+91-6377525805",
            github_url="https://github.com/sarthaktomar579",
            degree="B.Tech in Electronics and Communication Engineering",
            college="Indian Institute of Information Technology, Kota",
            graduation_year=2026,
            summary="Full-stack developer with hands-on experience building AI-powered applications. "
                     "Experienced in end-to-end development using React, Next.js, Node.js, FastAPI, Django, "
                     "and cloud services. Strong problem-solving skills with 1500+ DSA problems solved.",
            strongest_areas=json.dumps([
                "End-to-end full-stack development",
                "API integration",
                "Real-time applications",
                "AI-powered products",
                "Problem-solving"
            ]),
            dsa_problems_solved=1500,
            leetcode_rating="Knight",
            codechef_rating="3-Star",
        )
        session.add(profile)
        await session.flush()
        
        # Skills
        skills_data = [
            # Programming Languages
            ("Programming Languages", "C++", "advanced"),
            ("Programming Languages", "Python", "advanced"),
            ("Programming Languages", "JavaScript", "advanced"),
            ("Programming Languages", "SQL", "intermediate"),
            # Frontend
            ("Frontend", "React", "advanced"),
            ("Frontend", "Next.js", "advanced"),
            ("Frontend", "Tailwind CSS", "advanced"),
            # Backend
            ("Backend", "Node.js", "advanced"),
            ("Backend", "Express.js", "advanced"),
            ("Backend", "Django REST Framework", "advanced"),
            ("Backend", "FastAPI", "advanced"),
            # Databases
            ("Databases", "PostgreSQL", "advanced"),
            ("Databases", "MongoDB", "intermediate"),
            ("Databases", "MySQL", "intermediate"),
            # Other
            ("Other Technologies", "REST APIs", "advanced"),
            ("Other Technologies", "WebSockets", "advanced"),
            ("Other Technologies", "Web Audio API", "intermediate"),
            ("Other Technologies", "LLM Integration", "advanced"),
            ("Other Technologies", "Google Gemini API", "advanced"),
            ("Other Technologies", "Deepgram", "intermediate"),
            ("Other Technologies", "Soniox", "intermediate"),
            ("Other Technologies", "Docker", "intermediate"),
            ("Other Technologies", "Git & GitHub", "advanced"),
            ("Other Technologies", "AWS Deployment", "intermediate"),
            ("Other Technologies", "CI/CD Pipelines", "intermediate"),
        ]
        for category, name, proficiency in skills_data:
            session.add(Skill(profile_id=profile.id, category=category, name=name, proficiency=proficiency))
        
        # Experience
        exp1 = Experience(
            profile_id=profile.id,
            company="Skygnosis",
            role="Full Stack Developer",
            start_date="June 2026",
            end_date="September 2026",
            description="Worked on AI-powered applications using Next.js, React, FastAPI, LLMs, speech-to-text technologies, and third-party APIs.",
            highlights=json.dumps([
                "Building full-stack applications from frontend to backend",
                "Integrating Deepgram, Soniox, and LLM-based clinical summarization workflows",
                "Developing AI-assisted medical documentation and structured reporting",
                "Building real-time streaming workflows using WebSockets",
                "Working with PostgreSQL, Supabase, and external APIs"
            ]),
            technologies=json.dumps(["Next.js", "React", "FastAPI", "LLMs", "Deepgram", "Soniox", "WebSockets", "PostgreSQL", "Supabase"])
        )
        session.add(exp1)
        
        exp2 = Experience(
            profile_id=profile.id,
            company="Xelron AI",
            role="Software Development Engineer Intern",
            start_date="March 2026",
            end_date="June 2026",
            description="Worked on AI model evaluation and benchmark development.",
            highlights=json.dumps([
                "Developing benchmark tasks to evaluate AI models",
                "Building deterministic verification workflows",
                "Working with Dockerized environments and CI/CD",
                "Contributing through GitHub repositories and pull requests"
            ]),
            technologies=json.dumps(["Python", "Docker", "CI/CD", "Git", "GitHub"])
        )
        session.add(exp2)
        
        # Projects
        project1 = Project(
            profile_id=profile.id,
            name="AI Medical Reporting Platform — Skygnosis",
            problem="Doctors had to switch constantly between the application and their hospital EHR software while dictating patient findings. This disrupted consultations. A typical floating browser interface could not remain visible over another browser tab because of normal browser security restrictions.",
            solution="Implemented a floating mini-player using the browser's Document Picture-in-Picture API and React Portals. When a doctor switches to the EHR tab during recording, the application can launch a compact, always-on-top window. Audio continues streaming through WebSockets without interrupting the recording workflow.",
            impact="The solution helped doctors dictate findings while using their existing EHR workflow, reducing screen disruption and documentation effort.",
            technologies=json.dumps(["React", "Document Picture-in-Picture API", "React Portals", "WebSockets", "Real-time Audio Streaming"]),
            is_highlight=True,
        )
        session.add(project1)
        
        project2 = Project(
            profile_id=profile.id,
            name="AI Saraj — AI Technical Interview Platform",
            description="An AI-powered technical interview platform built using FastAPI on the backend and React on the frontend.",
            solution="The platform uses an AI interviewer to conduct interviews, speaks questions aloud and listens to candidate responses, supports timed DSA coding rounds, uses Google's Gemini API to evaluate interviews, offers practice and scheduled interview modes, and includes webcam-based face detection and tab-switch monitoring for proctoring.",
            technologies=json.dumps(["Django", "React", "Google Gemini API", "Speech-to-Text", "Face Detection", "WebSockets"]),
            is_highlight=True,
        )
        session.add(project2)
        
        # Education
        edu = Education(
            profile_id=profile.id,
            institution="Indian Institute of Information Technology, Kota",
            degree="B.Tech",
            field_of_study="Electronics and Communication Engineering",
            graduation_year=2026,
        )
        session.add(edu)
        
        # Job Preferences
        pref = JobPreference(
            user_id=1,
            experience_level="fresher",
            min_experience_years=0,
            max_experience_years=2,
            min_salary_lpa=5.0,
            max_salary_lpa=6.0,
            accept_unpaid=False,
            remote_ok=True,
            hybrid_ok=True,
            onsite_ok=True,
            willing_to_relocate=True,
            full_time=True,
            internship=True,
            contract=False,
        )
        session.add(pref)
        await session.flush()
        
        # Preferred locations
        locations = [
            ("Bengaluru", "Karnataka"),
            ("Hyderabad", "Telangana"),
            ("Pune", "Maharashtra"),
            ("Delhi NCR", "Delhi"),
            ("Noida", "Uttar Pradesh"),
            ("Mumbai", "Maharashtra"),
            ("Gurgaon", "Haryana"),
            ("Chennai", "Tamil Nadu"),
            ("Kolkata", "West Bengal"),
            ("Ahmedabad", "Gujarat"),
        ]
        for city, state in locations:
            session.add(PreferredLocation(preference_id=pref.id, city=city, state=state, country="India"))
        
        # Preferred roles
        roles = [
            ("Software Development Engineer", 1),
            ("Software Engineer", 1),
            ("Full Stack Developer", 1),
            ("Backend Developer", 2),
            ("Frontend Developer", 2),
            ("Junior Software Engineer", 2),
            ("AI Application Developer", 3),
            ("AI/LLM Engineer", 3),
            ("Software Engineering Intern", 2),
            ("Full Stack Developer Intern", 2),
            ("Backend Developer Intern", 3),
        ]
        for title, priority in roles:
            session.add(PreferredRole(preference_id=pref.id, title=title, priority=priority))
        
        await session.commit()
        print("[OK] Default user profile seeded successfully")

        # Seed initial recruiters
        from app.services.recruiter_finder import recruiter_finder_service
        from app.services.job_discovery import job_discovery_service

        await recruiter_finder_service.seed_initial_recruiters(session)
        print("[OK] Recruiter directory seeded")

        profile_data = {
            "full_name": profile.full_name,
            "skills": [s[1] for s in skills_data],
            "preferred_locations": [l[0] for l in locations] + ["Remote"],
        }
        await job_discovery_service.discover_jobs(session, profile_data)
        print("[OK] Curated jobs discovered and matched")
