import React, { useState, useEffect } from 'react';
import { getGmailStatus, getGmailConnectUrl, disconnectGmail, getAIProviderStatus, testAIProvider } from '../services/api';
import { Navbar } from '../components/Navbar';
import {
  Mail,
  Sparkles,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  ExternalLink,
  Loader2,
  Key,
  Server,
  Settings,
  Info
} from 'lucide-react';

export const SettingsPage: React.FC = () => {
  const [gmailStatus, setGmailStatus] = useState<{ configured: boolean; connected: boolean; email: string | null; last_error: string | null } | null>(null);
  const [aiStatus, setAiStatus] = useState<{ providers: any[]; active_provider: string | null } | null>(null);
  const [testingProvider, setTestingProvider] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<{ provider: string; message: string; success: boolean } | null>(null);
  const [loading, setLoading] = useState(true);

  const loadStatus = async () => {
    setLoading(true);
    try {
      const [gmail, ai] = await Promise.all([getGmailStatus(), getAIProviderStatus()]);
      setGmailStatus(gmail);
      setAiStatus(ai);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStatus();
  }, []);

  const handleConnectGmail = async () => {
    try {
      const res = await getGmailConnectUrl();
      if (res.auth_url) {
        window.location.href = res.auth_url;
      }
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to initialize Gmail OAuth. Please check backend .env credentials.');
    }
  };

  const handleDisconnectGmail = async () => {
    try {
      await disconnectGmail();
      await loadStatus();
    } catch (err) {
      console.error(err);
    }
  };

  const handleTestAI = async (provider: string) => {
    setTestingProvider(provider);
    setTestResult(null);
    try {
      const res = await testAIProvider(provider);
      setTestResult({ provider, message: res.response || 'Connection successful!', success: true });
    } catch (err: any) {
      setTestResult({
        provider,
        message: err?.response?.data?.detail || 'Test failed. Please verify API key.',
        success: false,
      });
    } finally {
      setTestingProvider(null);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Navbar
        title="Integrations & Settings"
        subtitle="Manage Gmail OAuth mailbox connection, AI engine preferences, and security policies"
      />

      <main className="flex-1 p-8 space-y-8 max-w-5xl mx-auto w-full">
        {/* Gmail OAuth Integration Card */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-3.5">
              <div className="w-11 h-11 rounded-xl bg-red-500/10 text-red-400 flex items-center justify-center shrink-0 border border-red-500/20">
                <Mail className="w-6 h-6" />
              </div>
              <div>
                <h3 className="font-bold text-white text-base flex items-center gap-2">
                  Gmail OAuth Account
                  {gmailStatus?.connected ? (
                    <span className="text-xs bg-emerald-500/10 text-emerald-400 px-2 py-0.5 rounded-full border border-emerald-500/20 font-medium">
                      Connected
                    </span>
                  ) : (
                    <span className="text-xs bg-slate-800 text-slate-400 px-2 py-0.5 rounded-full border border-slate-700">
                      Not Linked
                    </span>
                  )}
                </h3>
                <p className="text-xs text-slate-400">
                  Authorizes sending cold outreach and following up directly from your personal mailbox
                </p>
              </div>
            </div>

            {gmailStatus?.connected ? (
              <button
                onClick={handleDisconnectGmail}
                className="px-4 py-2 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 text-xs font-semibold border border-red-500/30 transition-colors shrink-0"
              >
                Disconnect Mailbox
              </button>
            ) : (
              <button
                onClick={handleConnectGmail}
                className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-600/30 transition-colors shrink-0"
              >
                <Mail className="w-4 h-4" />
                Connect via Google OAuth
              </button>
            )}
          </div>

          {gmailStatus?.connected && (
            <div className="p-3.5 bg-slate-950 rounded-xl border border-slate-800 flex items-center gap-3 text-xs text-slate-300">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
              <span>
                Sending enabled from authorized address: <strong className="text-white">{gmailStatus.email}</strong>
              </span>
            </div>
          )}

          {/* Setup Walkthrough Guide */}
          <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800/80 space-y-2.5 text-xs text-slate-400">
            <span className="font-semibold text-slate-200 flex items-center gap-1.5">
              <Info className="w-4 h-4 text-indigo-400" />
              How Gmail OAuth works with Human Approval:
            </span>
            <ul className="space-y-1.5 list-disc list-inside text-slate-400">
              <li>Emails are strictly drafted in "Awaiting Approval" state.</li>
              <li>Nothing is sent without your explicit review and one-click authorization.</li>
              <li>Every outbound email uses UUID-based idempotency to guarantee zero accidental duplicate sends.</li>
              <li>Configure <code className="text-indigo-300">GMAIL_CLIENT_ID</code> and <code className="text-indigo-300">GMAIL_CLIENT_SECRET</code> in <code className="text-slate-300">backend/.env</code> to link with Google Cloud Console.</li>
            </ul>
          </div>
        </div>

        {/* AI Providers Section */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-5">
          <div className="flex items-center gap-3.5">
            <div className="w-11 h-11 rounded-xl bg-purple-500/10 text-purple-400 flex items-center justify-center shrink-0 border border-purple-500/20">
              <Sparkles className="w-6 h-6" />
            </div>
            <div>
              <h3 className="font-bold text-white text-base">AI Intelligence Providers</h3>
              <p className="text-xs text-slate-400">
                Multi-provider engine powering job matching, resume tailoring, and personalized outreach
              </p>
            </div>
          </div>

          {testResult && (
            <div
              className={`p-3.5 rounded-xl border text-xs flex items-center gap-2 ${
                testResult.success
                  ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                  : 'bg-red-500/10 border-red-500/30 text-red-300'
              }`}
            >
              {testResult.success ? <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" /> : <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />}
              <span>{testResult.message}</span>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {aiStatus?.providers.map((p: any) => (
              <div
                key={p.provider}
                className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col justify-between space-y-4"
              >
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-sm text-white">{p.name}</span>
                    {p.configured ? (
                      <span className="text-[10px] bg-emerald-500/10 text-emerald-400 px-2 py-0.5 rounded-full border border-emerald-500/20 font-medium">
                        Configured
                      </span>
                    ) : (
                      <span className="text-[10px] bg-slate-800 text-slate-500 px-2 py-0.5 rounded-full border border-slate-700">
                        Not Set
                      </span>
                    )}
                  </div>
                  <div className="text-[11px] font-mono text-slate-400">{p.model}</div>
                  <div className="text-[11px] text-slate-500">
                    Priority: #{p.priority} • {p.free_tier ? 'Free tier eligible' : 'Standard'}
                  </div>
                </div>

                <button
                  onClick={() => handleTestAI(p.provider)}
                  disabled={testingProvider === p.provider || !p.configured}
                  className="w-full py-2 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-slate-200 text-xs font-medium border border-slate-700 transition-colors flex items-center justify-center gap-1.5"
                >
                  {testingProvider === p.provider ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <Key className="w-3.5 h-3.5 text-purple-400" />
                  )}
                  Test Connection
                </button>
              </div>
            ))}
          </div>

          <div className="p-4 bg-slate-950/60 rounded-xl border border-slate-800 text-xs text-slate-400 space-y-1">
            <span className="font-semibold text-slate-300">Intelligent Heuristic Fallback Active:</span>
            <p>
              Even when API keys are not yet configured, ApplyPilot AI includes a built-in algorithmic matching & template engine so all features (scoring, cold email generation, and resume tailoring) work immediately out-of-the-box.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
};
