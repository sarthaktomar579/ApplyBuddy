import React from 'react';
import { Job } from '../types';
import { MatchBadge } from './MatchBadge';
import {
  X,
  ExternalLink,
  Mail,
  FileText,
  MapPin,
  Building2,
  DollarSign,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Lightbulb,
  Plus
} from 'lucide-react';

interface JobDetailsModalProps {
  job: Job | null;
  onClose: () => void;
  onDraftEmail: (job: Job) => void;
  onTrackApplication: (job: Job) => void;
  onTailorResume: (job: Job) => void;
}

export const JobDetailsModal: React.FC<JobDetailsModalProps> = ({
  job,
  onClose,
  onDraftEmail,
  onTrackApplication,
  onTailorResume,
}) => {
  if (!job) return null;

  const match = job.match;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col shadow-2xl">
        {/* Header */}
        <div className="p-6 border-b border-slate-800 flex items-start justify-between bg-slate-950/50">
          <div className="space-y-1">
            <div className="flex items-center gap-3">
              <h2 className="text-xl font-bold text-white tracking-tight">{job.title}</h2>
              {match && <MatchBadge score={match.overall_score} size="md" />}
            </div>
            <div className="flex flex-wrap items-center gap-4 text-xs text-slate-400 mt-2">
              <span className="flex items-center gap-1.5 font-medium text-slate-200">
                <Building2 className="w-3.5 h-3.5 text-indigo-400" />
                {job.company}
              </span>
              <span className="flex items-center gap-1.5">
                <MapPin className="w-3.5 h-3.5 text-slate-500" />
                {job.location || 'Remote'} ({job.work_arrangement || 'Flexible'})
              </span>
              {job.salary_min && (
                <span className="flex items-center gap-1.5 text-emerald-400 font-medium">
                  <DollarSign className="w-3.5 h-3.5" />
                  ₹{(job.salary_min / 100000).toFixed(1)} - ₹{((job.salary_max || job.salary_min) / 100000).toFixed(1)} LPA
                </span>
              )}
              {job.experience_required && (
                <span className="flex items-center gap-1.5">
                  <Clock className="w-3.5 h-3.5 text-slate-500" />
                  {job.experience_required}
                </span>
              )}
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* AI Match Overview Card */}
          {match && (
            <div className="bg-gradient-to-r from-indigo-950/40 via-purple-950/30 to-slate-900 border border-indigo-500/30 rounded-xl p-5 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-white text-sm flex items-center gap-2">
                  <Lightbulb className="w-4 h-4 text-amber-400" />
                  AI Match Analysis
                </h3>
                <span className="text-xs text-indigo-300 font-medium">
                  {match.recommended_action}
                </span>
              </div>

              {/* Sub-score Bars */}
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 pt-2">
                <div className="bg-slate-900/60 p-2.5 rounded-lg border border-slate-800">
                  <div className="text-[11px] text-slate-400">Skills Match</div>
                  <div className="text-sm font-bold text-white mt-0.5">{match.skills_score}%</div>
                  <div className="w-full bg-slate-800 h-1.5 rounded-full mt-1.5 overflow-hidden">
                    <div className="bg-indigo-500 h-full rounded-full" style={{ width: `${match.skills_score}%` }}></div>
                  </div>
                </div>

                <div className="bg-slate-900/60 p-2.5 rounded-lg border border-slate-800">
                  <div className="text-[11px] text-slate-400">Experience</div>
                  <div className="text-sm font-bold text-white mt-0.5">{match.experience_score}%</div>
                  <div className="w-full bg-slate-800 h-1.5 rounded-full mt-1.5 overflow-hidden">
                    <div className="bg-emerald-500 h-full rounded-full" style={{ width: `${match.experience_score}%` }}></div>
                  </div>
                </div>

                <div className="bg-slate-900/60 p-2.5 rounded-lg border border-slate-800">
                  <div className="text-[11px] text-slate-400">Location</div>
                  <div className="text-sm font-bold text-white mt-0.5">{match.location_score}%</div>
                  <div className="w-full bg-slate-800 h-1.5 rounded-full mt-1.5 overflow-hidden">
                    <div className="bg-purple-500 h-full rounded-full" style={{ width: `${match.location_score}%` }}></div>
                  </div>
                </div>

                <div className="bg-slate-900/60 p-2.5 rounded-lg border border-slate-800">
                  <div className="text-[11px] text-slate-400">Salary Fit</div>
                  <div className="text-sm font-bold text-white mt-0.5">{match.salary_score}%</div>
                  <div className="w-full bg-slate-800 h-1.5 rounded-full mt-1.5 overflow-hidden">
                    <div className="bg-amber-500 h-full rounded-full" style={{ width: `${match.salary_score}%` }}></div>
                  </div>
                </div>

                <div className="bg-slate-900/60 p-2.5 rounded-lg border border-slate-800">
                  <div className="text-[11px] text-slate-400">Education</div>
                  <div className="text-sm font-bold text-white mt-0.5">{match.education_score}%</div>
                  <div className="w-full bg-slate-800 h-1.5 rounded-full mt-1.5 overflow-hidden">
                    <div className="bg-cyan-500 h-full rounded-full" style={{ width: `${match.education_score}%` }}></div>
                  </div>
                </div>
              </div>

              {/* Match Reasons */}
              {match.match_reasons && match.match_reasons.length > 0 && (
                <div className="space-y-1.5 pt-2 border-t border-slate-800/80">
                  <div className="text-xs font-semibold text-slate-300">Why You're a Strong Fit:</div>
                  <ul className="space-y-1 text-xs text-slate-400">
                    {match.match_reasons.map((r, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                        <span>{r}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* Skills Breakdown */}
          <div className="space-y-3">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Skills Comparison</h4>
            <div className="space-y-3">
              <div>
                <span className="text-xs text-emerald-400 font-medium flex items-center gap-1.5 mb-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  Your Matching Skills ({match?.matching_skills?.length || 0})
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {match?.matching_skills?.map((s, idx) => (
                    <span key={idx} className="px-2.5 py-1 rounded-md text-xs font-medium bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">
                      {s}
                    </span>
                  ))}
                  {(!match?.matching_skills || match.matching_skills.length === 0) && (
                    <span className="text-xs text-slate-500 italic">None specifically matched</span>
                  )}
                </div>
              </div>

              {match?.missing_skills && match.missing_skills.length > 0 && (
                <div>
                  <span className="text-xs text-amber-400 font-medium flex items-center gap-1.5 mb-1.5">
                    <AlertTriangle className="w-3.5 h-3.5" />
                    Missing / Preferred Keywords ({match.missing_skills.length})
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {match.missing_skills.map((s, idx) => (
                      <span key={idx} className="px-2.5 py-1 rounded-md text-xs font-medium bg-amber-500/10 text-amber-300 border border-amber-500/20">
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Description */}
          {job.description && (
            <div className="space-y-2">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Job Description</h4>
              <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800 text-xs text-slate-300 leading-relaxed max-h-56 overflow-y-auto whitespace-pre-line">
                {job.description}
              </div>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="p-4 bg-slate-950 border-t border-slate-800 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <button
              onClick={() => onDraftEmail(job)}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs shadow-md shadow-indigo-600/30 transition-colors"
            >
              <Mail className="w-4 h-4" />
              Draft Cold Email
            </button>

            <button
              onClick={() => onTailorResume(job)}
              className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition-colors"
            >
              <FileText className="w-4 h-4 text-purple-400" />
              Tailor Resume
            </button>

            <button
              onClick={() => onTrackApplication(job)}
              className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition-colors"
            >
              <Plus className="w-4 h-4 text-emerald-400" />
              Track in Pipeline
            </button>
          </div>

          {job.application_url && (
            <a
              href={job.application_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-slate-400 hover:text-white text-xs font-medium transition-colors"
            >
              <span>Apply on Company Portal</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          )}
        </div>
      </div>
    </div>
  );
};
