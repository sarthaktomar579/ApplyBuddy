import React, { useEffect, useState } from 'react';
import { getDashboardStats, getJobs, triggerJobDiscovery, createApplication } from '../services/api';
import { DashboardStats, Job } from '../types';
import { Navbar } from '../components/Navbar';
import { MatchBadge } from '../components/MatchBadge';
import { JobDetailsModal } from '../components/JobDetailsModal';
import { EmailComposerModal } from '../components/EmailComposerModal';
import { ManualJobModal } from '../components/ManualJobModal';
import { Link, useNavigate } from 'react-router-dom';
import {
  Briefcase,
  Mail,
  KanbanSquare,
  Sparkles,
  Users,
  Search,
  Plus,
  ArrowRight,
  TrendingUp,
  MapPin,
  Building2,
  Clock,
  CheckCircle2,
  Loader2,
  DollarSign
} from 'lucide-react';

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [topJobs, setTopJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [discovering, setDiscovering] = useState(false);
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [emailJob, setEmailJob] = useState<Job | null>(null);
  const [showManualModal, setShowManualModal] = useState(false);
  const [notification, setNotification] = useState<string | null>(null);

  const loadData = async () => {
    try {
      const [statsData, jobsData] = await Promise.all([
        getDashboardStats(),
        getJobs({ limit: 6 }),
      ]);
      setStats(statsData);
      setTopJobs(jobsData.jobs);
    } catch (err) {
      console.error('Failed to load dashboard data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleDiscover = async () => {
    setDiscovering(true);
    try {
      const res = await triggerJobDiscovery();
      setNotification(`Job discovery completed! Found ${res.discovered} fresh positions.`);
      setTimeout(() => setNotification(null), 4000);
      await loadData();
    } catch (err) {
      console.error(err);
    } finally {
      setDiscovering(false);
    }
  };

  const handleTrackApplication = async (job: Job) => {
    try {
      await createApplication({ job_id: job.id, status: 'shortlisted' });
      setNotification(`Job "${job.title}" added to your application tracker!`);
      setTimeout(() => setNotification(null), 3000);
      setSelectedJob(null);
      await loadData();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to add application');
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Navbar
        title="Mission Control"
        subtitle="AI-driven job discovery, matching, cold email generation, and tracking"
        actions={
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowManualModal(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition-colors"
            >
              <Plus className="w-3.5 h-3.5" />
              Add Job
            </button>
            <button
              onClick={handleDiscover}
              disabled={discovering}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white text-xs font-medium shadow-md shadow-indigo-600/30 transition-all disabled:opacity-60"
            >
              {discovering ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
              Discover Fresh Jobs
            </button>
          </div>
        }
      />

      <main className="flex-1 p-8 space-y-8 max-w-7xl mx-auto w-full">
        {notification && (
          <div className="p-3.5 rounded-xl bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-xs flex items-center justify-between animate-in fade-in">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>{notification}</span>
            </div>
            <button onClick={() => setNotification(null)} className="text-slate-400 hover:text-white">✕</button>
          </div>
        )}

        {/* Hero Candidate Profile Bar */}
        <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-indigo-950/60 via-purple-950/40 to-slate-900 border border-indigo-500/20 p-6 md:p-8">
          <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="space-y-2">
              <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-indigo-500/20 text-indigo-300 text-xs font-semibold">
                <SparkAgentIcon className="w-3.5 h-3.5" /> Active Agent Workspace
              </div>
              <h2 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
                Welcome back, Sarthak.
              </h2>
              <p className="text-sm text-slate-300 max-w-2xl leading-relaxed">
                ApplyPilot is continuously scouring tech portals, calculating precision match scores for
                roles in Bengaluru, Hyderabad, Pune, & Remote, and preparing tailored recruiter emails.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <button
                onClick={handleDiscover}
                disabled={discovering}
                className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/30 transition-all"
              >
                {discovering ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                Scan For Opportunities
              </button>
              <Link
                to="/emails"
                className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition-all"
              >
                <Mail className="w-4 h-4 text-purple-400" />
                Review Approvals ({stats?.emails?.awaiting_approval || 0})
              </Link>
            </div>
          </div>
        </div>

        {/* KPI Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="glass-panel p-5 rounded-xl border border-slate-800/80 hover:border-slate-700 transition-all">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-400">Discovered Jobs</span>
              <div className="w-8 h-8 rounded-lg bg-indigo-500/10 text-indigo-400 flex items-center justify-center">
                <Briefcase className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-3xl font-extrabold text-white">{stats?.jobs.total || 0}</span>
              <span className="text-xs text-indigo-400 font-medium">{stats?.jobs.active || 0} Active</span>
            </div>
            <p className="text-[11px] text-slate-500 mt-1">Deduplicated from curated sources</p>
          </div>

          <div className="glass-panel p-5 rounded-xl border border-slate-800/80 hover:border-slate-700 transition-all">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-400">High AI Match (70%+)</span>
              <div className="w-8 h-8 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center">
                <TrendingUp className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-3xl font-extrabold text-white">{stats?.jobs.high_match || 0}</span>
              <span className="text-xs text-emerald-400 font-medium">Strong Fit</span>
            </div>
            <p className="text-[11px] text-slate-500 mt-1">Direct skills & project alignment</p>
          </div>

          <div className="glass-panel p-5 rounded-xl border border-slate-800/80 hover:border-slate-700 transition-all">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-400">Email Approvals</span>
              <div className="w-8 h-8 rounded-lg bg-purple-500/10 text-purple-400 flex items-center justify-center">
                <Mail className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-3xl font-extrabold text-white">{stats?.emails.awaiting_approval || 0}</span>
              <span className="text-xs text-purple-400 font-medium">{stats?.emails.draft || 0} Drafts</span>
            </div>
            <p className="text-[11px] text-slate-500 mt-1">Human approval gate enabled</p>
          </div>

          <div className="glass-panel p-5 rounded-xl border border-slate-800/80 hover:border-slate-700 transition-all">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-400">Pipeline Applications</span>
              <div className="w-8 h-8 rounded-lg bg-amber-500/10 text-amber-400 flex items-center justify-center">
                <KanbanSquare className="w-4 h-4" />
              </div>
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-3xl font-extrabold text-white">{stats?.applications.total || 0}</span>
              <span className="text-xs text-amber-400 font-medium">{stats?.recruiters.verified || 0} Recruiters</span>
            </div>
            <p className="text-[11px] text-slate-500 mt-1">Interviews & follow-ups tracked</p>
          </div>
        </div>

        {/* Top Matches Section */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-bold text-white tracking-tight flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-indigo-400" />
                Top Opportunities Matched to Your Profile
              </h3>
              <p className="text-xs text-slate-400">
                Ranked by AI matching engine using your skills, projects (Medical PiP & AI Saraj), and experience
              </p>
            </div>
            <Link
              to="/jobs"
              className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 flex items-center gap-1"
            >
              View All Opportunities <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {topJobs.map((job) => (
              <div
                key={job.id}
                className="glass-panel p-5 rounded-xl border border-slate-800/80 hover:border-indigo-500/40 transition-all flex flex-col justify-between group"
              >
                <div className="space-y-3">
                  <div className="flex items-start justify-between gap-2">
                    <span className="text-xs font-semibold text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20">
                      {job.company}
                    </span>
                    {job.match && <MatchBadge score={job.match.overall_score} size="sm" />}
                  </div>

                  <div>
                    <h4
                      onClick={() => setSelectedJob(job)}
                      className="text-sm font-bold text-white group-hover:text-indigo-300 transition-colors cursor-pointer line-clamp-1"
                    >
                      {job.title}
                    </h4>
                    <div className="flex items-center gap-3 text-xs text-slate-400 mt-1.5">
                      <span className="flex items-center gap-1">
                        <MapPin className="w-3 h-3 text-slate-500" />
                        {job.location || 'Remote'}
                      </span>
                      {job.salary_min && (
                        <span className="flex items-center gap-1 text-emerald-400 font-medium">
                          <DollarSign className="w-3 h-3" />
                          ₹{(job.salary_min / 100000).toFixed(1)}L+
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Skills tags preview */}
                  <div className="flex flex-wrap gap-1 pt-1">
                    {job.required_skills?.slice(0, 3).map((s, idx) => (
                      <span key={idx} className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700/60">
                        {s}
                      </span>
                    ))}
                    {(job.required_skills?.length || 0) > 3 && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800/50 text-slate-500">
                        +{(job.required_skills?.length || 0) - 3} more
                      </span>
                    )}
                  </div>
                </div>

                <div className="pt-4 mt-4 border-t border-slate-800/80 flex items-center justify-between gap-2">
                  <button
                    onClick={() => setSelectedJob(job)}
                    className="text-xs text-slate-400 hover:text-white transition-colors"
                  >
                    View Analysis
                  </button>
                  <button
                    onClick={() => setEmailJob(job)}
                    className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-indigo-600/80 hover:bg-indigo-600 text-white text-xs font-medium transition-colors"
                  >
                    <Mail className="w-3 h-3" />
                    Draft Email
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </main>

      {/* Modals */}
      {selectedJob && (
        <JobDetailsModal
          job={selectedJob}
          onClose={() => setSelectedJob(null)}
          onDraftEmail={(j) => {
            setSelectedJob(null);
            setEmailJob(j);
          }}
          onTrackApplication={handleTrackApplication}
          onTailorResume={(j) => {
            navigate('/resume-studio');
          }}
        />
      )}

      {emailJob && (
        <EmailComposerModal
          job={emailJob}
          onClose={() => setEmailJob(null)}
          onSuccess={() => {
            loadData();
          }}
        />
      )}

      {showManualModal && (
        <ManualJobModal
          onClose={() => setShowManualModal(false)}
          onSuccess={() => {
            loadData();
          }}
        />
      )}
    </div>
  );
};

const SparkAgentIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
    <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
  </svg>
);
