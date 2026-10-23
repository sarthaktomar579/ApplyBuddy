export interface JobMatch {
  overall_score: number;
  skills_score: number;
  experience_score: number;
  education_score: number;
  location_score: number;
  salary_score: number;
  matching_skills: string[];
  missing_skills: string[];
  relevant_projects: string[];
  is_eligible: boolean;
  eligibility_issues: string[];
  match_reasons: string[];
  recommended_action: string;
}

export interface Job {
  id: number;
  title: string;
  company: string;
  location: string | null;
  employment_type: string | null;
  work_arrangement: string | null;
  experience_required: string | null;
  salary_min: number | null;
  salary_max: number | null;
  salary_currency: string;
  description: string | null;
  required_skills: string[];
  preferred_skills: string[];
  application_url: string | null;
  source_url: string | null;
  source: string;
  date_posted: string | null;
  application_deadline: string | null;
  discovered_at: string | null;
  is_active: boolean;
  is_bookmarked: boolean;
  is_relevant: boolean;
  match?: JobMatch | null;
  skills?: { name: string; is_required: boolean }[];
}

export interface Application {
  id: number;
  job_id: number;
  job_title: string;
  company: string;
  location: string | null;
  application_url: string | null;
  status: string;
  notes: string | null;
  follow_up_date: string | null;
  interview_date: string | null;
  interview_type: string | null;
  interview_notes: string | null;
  response_content: string | null;
  offer_salary: string | null;
  offer_details: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface Email {
  id: number;
  job_id: number | null;
  idempotency_key: string;
  to_email: string;
  to_name: string | null;
  from_email: string | null;
  subject: string;
  body: string;
  status: 'draft' | 'awaiting_approval' | 'approved' | 'sending' | 'sent' | 'failed' | 'cancelled';
  recipient_verified: boolean;
  recipient_source: string | null;
  resume_id: number | null;
  gmail_message_id: string | null;
  sent_at: string | null;
  error_message: string | null;
  retry_count: number;
  is_personalized: boolean;
  generation_model: string | null;
  created_at: string | null;
}

export interface Recruiter {
  id: number;
  name: string | null;
  email: string;
  title: string | null;
  department: string | null;
  company: string;
  verification_status: 'verified_official' | 'pattern_derived' | 'unverified';
  source_url: string | null;
  evidence: string | null;
  emails_sent_count: number;
  last_contacted: string | null;
  last_verified: string | null;
}

export interface Resume {
  id: number;
  filename: string;
  label: string;
  is_default: boolean;
  is_tailored: boolean;
  file_size: number;
  version: number;
  uploaded_at: string | null;
  has_parsed_data?: boolean;
  raw_text?: string;
}

export interface Profile {
  id: number;
  full_name: string;
  email: string;
  phone: string | null;
  github_url: string | null;
  linkedin_url: string | null;
  portfolio_url: string | null;
  degree: string | null;
  college: string | null;
  graduation_year: number | null;
  summary: string | null;
  strongest_areas: string[];
  dsa_problems_solved: number | null;
  leetcode_rating: string | null;
  codechef_rating: string | null;
  other_achievements: string | null;
  skills: { id?: number; category: string; name: string; proficiency?: string }[];
  experiences: { id?: number; company: string; role: string; start_date?: string; end_date?: string; description?: string; highlights?: string[]; technologies?: string[] }[];
  projects: { id?: number; name: string; problem?: string; solution?: string; impact?: string; technologies?: string[]; github_url?: string; live_url?: string; is_highlight?: boolean }[];
  education: { id?: number; institution: string; degree: string; field_of_study?: string; graduation_year?: number; gpa?: string; achievements?: string[] }[];
}

export interface DashboardStats {
  jobs: {
    total: number;
    active: number;
    bookmarked: number;
    matched: number;
    high_match: number;
  };
  applications: {
    total: number;
    discovered: number;
    shortlisted: number;
    preparing_application: number;
    awaiting_approval: number;
    email_sent: number;
    application_submitted: number;
    follow_up_due: number;
    recruiter_replied: number;
    interview_scheduled: number;
    rejected: number;
    offer_received: number;
    withdrawn: number;
  };
  emails: {
    draft: number;
    awaiting_approval: number;
    approved: number;
    sending: number;
    sent: number;
    failed: number;
    cancelled: number;
  };
  recruiters: {
    total: number;
    verified: number;
  };
}
