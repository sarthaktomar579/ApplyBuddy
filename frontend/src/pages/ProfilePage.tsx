import React, { useState, useEffect } from 'react';
import { getProfile, updateProfile } from '../services/api';
import { Profile } from '../types';
import { Navbar } from '../components/Navbar';
import {
  User,
  GraduationCap,
  Briefcase,
  Code2,
  FolderGit2,
  Award,
  Save,
  CheckCircle2,
  ExternalLink,
  MapPin,
  Sparkles,
  Loader2
} from 'lucide-react';

export const ProfilePage: React.FC = () => {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const fetchProfileData = async () => {
    setLoading(true);
    try {
      const data = await getProfile();
      setProfile(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProfileData();
  }, []);

  const handleSave = async () => {
    if (!profile) return;
    setSaving(true);
    try {
      await updateProfile(profile);
      setToastMessage('Profile updated successfully!');
      setTimeout(() => setToastMessage(null), 3000);
    } catch (err) {
      alert('Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  if (loading || !profile) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Navbar
        title="Candidate Profile & Preferences"
        subtitle="The central ground truth used by AI to score jobs, tailor resumes, and write cold outreach"
        actions={
          <button
            onClick={handleSave}
            disabled={saving}
            className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-600/30 transition-colors"
          >
            {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
            Save Changes
          </button>
        }
      />

      <main className="flex-1 p-8 space-y-8 max-w-7xl mx-auto w-full">
        {toastMessage && (
          <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4" />
              <span>{toastMessage}</span>
            </div>
            <button onClick={() => setToastMessage(null)} className="text-slate-400 hover:text-white">✕</button>
          </div>
        )}

        {/* Header Summary Card */}
        <div className="glass-panel p-6 rounded-2xl border border-indigo-500/30 bg-gradient-to-r from-indigo-950/40 via-purple-950/20 to-slate-900 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-indigo-600 to-purple-500 flex items-center justify-center text-white font-extrabold text-2xl shadow-xl shadow-indigo-600/30">
              ST
            </div>
            <div className="space-y-1">
              <h2 className="text-2xl font-extrabold text-white">{profile.full_name}</h2>
              <p className="text-xs text-indigo-300 font-medium flex items-center gap-2">
                <GraduationCap className="w-4 h-4" />
                {profile.degree} • {profile.college} ({profile.graduation_year})
              </p>
              <div className="flex flex-wrap items-center gap-4 text-xs text-slate-400 pt-1">
                <span>{profile.email}</span>
                <span>{profile.phone}</span>
                {profile.github_url && (
                  <a
                    href={profile.github_url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-indigo-400 hover:underline flex items-center gap-1"
                  >
                    GitHub <ExternalLink className="w-3 h-3" />
                  </a>
                )}
              </div>
            </div>
          </div>

          {/* DSA Badge */}
          <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center gap-4">
            <div className="w-10 h-10 rounded-xl bg-amber-500/10 text-amber-400 flex items-center justify-center shrink-0">
              <Award className="w-5 h-5" />
            </div>
            <div>
              <div className="text-xs font-semibold text-slate-300">Competitive Programming</div>
              <div className="text-base font-bold text-white mt-0.5">
                {profile.dsa_problems_solved}+ Solved
              </div>
              <p className="text-[11px] text-amber-400">
                LeetCode: {profile.leetcode_rating} • CodeChef: {profile.codechef_rating}
              </p>
            </div>
          </div>
        </div>

        {/* Section: Professional Summary */}
        <div className="glass-panel p-6 rounded-xl border border-slate-800 space-y-3">
          <h3 className="font-bold text-white text-sm flex items-center gap-2">
            <User className="w-4 h-4 text-indigo-400" />
            Executive Summary
          </h3>
          <textarea
            rows={3}
            value={profile.summary || ''}
            onChange={(e) => setProfile({ ...profile, summary: e.target.value })}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-xs text-slate-300 leading-relaxed focus:outline-none focus:border-indigo-500 font-sans"
          />
        </div>

        {/* Section: Key Projects */}
        <div className="space-y-4">
          <h3 className="font-bold text-white text-base flex items-center gap-2">
            <FolderGit2 className="w-4 h-4 text-indigo-400" />
            Key Highlighted Projects
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {profile.projects?.map((proj, idx) => (
              <div key={idx} className="glass-panel p-5 rounded-xl border border-slate-800 space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="font-bold text-sm text-indigo-300">{proj.name}</h4>
                  <span className="text-[10px] bg-purple-500/10 text-purple-300 px-2 py-0.5 rounded border border-purple-500/20">
                    Production Project
                  </span>
                </div>

                {proj.problem && (
                  <div>
                    <span className="text-[11px] font-semibold text-slate-400">Problem Addressed:</span>
                    <p className="text-xs text-slate-300 leading-relaxed mt-0.5">{proj.problem}</p>
                  </div>
                )}

                {proj.solution && (
                  <div>
                    <span className="text-[11px] font-semibold text-slate-400">Engineering Solution:</span>
                    <p className="text-xs text-slate-300 leading-relaxed mt-0.5">{proj.solution}</p>
                  </div>
                )}

                {proj.technologies && (
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {proj.technologies.map((t, tidx) => (
                      <span key={tidx} className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">
                        {t}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Section: Experience */}
        <div className="space-y-4">
          <h3 className="font-bold text-white text-base flex items-center gap-2">
            <Briefcase className="w-4 h-4 text-indigo-400" />
            Work & Internship Experience
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {profile.experiences?.map((exp, idx) => (
              <div key={idx} className="glass-panel p-5 rounded-xl border border-slate-800 space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-bold text-sm text-white">{exp.role}</h4>
                    <span className="text-xs font-semibold text-indigo-400">{exp.company}</span>
                  </div>
                  <span className="text-[11px] text-slate-400 font-medium">
                    {exp.start_date} – {exp.end_date}
                  </span>
                </div>

                <p className="text-xs text-slate-300 leading-relaxed">{exp.description}</p>

                {exp.highlights && (
                  <ul className="space-y-1 text-xs text-slate-400">
                    {exp.highlights.map((h, hidx) => (
                      <li key={hidx} className="flex items-start gap-1.5">
                        <span className="text-indigo-400">•</span>
                        <span>{h}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Section: Categorized Skills */}
        <div className="glass-panel p-6 rounded-xl border border-slate-800 space-y-4">
          <h3 className="font-bold text-white text-base flex items-center gap-2">
            <Code2 className="w-4 h-4 text-indigo-400" />
            Skills & Technical Stack
          </h3>
          <div className="flex flex-wrap gap-2">
            {profile.skills?.map((s, idx) => (
              <span
                key={idx}
                className="px-3 py-1 rounded-lg text-xs font-medium bg-slate-900 text-slate-200 border border-slate-700/80 flex items-center gap-1.5"
              >
                <span>{s.name}</span>
                <span className="text-[10px] text-slate-500 uppercase">{s.proficiency}</span>
              </span>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
};
