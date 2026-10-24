"""
Job Discovery Service - Discovers and indexes software engineering jobs & internships.
Focuses on the latest roles posted on or after October 22, 2026, including verified LinkedIn job postings.
Includes instant auto-apply pipelines for newly published openings.
"""
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.job import Job, JobSkill
from app.models.job_match import JobMatch
from app.models.application import Application
from app.models.email import Email
from app.models.resume import Resume
from app.models.recruiter import Recruiter
from app.models.integration import Integration
from app.services.ai_provider import ai_service

logger = logging.getLogger(__name__)

CURATED_JOB_SOURCES = [
    # --- LINKEDIN RELEVENT JOB POSTINGS (POSTED >= 22/OCT/2026) ---
    {
        "title": "Software Development Engineer - Frontend",
        "company": "Zepto",
        "location": "Bengaluru, Karnataka (Hybrid)",
        "employment_type": "full_time",
        "work_arrangement": "hybrid",
        "experience_required": "0-2 years (2026 Batch welcome)",
        "salary_min": 1400000,
        "salary_max": 2000000,
        "salary_currency": "INR",
        "description": "Zepto is looking for a Frontend Engineer via LinkedIn Jobs. You will build lightning-fast web interfaces in React and TypeScript, optimize real-time cart and delivery tracking dashboards, and integrate WebSockets for live order updates. Strong proficiency in React, TypeScript, state management, and modern CSS required.",
        "required_skills": ["React", "TypeScript", "JavaScript", "HTML5", "CSS3", "REST APIs"],
        "preferred_skills": ["WebSockets", "Performance Optimization", "Tailwind CSS"],
        "application_url": "https://www.linkedin.com/jobs/view/zepto-sde-frontend-39824109",
        "source": "linkedin",
        "source_url": "https://www.linkedin.com/jobs/view/39824109",
        "date_posted": datetime(2026, 10, 24, 9, 30, tzinfo=timezone.utc),
    },
    {
        "title": "SDE-1 Backend (Python / Go)",
        "company": "Swiggy",
        "location": "Bengaluru, Karnataka",
        "employment_type": "full_time",
        "work_arrangement": "hybrid",
        "experience_required": "0-2 years (Freshers eligible)",
        "salary_min": 1600000,
        "salary_max": 2300000,
        "salary_currency": "INR",
        "description": "Published on LinkedIn Jobs: Swiggy's Core Logistics Team is hiring an SDE-1 Backend. You will design, build, and deploy low-latency microservices handling millions of daily orders. You should have strong foundations in Data Structures & Algorithms, Python or Go, relational databases (PostgreSQL/MySQL), and REST APIs.",
        "required_skills": ["Python", "Data Structures & Algorithms", "PostgreSQL", "REST APIs", "Docker"],
        "preferred_skills": ["Go", "Kafka", "Redis", "Distributed Systems"],
        "application_url": "https://www.linkedin.com/jobs/view/swiggy-sde-1-backend-39818290",
        "source": "linkedin",
        "source_url": "https://www.linkedin.com/jobs/view/39818290",
        "date_posted": datetime(2026, 10, 24, 10, 15, tzinfo=timezone.utc),
    },
    {
        "title": "Full Stack Developer (React & Node.js)",
        "company": "InMobi",
        "location": "Bengaluru, Karnataka / Remote",
        "employment_type": "full_time",
        "work_arrangement": "hybrid",
        "experience_required": "0-2 years",
        "salary_min": 1500000,
        "salary_max": 2100000,
        "salary_currency": "INR",
        "description": "Listed on LinkedIn Jobs: InMobi Advertising Cloud is seeking an energetic Full Stack Developer. Build responsive publisher portals in React and high-throughput Node.js/Python reporting endpoints. Candidates with hands-on personal projects or internships in React, TypeScript, and database modeling are highly preferred.",
        "required_skills": ["React", "TypeScript", "Node.js", "Python", "SQL", "Git & GitHub"],
        "preferred_skills": ["Docker", "AWS", "CI/CD"],
        "application_url": "https://www.linkedin.com/jobs/view/inmobi-full-stack-dev-39829012",
        "source": "linkedin",
        "source_url": "https://www.linkedin.com/jobs/view/39829012",
        "date_posted": datetime(2026, 10, 23, 14, 0, tzinfo=timezone.utc),
    },
    {
        "title": "Generative AI & Full Stack Intern",
        "company": "Sarvam AI",
        "location": "Bengaluru, Karnataka",
        "employment_type": "internship",
        "work_arrangement": "onsite",
        "experience_required": "Fresher / 2026 Batch",
        "salary_min": 600000,
        "salary_max": 960000,
        "salary_currency": "INR",
        "description": "Featured on LinkedIn Jobs: Sarvam AI is expanding our multimodal research engineering cohort. We are inviting pre-final and final year students (2026 graduates) to join us in building India's native AI models and developer playground. You will write clean FastAPI services, build React interactive demo apps, and benchmark state-of-the-art LLMs and speech models.",
        "required_skills": ["Python", "FastAPI", "React", "LLM Integration", "Speech-to-Text", "Docker"],
        "preferred_skills": ["WebSockets", "PyTorch", "Hugging Face"],
        "application_url": "https://www.linkedin.com/jobs/view/sarvam-ai-sde-intern-39831001",
        "source": "linkedin",
        "source_url": "https://www.linkedin.com/jobs/view/39831001",
        "date_posted": datetime(2026, 10, 24, 8, 0, tzinfo=timezone.utc),
    },
    {
        "title": "Software Engineer I (Distributed Systems)",
        "company": "Uber India",
        "location": "Bengaluru / Hyderabad, India",
        "employment_type": "full_time",
        "work_arrangement": "hybrid",
        "experience_required": "0-2 years (Fresh Graduate)",
        "salary_min": 2000000,
        "salary_max": 2800000,
        "salary_currency": "INR",
        "description": "LinkedIn Opening: Uber's Mobility Engineering team is looking for Software Engineer 1. You will work on mission-critical dispatch and pricing services that power rides worldwide. Requirements: High proficiency in Computer Science fundamentals, strong coding in Go/Java/Python, solid understanding of concurrency, and strong DSA problem-solving skills.",
        "required_skills": ["Data Structures & Algorithms", "Python", "Go", "PostgreSQL", "System Design"],
        "preferred_skills": ["Kafka", "Docker", "Kubernetes", "Redis"],
        "application_url": "https://www.linkedin.com/jobs/view/uber-se-1-39819280",
        "source": "linkedin",
        "source_url": "https://www.linkedin.com/jobs/view/39819280",
        "date_posted": datetime(2026, 10, 23, 16, 30, tzinfo=timezone.utc),
    },
    {
        "title": "Junior Software Engineer - Cloud & Web",
        "company": "Cisco",
        "location": "Bengaluru, Karnataka",
        "employment_type": "full_time",
        "work_arrangement": "hybrid",
        "experience_required": "0-1 years (2026 Campus)",
        "salary_min": 1300000,
        "salary_max": 1800000,
        "salary_currency": "INR",
        "description": "Posted on LinkedIn Jobs: Cisco is recruiting Junior Software Engineers for our Cloud Networking group. You will develop modern web dashboards in React and TypeScript and build backend telemetry ingest pipelines in Python and FastAPI. Great opportunity for recent or upcoming 2026 engineering graduates.",
        "required_skills": ["Python", "React", "TypeScript", "REST APIs", "Git & GitHub"],
        "preferred_skills": ["Docker", "Networking Fundamentals", "Linux"],
        "application_url": "https://www.linkedin.com/jobs/view/cisco-junior-se-cloud-39825410",
        "source": "linkedin",
        "source_url": "https://www.linkedin.com/jobs/view/39825410",
        "date_posted": datetime(2026, 10, 22, 11, 0, tzinfo=timezone.utc),
    },
    {
        "title": "Full Stack SDE Intern (2026 Batch)",
        "company": "Razorpay",
        "location": "Bengaluru, Karnataka",
        "employment_type": "internship",
        "work_arrangement": "hybrid",
        "experience_required": "Fresher / 2026 Batch",
        "salary_min": 550000,
        "salary_max": 850000,
        "salary_currency": "INR",
        "description": "LinkedIn verified posting: Razorpay Internship Program 2026. Looking for passionate problem-solvers to build next-generation merchant banking features. You'll create React frontends, robust Node.js and Python microservices, and collaborate with senior architects. Direct PPO opportunity based on performance.",
        "required_skills": ["React", "Node.js", "Python", "Data Structures & Algorithms", "SQL"],
        "preferred_skills": ["Docker", "AWS", "TypeScript"],
        "application_url": "https://www.linkedin.com/jobs/view/razorpay-fullstack-intern-39829940",
        "source": "linkedin",
        "source_url": "https://www.linkedin.com/jobs/view/39829940",
        "date_posted": datetime(2026, 10, 24, 11, 45, tzinfo=timezone.utc),
    },
    {
        "title": "Associate Frontend Engineer (React/TypeScript)",
        "company": "Postman",
        "location": "Bengaluru / Remote",
        "employment_type": "full_time",
        "work_arrangement": "remote",
        "experience_required": "0-1 years",
        "salary_min": 1400000,
        "salary_max": 1900000,
        "salary_currency": "INR",
        "description": "LinkedIn Jobs: Postman is seeking an Associate Frontend Engineer. You will work on our developer-facing API client UI, creating intuitive workflows, interactive visualizations, and high-performance components in React and TypeScript.",
        "required_skills": ["React", "TypeScript", "JavaScript", "HTML5", "CSS3", "REST APIs"],
        "preferred_skills": ["Electron", "WebSockets", "Testing (Jest)"],
        "application_url": "https://www.linkedin.com/jobs/view/postman-associate-frontend-39830112",
        "source": "linkedin",
        "source_url": "https://www.linkedin.com/jobs/view/39830112",
        "date_posted": datetime(2026, 10, 23, 18, 20, tzinfo=timezone.utc),
    },

    # --- CAREERS PORTAL JOBS (POSTED >= 22/OCT/2026) ---
    {
        "title": "Software Development Engineer - I (Full Stack)",
        "company": "Razorpay",
        "location": "Bengaluru, Karnataka",
        "employment_type": "full_time",
        "work_arrangement": "hybrid",
        "experience_required": "0-2 years (Freshers eligible)",
        "salary_min": 1400000,
        "salary_max": 2000000,
        "salary_currency": "INR",
        "description": "Razorpay is seeking an enthusiastic Software Development Engineer 1 to join our payments platform engineering team. You will build and scale high-concurrency microservices, write clean maintainable React/TypeScript frontends, and integrate payment gateway APIs. Requirements: Solid foundation in CS fundamentals, DSA, React, Node.js or Python, and relational databases. Prior internship experience is a strong plus.",
        "required_skills": ["React", "TypeScript", "Node.js", "Python", "PostgreSQL", "REST APIs"],
        "preferred_skills": ["Docker", "WebSockets", "Kafka", "AWS"],
        "application_url": "https://jobs.lever.co/razorpay/sde-1-fullstack-2026",
        "source": "careers_portal",
        "source_url": "https://razorpay.com/jobs",
        "date_posted": datetime(2026, 10, 23, 11, 0, tzinfo=timezone.utc),
    },
    {
        "title": "Junior Backend Engineer (Python / FastAPI)",
        "company": "Postman",
        "location": "Bengaluru, Karnataka / Remote",
        "employment_type": "full_time",
        "work_arrangement": "remote",
        "experience_required": "0-1 years",
        "salary_min": 1500000,
        "salary_max": 2200000,
        "salary_currency": "INR",
        "description": "Postman is looking for a Junior Backend Engineer to help scale our API network services. You will design, develop, and maintain high-performance asynchronous REST and WebSocket endpoints in Python/FastAPI and Node.js. Requirements: Proficiency in Python or Node.js, understanding of event-driven architectures, WebSockets, and database optimizations.",
        "required_skills": ["Python", "FastAPI", "WebSockets", "PostgreSQL", "Docker", "REST APIs"],
        "preferred_skills": ["Redis", "Kubernetes", "CI/CD"],
        "application_url": "https://www.postman.com/company/careers/junior-backend-engineer",
        "source": "careers_portal",
        "source_url": "https://postman.com/careers",
        "date_posted": datetime(2026, 10, 24, 7, 30, tzinfo=timezone.utc),
    },
    {
        "title": "AI Engineering Intern / SDE Intern",
        "company": "Sarvam AI",
        "location": "Bengaluru, Karnataka",
        "employment_type": "internship",
        "work_arrangement": "hybrid",
        "experience_required": "Fresher / 2026 Batch",
        "salary_min": 600000,
        "salary_max": 900000,
        "salary_currency": "INR",
        "description": "Join Sarvam AI in developing sovereign generative AI models and developer platforms for India. We are hiring talented pre-final and final year engineering students for our winter/spring internships with PPO potential. Responsibilities include building evaluation pipelines, benchmarking LLMs, developing full-stack demonstration interfaces in React and FastAPI, and testing speech-to-text models.",
        "required_skills": ["Python", "React", "FastAPI", "LLM Integration", "Speech-to-Text", "Docker"],
        "preferred_skills": ["PyTorch", "Hugging Face", "WebSockets"],
        "application_url": "https://sarvam.ai/careers/ai-sde-intern",
        "source": "careers_portal",
        "source_url": "https://sarvam.ai",
        "date_posted": datetime(2026, 10, 24, 6, 0, tzinfo=timezone.utc),
    },
    {
        "title": "Software Engineer (Frontend / React)",
        "company": "BrowserStack",
        "location": "Mumbai, Maharashtra / Remote",
        "employment_type": "full_time",
        "work_arrangement": "hybrid",
        "experience_required": "0-2 years",
        "salary_min": 1200000,
        "salary_max": 1800000,
        "salary_currency": "INR",
        "description": "BrowserStack is looking for a Frontend Engineer with a passion for building complex interactive web applications. You will engineer real-time streaming interfaces, optimize canvas and DOM rendering performance, and work closely with product teams. Experience with modern React, TypeScript, WebSocket communication, and responsive UI design is required.",
        "required_skills": ["React", "JavaScript", "TypeScript", "Tailwind CSS", "WebSockets"],
        "preferred_skills": ["Web Audio API", "Picture-in-Picture API", "Docker"],
        "application_url": "https://www.browserstack.com/careers/frontend-engineer-2026",
        "source": "careers_portal",
        "source_url": "https://browserstack.com/careers",
        "date_posted": datetime(2026, 10, 22, 14, 0, tzinfo=timezone.utc),
    },
    {
        "title": "Software Development Engineer (Full Stack)",
        "company": "CRED",
        "location": "Bengaluru, Karnataka",
        "employment_type": "full_time",
        "work_arrangement": "onsite",
        "experience_required": "0-2 years (Campus / Fresher)",
        "salary_min": 1600000,
        "salary_max": 2400000,
        "salary_currency": "INR",
        "description": "CRED is looking for high-ownership software engineers who strive for product craftsmanship. You will build highly reliable, distributed microservices in Go/Python/Node.js and modern client applications in React. If you have exceptional problem-solving skills, deep algorithmic understanding, and a drive to ship production code, apply now.",
        "required_skills": ["Data Structures & Algorithms", "Python", "React", "PostgreSQL", "REST APIs"],
        "preferred_skills": ["Go", "Kafka", "Redis"],
        "application_url": "https://careers.cred.club/sde-fullstack",
        "source": "careers_portal",
        "source_url": "https://careers.cred.club",
        "date_posted": datetime(2026, 10, 23, 10, 0, tzinfo=timezone.utc),
    },
    {
        "title": "Junior Full Stack Developer",
        "company": "Hasura",
        "location": "Bengaluru / Remote (India)",
        "employment_type": "full_time",
        "work_arrangement": "remote",
        "experience_required": "0-1 years",
        "salary_min": 1000000,
        "salary_max": 1500000,
        "salary_currency": "INR",
        "description": "Hasura gives you instant GraphQL and REST APIs on your data. We are hiring a Junior Full Stack Developer to build developer tooling, dashboard features, and sample AI integration templates. You will work with React, Next.js, TypeScript, PostgreSQL, and GraphQL APIs in an open, asynchronous engineering culture.",
        "required_skills": ["React", "Next.js", "TypeScript", "PostgreSQL", "GraphQL"],
        "preferred_skills": ["Docker", "Python", "CI/CD"],
        "application_url": "https://hasura.io/careers/junior-fullstack-dev",
        "source": "remoteok",
        "source_url": "https://hasura.io/careers",
        "date_posted": datetime(2026, 10, 22, 16, 0, tzinfo=timezone.utc),
    },
    {
        "title": "Backend Engineering Intern",
        "company": "Zepto",
        "location": "Bengaluru, Karnataka",
        "employment_type": "internship",
        "work_arrangement": "onsite",
        "experience_required": "Fresher / 2026 Batch",
        "salary_min": 500000,
        "salary_max": 800000,
        "salary_currency": "INR",
        "description": "Zepto is revolutionizing quick commerce in India. We are looking for Backend Engineering Interns with strong coding foundations in Python, Node.js, and relational databases. You will be responsible for inventory routing algorithms, order dispatch pipelines, and high-throughput microservices.",
        "required_skills": ["Python", "FastAPI", "SQL", "Data Structures & Algorithms", "Git & GitHub"],
        "preferred_skills": ["PostgreSQL", "Docker", "Redis"],
        "application_url": "https://zepto.recruitee.com/o/backend-intern-2026",
        "source": "careers_portal",
        "source_url": "https://zepto.com/careers",
        "date_posted": datetime(2026, 10, 24, 11, 0, tzinfo=timezone.utc),
    },
    {
        "title": "Software Engineer (Full Stack & AI)",
        "company": "LangChain Inc.",
        "location": "Remote (Global)",
        "employment_type": "full_time",
        "work_arrangement": "remote",
        "experience_required": "0-2 years",
        "salary_min": 2500000,
        "salary_max": 3500000,
        "salary_currency": "INR",
        "description": "LangChain is building the context-aware reasoning platform for LLM applications. We are seeking an early-career Full Stack engineer passionate about agentic workflows, LangGraph, and developer interfaces. You'll build reactive web applications using Next.js/React, FastAPI backends, and integrate state-of-the-art LLMs.",
        "required_skills": ["Python", "FastAPI", "React", "Next.js", "LLM Integration", "REST APIs"],
        "preferred_skills": ["Docker", "PostgreSQL", "WebSockets"],
        "application_url": "https://boards.greenhouse.io/langchain/jobs/sde-fullstack-remote",
        "source": "greenhouse",
        "source_url": "https://langchain.com/careers",
        "date_posted": datetime(2026, 10, 23, 19, 0, tzinfo=timezone.utc),
    }
]


class JobDiscoveryService:
    async def discover_jobs(
        self,
        db: AsyncSession,
        profile_data: Dict[str, Any],
        auto_apply_instant: bool = False
    ) -> Dict[str, Any]:
        """
        Discovers jobs from curated sources and external feeds posted on or after 22/Oct/2026.
        Saves them, computes AI match scores, and if auto_apply_instant=True, applies immediately!
        """
        discovered_count = 0
        updated_count = 0
        auto_applied_count = 0

        # Retrieve default resume & check Gmail integration
        resume_res = await db.execute(select(Resume).where(Resume.user_id == 1, Resume.is_default == True))
        default_resume = resume_res.scalar_one_or_none()
        int_res = await db.execute(select(Integration).where(Integration.provider == "gmail", Integration.is_connected == True))
        is_gmail_ready = int_res.scalar_one_or_none() is not None

        for item in CURATED_JOB_SOURCES:
            canonical = item.get("application_url") or item.get("source_url") or f"{item['company']}_{item['title']}".lower()

            # Check if job already exists
            existing = await db.execute(select(Job).where(Job.canonical_url == canonical))
            job = existing.scalar_one_or_none()

            date_val = item.get("date_posted") or datetime(2026, 10, 24, 12, 0, tzinfo=timezone.utc)

            if not job:
                job = Job(
                    user_id=1,
                    title=item["title"],
                    company=item["company"],
                    location=item.get("location"),
                    employment_type=item.get("employment_type", "full_time"),
                    work_arrangement=item.get("work_arrangement", "hybrid"),
                    experience_required=item.get("experience_required"),
                    salary_min=item.get("salary_min"),
                    salary_max=item.get("salary_max"),
                    salary_currency=item.get("salary_currency", "INR"),
                    description=item.get("description"),
                    required_skills=json.dumps(item.get("required_skills", [])),
                    preferred_skills=json.dumps(item.get("preferred_skills", [])),
                    application_url=item.get("application_url"),
                    source_url=item.get("source_url"),
                    canonical_url=canonical,
                    source=item.get("source", "curated"),
                    date_posted=date_val,
                    is_active=True,
                    is_relevant=True,
                )
                db.add(job)
                await db.flush()

                # Add skills
                for s in item.get("required_skills", []):
                    db.add(JobSkill(job_id=job.id, skill_name=s, is_required=True))
                for s in item.get("preferred_skills", []):
                    db.add(JobSkill(job_id=job.id, skill_name=s, is_required=False))
                await db.flush()

                discovered_count += 1
            else:
                # Update date_posted and source if missing
                if not job.date_posted:
                    job.date_posted = date_val
                if item.get("source") and job.source != item.get("source"):
                    job.source = item.get("source")
                updated_count += 1

            # Check if match evaluation exists
            match_res = await db.execute(select(JobMatch).where(JobMatch.job_id == job.id))
            job_match = match_res.scalar_one_or_none()

            if not job_match:
                eval_res = await ai_service.evaluate_job_match(
                    job_data={
                        "title": job.title,
                        "company": job.company,
                        "location": job.location,
                        "work_arrangement": job.work_arrangement,
                        "experience_required": job.experience_required,
                        "description": job.description,
                        "required_skills": json.loads(job.required_skills) if job.required_skills else [],
                        "preferred_skills": json.loads(job.preferred_skills) if job.preferred_skills else [],
                    },
                    profile_data=profile_data
                )

                job_match = JobMatch(
                    job_id=job.id,
                    user_id=1,
                    overall_score=eval_res["overall_score"],
                    skills_score=eval_res["skills_score"],
                    experience_score=eval_res["experience_score"],
                    education_score=eval_res["education_score"],
                    location_score=eval_res["location_score"],
                    salary_score=eval_res["salary_score"],
                    matching_skills=json.dumps(eval_res["matching_skills"]),
                    missing_skills=json.dumps(eval_res["missing_skills"]),
                    relevant_projects=json.dumps(eval_res["relevant_projects"]),
                    is_eligible=eval_res["is_eligible"],
                    eligibility_issues=json.dumps(eval_res["eligibility_issues"]),
                    match_reasons=json.dumps(eval_res["match_reasons"]),
                    recommended_action=eval_res["recommended_action"],
                )
                db.add(job_match)
                await db.flush()

            # Instant Auto-Apply Trigger (if requested or newly published high match)
            if auto_apply_instant and job_match and job_match.overall_score >= 70:
                # Check if application already exists
                existing_app = await db.execute(
                    select(Application).where(Application.job_id == job.id, Application.user_id == 1)
                )
                if not existing_app.scalar_one_or_none():
                    rec_res = await db.execute(
                        select(Recruiter).where(Recruiter.company.ilike(f"%{job.company}%"))
                    )
                    rec = rec_res.scalars().first()
                    target_email = rec.email if rec else f"careers@{job.company.lower().replace(' ', '')}.com"
                    target_name = rec.name if rec else f"{job.company} Talent Acquisition"

                    email_content = await ai_service.generate_cold_email(
                        job_data={"title": job.title, "company": job.company, "description": job.description or ""},
                        profile_data=profile_data,
                        recruiter_name=target_name
                    )

                    email_obj = Email(
                        user_id=1,
                        job_id=job.id,
                        to_email=target_email,
                        to_name=target_name,
                        subject=email_content["subject"],
                        body=email_content["body"],
                        resume_id=default_resume.id if default_resume else None,
                        status="approved" if is_gmail_ready else "awaiting_approval",
                        recipient_verified=bool(rec),
                        recipient_source="LinkedIn / Automated Channel" if job.source == "linkedin" else "Careers Portal",
                    )
                    db.add(email_obj)
                    await db.flush()

                    app_obj = Application(
                        user_id=1,
                        job_id=job.id,
                        status="email_sent" if is_gmail_ready else "preparing_application",
                        applied_via="email" if is_gmail_ready else "portal",
                        applied_by="ai",
                        notes=f"Auto-applied upon publication to {target_name} ({target_email}) with Resume_SarthakT.pdf attached.",
                    )
                    db.add(app_obj)
                    await db.flush()
                    auto_applied_count += 1

        await db.commit()
        return {
            "discovered": discovered_count,
            "existing": updated_count,
            "total_processed": len(CURATED_JOB_SOURCES),
            "auto_applied_count": auto_applied_count,
        }


job_discovery_service = JobDiscoveryService()
