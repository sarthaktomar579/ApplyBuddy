import React, { useState, useEffect } from 'react';
import { getApplications, updateApplicationStatus, updateApplicationDetails } from '../services/api';
import { Application } from '../types';
import { Navbar } from '../components/Navbar';
import {
  KanbanSquare,
  Table as TableIcon,
  Building2,
  Calendar,
  ExternalLink,
  CheckCircle2,
  Clock,
  MessageSquare,
  AlertCircle,
  Plus,
  Loader2,
  ChevronRight
} from 'lucide-react';

const STAGES = [
  { id: 'shortlisted', label: 'Shortlisted', color: 'border-slate-700 bg-slate-900/50' },
  { id: 'preparing_application', label: 'Preparing', color: 'border-purple-500/30 bg-purple-950/20' },
  { id: 'awaiting_approval', label: 'Approval Required', color: 'border-indigo-500/30 bg-indigo-950/20' },
  { id: 'email_sent', label: 'Email Sent', color: 'border-blue-500/30 bg-blue-950/20' },
  { id: 'application_submitted', label: 'Applied', color: 'border-cyan-500/30 bg-cyan-950/20' },
  { id: 'recruiter_replied', label: 'Reply Received', color: 'border-emerald-500/30 bg-emerald-950/20' },
  { id: 'interview_scheduled', label: 'Interview Scheduled', color: 'border-amber-500/30 bg-amber-950/20' },
  { id: 'offer_received', label: 'Offer Received 🎉', color: 'border-emerald-500/50 bg-emerald-950/30' },
];

export const ApplicationsTrackerPage: React.FC = () => {
  const [applications, setApplications] = useState<Application[]>([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<'kanban' | 'table'>('kanban');
  const [activeApp, setActiveApp] = useState<Application | null>(null);
  const [notesInput, setNotesInput] = useState('');
  const [interviewDate, setInterviewDate] = useState('');
  const [updating, setUpdating] = useState(false);

  const fetchApplications = async () => {
    setLoading(true);
    try {
      const data = await getApplications();
      setApplications(data.applications);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApplications();
  }, []);

  const handleAdvanceStatus = async (app: Application, nextStatus: string) => {
    try {
      await updateApplicationStatus(app.id, nextStatus);
      await fetchApplications();
    } catch (err) {
      console.error(err);
    }
  };

  const handleSaveDetails = async () => {
    if (!activeApp) return;
    setUpdating(true);
    try {
      await updateApplicationDetails(activeApp.id, {
        notes: notesInput,
        interview_date: interviewDate || undefined,
      });
      setActiveApp(null);
      await fetchApplications();
    } catch (err) {
      console.error(err);
    } finally {
      setUpdating(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Navbar
        title="Application Pipeline Tracker"
        subtitle="Manage end-to-end progress across every role, outreach email, and interview round"
        actions={
          <div className="flex items-center gap-2 bg-slate-900 p-1 rounded-lg border border-slate-800">
            <button
              onClick={() => setViewMode('kanban')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                viewMode === 'kanban' ? 'bg-indigo-600 text-white shadow' : 'text-slate-400 hover:text-white'
              }`}
            >
              <KanbanSquare className="w-3.5 h-3.5" />
              Board View
            </button>
            <button
              onClick={() => setViewMode('table')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                viewMode === 'table' ? 'bg-indigo-600 text-white shadow' : 'text-slate-400 hover:text-white'
              }`}
            >
              <TableIcon className="w-3.5 h-3.5" />
              Table View
            </button>
          </div>
        }
      />

      <main className="flex-1 p-6 max-w-7xl mx-auto w-full overflow-x-auto">
        {loading ? (
          <div className="p-16 flex flex-col items-center justify-center space-y-3">
            <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
            <p className="text-xs text-slate-400">Loading your pipeline...</p>
          </div>
        ) : viewMode === 'kanban' ? (
          /* Kanban Board */
          <div className="flex gap-4 pb-6 min-w-max">
            {STAGES.map((stage) => {
              const stageApps = applications.filter((a) => a.status === stage.id);
              return (
                <div
                  key={stage.id}
                  className={`w-72 rounded-xl border flex flex-col max-h-[80vh] ${stage.color}`}
                >
                  {/* Column Header */}
                  <div className="p-3.5 border-b border-slate-800/80 flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-200 tracking-tight">
                      {stage.label}
                    </span>
                    <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 font-mono">
                      {stageApps.length}
                    </span>
                  </div>

                  {/* Column Cards */}
                  <div className="p-3 flex-1 overflow-y-auto space-y-3">
                    {stageApps.map((app) => (
                      <div
                        key={app.id}
                        className="bg-slate-900/90 border border-slate-800 rounded-lg p-3.5 hover:border-indigo-500/40 transition-all space-y-2 shadow-sm"
                      >
                        <div className="flex items-start justify-between gap-1">
                          <span className="text-[11px] font-semibold text-indigo-400">
                            {app.company}
                          </span>
                          {app.application_url && (
                            <a
                              href={app.application_url}
                              target="_blank"
                              rel="noreferrer"
                              className="text-slate-500 hover:text-slate-300"
                            >
                              <ExternalLink className="w-3.5 h-3.5" />
                            </a>
                          )}
                        </div>

                        <h4 className="text-xs font-bold text-white line-clamp-1">{app.job_title}</h4>

                        {app.interview_date && (
                          <div className="text-[11px] text-amber-400 font-medium flex items-center gap-1">
                            <Calendar className="w-3 h-3" />
                            {new Date(app.interview_date).toLocaleDateString()}
                          </div>
                        )}

                        {app.notes && (
                          <p className="text-[11px] text-slate-400 line-clamp-2 italic">
                            "{app.notes}"
                          </p>
                        )}

                        {/* Card Footer Actions */}
                        <div className="pt-2 border-t border-slate-800/60 flex items-center justify-between text-[11px]">
                          <button
                            onClick={() => {
                              setActiveApp(app);
                              setNotesInput(app.notes || '');
                              setInterviewDate(app.interview_date || '');
                            }}
                            className="text-slate-400 hover:text-white flex items-center gap-1"
                          >
                            <MessageSquare className="w-3 h-3" /> Note
                          </button>

                          {/* Quick advance status dropdown */}
                          <select
                            value={app.status}
                            onChange={(e) => handleAdvanceStatus(app, e.target.value)}
                            className="bg-slate-950 border border-slate-700 rounded px-1.5 py-0.5 text-[10px] text-slate-300 focus:outline-none"
                          >
                            {STAGES.map((s) => (
                              <option key={s.id} value={s.id}>
                                {s.label}
                              </option>
                            ))}
                          </select>
                        </div>
                      </div>
                    ))}

                    {stageApps.length === 0 && (
                      <div className="p-6 text-center text-xs text-slate-500 italic">
                        No applications here
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          /* Table View */
          <div className="glass-panel rounded-xl border border-slate-800 overflow-hidden">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-900/80 text-slate-400 font-semibold border-b border-slate-800 uppercase tracking-wider text-[10px]">
                <tr>
                  <th className="py-3 px-4">Company & Role</th>
                  <th className="py-3 px-4">Current Stage</th>
                  <th className="py-3 px-4">Location</th>
                  <th className="py-3 px-4">Interview Schedule</th>
                  <th className="py-3 px-4">Notes</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {applications.map((app) => (
                  <tr key={app.id} className="hover:bg-slate-900/50 transition-colors">
                    <td className="py-3 px-4">
                      <div className="font-bold text-white">{app.company}</div>
                      <div className="text-slate-400 text-[11px]">{app.job_title}</div>
                    </td>
                    <td className="py-3 px-4">
                      <span className="px-2.5 py-1 rounded-full text-[11px] font-medium bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                        {STAGES.find((s) => s.id === app.status)?.label || app.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-400">{app.location || 'Remote'}</td>
                    <td className="py-3 px-4">
                      {app.interview_date ? (
                        <span className="text-amber-400 font-medium">
                          {new Date(app.interview_date).toLocaleDateString()}
                        </span>
                      ) : (
                        <span className="text-slate-500">—</span>
                      )}
                    </td>
                    <td className="py-3 px-4 max-w-xs truncate text-slate-400">
                      {app.notes || '—'}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => {
                          setActiveApp(app);
                          setNotesInput(app.notes || '');
                          setInterviewDate(app.interview_date || '');
                        }}
                        className="text-xs text-indigo-400 hover:text-indigo-300 font-medium"
                      >
                        Edit
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>

      {/* Edit Details Modal */}
      {activeApp && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 w-full max-w-md space-y-4">
            <h3 className="font-bold text-white text-base">
              Update {activeApp.company} Application
            </h3>

            <div>
              <label className="block text-xs text-slate-400 mb-1">Status</label>
              <select
                value={activeApp.status}
                onChange={(e) => setActiveApp({ ...activeApp, status: e.target.value })}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-slate-200"
              >
                {STAGES.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs text-slate-400 mb-1">Interview Date (Optional)</label>
              <input
                type="date"
                value={interviewDate}
                onChange={(e) => setInterviewDate(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-slate-200"
              />
            </div>

            <div>
              <label className="block text-xs text-slate-400 mb-1">Notes & Follow-up Details</label>
              <textarea
                rows={3}
                value={notesInput}
                onChange={(e) => setNotesInput(e.target.value)}
                placeholder="e.g. Recruiter mentioned round 1 is timed DSA (graphs/trees)..."
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-slate-200"
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                onClick={() => setActiveApp(null)}
                className="px-3.5 py-1.5 rounded-lg bg-slate-800 text-slate-300 text-xs"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveDetails}
                disabled={updating}
                className="px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium"
              >
                {updating ? 'Saving...' : 'Save Updates'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
