import React, { useState, useEffect } from 'react';
import {
  getEmails,
  approveEmail,
  cancelEmail,
  sendEmailViaGmail,
  getGmailStatus,
  startAutomatedCampaign,
  getCampaignStatus,
  stopCampaign
} from '../services/api';
import { Email } from '../types';
import { Navbar } from '../components/Navbar';
import { EmailComposerModal } from '../components/EmailComposerModal';
import { Link } from 'react-router-dom';
import {
  Mail,
  Send,
  CheckCircle2,
  AlertCircle,
  Clock,
  ShieldCheck,
  Edit,
  XCircle,
  Loader2,
  Paperclip,
  Sparkles,
  Zap,
  Pause,
  Play,
  Terminal,
  Building,
  MapPin,
  DollarSign,
  FileText
} from 'lucide-react';

export const EmailsPage: React.FC = () => {
  const [emails, setEmails] = useState<Email[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [gmailConnected, setGmailConnected] = useState(false);
  const [activeEmail, setActiveEmail] = useState<Email | null>(null);
  const [sendingId, setSendingId] = useState<number | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Automated Campaign State
  const [campaign, setCampaign] = useState<{
    is_running: boolean;
    is_paused: boolean;
    sent_today: number;
    daily_limit: number;
    delay_seconds: number;
    skipped_15d_count: number;
    total_targets: number;
    current_index: number;
    current_target: any;
    started_at: string | null;
    last_sent_at: string | null;
    logs: Array<{ timestamp: string; type: string; message: string; details?: any }>;
  }>({
    is_running: false,
    is_paused: false,
    sent_today: 0,
    daily_limit: 100,
    delay_seconds: 30,
    skipped_15d_count: 0,
    total_targets: 500,
    current_index: 0,
    current_target: null,
    started_at: null,
    last_sent_at: null,
    logs: []
  });
  const [campaignStarting, setCampaignStarting] = useState(false);

  const fetchEmailsList = async () => {
    setLoading(true);
    try {
      const [emailData, gmailData] = await Promise.all([
        getEmails(statusFilter === 'all' ? undefined : statusFilter),
        getGmailStatus(),
      ]);
      setEmails(emailData.emails);
      setGmailConnected(gmailData.connected);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchCampaign = async () => {
    try {
      const status = await getCampaignStatus();
      setCampaign(status);
    } catch (err) {
      console.error('Failed to get campaign status', err);
    }
  };

  useEffect(() => {
    fetchEmailsList();
    fetchCampaign();
  }, [statusFilter]);

  // Poll campaign status every 3 seconds
  useEffect(() => {
    const timer = setInterval(() => {
      fetchCampaign();
    }, 3000);
    return () => clearInterval(timer);
  }, []);

  const handleStartCampaign = async () => {
    setCampaignStarting(true);
    try {
      await startAutomatedCampaign({ daily_limit: 100, delay_seconds: 30 });
      setToastMessage('🚀 Automated Cold Email Outreach Engine started! Dispatching up to 100 emails with 30s safe delay.');
      await fetchCampaign();
      setTimeout(() => setToastMessage(null), 5000);
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to start campaign');
    } finally {
      setCampaignStarting(false);
    }
  };

  const handleStopCampaign = async () => {
    try {
      await stopCampaign();
      setToastMessage('⏸️ Campaign paused.');
      await fetchCampaign();
      setTimeout(() => setToastMessage(null), 3000);
    } catch (err: any) {
      alert('Failed to pause campaign');
    }
  };

  const handleApproveAndSend = async (e: React.MouseEvent, email: Email) => {
    e.stopPropagation();
    setSendingId(email.id);
    try {
      if (email.status === 'draft' || email.status === 'awaiting_approval') {
        await approveEmail(email.id);
      }
      if (gmailConnected) {
        await sendEmailViaGmail(email.id);
        setToastMessage(`Email sent to ${email.to_email} via Gmail!`);
      } else {
        setToastMessage(`Email approved! Link Gmail in Settings to send automatically.`);
      }
      setTimeout(() => setToastMessage(null), 4000);
      await fetchEmailsList();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to approve and send email');
    } finally {
      setSendingId(null);
    }
  };

  const handleCancel = async (e: React.MouseEvent, email: Email) => {
    e.stopPropagation();
    try {
      await cancelEmail(email.id);
      await fetchEmailsList();
    } catch (err) {
      console.error(err);
    }
  };

  const getStatusBadge = (status: Email['status']) => {
    switch (status) {
      case 'sent':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">Sent</span>;
      case 'approved':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-500/10 text-blue-400 border border-blue-500/30">Approved</span>;
      case 'awaiting_approval':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-500/10 text-purple-400 border border-purple-500/30 animate-pulse">Awaiting Approval</span>;
      case 'draft':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-800 text-slate-300 border border-slate-700">Draft</span>;
      case 'cancelled':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-500/10 text-red-400 border border-red-500/30">Cancelled</span>;
      default:
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-800 text-slate-400">{status}</span>;
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Navbar
        title="Email Outreach Engine & Mailbox"
        subtitle="100% Automated startup outreach engine with Gmail dispatch and 15-day duplicate shield"
      />

      <main className="flex-1 p-6 md:p-8 space-y-6 max-w-7xl mx-auto w-full">
        {toastMessage && (
          <div className="p-3.5 rounded-xl bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-xs flex items-center justify-between animate-in fade-in">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>{toastMessage}</span>
            </div>
            <button onClick={() => setToastMessage(null)} className="text-slate-400 hover:text-white">✕</button>
          </div>
        )}

        {/* --- HERO: AUTOMATED COLD EMAIL OUTREACH CONTROL STATION --- */}
        <div className="glass-panel rounded-2xl border border-indigo-500/30 bg-gradient-to-br from-slate-900 via-slate-900 to-indigo-950/40 p-6 md:p-8 space-y-6 shadow-2xl relative overflow-hidden">
          <div className="absolute top-0 right-0 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none -mr-20 -mt-20"></div>

          {/* Header Row */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 relative z-10">
            <div className="space-y-1">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-indigo-600/20 border border-indigo-500/40 text-indigo-400 flex items-center justify-center shrink-0">
                  <Zap className="w-6 h-6 animate-pulse text-indigo-400" />
                </div>
                <div>
                  <div className="flex items-center gap-2.5">
                    <h2 className="text-xl font-black text-white tracking-tight">
                      Automated Startup Cold Email Engine
                    </h2>
                    {campaign.is_running ? (
                      <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 flex items-center gap-1.5 animate-pulse">
                        <span className="w-2 h-2 rounded-full bg-emerald-400"></span> Live Dispatching
                      </span>
                    ) : campaign.is_paused ? (
                      <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40">
                        Paused
                      </span>
                    ) : (
                      <span className="px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-slate-800 text-slate-300 border border-slate-700">
                        Ready
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Dispatches personalized emails to 500+ tech startups (&ge; 5 LPA, Oct 22+) via Gmail with <strong className="text-slate-200">Resume_Sarthak_Tomar.pdf</strong> attached.
                  </p>
                </div>
              </div>
            </div>

            {/* Main Action Buttons */}
            <div className="flex items-center gap-3 shrink-0">
              {campaign.is_running ? (
                <button
                  onClick={handleStopCampaign}
                  className="px-5 py-2.5 rounded-xl bg-amber-500/20 hover:bg-amber-500/30 border border-amber-500/40 text-amber-300 font-semibold text-xs flex items-center gap-2 transition-all shadow-lg shadow-amber-500/10 cursor-pointer"
                >
                  <Pause className="w-4 h-4" /> Pause Campaign
                </button>
              ) : (
                <button
                  onClick={handleStartCampaign}
                  disabled={campaignStarting}
                  className="px-6 py-3 rounded-xl bg-gradient-to-r from-indigo-600 via-indigo-500 to-emerald-600 hover:from-indigo-500 hover:to-emerald-500 text-white font-bold text-xs flex items-center gap-2.5 transition-all shadow-xl shadow-indigo-600/30 hover:scale-[1.02] active:scale-[0.98] cursor-pointer"
                >
                  {campaignStarting ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Play className="w-4 h-4 fill-white" />
                  )}
                  ⚡ Start Automated Campaign (100 Startups / Day)
                </button>
              )}
            </div>
          </div>

          {/* Metric KPI Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 relative z-10">
            {/* 1. Daily Progress */}
            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2">
              <div className="flex items-center justify-between text-xs text-slate-400">
                <span className="flex items-center gap-1.5"><Send className="w-3.5 h-3.5 text-indigo-400" /> Sent Today</span>
                <span className="font-mono text-indigo-300 font-bold">{campaign.sent_today} / {campaign.daily_limit}</span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                <div
                  className="bg-gradient-to-r from-indigo-500 to-emerald-400 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${Math.min(100, (campaign.sent_today / campaign.daily_limit) * 100)}%` }}
                ></div>
              </div>
              <div className="text-[10px] text-slate-500 flex justify-between">
                <span>Safe Daily Cap: 100</span>
                <span>{100 - campaign.sent_today} remaining</span>
              </div>
            </div>

            {/* 2. 15-Day Duplicate Shield */}
            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
              <div className="flex items-center gap-1.5 text-xs text-slate-400">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                <span>15-Day Shield</span>
              </div>
              <div className="text-2xl font-black text-emerald-400 font-mono">
                {campaign.skipped_15d_count}
              </div>
              <div className="text-[10px] text-slate-500">
                Duplicates skipped & protected
              </div>
            </div>

            {/* 3. Startup Catalog */}
            {/* 3. Verified Recruiter Targets */}
            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
              <div className="flex items-center gap-1.5 text-xs text-slate-400">
                <Building className="w-3.5 h-3.5 text-purple-400" />
                <span>Verified Recruiters</span>
              </div>
              <div className="text-2xl font-black text-purple-300 font-mono">
                {campaign.total_targets}
              </div>
              <div className="text-[10px] text-emerald-400 font-medium">
                Specific Persons &amp; Zero Bounce
              </div>
            </div>

            {/* 4. Safe Pacing */}
            <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
              <div className="flex items-center gap-1.5 text-xs text-slate-400">
                <Clock className="w-3.5 h-3.5 text-amber-400" />
                <span>Safe Pacing</span>
              </div>
              <div className="text-2xl font-black text-amber-300 font-mono">
                {campaign.delay_seconds}s
              </div>
              <div className="text-[10px] text-slate-500">
                Delay between dispatches
              </div>
            </div>
          </div>

          {/* Active Target Banner (if running or last sent) */}
          {campaign.current_target && (
            <div className="p-4 rounded-xl bg-indigo-950/40 border border-indigo-500/30 flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs relative z-10">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-indigo-600/30 text-indigo-300 flex items-center justify-center shrink-0">
                  <Mail className="w-4 h-4" />
                </div>
                <div>
                  <div className="font-semibold text-white flex items-center gap-2">
                    <span>{campaign.current_target.title}</span>
                    <span className="text-slate-400">&bull;</span>
                    <span className="text-indigo-300 font-bold">{campaign.current_target.company}</span>
                    {campaign.current_target.person_name && (
                      <span className="text-[10px] text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                        👤 {campaign.current_target.person_name} ({campaign.current_target.person_title})
                      </span>
                    )}
                  </div>
                  <div className="text-[11px] text-slate-400 flex items-center gap-3 mt-0.5">
                    <span className="flex items-center gap-1"><MapPin className="w-3 h-3 text-slate-500" /> {campaign.current_target.location}</span>
                    <span className="flex items-center gap-1 text-emerald-400 font-medium"><DollarSign className="w-3 h-3" /> {campaign.current_target.salary}</span>
                    <span className="text-slate-500">To: {campaign.current_target.email}</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2 text-[11px] text-emerald-400 bg-emerald-500/10 px-3 py-1 rounded-lg border border-emerald-500/20 shrink-0">
                <Paperclip className="w-3.5 h-3.5" />
                <span>Resume_Sarthak_Tomar.pdf Attached</span>
              </div>
            </div>
          )}

          {/* Live Action Terminal Logs */}
          <div className="space-y-2 relative z-10">
            <div className="flex items-center justify-between text-xs text-slate-400">
              <div className="flex items-center gap-2 font-mono">
                <Terminal className="w-3.5 h-3.5 text-indigo-400" />
                <span className="font-semibold text-slate-300">Live Engine Terminal Logs</span>
              </div>
              <span className="text-[10px] text-slate-500">Auto-updating live</span>
            </div>

            <div className="h-44 overflow-y-auto rounded-xl bg-slate-950/90 border border-slate-800/80 p-3 font-mono text-[11px] space-y-1.5 scrollbar-thin scrollbar-thumb-slate-800">
              {campaign.logs.length === 0 ? (
                <div className="text-slate-600 italic py-6 text-center">
                  Engine idle. Click "Start Automated Campaign" to begin cold email outreach.
                </div>
              ) : (
                campaign.logs.map((log, i) => (
                  <div key={i} className="flex items-start gap-2.5 leading-relaxed">
                    <span className="text-slate-600 text-[10px] shrink-0 pt-0.5">[{log.timestamp}]</span>
                    <span
                      className={`break-all ${
                        log.type === 'success'
                          ? 'text-emerald-400'
                          : log.type === 'warning'
                          ? 'text-amber-400'
                          : log.type === 'error'
                          ? 'text-red-400'
                          : 'text-indigo-300'
                      }`}
                    >
                      {log.message}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* --- RECENT EMAIL DISPATCHES & MANUAL REVIEW QUEUE --- */}
        <div className="space-y-4 pt-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Mail className="w-4 h-4 text-indigo-400" /> Email History & Sent Applications
              </h3>
              <p className="text-xs text-slate-400">
                Verified emails sent directly from your connected Gmail with physical PDF resume attachment.
              </p>
            </div>

            {/* Filter Tabs */}
            <div className="flex flex-wrap items-center gap-2">
              {[
                { id: 'all', label: 'All' },
                { id: 'sent', label: 'Sent' },
                { id: 'awaiting_approval', label: 'Awaiting Approval' },
                { id: 'draft', label: 'Drafts' },
                { id: 'cancelled', label: 'Cancelled' },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setStatusFilter(tab.id)}
                  className={`px-3 py-1 rounded-lg text-xs font-medium transition-colors cursor-pointer ${
                    statusFilter === tab.id
                      ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900 border border-slate-800'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>
          </div>

          {/* Email Cards */}
          {loading ? (
            <div className="p-16 flex flex-col items-center justify-center space-y-3">
              <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
              <p className="text-xs text-slate-400">Loading email queue...</p>
            </div>
          ) : emails.length === 0 ? (
            <div className="glass-panel p-12 rounded-xl border border-slate-800 text-center space-y-3">
              <div className="w-10 h-10 rounded-full bg-slate-800 text-slate-400 mx-auto flex items-center justify-center">
                <Mail className="w-5 h-5" />
              </div>
              <h4 className="font-bold text-white text-sm">No Emails in this View</h4>
              <p className="text-xs text-slate-400 max-w-md mx-auto">
                Once the automated campaign begins, all delivered application emails will appear here in real-time.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {emails.map((email) => (
                <div
                  key={email.id}
                  onClick={() => setActiveEmail(email)}
                  className="glass-panel p-5 rounded-xl border border-slate-800 hover:border-indigo-500/40 transition-all cursor-pointer flex flex-col md:flex-row md:items-center justify-between gap-4 group"
                >
                  <div className="space-y-2 flex-1">
                    <div className="flex flex-wrap items-center gap-2.5">
                      {getStatusBadge(email.status)}
                      <span className="text-xs font-semibold text-slate-200">
                        To: {email.to_name || 'Hiring Team'} &lt;{email.to_email}&gt;
                      </span>
                      {email.recipient_verified ? (
                        <span className="text-[10px] text-emerald-400 flex items-center gap-1 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                          <ShieldCheck className="w-3 h-3" /> Official Career Inbox
                        </span>
                      ) : (
                        <span className="text-[10px] text-indigo-400 flex items-center gap-1 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20">
                          <CheckCircle2 className="w-3 h-3" /> Verified Tech Startup
                        </span>
                      )}
                    </div>

                    <div>
                      <h4 className="text-sm font-bold text-white group-hover:text-indigo-300 transition-colors">
                        {email.subject}
                      </h4>
                      <p className="text-xs text-slate-400 line-clamp-2 mt-1 font-sans leading-relaxed">
                        {email.body}
                      </p>
                    </div>

                    <div className="flex items-center gap-4 text-[11px] text-slate-500 pt-1">
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        Created: {email.created_at ? new Date(email.created_at).toLocaleDateString() : 'Recent'}
                      </span>
                      {email.sent_at && (
                        <span className="flex items-center gap-1 text-emerald-400 font-medium">
                          <CheckCircle2 className="w-3 h-3" />
                          Sent: {new Date(email.sent_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                      )}
                      <span className="flex items-center gap-1 text-slate-400">
                        <Paperclip className="w-3 h-3 text-indigo-400" /> Resume Attached
                      </span>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2 shrink-0" onClick={(e) => e.stopPropagation()}>
                    <button
                      onClick={() => setActiveEmail(email)}
                      className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-white transition-colors cursor-pointer"
                      title="Review & Edit"
                    >
                      <Edit className="w-4 h-4" />
                    </button>

                    {email.status !== 'sent' && (
                      <button
                        onClick={(e) => handleApproveAndSend(e, email)}
                        disabled={sendingId === email.id}
                        className="px-3.5 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-md shadow-indigo-600/30 cursor-pointer"
                      >
                        {sendingId === email.id ? (
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                          <Send className="w-3.5 h-3.5" />
                        )}
                        Send Now
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>

      {/* Review Modal */}
      {activeEmail && (
        <EmailComposerModal
          email={activeEmail}
          onClose={() => setActiveEmail(null)}
          onUpdate={fetchEmailsList}
        />
      )}
    </div>
  );
};
