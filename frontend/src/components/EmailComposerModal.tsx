import React, { useState, useEffect } from 'react';
import { Job, Resume, Email } from '../types';
import { generateColdEmail, createEmailDraft, updateEmailDraft, approveEmail, sendEmailViaGmail, getResumes } from '../services/api';
import {
  X,
  Send,
  Sparkles,
  Paperclip,
  CheckCircle2,
  AlertCircle,
  ShieldCheck,
  FileText,
  Loader2,
  Save
} from 'lucide-react';

interface EmailComposerModalProps {
  job?: Job | null;
  existingEmail?: Email | null;
  onClose: () => void;
  onSuccess: () => void;
}

export const EmailComposerModal: React.FC<EmailComposerModalProps> = ({
  job,
  existingEmail,
  onClose,
  onSuccess,
}) => {
  const [toEmail, setToEmail] = useState('');
  const [toName, setToName] = useState('');
  const [subject, setSubject] = useState('');
  const [body, setBody] = useState('');
  const [resumeId, setResumeId] = useState<number | null>(null);
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [isVerified, setIsVerified] = useState(false);
  const [recipientSource, setRecipientSource] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  // Load resumes
  useEffect(() => {
    const fetchResumes = async () => {
      try {
        const list = await getResumes();
        setResumes(list);
        const def = list.find((r) => r.is_default);
        if (def && !resumeId) setResumeId(def.id);
      } catch (err) {
        console.error('Failed to fetch resumes', err);
      }
    };
    fetchResumes();
  }, []);

  // Prepopulate if editing existing or generate if new from job
  useEffect(() => {
    if (existingEmail) {
      setToEmail(existingEmail.to_email);
      setToName(existingEmail.to_name || '');
      setSubject(existingEmail.subject);
      setBody(existingEmail.body);
      setResumeId(existingEmail.resume_id);
      setIsVerified(existingEmail.recipient_verified);
      setRecipientSource(existingEmail.recipient_source);
    } else if (job) {
      handleGenerate();
    }
  }, [job, existingEmail]);

  const handleGenerate = async () => {
    if (!job) return;
    setGenerating(true);
    setError(null);
    try {
      const data = await generateColdEmail({ job_id: job.id });
      setToEmail(data.to_email);
      setToName(data.to_name);
      setSubject(data.subject);
      setBody(data.body);
      setIsVerified(data.recipient_verified);
      setRecipientSource(data.recipient_source);
      if (data.resume_id) setResumeId(data.resume_id);
    } catch (err: any) {
      setError('Failed to auto-generate cold email. You can type manually.');
    } finally {
      setGenerating(false);
    }
  };

  const handleSaveDraft = async () => {
    setLoading(true);
    setError(null);
    try {
      if (existingEmail) {
        await updateEmailDraft(existingEmail.id, {
          to_email: toEmail,
          to_name: toName,
          subject,
          body,
          resume_id: resumeId || undefined,
        });
      } else {
        await createEmailDraft({
          job_id: job?.id,
          to_email: toEmail,
          to_name: toName,
          subject,
          body,
          resume_id: resumeId || undefined,
          recipient_verified: isVerified,
          recipient_source: recipientSource || undefined,
        });
      }
      setStatusMessage('Draft saved successfully!');
      setTimeout(() => {
        onSuccess();
        onClose();
      }, 700);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to save draft');
    } finally {
      setLoading(false);
    }
  };

  const handleApproveAndSend = async () => {
    setLoading(true);
    setError(null);
    try {
      let emailId = existingEmail?.id;
      if (!emailId) {
        const created = await createEmailDraft({
          job_id: job?.id,
          to_email: toEmail,
          to_name: toName,
          subject,
          body,
          resume_id: resumeId || undefined,
          recipient_verified: isVerified,
          recipient_source: recipientSource || undefined,
        });
        emailId = created.id;
      } else {
        await updateEmailDraft(emailId, {
          to_email: toEmail,
          to_name: toName,
          subject,
          body,
          resume_id: resumeId || undefined,
        });
      }

      // Approve
      await approveEmail(emailId);

      // Attempt send via Gmail
      try {
        await sendEmailViaGmail(emailId);
        setStatusMessage('Email approved and sent through Gmail!');
      } catch (gmailErr: any) {
        // If Gmail not connected, it remains safely marked as approved
        setStatusMessage('Email approved! (Link Gmail in Settings to send automatically).');
      }

      setTimeout(() => {
        onSuccess();
        onClose();
      }, 1200);
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to approve email');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-2xl max-h-[92vh] overflow-hidden flex flex-col shadow-2xl">
        {/* Header */}
        <div className="p-5 border-b border-slate-800 flex items-center justify-between bg-slate-950/60">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-indigo-500/20 text-indigo-400 flex items-center justify-center">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-bold text-white text-base">
                {existingEmail ? 'Review Cold Email Draft' : `Cold Application Email — ${job?.company || 'Company'}`}
              </h3>
              <p className="text-[11px] text-slate-400">
                Personalized candidate introduction citing real projects & achievements
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form Body */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4 text-xs">
          {error && (
            <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {statusMessage && (
            <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span>{statusMessage}</span>
            </div>
          )}

          {/* Recipient Details */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-slate-400 mb-1 font-medium">To Recruiter Name</label>
              <input
                type="text"
                value={toName}
                onChange={(e) => setToName(e.target.value)}
                placeholder="e.g. Ananya Sharma (Tech Talent)"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 placeholder-slate-600 focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="text-slate-400 font-medium">Recipient Email</label>
                {isVerified ? (
                  <span className="text-[10px] text-emerald-400 flex items-center gap-1 font-medium">
                    <ShieldCheck className="w-3 h-3" /> Verified Official
                  </span>
                ) : (
                  <span className="text-[10px] text-amber-400 flex items-center gap-1">
                    <AlertCircle className="w-3 h-3" /> Pattern / Unverified
                  </span>
                )}
              </div>
              <input
                type="email"
                value={toEmail}
                onChange={(e) => setToEmail(e.target.value)}
                placeholder="recruiter@company.com"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 placeholder-slate-600 focus:outline-none focus:border-indigo-500 font-mono"
              />
            </div>
          </div>

          {/* Subject */}
          <div>
            <label className="block text-slate-400 mb-1 font-medium">Subject Line</label>
            <input
              type="text"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              placeholder="Application: Software Engineer — Sarthak Singh Tomar"
              className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-slate-200 placeholder-slate-600 focus:outline-none focus:border-indigo-500 font-medium"
            />
          </div>

          {/* Email Body */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-slate-400 font-medium">Email Content</label>
              <button
                type="button"
                onClick={handleGenerate}
                disabled={generating}
                className="text-[11px] text-indigo-400 hover:text-indigo-300 flex items-center gap-1 font-medium"
              >
                {generating ? <Loader2 className="w-3 h-3 animate-spin" /> : <Sparkles className="w-3 h-3" />}
                Regenerate AI Body
              </button>
            </div>
            <textarea
              rows={9}
              value={body}
              onChange={(e) => setBody(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-slate-200 placeholder-slate-600 focus:outline-none focus:border-indigo-500 font-sans leading-relaxed text-xs resize-y"
            />
          </div>

          {/* Attach Resume */}
          <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Paperclip className="w-4 h-4 text-slate-400" />
              <span className="text-slate-300 font-medium">Attached Resume PDF:</span>
            </div>
            <select
              value={resumeId || ''}
              onChange={(e) => setResumeId(Number(e.target.value) || null)}
              className="bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1 text-slate-200 text-xs focus:outline-none focus:border-indigo-500"
            >
              <option value="">None</option>
              {resumes.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.label} {r.is_default ? '(Default)' : ''}
                </option>
              ))}
              {resumes.length === 0 && <option value="1">Sarthak_Singh_Tomar_Resume.pdf (Auto-attached)</option>}
            </select>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 bg-slate-950 border-t border-slate-800 flex items-center justify-between">
          <div className="text-[11px] text-slate-500 flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-indigo-400" />
            Human approval required before any message leaves your mailbox.
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleSaveDraft}
              disabled={loading}
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium text-xs border border-slate-700 transition-colors"
            >
              <Save className="w-3.5 h-3.5" />
              Save Draft
            </button>

            <button
              onClick={handleApproveAndSend}
              disabled={loading || !toEmail || !subject}
              className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium text-xs shadow-md shadow-indigo-600/30 transition-colors"
            >
              {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
              Approve & Send via Gmail
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
