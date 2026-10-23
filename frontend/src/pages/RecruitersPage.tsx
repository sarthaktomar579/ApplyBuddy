import React, { useState, useEffect } from 'react';
import { getRecruiters, discoverRecruiters } from '../services/api';
import { Recruiter } from '../types';
import { Navbar } from '../components/Navbar';
import { EmailComposerModal } from '../components/EmailComposerModal';
import {
  Users,
  Search,
  ShieldCheck,
  AlertCircle,
  Mail,
  Building2,
  ExternalLink,
  Sparkles,
  Loader2,
  CheckCircle2,
  Briefcase
} from 'lucide-react';

export const RecruitersPage: React.FC = () => {
  const [recruiters, setRecruiters] = useState<Recruiter[]>([]);
  const [loading, setLoading] = useState(true);
  const [companySearch, setCompanySearch] = useState('');
  const [discoverInput, setDiscoverInput] = useState('');
  const [discovering, setDiscovering] = useState(false);
  const [discoveredRecruiters, setDiscoveredRecruiters] = useState<Recruiter[]>([]);
  const [selectedRecruiter, setSelectedRecruiter] = useState<Recruiter | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const fetchRecruitersList = async () => {
    setLoading(true);
    try {
      const data = await getRecruiters({
        company: companySearch || undefined,
      });
      setRecruiters(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecruitersList();
  }, [companySearch]);

  const handleDiscoverCompany = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!discoverInput.trim()) return;

    setDiscovering(true);
    try {
      const res = await discoverRecruiters(discoverInput.trim());
      setDiscoveredRecruiters(res.recruiters);
      setStatusMessage(`Found ${res.count} recruiter contacts for ${res.company}!`);
      setTimeout(() => setStatusMessage(null), 4000);
      await fetchRecruitersList();
    } catch (err) {
      console.error(err);
    } finally {
      setDiscovering(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Navbar
        title="Recruiter & HR Contact Intelligence"
        subtitle="Publicly verified recruiter emails, pattern derivations, and direct outreach contacts"
      />

      <main className="flex-1 p-8 space-y-8 max-w-7xl mx-auto w-full">
        {statusMessage && (
          <div className="p-3.5 rounded-xl bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-xs flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>{statusMessage}</span>
            </div>
            <button onClick={() => setStatusMessage(null)} className="text-slate-400 hover:text-white">✕</button>
          </div>
        )}

        {/* Discovery Tool Bar */}
        <div className="glass-panel p-6 rounded-xl border border-indigo-500/30 bg-gradient-to-r from-indigo-950/40 via-purple-950/20 to-slate-900 space-y-3">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-indigo-500/20 text-indigo-400 flex items-center justify-center">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white">Discover Recruiter Contacts for Any Company</h3>
              <p className="text-xs text-slate-400">
                Type any company (e.g. Razorpay, CRED, Postman, Zepto, Swiggy) to look up official contacts or syntax patterns
              </p>
            </div>
          </div>

          <form onSubmit={handleDiscoverCompany} className="flex gap-2 max-w-md pt-1">
            <input
              type="text"
              value={discoverInput}
              onChange={(e) => setDiscoverInput(e.target.value)}
              placeholder="e.g. BrowserStack, Sarvam AI, CRED..."
              className="flex-1 bg-slate-950 border border-slate-700 rounded-lg px-3.5 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            />
            <button
              type="submit"
              disabled={discovering || !discoverInput.trim()}
              className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-semibold shadow-md shadow-indigo-600/30 transition-colors"
            >
              {discovering ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Search className="w-3.5 h-3.5" />}
              Find Contacts
            </button>
          </form>
        </div>

        {/* Directory Search & List */}
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Users className="w-4 h-4 text-indigo-400" />
                Verified Recruiter Directory
              </h3>
              <p className="text-xs text-slate-400">
                Indexed technical recruiters and talent acquisition leads
              </p>
            </div>

            <div className="relative w-72">
              <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-500" />
              <input
                type="text"
                value={companySearch}
                onChange={(e) => setCompanySearch(e.target.value)}
                placeholder="Filter by company name..."
                className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
              />
            </div>
          </div>

          {loading ? (
            <div className="p-16 flex flex-col items-center justify-center space-y-3">
              <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
              <p className="text-xs text-slate-400">Loading recruiter intelligence...</p>
            </div>
          ) : recruiters.length === 0 ? (
            <div className="glass-panel p-12 rounded-xl border border-slate-800 text-center space-y-3">
              <p className="text-xs text-slate-400">No recruiters found for this search filter.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {recruiters.map((r) => (
                <div
                  key={r.id}
                  className="glass-panel p-5 rounded-xl border border-slate-800/80 hover:border-indigo-500/40 transition-all flex flex-col justify-between space-y-4"
                >
                  <div className="space-y-2.5">
                    <div className="flex items-start justify-between gap-2">
                      <span className="text-xs font-semibold text-indigo-400 bg-indigo-500/10 px-2.5 py-0.5 rounded border border-indigo-500/20">
                        {r.company}
                      </span>
                      {r.verification_status === 'verified_official' ? (
                        <span className="text-[10px] text-emerald-400 flex items-center gap-1 font-medium bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                          <ShieldCheck className="w-3 h-3" /> Official
                        </span>
                      ) : (
                        <span className="text-[10px] text-amber-400 flex items-center gap-1 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
                          <AlertCircle className="w-3 h-3" /> Pattern
                        </span>
                      )}
                    </div>

                    <div>
                      <h4 className="text-sm font-bold text-white">{r.name || 'Recruiter'}</h4>
                      <p className="text-xs text-slate-400">{r.title || 'Technical Recruiter'}</p>
                    </div>

                    <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800/80 font-mono text-xs text-indigo-300 select-all truncate">
                      {r.email}
                    </div>

                    {r.evidence && (
                      <p className="text-[11px] text-slate-500 leading-relaxed italic">
                        "{r.evidence}"
                      </p>
                    )}
                  </div>

                  <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between gap-2">
                    <button
                      onClick={() => setSelectedRecruiter(r)}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium shadow-md shadow-indigo-600/30 transition-colors w-full justify-center"
                    >
                      <Mail className="w-3.5 h-3.5" />
                      Draft Cold Email
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>

      {/* Email Modal */}
      {selectedRecruiter && (
        <EmailComposerModal
          onClose={() => setSelectedRecruiter(null)}
          onSuccess={() => {
            fetchRecruitersList();
          }}
          existingEmail={{
            id: 0,
            job_id: null,
            idempotency_key: '',
            to_email: selectedRecruiter.email,
            to_name: selectedRecruiter.name,
            from_email: null,
            subject: `Application: Software Engineer — Sarthak Singh Tomar (${selectedRecruiter.company})`,
            body: `Hi ${selectedRecruiter.name || 'Hiring Team'},\n\nI am writing to express my strong interest in software engineering opportunities at ${selectedRecruiter.company}. As a final-year B.Tech student at IIIT Kota ('26) with production experience in React, FastAPI, WebSockets, and 1,500+ DSA problems solved, I would love to connect.\n\nBest regards,\nSarthak Singh Tomar\ngithub.com/sarthaktomar579`,
            status: 'draft',
            recipient_verified: selectedRecruiter.verification_status === 'verified_official',
            recipient_source: selectedRecruiter.evidence,
            resume_id: null,
            gmail_message_id: null,
            sent_at: null,
            error_message: null,
            retry_count: 0,
            is_personalized: true,
            generation_model: 'gemini-1.5-flash',
            created_at: new Date().toISOString(),
          }}
        />
      )}
    </div>
  );
};
