"""
AI Provider Service - Multi-provider AI abstraction layer.
Supports Google Gemini, Groq, and intelligent heuristic fallback.
"""
import json
import logging
from typing import Optional, Dict, Any, List
from app.core.config import settings

logger = logging.getLogger(__name__)


class AIProviderService:
    def __init__(self):
        self.gemini_key = settings.GEMINI_API_KEY
        self.groq_key = settings.GROQ_API_KEY
        self.openrouter_key = settings.OPENROUTER_API_KEY

    async def generate_text(self, prompt: str, system_prompt: str = "") -> str:
        """Generate text using available AI provider."""
        # 1. Try Gemini (via direct REST API)
        if self.gemini_key:
            try:
                import httpx
                gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={self.gemini_key}"
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}]
                }
                if system_prompt:
                    payload["systemInstruction"] = {
                        "parts": [{"text": system_prompt}]
                    }
                async with httpx.AsyncClient(timeout=20.0) as client:
                    resp = await client.post(gemini_url, json=payload)
                    if resp.status_code == 200:
                        cand = resp.json().get("candidates", [])
                        if cand and "content" in cand[0] and "parts" in cand[0]["content"]:
                            text_parts = [p.get("text", "") for p in cand[0]["content"]["parts"] if "text" in p]
                            if text_parts:
                                return "".join(text_parts).strip()
            except Exception as e:
                logger.warning(f"Gemini REST call failed: {e}. Trying fallback...")

        # 2. Try Groq
        if self.groq_key:
            try:
                import httpx
                messages = []
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})
                messages.append({"role": "user", "content": prompt})

                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers={"Authorization": f"Bearer {self.groq_key}"},
                        json={
                            "model": "llama-3.1-70b-versatile",
                            "messages": messages,
                            "temperature": 0.7,
                            "max_tokens": 1500,
                        },
                    )
                if resp.status_code == 200:
                    data = resp.json()
                    return data["choices"][0]["message"]["content"].strip()
            except Exception as e:
                logger.warning(f"Groq generation failed: {e}. Falling back to heuristic.")

        # 3. Fallback / offline mode message
        return ""

    async def evaluate_job_match(self, job_data: Dict[str, Any], profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate candidate-to-job match score and produce detailed analysis.
        Uses AI if configured, otherwise computes high-precision heuristic match.
        """
        # User skills set (lowercased)
        candidate_skills = {s.lower() for s in profile_data.get("skills", [])}
        req_skills = [s.strip() for s in job_data.get("required_skills", []) if s.strip()]
        pref_skills = [s.strip() for s in job_data.get("preferred_skills", []) if s.strip()]
        all_job_skills = req_skills + pref_skills

        matching_skills = []
        missing_skills = []

        for skill in req_skills:
            if any(candidate_skill in skill.lower() or skill.lower() in candidate_skill for candidate_skill in candidate_skills):
                matching_skills.append(skill)
            else:
                missing_skills.append(skill)

        for skill in pref_skills:
            if any(candidate_skill in skill.lower() or skill.lower() in candidate_skill for candidate_skill in candidate_skills):
                if skill not in matching_skills:
                    matching_skills.append(skill)
            else:
                if skill not in missing_skills:
                    missing_skills.append(skill)

        # Skills Score
        if all_job_skills:
            skills_score = int((len(matching_skills) / len(all_job_skills)) * 100)
        else:
            skills_score = 85  # default if no specific skill requirements listed

        # Experience Score (Sarthak is fresher / 2026 grad with 2 internships)
        exp_req = (job_data.get("experience_required") or "").lower()
        if any(w in exp_req for w in ["fresher", "0-1", "0-2", "intern", "entry", "graduate", "0 years"]):
            exp_score = 95
        elif any(w in exp_req for w in ["1-3", "1-2", "2 years"]):
            exp_score = 80
        elif any(w in exp_req for w in ["3+", "4+", "5+", "senior"]):
            exp_score = 40
        else:
            exp_score = 88

        # Education Score (IIIT Kota B.Tech 2026)
        edu_score = 92

        # Location Score
        location = (job_data.get("location") or "").lower()
        work_arr = (job_data.get("work_arrangement") or "").lower()
        preferred_locs = [l.lower() for l in profile_data.get("preferred_locations", [])]
        if "remote" in work_arr or "remote" in location:
            loc_score = 100
        elif any(pl in location for pl in preferred_locs):
            loc_score = 95
        elif any(loc in location for loc in ["bengaluru", "bangalore", "hyderabad", "pune", "delhi", "noida", "gurgaon", "mumbai"]):
            loc_score = 90
        else:
            loc_score = 75

        # Salary Score
        sal_score = 90

        # Overall Score
        overall_score = int(
            skills_score * 0.40 +
            exp_score * 0.25 +
            loc_score * 0.15 +
            edu_score * 0.10 +
            sal_score * 0.10
        )
        overall_score = max(30, min(99, overall_score))

        # Relevant projects identification
        relevant_projects = []
        job_title_desc = f"{job_data.get('title', '')} {job_data.get('description', '')}".lower()

        if any(k in job_title_desc for k in ["react", "frontend", "full stack", "audio", "streaming", "websocket", "ui"]):
            relevant_projects.append("AI Medical Reporting Platform (Document Picture-in-Picture & WebSockets)")
        if any(k in job_title_desc for k in ["ai", "llm", "gemini", "fastapi", "django", "interview", "speech"]):
            relevant_projects.append("AI Saraj — AI Technical Interview Platform (Gemini API & Proctoring)")

        if not relevant_projects:
            relevant_projects = ["AI Medical Reporting Platform", "AI Saraj Interview Platform"]

        # Match reasons
        match_reasons = []
        if matching_skills:
            match_reasons.append(f"Strong overlap on core technologies: {', '.join(matching_skills[:4])}")
        match_reasons.append(f"Hands-on production internship experience at Skygnosis & Xelron AI")
        match_reasons.append(f"Competitive programming background: 1500+ DSA problems solved (Knight on LeetCode)")
        if "remote" in work_arr or "remote" in location:
            match_reasons.append("100% location fit (Remote position)")
        else:
            match_reasons.append(f"Located or willing to relocate to target tech hubs ({job_data.get('location', 'India')})")

        # Eligibility check
        is_eligible = overall_score >= 60
        eligibility_issues = []
        if overall_score < 60:
            eligibility_issues.append("Experience requirement may be higher than current candidate profile")
        if len(missing_skills) > 3:
            eligibility_issues.append(f"Missing several required technologies: {', '.join(missing_skills[:3])}")

        # Recommended Action
        if overall_score >= 80:
            recommended_action = "High Priority: Apply immediately and send personalized cold email to hiring team"
        elif overall_score >= 65:
            recommended_action = "Good Match: Tailor resume to emphasize matching skills and apply"
        else:
            recommended_action = "Consider applying only if interested in stretching skills"

        # Try to refine with AI if API key is present
        ai_prompt = f"""
You are an expert technical recruiter analyzing job match for a candidate.
Job: {job_data.get('title')} at {job_data.get('company')}
Description: {job_data.get('description', '')[:500]}
Required Skills: {req_skills}
Candidate Profile: Sarthak Singh Tomar, B.Tech ECE 2026 IIIT Kota, Full Stack & AI Developer.
Candidate Skills: {list(candidate_skills)[:20]}
Projects: Medical Reporting Platform (React, PiP, WebSockets), AI Saraj (FastAPI, Gemini).

Provide 2 bullet points on why this candidate is a strong fit for this specific role. Format as JSON list of strings.
"""
        try:
            ai_text = await self.generate_text(ai_prompt)
            if ai_text:
                import re
                match = re.search(r'\[.*\]', ai_text, re.DOTALL)
                if match:
                    parsed_bullets = json.loads(match.group(0))
                    if isinstance(parsed_bullets, list) and parsed_bullets:
                        match_reasons = parsed_bullets + match_reasons[:2]
        except Exception:
            pass

        return {
            "overall_score": overall_score,
            "skills_score": skills_score,
            "experience_score": exp_score,
            "education_score": edu_score,
            "location_score": loc_score,
            "salary_score": sal_score,
            "matching_skills": matching_skills,
            "missing_skills": missing_skills,
            "relevant_projects": relevant_projects,
            "is_eligible": is_eligible,
            "eligibility_issues": eligibility_issues,
            "match_reasons": match_reasons,
            "recommended_action": recommended_action,
        }

    async def generate_cold_email(
        self,
        job_data: Dict[str, Any],
        profile_data: Dict[str, Any],
        recruiter_name: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Generate a high-converting, personalized cold email for job application.
        Cites Sarthak's actual projects, stats, and explains why he fits the role.
        """
        candidate_name = profile_data.get("full_name", "Sarthak Singh Tomar")
        company = job_data.get("company", "the company")
        role = job_data.get("title", "Software Engineer")
        greeting = f"Hi {recruiter_name}," if recruiter_name and recruiter_name.strip() else "Hello Hiring Team,"

        system_prompt = (
            "You are an expert executive cold email writer for top software engineers. "
            "Write concise, highly impactful, and personalized cold application emails. "
            "Never use generic buzzwords like 'I am writing to express my enthusiasm'. "
            "Get straight to value, mention concrete technical achievements, cite specific projects, "
            "and end with a polite, low-friction call to action."
        )

        user_prompt = f"""
Write a personalized cold email for:
Candidate: {candidate_name}
Education: Final-year B.Tech at IIIT Kota (2026 graduate)
Role applied: {role} at {company}
Target Company: {company}
Work Experience: Full Stack Developer at Skygnosis (built real-time audio streaming workflows with WebSockets and Document PiP mini-player) and Software Developer at Xelron AI (Dockerized evaluation benchmarks).
Key Achievements: 1500+ DSA problems solved (Knight on LeetCode), strong in React, FastAPI, Node.js, Python, LLM integrations.
Projects:
1. AI Medical Reporting Platform: Floating mini-player using Document PiP API + React Portals for real-time dictation without switching tabs.
2. AI Saraj: AI Technical Interview Platform with Gemini API evaluation, speech-to-text, and proctoring.
Job Description snippet: {job_data.get('description', '')[:400]}

Return JSON formatted exactly as:
{{
  "subject": "Clear, high-CTR subject line",
  "body": "The full email body text with paragraph breaks"
}}
"""
        generated_email = None
        try:
            ai_response = await self.generate_text(user_prompt, system_prompt=system_prompt)
            if ai_response:
                import re
                match = re.search(r'\{.*\}', ai_response, re.DOTALL)
                if match:
                    parsed = json.loads(match.group(0))
                    if "subject" in parsed and "body" in parsed:
                        generated_email = parsed
        except Exception as e:
            logger.warning(f"AI cold email generation failed: {e}")

        if not generated_email:
            # High quality bespoke template if AI API key is not yet set
            subject = f"Application: {role} — Sarthak Singh Tomar (IIIT Kota '26 | Full-Stack & AI)"
            body = (
                f"{greeting}\n\n"
                f"I've been following {company}'s engineering work and noticed your opening for the {role} role. "
                f"As a final-year B.Tech student at IIIT Kota with production full-stack and AI engineering experience, "
                f"I would love to contribute to your team.\n\n"
                f"A few quick highlights relevant to this role:\n"
                f"- Full Stack & Real-time Systems: At Skygnosis, I engineered real-time audio streaming workflows with WebSockets "
                f"and built a floating mini-player utilizing the browser Document Picture-in-Picture API so doctors can dictate patient EHR notes seamlessly.\n"
                f"- AI & API Integration: Built AI Saraj, an AI technical interview platform evaluating candidates via Google Gemini API with real-time proctoring.\n"
                f"- Algorithmic Rigor: Solved 1,500+ Data Structures & Algorithms problems across platforms (LeetCode Knight rating).\n\n"
                f"I have attached my resume PDF for your review and would appreciate 10 minutes to discuss how my skill set aligns with your current technical roadmap.\n\n"
                f"Best regards,\n"
                f"{candidate_name}\n"
                f"GitHub: https://github.com/sarthaktomar579\n"
                f"Phone: +91-6377525805 | Email: sarthakt579@gmail.com"
            )
            generated_email = {"subject": subject, "body": body}

        return generated_email

    async def tailor_resume_suggestions(
        self,
        job_data: Dict[str, Any],
        profile_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate targeted resume tailoring recommendations for a job."""
        title = job_data.get("title", "Software Engineer")
        company = job_data.get("company", "Company")
        desc = job_data.get("description", "")
        req_skills = job_data.get("required_skills", [])

        summary_suggestion = (
            f"Results-driven Full Stack & AI Software Engineer (IIIT Kota '26) with production experience building "
            f"high-concurrency web applications, WebSockets, and LLM-powered systems. Proven track record delivering "
            f"robust features at Skygnosis and Xelron AI. Targeting {title} at {company} to leverage deep expertise in "
            f"{', '.join(req_skills[:3]) if req_skills else 'React, Python, FastAPI, and scalable architectures'}."
        )

        bullet_points = [
            f"Architected real-time client-server communication using WebSockets and FastAPI, reducing latency by 40%.",
            f"Engineered browser Document Picture-in-Picture floating UI enabling uninterrupted background audio streaming during user workflows.",
            f"Integrated Google Gemini LLM API and deterministic benchmarking pipelines to evaluate complex model outputs.",
            f"Maintained rigorous algorithmic problem-solving standards with 1,500+ DSA problems solved and LeetCode Knight ranking.",
        ]

        keywords_to_add = [s for s in req_skills if s]
        if not keywords_to_add:
            keywords_to_add = ["React", "FastAPI", "WebSockets", "Docker", "REST APIs", "CI/CD"]

        return {
            "target_role": f"{title} at {company}",
            "summary_suggestion": summary_suggestion,
            "highlighted_projects": [
                {
                    "name": "AI Medical Reporting Platform",
                    "focus": "Emphasize React Portals, Document PiP API, and WebSocket streaming under high reliability."
                },
                {
                    "name": "AI Saraj Interview Platform",
                    "focus": "Highlight Gemini API prompt engineering, proctoring security, and FastAPI backend latency."
                }
            ],
            "tailored_bullet_points": bullet_points,
            "keywords_to_emphasize": keywords_to_add[:8],
            "ats_tips": [
                f"Ensure the exact phrase '{title}' appears in your resume header or professional summary.",
                "Quantify impact with metrics (e.g. 1500+ DSA problems, 40% latency reduction).",
                "Include clean links to GitHub (github.com/sarthaktomar579) and live demos."
            ]
        }

    async def answer_application_questions(
        self,
        questions: List[str],
        job_data: Dict[str, Any],
        profile_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate tailored answers for job portal application questions."""
        results = []
        role = job_data.get("title", "Software Engineer")
        company = job_data.get("company", "your company")

        for q in questions:
            q_lower = q.lower()
            if "why" in q_lower and ("work" in q_lower or "join" in q_lower or "company" in q_lower or "us" in q_lower):
                answer = (
                    f"I am eager to join {company} as a {role} because of your focus on solving challenging technical problems at scale. "
                    f"During my internships at Skygnosis and Xelron AI, I discovered how much I enjoy building real-time, user-facing software "
                    f"that directly impacts workflows—like building floating Document PiP interfaces and integrating LLM pipelines. "
                    f"I am excited to bring my full-stack background in React, FastAPI, Python, and 1,500+ DSA problem-solving foundation to {company}."
                )
            elif "tell me about yourself" in q_lower or "brief introduction" in q_lower:
                answer = (
                    f"I am a final-year B.Tech student at IIIT Kota graduating in 2026 with hands-on full-stack and AI development experience. "
                    f"I have worked at Skygnosis developing real-time audio and clinical summarization applications using React and FastAPI, "
                    f"and at Xelron AI building evaluation benchmarks with Docker. I am passionate about clean architecture, rapid execution, "
                    f"and solving complex algorithmic problems (1500+ problems solved, LeetCode Knight)."
                )
            elif "challenge" in q_lower or "difficult" in q_lower or "bug" in q_lower:
                answer = (
                    "While developing the AI Medical Reporting platform at Skygnosis, doctors needed to dictate patient findings without losing "
                    "their hospital EHR tab. Standard browser tabs restricted floating windows across different tabs. I solved this by leveraging the "
                    "emerging Document Picture-in-Picture API combined with React Portals and persistent WebSocket audio streams, allowing the recording "
                    "UI to remain visible and active over any browser window without losing audio packets."
                )
            else:
                answer = (
                    f"As a full-stack engineer graduating from IIIT Kota in 2026, my experience with React, FastAPI, Node.js, and LLM integrations "
                    f"aligns closely with this role. I have delivered production features in fast-paced startup environments and bring a strong problem-solving "
                    f"foundation to every technical challenge."
                )

            results.append({
                "question": q,
                "suggested_answer": answer,
                "word_count": len(answer.split()),
            })

        return results


ai_service = AIProviderService()
