import React, { useEffect, useState } from 'react';
import { getGmailStatus, getAIProviderStatus } from '../services/api';
import { Mail, Sparkles, CheckCircle2, AlertCircle } from 'lucide-react';
import { Link } from 'react-router-dom';

interface NavbarProps {
  title: string;
  subtitle?: string;
  actions?: React.ReactNode;
}

export const Navbar: React.FC<NavbarProps> = ({ title, subtitle, actions }) => {
  const [gmailConnected, setGmailConnected] = useState(false);
  const [aiReady, setAiReady] = useState(false);

  useEffect(() => {
    const checkIntegrations = async () => {
      try {
        const [gmail, ai] = await Promise.all([getGmailStatus(), getAIProviderStatus()]);
        setGmailConnected(gmail.connected);
        setAiReady(Boolean(ai.active_provider));
      } catch (err) {
        // quiet fallback
      }
    };
    checkIntegrations();
  }, []);

  return (
    <header className="h-20 bg-slate-900/60 backdrop-blur-md border-b border-slate-800/80 sticky top-0 z-20 px-8 flex items-center justify-between">
      <div>
        <h2 className="text-xl font-bold text-white tracking-tight">{title}</h2>
        {subtitle && <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>}
      </div>

      <div className="flex items-center gap-4">
        {/* Integration Status Badges */}
        <div className="hidden md:flex items-center gap-2">
          <Link
            to="/settings"
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border transition-colors ${
              gmailConnected
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20 hover:bg-emerald-500/20'
                : 'bg-slate-800 text-slate-400 border-slate-700 hover:text-slate-200'
            }`}
          >
            <Mail className="w-3.5 h-3.5" />
            <span>Gmail {gmailConnected ? 'Connected' : 'Not Linked'}</span>
            {gmailConnected ? <CheckCircle2 className="w-3 h-3 text-emerald-400" /> : <AlertCircle className="w-3 h-3 text-slate-500" />}
          </Link>

          <Link
            to="/settings"
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border transition-colors ${
              aiReady
                ? 'bg-purple-500/10 text-purple-400 border-purple-500/20 hover:bg-purple-500/20'
                : 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20 hover:bg-indigo-500/20'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>AI Match & Generator Active</span>
          </Link>
        </div>

        {actions && <div className="flex items-center gap-2">{actions}</div>}
      </div>
    </header>
  );
};
