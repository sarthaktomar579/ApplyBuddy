import axios from 'axios';
import { Job, Application, Email, Recruiter, Resume, Profile, DashboardStats } from '../types';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Dashboard
export const getDashboardStats = async (): Promise<DashboardStats> => {
  const res = await api.get('/dashboard/stats');
  return res.data;
};

// Jobs
export const getJobs = async (params?: {
  search?: string;
  location?: string;
  employment_type?: string;
  source?: string;
  posted_after?: string;
  latest_only?: boolean;
  is_bookmarked?: boolean;
  skip?: number;
  limit?: number;
}): Promise<{ total: number; jobs: Job[] }> => {
  const res = await api.get('/jobs', { params });
  return res.data;
};

export const getJob = async (id: number): Promise<Job> => {
  const res = await api.get(`/jobs/${id}`);
  return res.data;
};

export const createManualJob = async (jobData: Partial<Job>): Promise<{ id: number }> => {
  const res = await api.post('/jobs', jobData);
  return res.data;
};

export const toggleBookmark = async (id: number): Promise<{ bookmarked: boolean }> => {
  const res = await api.put(`/jobs/${id}/bookmark`);
  return res.data;
};

export const triggerJobDiscovery = async (autoApply: boolean = false): Promise<{ discovered: number; total_processed: number; auto_applied_count: number; message: string }> => {
  const res = await api.post('/jobs/discover', null, { params: { auto_apply: autoApply } });
  return res.data;
};

export const instantApplyAllLatest = async (minScore: number = 70): Promise<{
  newly_discovered: number;
  applications_processed: number;
  results: any[];
  gmail_connected: boolean;
  message: string;
}> => {
  const res = await api.post('/jobs/instant-apply-all', null, { params: { min_score: minScore } });
  return res.data;
};

export const evaluateJobMatch = async (id: number): Promise<{ message: string; match: any }> => {
  const res = await api.post(`/jobs/${id}/match`);
  return res.data;
};

// Applications
export const getApplications = async (status?: string): Promise<{ total: number; applications: Application[] }> => {
  const res = await api.get('/applications', { params: { status, limit: 100 } });
  return res.data;
};

export interface AppliedJobsResponse {
  metrics: {
    total_applied: number;
    applied_by_ai: number;
    applied_by_user: number;
    responses_count: number;
    interview_count: number;
  };
  applications: Application[];
  skip: number;
  limit: number;
}

export const getAppliedJobs = async (appliedBy?: string): Promise<AppliedJobsResponse> => {
  const res = await api.get('/applications/applied', { params: { applied_by: appliedBy } });
  return res.data;
};

export const recordManualApplication = async (data: {
  job_id?: number;
  company?: string;
  title?: string;
  applied_via?: string;
  status?: string;
  notes?: string;
  application_url?: string;
}): Promise<{ status: string; application_id: number; message: string }> => {
  const res = await api.post('/applications/record-manual', data);
  return res.data;
};

export const createApplication = async (data: { job_id: number; status?: string; notes?: string }): Promise<{ id: number }> => {
  const res = await api.post('/applications', data);
  return res.data;
};

export const updateApplicationStatus = async (id: number, status: string, notes?: string): Promise<any> => {
  const res = await api.put(`/applications/${id}/status`, { status, notes });
  return res.data;
};

export const updateApplicationDetails = async (id: number, details: Partial<Application>): Promise<any> => {
  const res = await api.put(`/applications/${id}`, details);
  return res.data;
};

export const autoApplyMatches = async (params?: { min_score?: number; max_count?: number; send_now?: boolean }): Promise<{
  processed_count: number;
  results: any[];
  gmail_connected: boolean;
}> => {
  const res = await api.post('/applications/auto-apply', params || {});
  return res.data;
};

// Emails
export const getEmails = async (status?: string): Promise<{ total: number; emails: Email[] }> => {
  const res = await api.get('/emails', { params: { status } });
  return res.data;
};

export const generateColdEmail = async (data: {
  job_id: number;
  recruiter_name?: string;
  recruiter_email?: string;
  recruiter_verified?: boolean;
  recipient_source?: string;
}): Promise<{
  job_id: number;
  job_title: string;
  company: string;
  to_email: string;
  to_name: string;
  subject: string;
  body: string;
  resume_id: number | null;
  recipient_verified: boolean;
  recipient_source: string | null;
}> => {
  const res = await api.post('/emails/generate', data);
  return res.data;
};

export const createEmailDraft = async (data: {
  job_id?: number;
  to_email: string;
  to_name?: string;
  subject: string;
  body: string;
  resume_id?: number;
  recipient_verified?: boolean;
  recipient_source?: string;
}): Promise<{ id: number }> => {
  const res = await api.post('/emails', data);
  return res.data;
};

export const updateEmailDraft = async (id: number, data: Partial<Email>): Promise<any> => {
  const res = await api.put(`/emails/${id}`, data);
  return res.data;
};

export const approveEmail = async (id: number): Promise<any> => {
  const res = await api.put(`/emails/${id}/approve`);
  return res.data;
};

export const cancelEmail = async (id: number): Promise<any> => {
  const res = await api.put(`/emails/${id}/cancel`);
  return res.data;
};

export const sendEmailViaGmail = async (id: number): Promise<any> => {
  const res = await api.post(`/gmail/send/${id}`);
  return res.data;
};

// Recruiters
export const getRecruiters = async (params?: { company?: string; status?: string }): Promise<Recruiter[]> => {
  const res = await api.get('/recruiters', { params });
  return res.data;
};

export const discoverRecruiters = async (company: string): Promise<{ company: string; count: number; recruiters: Recruiter[] }> => {
  const res = await api.post(`/recruiters/discover/${encodeURIComponent(company)}`);
  return res.data;
};

export const addRecruiter = async (data: Partial<Recruiter>): Promise<{ id: number }> => {
  const res = await api.post('/recruiters', data);
  return res.data;
};

// Resumes
export const getResumes = async (): Promise<Resume[]> => {
  const res = await api.get('/resumes');
  return res.data;
};

export const uploadResume = async (formData: FormData): Promise<any> => {
  const res = await api.post('/resumes/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return res.data;
};

export const setDefaultResume = async (id: number): Promise<any> => {
  const res = await api.put(`/resumes/${id}/set-default`);
  return res.data;
};

export const tailorResumeForJob = async (job_id: number): Promise<{ job_id: number; job_title: string; company: string; data: any }> => {
  const res = await api.post('/resumes/tailor', { job_id });
  return res.data;
};

export const answerApplicationQuestions = async (job_id: number, questions: string[]): Promise<{ answers: any[] }> => {
  const res = await api.post('/resumes/answer-questions', { job_id, questions });
  return res.data;
};

// Profile
export const getProfile = async (): Promise<Profile> => {
  const res = await api.get('/profile');
  return res.data;
};

export const updateProfile = async (profileData: Partial<Profile>): Promise<any> => {
  const res = await api.put('/profile', profileData);
  return res.data;
};

// Gmail Integration
export const getGmailStatus = async (): Promise<{ configured: boolean; connected: boolean; email: string | null; last_error: string | null }> => {
  const res = await api.get('/gmail/status');
  return res.data;
};

export const getGmailConnectUrl = async (): Promise<{ auth_url: string }> => {
  const res = await api.get('/gmail/connect');
  return res.data;
};

export const disconnectGmail = async (): Promise<any> => {
  const res = await api.post('/gmail/disconnect');
  return res.data;
};

// AI Providers
export const getAIProviderStatus = async (): Promise<{ providers: any[]; active_provider: string | null }> => {
  const res = await api.get('/ai/status');
  return res.data;
};

export const testAIProvider = async (provider: string): Promise<any> => {
  const res = await api.post(`/ai/test/${provider}`);
  return res.data;
};
