import React, { useState, useEffect } from 'react';
import { getEmails, approveEmail, cancelEmail, sendEmailViaGmail, getGmailStatus } from '../services/api';
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
  ExternalLink,
  Sparkles
} from 'lucide-react';

export const EmailsPage: React.FC = () => {
  const [emails, setEmails] = useState<Email[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [gmailConnected, setGmailConnected] = useState(false);
  const [activeEmail, setActiveEmail] = useState<Email | null>(null);
  const [sendingId, setSendingId] = useState<number | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

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

  useEffect(() => {
    fetchEmailsList();
  }, [statusFilter]);

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
        title="Email Center & Human Approval"
        subtitle="Review, customize, and authorize personalized cold emails before sending"
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

        {/* Gmail status banner */}
        {!gmailConnected && (
          <div className="p-4 rounded-xl bg-gradient-to-r from-amber-500/10 via-slate-900 to-slate-900 border border-amber-500/30 flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-amber-500/20 text-amber-400 flex items-center justify-center shrink-0">
                <AlertCircle className="w-5 h-5" />
              </div>
              <div>
                <h4 className="text-sm font-semibold text-white">Gmail Integration Not Linked Yet</h4>
                <p className="text-xs text-slate-400">
                  Approved emails will be queued safely. You can connect your Gmail account in Settings with 1-click OAuth.
                </p>
              </div>
            </div>
            <Link
              to="/settings"
              className="px-3.5 py-2 rounded-lg bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 text-xs font-semibold border border-amber-500/30 transition-colors shrink-0"
            >
              Configure Gmail
            </Link>
          </div>
        )}

        {/* Filter Tabs */}
        <div className="flex flex-wrap items-center gap-2 border-b border-slate-800 pb-3">
          {[
            { id: 'all', label: 'All Emails' },
            { id: 'awaiting_approval', label: 'Awaiting Approval' },
            { id: 'draft', label: 'Drafts' },
            { id: 'approved', label: 'Approved' },
            { id: 'sent', label: 'Sent' },
            { id: 'cancelled', label: 'Cancelled' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setStatusFilter(tab.id)}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                statusFilter === tab.id
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Email Cards */}
        {loading ? (
          <div className="p-16 flex flex-col items-center justify-center space-y-3">
            <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
            <p className="text-xs text-slate-400">Loading email queue...</p>
          </div>
        ) : emails.length === 0 ? (
          <div className="glass-panel p-16 rounded-xl border border-slate-800 text-center space-y-4">
            <div className="w-12 h-12 rounded-full bg-slate-800 text-slate-400 mx-auto flex items-center justify-center">
              <Mail className="w-6 h-6" />
            </div>
            <div>
              <h3 className="font-bold text-white text-base">No Emails in this View</h3>
              <p className="text-xs text-slate-400 max-w-md mx-auto mt-1">
                Go to the Job Discovery page and click "Draft Cold Email" on any matched opportunity to prepare tailored outreach.
              </p>
            </div>
            <Link
              to="/jobs"
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium shadow-md shadow-indigo-600/30"
            >
              Browse Job Opportunities
            </Link>
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
                        <ShieldCheck className="w-3 h-3" /> Official Recruiter
                      </span>
                    ) : (
                      <span className="text-[10px] text-amber-400 flex items-center gap-1 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
                        <AlertCircle className="w-3 h-3" /> Pattern Verified
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
                      <span className="flex items-center gap-1 text-emerald-400">
                        <CheckCircle2 className="w-3 h-3" />
                        Sent: {new Date(email.sent_at).toLocaleString()}
                      </span>
                    )}
                    <span className="font-mono text-[10px] text-slate-600">
                      ID: {email.idempotency_key?.slice(0, 12)}...
                    </span>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2 shrink-0" onClick={(e) => e.stopPropagation()}>
                  <button
                    onClick={() => setActiveEmail(email)}
                    className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-white transition-colors"
                    title="Review & Edit"
                  >
                    <Edit className="w-4 h-4" />
                  </button>

                  {email.status !== 'sent' && (
                    <button
                      onClick={(e) => handleApproveAndSend(e, email)}
                      disabled={sendingId === email.id}
                      className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium shadow-md shadow-indigo-600/30 transition-colors disabled:opacity-60"
                    >
                      {sendingId === email.id ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <Send className="w-3.5 h-3.5" />
                      )}
                      {email.status === 'approved' ? 'Send via Gmail' : 'Approve & Send'}
                    </button>
                  )}

                  {email.status !== 'sent' && email.status !== 'cancelled' && (
                    <button
                      onClick={(e) => handleCancel(e, email)}
                      className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-red-400 transition-colors"
                      title="Cancel Email"
                    >
                      <XCircle className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      {/* Email Edit Modal */}
      {activeEmail && (
        <EmailComposerModal
          existingEmail={activeEmail}
          onClose={() => setActiveEmail(null)}
          onSuccess={() => {
            fetchEmailsList();
          }}
        />
      )}
    </div>
  );
};
