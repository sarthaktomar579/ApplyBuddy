"""
Job Discovery Service - Discovers and indexes software engineering jobs & internships.
Fetches from public developer job feeds and curated openings in India & Remote.
"""
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.job import Job, JobSkill
from app.models.job_match import JobMatch
from app.services.ai_provider import ai_service

logger = logging.getLogger(__name__)

CURATED_JOB_SOURCES = [
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
    }
]


class JobDiscoveryService:
    async def discover_jobs(self, db: AsyncSession, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Discovers jobs from public feeds and curated sources, saves them,
        and computes AI match scores.
        """
        discovered_count = 0
        updated_count = 0

        # Try fetching external public tech jobs feed
        external_jobs = []
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get("https://remoteok.com/api?tag=python", headers={"User-Agent": "ApplyPilotAI/1.0"})
                if resp.status_code == 200:
                    data = resp.json()
                    # Skip the legal disclaimer entry at index 0
                    for item in data[1:6]:
                        if isinstance(item, dict) and item.get("position"):
                            external_jobs.append({
                                "title": item.get("position"),
                                "company": item.get("company", "Tech Co"),
                                "location": item.get("location") or "Remote",
                                "employment_type": "full_time",
                                "work_arrangement": "remote",
                                "experience_required": "0-2 years",
                                "salary_min": 1500000,
                                "salary_max": 2500000,
                                "salary_currency": "INR",
                                "description": item.get("description", "")[:1000],
                                "required_skills": [t for t in item.get("tags", []) if len(t) < 20][:6],
                                "preferred_skills": ["Git", "REST APIs"],
                                "application_url": item.get("url") or f"https://remoteok.com/remote-jobs/{item.get('id')}",
                                "source": "remoteok",
                                "source_url": item.get("url"),
                            })
        except Exception as e:
            logger.info(f"External job feed fetch skipped: {e}")

        # Combine curated tech jobs + external jobs
        all_jobs_to_process = CURATED_JOB_SOURCES + external_jobs

        for item in all_jobs_to_process:
            canonical = item.get("application_url") or item.get("source_url") or f"{item['company']}_{item['title']}".lower()

            # Check if job already exists
            existing = await db.execute(select(Job).where(Job.canonical_url == canonical))
            job = existing.scalar_one_or_none()

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
                updated_count += 1

            # Check if match evaluation exists
            match_res = await db.execute(select(JobMatch).where(JobMatch.job_id == job.id))
            existing_match = match_res.scalar_one_or_none()

            if not existing_match:
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

        await db.commit()
        return {
            "discovered": discovered_count,
            "existing": updated_count,
            "total_processed": len(all_jobs_to_process),
        }


job_discovery_service = JobDiscoveryService()
