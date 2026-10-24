import React, { useState, useEffect } from 'react';
import {
  CheckCircle2,
  Bot,
  UserCheck,
  Send,
  Building2,
  MapPin,
  Calendar,
  ExternalLink,
  Plus,
  Search,
  Filter,
  FileText,
  Mail,
  Zap,
  Clock,
  Sparkles,
  ChevronDown,
  X,
  AlertCircle
} from 'lucide-react';
import { Application } from '../types';
import {
  getAppliedJobs,
  recordManualApplication,
  updateApplicationStatus,
  instantApplyAllLatest,
  AppliedJobsResponse
} from '../services/api';

const STATUS_OPTIONS = [
  { value: 'email_sent', label: 'Email Sent', color: 'bg-blue-500/10 text-blue-400 border-blue-500/20' },
  { value: 'application_submitted', label: 'Submitted (Portal/LinkedIn)', color: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20' },
  { value: 'preparing_application', label: 'Preparing / Queued', color: 'bg-amber-500/10 text-amber-400 border-amber-500/20' },
  { value: 'recruiter_replied', label: 'Recruiter Replied', color: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' },
  { value: 'interview_scheduled', label: 'Interview Scheduled', color: 'bg-purple-500/10 text-purple-400 border-purple-500/20' },
  { value: 'offer_received', label: 'Offer Received', color: 'bg-green-500/10 text-green-300 border-green-500/30' },
  { value: 'rejected', label: 'Not Selected', color: 'bg-rose-500/10 text-rose-400 border-rose-500/20' },
];

export const AppliedJobsPage: React.FC = () => {
  const [data, setData] = useState<AppliedJobsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'all' | 'ai' | 'user'>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [isApplyingAll, setIsApplyingAll] = useState(false);
  const [notification, setNotification] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  // Manual record modal
  const [showManualModal, setShowManualModal] = useState(false);
  const [manualCompany, setManualCompany] = useState('');
  const [manualTitle, setManualTitle] = useState('');
  const [manualVia, setManualVia] = useState('linkedin');
  const [manualStatus, setManualStatus] = useState('application_submitted');
  const [manualUrl, setManualUrl] = useState('');
  const [manualNotes, setManualNotes] = useState('');
  const [isSavingManual, setIsSavingManual] = useState(false);

  const fetchData = async (tab = activeTab) => {
    try {
      setLoading(true);
      const appliedByParam = tab === 'all' ? undefined : tab;
      const res = await getAppliedJobs(appliedByParam);
      setData(res);
    } catch (err) {
      console.error('Failed to load applied jobs', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData(activeTab);
  }, [activeTab]);

  const handleInstantApplyAll = async () => {
    try {
      setIsApplyingAll(true);
      const res = await instantApplyAllLatest(70);
      setNotification({
        message: res.message || `Successfully auto-applied to relevant positions!`,
        type: 'success'
      });
      fetchData(activeTab);
    } catch (err: any) {
      setNotification({
        message: err.response?.data?.detail || 'Failed to trigger instant auto-apply',
        type: 'error'
      });
    } finally {
      setIsApplyingAll(false);
    }
  };

  const handleStatusChange = async (appId: number, newStatus: string) => {
    try {
      await updateApplicationStatus(appId, newStatus);
      setNotification({ message: 'Status updated successfully', type: 'success' });
      fetchData(activeTab);
    } catch (err) {
      setNotification({ message: 'Failed to update status', type: 'error' });
    }
  };

  const handleSaveManualApplication = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!manualCompany || !manualTitle) {
      setNotification({ message: 'Please provide company and job title', type: 'error' });
      return;
    }
    try {
      setIsSavingManual(true);
      await recordManualApplication({
        company: manualCompany,
        title: manualTitle,
        applied_via: manualVia,
        status: manualStatus,
        application_url: manualUrl,
        notes: manualNotes,
      });
      setNotification({ message: 'Application recorded under "Applied by You"!', type: 'success' });
      setShowManualModal(false);
      setManualCompany('');
      setManualTitle('');
      setManualUrl('');
      setManualNotes('');
      fetchData(activeTab);
    } catch (err: any) {
      setNotification({ message: err.response?.data?.detail || 'Failed to record application', type: 'error' });
    } finally {
      setIsSavingManual(false);
    }
  };

  const applications = data?.applications || [];
  const filteredApplications = applications.filter((app) => {
    const title = app.job?.title || app.job_title || '';
    const company = app.job?.company || app.company || '';
    const query = searchQuery.toLowerCase();
    return title.toLowerCase().includes(query) || company.toLowerCase().includes(query);
  });

  return (
    <div className="space-y-6">
      {/* Top Banner & Alert */}
      {notification && (
        <div
          className={`flex items-center justify-between p-4 rounded-xl border backdrop-blur-md transition-all ${
            notification.type === 'success'
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
              : 'bg-rose-500/10 border-rose-500/30 text-rose-300'
          }`}
        >
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 shrink-0" />
            <span className="text-sm font-medium">{notification.message}</span>
          </div>
          <button onClick={() => setNotification(null)} className="p-1 hover:opacity-75">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-bold tracking-tight text-white">Applied Jobs</h1>
            <span className="px-3 py-1 rounded-full text-xs font-semibold bg-primary-500/10 text-primary-400 border border-primary-500/20">
              {data?.metrics.total_applied || 0} Total Applied
            </span>
          </div>
          <p className="text-gray-400 text-sm mt-1">
            Complete registry of all jobs applied either autonomously by your AI agent or recorded by you.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowManualModal(true)}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gray-800 hover:bg-gray-700 text-white font-medium text-sm border border-gray-700 shadow-sm transition-all"
          >
            <Plus className="w-4 h-4 text-emerald-400" />
            Record Job Applied by Me
          </button>

          <button
            onClick={handleInstantApplyAll}
            disabled={isApplyingAll}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-primary-600 via-indigo-600 to-purple-600 hover:from-primary-500 hover:to-purple-500 text-white font-medium text-sm shadow-lg shadow-primary-500/25 transition-all disabled:opacity-50"
          >
            {isApplyingAll ? (
              <>
                <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                <span>Auto-Applying...</span>
              </>
            ) : (
              <>
                <Zap className="w-4 h-4 text-amber-300" />
                <span>Instant Auto-Apply All</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 rounded-2xl bg-gray-900/60 border border-gray-800 backdrop-blur-xl">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Total Applied</span>
            <div className="p-2 rounded-xl bg-primary-500/10 text-primary-400">
              <CheckCircle2 className="w-5 h-5" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-white mt-3">{data?.metrics.total_applied || 0}</div>
          <p className="text-xs text-gray-500 mt-1">Positions actively submitted</p>
        </div>

        <div className="p-5 rounded-2xl bg-gradient-to-br from-purple-950/40 to-gray-900/60 border border-purple-500/20 backdrop-blur-xl">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-purple-300 uppercase tracking-wider">Applied by AI Agent</span>
            <div className="p-2 rounded-xl bg-purple-500/20 text-purple-300">
              <Bot className="w-5 h-5" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-purple-200 mt-3">{data?.metrics.applied_by_ai || 0}</div>
          <p className="text-xs text-purple-400/80 mt-1">Autonomous instant applications</p>
        </div>

        <div className="p-5 rounded-2xl bg-gradient-to-br from-emerald-950/40 to-gray-900/60 border border-emerald-500/20 backdrop-blur-xl">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-emerald-300 uppercase tracking-wider">Applied by You</span>
            <div className="p-2 rounded-xl bg-emerald-500/20 text-emerald-300">
              <UserCheck className="w-5 h-5" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-emerald-200 mt-3">{data?.metrics.applied_by_user || 0}</div>
          <p className="text-xs text-emerald-400/80 mt-1">Manual LinkedIn / portal submissions</p>
        </div>

        <div className="p-5 rounded-2xl bg-gradient-to-br from-amber-950/40 to-gray-900/60 border border-amber-500/20 backdrop-blur-xl">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-amber-300 uppercase tracking-wider">Responses & Interviews</span>
            <div className="p-2 rounded-xl bg-amber-500/20 text-amber-300">
              <Sparkles className="w-5 h-5" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-amber-200 mt-3">{data?.metrics.responses_count || 0}</div>
          <p className="text-xs text-amber-400/80 mt-1">Direct recruiter replies & calls</p>
        </div>
      </div>

      {/* Tabs and Search Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 p-2 bg-gray-900/40 rounded-2xl border border-gray-800">
        <div className="flex items-center gap-2 p-1 bg-gray-900 rounded-xl border border-gray-800/80 w-full sm:w-auto">
          <button
            onClick={() => setActiveTab('all')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'all'
                ? 'bg-primary-600 text-white shadow-md'
                : 'text-gray-400 hover:text-white hover:bg-gray-800/50'
            }`}
          >
            All Applied ({data?.metrics.total_applied || 0})
          </button>
          <button
            onClick={() => setActiveTab('ai')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'ai'
                ? 'bg-purple-600 text-white shadow-md'
                : 'text-gray-400 hover:text-white hover:bg-gray-800/50'
            }`}
          >
            <Bot className="w-4 h-4 text-purple-300" />
            By AI Agent ({data?.metrics.applied_by_ai || 0})
          </button>
          <button
            onClick={() => setActiveTab('user')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'user'
                ? 'bg-emerald-600 text-white shadow-md'
                : 'text-gray-400 hover:text-white hover:bg-gray-800/50'
            }`}
          >
            <UserCheck className="w-4 h-4 text-emerald-300" />
            By You ({data?.metrics.applied_by_user || 0})
          </button>
        </div>

        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 absolute left-3.5 top-3 text-gray-500" />
          <input
            type="text"
            placeholder="Search company or role..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-gray-900 border border-gray-800 rounded-xl text-sm text-white placeholder-gray-500 focus:outline-none focus:border-primary-500"
          >
          </input>
        </div>
      </div>

      {/* Applications List */}
      {loading ? (
        <div className="py-20 flex flex-col items-center justify-center text-gray-500">
          <div className="w-8 h-8 border-2 border-primary-500 border-t-transparent rounded-full animate-spin mb-3" />
          <p className="text-sm">Loading applied jobs...</p>
        </div>
      ) : filteredApplications.length === 0 ? (
        <div className="py-16 text-center rounded-2xl border border-dashed border-gray-800 bg-gray-900/30">
          <CheckCircle2 className="w-12 h-12 mx-auto text-gray-600 mb-3" />
          <h3 className="text-lg font-semibold text-white">No applications found in this view</h3>
          <p className="text-sm text-gray-400 max-w-md mx-auto mt-1 mb-6">
            {activeTab === 'user'
              ? 'You have not recorded any manual applications yet. Click below to add one.'
              : 'Click "Instant Auto-Apply All" to automatically send tailored applications to recent high-match jobs.'}
          </p>
          <div className="flex items-center justify-center gap-3">
            <button
              onClick={() => setShowManualModal(true)}
              className="px-4 py-2 rounded-xl bg-gray-800 hover:bg-gray-700 text-white text-sm font-medium border border-gray-700"
            >
              Record Job Applied by Me
            </button>
            <button
              onClick={handleInstantApplyAll}
              className="px-4 py-2 rounded-xl bg-primary-600 hover:bg-primary-500 text-white text-sm font-medium"
            >
              Run Instant Auto-Apply
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredApplications.map((app) => {
            const isAi = app.applied_by === 'ai' || (app.notes || '').toLowerCase().includes('auto-applied');
            const jobTitle = app.job?.title || app.job_title || 'Software Engineering Role';
            const companyName = app.job?.company || app.company || 'Tech Company';
            const location = app.job?.location || app.location || 'Bengaluru / Remote';
            const source = app.job?.source || app.applied_via || 'careers_portal';
            const appUrl = app.job?.application_url || app.application_url;
            const appliedDate = app.updated_at || app.created_at;

            return (
              <div
                key={app.id}
                className="p-5 rounded-2xl bg-gray-900/70 border border-gray-800/90 hover:border-gray-700/80 transition-all shadow-sm"
              >
                <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                  {/* Left Column: Job & Company Details */}
                  <div className="flex items-start gap-4">
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-gray-800 to-gray-700 border border-gray-600/30 flex items-center justify-center text-white font-bold text-lg shrink-0 shadow-inner">
                      {companyName.slice(0, 2).toUpperCase()}
                    </div>

                    <div className="space-y-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <h3 className="text-base font-semibold text-white hover:text-primary-400 transition-colors">
                          {jobTitle}
                        </h3>

                        {/* Source Tag */}
                        <span
                          className={`px-2.5 py-0.5 rounded-md text-xs font-medium border ${
                            source === 'linkedin'
                              ? 'bg-blue-600/10 text-blue-400 border-blue-500/20'
                              : 'bg-gray-800 text-gray-300 border-gray-700'
                          }`}
                        >
                          {source === 'linkedin' ? 'LinkedIn Job' : source.replace('_', ' ')}
                        </span>

                        {/* Applied By Badge */}
                        {isAi ? (
                          <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-md text-xs font-semibold bg-purple-500/15 text-purple-300 border border-purple-500/30">
                            <Bot className="w-3.5 h-3.5 text-purple-300" />
                            Applied by AI Agent
                          </span>
                        ) : (
                          <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-md text-xs font-semibold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
                            <UserCheck className="w-3.5 h-3.5 text-emerald-300" />
                            Applied by You
                          </span>
                        )}
                      </div>

                      <div className="flex flex-wrap items-center gap-4 text-xs text-gray-400">
                        <span className="flex items-center gap-1 text-gray-300 font-medium">
                          <Building2 className="w-3.5 h-3.5 text-gray-400" />
                          {companyName}
                        </span>

                        <span className="flex items-center gap-1">
                          <MapPin className="w-3.5 h-3.5 text-gray-500" />
                          {location}
                        </span>

                        {appliedDate && (
                          <span className="flex items-center gap-1 text-gray-400">
                            <Calendar className="w-3.5 h-3.5 text-gray-500" />
                            Applied: {new Date(appliedDate).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                          </span>
                        )}

                        {/* Attached Resume */}
                        <span className="flex items-center gap-1 text-xs text-primary-400 bg-primary-500/10 px-2 py-0.5 rounded border border-primary-500/20 font-medium">
                          <FileText className="w-3 h-3" />
                          Resume_SarthakT.pdf attached
                        </span>
                      </div>

                      {/* Notes / Recruiter Evidence */}
                      {app.notes && (
                        <p className="text-xs text-gray-400 mt-1 italic line-clamp-1 bg-gray-950/40 px-2.5 py-1 rounded border border-gray-800/50">
                          {app.notes}
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Right Column: Status Dropdown & Actions */}
                  <div className="flex items-center gap-3 self-end lg:self-center shrink-0">
                    {/* Status Dropdown */}
                    <div className="relative">
                      <select
                        value={app.status}
                        onChange={(e) => handleStatusChange(app.id, e.target.value)}
                        className="appearance-none bg-gray-950 border border-gray-700 text-xs font-semibold rounded-xl px-3.5 py-2 pr-8 text-white focus:outline-none focus:border-primary-500 cursor-pointer shadow-sm hover:border-gray-600 transition-colors"
                      >
                        {STATUS_OPTIONS.map((opt) => (
                          <option key={opt.value} value={opt.value}>
                            {opt.label}
                          </option>
                        ))}
                      </select>
                      <ChevronDown className="w-3.5 h-3.5 absolute right-2.5 top-3 text-gray-400 pointer-events-none" />
                    </div>

                    {appUrl && (
                      <a
                        href={appUrl}
                        target="_blank"
                        rel="noreferrer"
                        className="p-2 rounded-xl bg-gray-800/80 hover:bg-gray-700 text-gray-300 hover:text-white border border-gray-700/60 transition-colors"
                        title="View Posting"
                      >
                        <ExternalLink className="w-4 h-4" />
                      </a>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Record Manual Application Modal */}
      {showManualModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-gray-900 border border-gray-800 rounded-2xl w-full max-w-lg p-6 shadow-2xl relative">
            <div className="flex items-center justify-between pb-4 border-b border-gray-800">
              <div className="flex items-center gap-2">
                <UserCheck className="w-5 h-5 text-emerald-400" />
                <h2 className="text-lg font-bold text-white">Record Job Applied by You</h2>
              </div>
              <button
                onClick={() => setShowManualModal(false)}
                className="text-gray-400 hover:text-white p-1 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSaveManualApplication} className="space-y-4 mt-4">
              <div>
                <label className="block text-xs font-medium text-gray-300 mb-1">Company Name *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Swiggy, Zepto, InMobi"
                  value={manualCompany}
                  onChange={(e) => setManualCompany(e.target.value)}
                  className="w-full px-3.5 py-2 bg-gray-950 border border-gray-800 rounded-xl text-sm text-white focus:outline-none focus:border-primary-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-300 mb-1">Role Title *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Software Engineer (Frontend / SDE-1)"
                  value={manualTitle}
                  onChange={(e) => setManualTitle(e.target.value)}
                  className="w-full px-3.5 py-2 bg-gray-950 border border-gray-800 rounded-xl text-sm text-white focus:outline-none focus:border-primary-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-gray-300 mb-1">Applied Via</label>
                  <select
                    value={manualVia}
                    onChange={(e) => setManualVia(e.target.value)}
                    className="w-full px-3 py-2 bg-gray-950 border border-gray-800 rounded-xl text-sm text-white focus:outline-none focus:border-primary-500"
                  >
                    <option value="linkedin">LinkedIn Easy Apply</option>
                    <option value="careers_portal">Company Careers Portal</option>
                    <option value="email">Direct Recruiter Email</option>
                    <option value="referral">Employee Referral</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-gray-300 mb-1">Current Status</label>
                  <select
                    value={manualStatus}
                    onChange={(e) => setManualStatus(e.target.value)}
                    className="w-full px-3 py-2 bg-gray-950 border border-gray-800 rounded-xl text-sm text-white focus:outline-none focus:border-primary-500"
                  >
                    <option value="application_submitted">Application Submitted</option>
                    <option value="recruiter_replied">Recruiter Replied</option>
                    <option value="interview_scheduled">Interview Scheduled</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-300 mb-1">Application URL (Optional)</label>
                <input
                  type="url"
                  placeholder="https://www.linkedin.com/jobs/view/..."
                  value={manualUrl}
                  onChange={(e) => setManualUrl(e.target.value)}
                  className="w-full px-3.5 py-2 bg-gray-950 border border-gray-800 rounded-xl text-sm text-white focus:outline-none focus:border-primary-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-300 mb-1">Notes / Follow-up details</label>
                <textarea
                  rows={2}
                  placeholder="e.g. Applied via LinkedIn, submitted tailored resume with Skygnosis & AI Saraj projects"
                  value={manualNotes}
                  onChange={(e) => setManualNotes(e.target.value)}
                  className="w-full px-3.5 py-2 bg-gray-950 border border-gray-800 rounded-xl text-sm text-white focus:outline-none focus:border-primary-500 resize-none"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-gray-800">
                <button
                  type="button"
                  onClick={() => setShowManualModal(false)}
                  className="px-4 py-2 rounded-xl bg-gray-800 hover:bg-gray-700 text-gray-300 text-sm font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSavingManual}
                  className="px-5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-medium shadow-md shadow-emerald-500/20 disabled:opacity-50"
                >
                  {isSavingManual ? 'Saving...' : 'Record Application'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
export default AppliedJobsPage;
