import React, { useState, useEffect } from 'react';
import { getJobs, toggleBookmark, triggerJobDiscovery, createApplication, evaluateJobMatch, autoApplyMatches } from '../services/api';
import { Job } from '../types';
import { Navbar } from '../components/Navbar';
import { MatchBadge } from '../components/MatchBadge';
import { JobDetailsModal } from '../components/JobDetailsModal';
import { EmailComposerModal } from '../components/EmailComposerModal';
import { ManualJobModal } from '../components/ManualJobModal';
import { useNavigate } from 'react-router-dom';
import {
  Search,
  Filter,
  Plus,
  Bookmark,
  BookmarkCheck,
  Mail,
  Building2,
  MapPin,
  Clock,
  DollarSign,
  Sparkles,
  ExternalLink,
  Loader2,
  RefreshCw,
  CheckCircle2,
  Send
} from 'lucide-react';

export const JobsPage: React.FC = () => {
  const navigate = useNavigate();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [locationFilter, setLocationFilter] = useState('');
  const [minScoreFilter, setMinScoreFilter] = useState<number>(0);
  const [bookmarkedOnly, setBookmarkedOnly] = useState(false);
  const [latestOnly, setLatestOnly] = useState(true);
  const [sourceFilter, setSourceFilter] = useState('');
  const [discovering, setDiscovering] = useState(false);
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [emailJob, setEmailJob] = useState<Job | null>(null);
  const [showManualModal, setShowManualModal] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [autoApplying, setAutoApplying] = useState(false);

  const fetchJobsList = async () => {
    setLoading(true);
    try {
      const data = await getJobs({
        search: search || undefined,
        location: locationFilter || undefined,
        source: sourceFilter || undefined,
        latest_only: latestOnly,
        is_bookmarked: bookmarkedOnly ? true : undefined,
        limit: 50,
      });
      setJobs(data.jobs);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobsList();
  }, [search, locationFilter, bookmarkedOnly, latestOnly, sourceFilter]);

  const handleToggleBookmark = async (e: React.MouseEvent, job: Job) => {
    e.stopPropagation();
    try {
      const res = await toggleBookmark(job.id);
      setJobs((prev) =>
        prev.map((j) => (j.id === job.id ? { ...j, is_bookmarked: res.bookmarked } : j))
      );
    } catch (err) {
      console.error(err);
    }
  };

  const handleDiscover = async () => {
    setDiscovering(true);
    try {
      const res = await triggerJobDiscovery();
      setToastMessage(res.message);
      setTimeout(() => setToastMessage(null), 4000);
      await fetchJobsList();
    } catch (err) {
      console.error(err);
    } finally {
      setDiscovering(false);
    }
  };

  const handleTrackApplication = async (job: Job) => {
    try {
      await createApplication({ job_id: job.id, status: 'shortlisted' });
      setToastMessage(`Job "${job.title}" added to your application tracker!`);
      setTimeout(() => setToastMessage(null), 3000);
      setSelectedJob(null);
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to add application');
    }
  };

  const handleAutoApply = async () => {
    if (!window.confirm('Auto-Apply will generate personalized cold emails for all 70%+ match jobs, attach your resume (Resume_SarthakT.pdf), and dispatch them via your Gmail. Proceed?')) {
      return;
    }
    setAutoApplying(true);
    try {
      const res = await autoApplyMatches({ min_score: 70, max_count: 5, send_now: true });
      if (res.processed_count > 0) {
        setToastMessage(`Auto-applied to ${res.processed_count} top matching jobs! Resume attached & emails processed.`);
      } else {
        setToastMessage('All high-match jobs are already applied to or in your pipeline!');
      }
      setTimeout(() => setToastMessage(null), 5000);
      await fetchJobsList();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to auto-apply');
    } finally {
      setAutoApplying(false);
    }
  };

  const filteredJobs = jobs.filter((j) => {
    if (minScoreFilter > 0) {
      return (j.match?.overall_score || 0) >= minScoreFilter;
    }
    return true;
  });

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Navbar
        title="Job Discovery & AI Matching"
        subtitle="Automated scouting of software engineering openings with instant match ranking"
        actions={
          <div className="flex items-center gap-2">
            <button
              onClick={() => navigate('/applied-jobs')}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition-colors"
            >
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              View Applied Jobs
            </button>
            <button
              onClick={handleAutoApply}
              disabled={autoApplying}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-xs font-semibold shadow-md shadow-emerald-600/30 transition-all disabled:opacity-60"
            >
              {autoApplying ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
              Auto-Apply to High Matches (70%+)
            </button>
            <button
              onClick={() => setShowManualModal(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition-colors"
            >
              <Plus className="w-3.5 h-3.5" />
              Add Job Manually
            </button>
            <button
              onClick={handleDiscover}
              disabled={discovering}
              className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium shadow-md shadow-indigo-600/30 transition-all disabled:opacity-60"
            >
              {discovering ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
              Scout Fresh Jobs
            </button>
          </div>
        }
      />

      <main className="flex-1 p-8 space-y-6 max-w-7xl mx-auto w-full">
        {toastMessage && (
          <div className="p-3.5 rounded-xl bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-xs flex items-center justify-between animate-in fade-in">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>{toastMessage}</span>
            </div>
            <button onClick={() => setToastMessage(null)} className="text-slate-400 hover:text-white">✕</button>
          </div>
        )}

        {/* Search & Filter Toolbar */}
        <div className="glass-panel p-4 rounded-xl border border-slate-800 space-y-3">
          <div className="flex flex-col md:flex-row gap-3">
            <div className="flex-1 relative">
              <Search className="w-4 h-4 absolute left-3.5 top-3 text-slate-500" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search by title, company, or tech stack (e.g. React, Python, SDE)..."
                className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-10 pr-4 py-2 text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div className="flex flex-wrap items-center gap-2">
              {/* Latest Jobs Filter Toggle */}
              <button
                type="button"
                onClick={() => setLatestOnly(!latestOnly)}
                className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold border transition-all ${
                  latestOnly
                    ? 'bg-gradient-to-r from-amber-500/20 to-orange-500/20 text-amber-300 border-amber-500/40 shadow-sm'
                    : 'bg-slate-950 text-slate-400 border-slate-800 hover:text-slate-200'
                }`}
              >
                <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                Latest Only (≥ Oct 22, 2026)
              </button>

              {/* Source Filter */}
              <select
                value={sourceFilter}
                onChange={(e) => setSourceFilter(e.target.value)}
                className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 font-medium"
              >
                <option value="">All Job Sources</option>
                <option value="linkedin">LinkedIn Jobs Only</option>
                <option value="careers_portal">Company Portals</option>
                <option value="greenhouse">Greenhouse / Lever</option>
              </select>

              <select
                value={locationFilter}
                onChange={(e) => setLocationFilter(e.target.value)}
                className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
              >
                <option value="">All Locations</option>
                <option value="Bengaluru">Bengaluru</option>
                <option value="Hyderabad">Hyderabad</option>
                <option value="Pune">Pune</option>
                <option value="Mumbai">Mumbai</option>
                <option value="Delhi">Delhi NCR</option>
                <option value="Remote">Remote</option>
              </select>

              <select
                value={minScoreFilter}
                onChange={(e) => setMinScoreFilter(Number(e.target.value))}
                className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
              >
                <option value="0">All Match Scores</option>
                <option value="80">High Fit (80%+)</option>
                <option value="70">Good Fit (70%+)</option>
                <option value="60">Eligible (60%+)</option>
              </select>

              <button
                type="button"
                onClick={() => setBookmarkedOnly(!bookmarkedOnly)}
                className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium border transition-colors ${
                  bookmarkedOnly
                    ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                    : 'bg-slate-950 text-slate-400 border-slate-800 hover:text-slate-200'
                }`}
              >
                <Bookmark className="w-3.5 h-3.5" />
                Bookmarked
              </button>
            </div>
          </div>
        </div>

        {/* Jobs List */}
        {loading ? (
          <div className="p-16 flex flex-col items-center justify-center space-y-3">
            <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
            <p className="text-xs text-slate-400">Loading matched opportunities...</p>
          </div>
        ) : filteredJobs.length === 0 ? (
          <div className="glass-panel p-16 rounded-xl border border-slate-800 text-center space-y-4">
            <div className="w-12 h-12 rounded-full bg-slate-800 text-slate-400 mx-auto flex items-center justify-center">
              <Search className="w-6 h-6" />
            </div>
            <div>
              <h3 className="font-bold text-white text-base">No Matching Jobs Found</h3>
              <p className="text-xs text-slate-400 max-w-md mx-auto mt-1">
                Try loosening your filters or click "Scout Fresh Jobs" to let the AI discover more active tech openings.
              </p>
            </div>
            <button
              onClick={handleDiscover}
              className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium shadow-md shadow-indigo-600/30"
            >
              Scout Fresh Jobs Now
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {filteredJobs.map((job) => (
              <div
                key={job.id}
                onClick={() => setSelectedJob(job)}
                className="glass-panel p-5 rounded-xl border border-slate-800 hover:border-indigo-500/40 transition-all cursor-pointer flex flex-col md:flex-row md:items-center justify-between gap-4 group"
              >
                {/* Left Job Info */}
                <div className="space-y-2 flex-1">
                  <div className="flex flex-wrap items-center gap-2.5">
                    <span className="text-xs font-semibold text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20">
                      {job.company}
                    </span>
                    <h3 className="text-base font-bold text-white group-hover:text-indigo-300 transition-colors">
                      {job.title}
                    </h3>
                    <span
                      className={`text-[11px] px-2 py-0.5 rounded font-medium border ${
                        job.source === 'linkedin'
                          ? 'bg-blue-600/15 text-blue-400 border-blue-500/30 font-semibold'
                          : 'bg-slate-800 text-slate-300 border-slate-700'
                      }`}
                    >
                      {job.source === 'linkedin' ? 'LinkedIn Job' : job.source?.replace('_', ' ') || 'Direct'}
                    </span>
                    {job.match && <MatchBadge score={job.match.overall_score} size="sm" />}
                  </div>

                  <div className="flex flex-wrap items-center gap-4 text-xs text-slate-400">
                    <span className="flex items-center gap-1">
                      <MapPin className="w-3.5 h-3.5 text-slate-500" />
                      {job.location || 'Remote'} ({job.work_arrangement || 'Flexible'})
                    </span>
                    {job.date_posted && (
                      <span className="flex items-center gap-1 text-amber-300/90 font-medium">
                        <Clock className="w-3.5 h-3.5 text-amber-400/80" />
                        Posted: {new Date(job.date_posted).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                      </span>
                    )}
                    {job.salary_min && (
                      <span className="flex items-center gap-1 text-emerald-400 font-medium">
                        <DollarSign className="w-3.5 h-3.5" />
                        ₹{(job.salary_min / 100000).toFixed(1)} - ₹{((job.salary_max || job.salary_min) / 100000).toFixed(1)} LPA
                      </span>
                    )}
                    {job.experience_required && (
                      <span className="flex items-center gap-1">
                        <Clock className="w-3.5 h-3.5 text-slate-500" />
                        {job.experience_required}
                      </span>
                    )}
                  </div>

                  {/* Skills Pills */}
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {job.match?.matching_skills?.slice(0, 4).map((s, idx) => (
                      <span key={idx} className="text-[10px] px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
                        ✓ {s}
                      </span>
                    ))}
                    {job.match?.missing_skills?.slice(0, 2).map((s, idx) => (
                      <span key={idx} className="text-[10px] px-2 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/20">
                        + {s}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Right Action Buttons */}
                <div className="flex items-center gap-2 shrink-0" onClick={(e) => e.stopPropagation()}>
                  <button
                    onClick={(e) => handleToggleBookmark(e, job)}
                    className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-amber-400 hover:border-slate-700 transition-colors"
                    title={job.is_bookmarked ? 'Remove bookmark' : 'Bookmark job'}
                  >
                    {job.is_bookmarked ? (
                      <BookmarkCheck className="w-4 h-4 text-amber-400" />
                    ) : (
                      <Bookmark className="w-4 h-4" />
                    )}
                  </button>

                  <button
                    onClick={() => setEmailJob(job)}
                    className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium shadow-md shadow-indigo-600/30 transition-colors"
                  >
                    <Mail className="w-3.5 h-3.5" />
                    Draft Email
                  </button>

                  {job.application_url && (
                    <a
                      href={job.application_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-white hover:border-slate-700 transition-colors"
                      title="Open job posting"
                    >
                      <ExternalLink className="w-4 h-4" />
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
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
            fetchJobsList();
          }}
        />
      )}

      {showManualModal && (
        <ManualJobModal
          onClose={() => setShowManualModal(false)}
          onSuccess={() => {
            fetchJobsList();
          }}
        />
      )}
    </div>
  );
};
