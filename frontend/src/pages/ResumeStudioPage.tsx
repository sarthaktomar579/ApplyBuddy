import React, { useState, useEffect } from 'react';
import { getResumes, uploadResume, setDefaultResume, getJobs, tailorResumeForJob, answerApplicationQuestions } from '../services/api';
import { Resume, Job } from '../types';
import { Navbar } from '../components/Navbar';
import {
  FileText,
  Upload,
  CheckCircle2,
  Sparkles,
  Paperclip,
  Copy,
  Lightbulb,
  Check,
  AlertCircle,
  Loader2,
  HelpCircle,
  Briefcase
} from 'lucide-react';

export const ResumeStudioPage: React.FC = () => {
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<number | null>(null);
  const [uploading, setUploading] = useState(false);
  const [tailoring, setTailoring] = useState(false);
  const [tailorResult, setTailorResult] = useState<any | null>(null);
  const [answering, setAnswering] = useState(false);
  const [questionsInput, setQuestionsInput] = useState(
    "Why do you want to work here?\nTell me about a difficult technical challenge you solved."
  );
  const [answersResult, setAnswersResult] = useState<any[]>([]);
  const [copiedIndex, setCopiedIndex] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const loadData = async () => {
    try {
      const [resumesList, jobsList] = await Promise.all([getResumes(), getJobs({ limit: 50 })]);
      setResumes(resumesList);
      setJobs(jobsList.jobs);
      if (jobsList.jobs.length > 0 && !selectedJobId) {
        setSelectedJobId(jobsList.jobs[0].id);
      }
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('label', file.name.replace('.pdf', ''));

    try {
      await uploadResume(formData);
      setStatusMessage(`Resume "${file.name}" uploaded successfully!`);
      setTimeout(() => setStatusMessage(null), 3500);
      await loadData();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to upload resume PDF');
    } finally {
      setUploading(false);
    }
  };

  const handleSetDefault = async (resume: Resume) => {
    try {
      await setDefaultResume(resume.id);
      await loadData();
    } catch (err) {
      console.error(err);
    }
  };

  const handleRunTailor = async () => {
    if (!selectedJobId) return;
    setTailoring(true);
    try {
      const res = await tailorResumeForJob(selectedJobId);
      setTailorResult(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setTailoring(false);
    }
  };

  const handleRunAnswerQuestions = async () => {
    if (!selectedJobId) return;
    setAnswering(true);
    const questions = questionsInput.split('\n').map((q) => q.trim()).filter(Boolean);
    try {
      const res = await answerApplicationQuestions(selectedJobId, questions);
      setAnswersResult(res.answers);
    } catch (err) {
      console.error(err);
    } finally {
      setAnswering(false);
    }
  };

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(id);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Navbar
        title="Resume & Application QA Studio"
        subtitle="AI resume optimization, keyword tailoring, and high-impact portal question answers"
      />

      <main className="flex-1 p-8 space-y-8 max-w-7xl mx-auto w-full">
        {statusMessage && (
          <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4" />
              <span>{statusMessage}</span>
            </div>
            <button onClick={() => setStatusMessage(null)} className="text-slate-400 hover:text-white">✕</button>
          </div>
        )}

        {/* Section 1: Resume PDFs */}
        <div className="glass-panel p-6 rounded-xl border border-slate-800 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <FileText className="w-4 h-4 text-indigo-400" />
                Resume Documents
              </h3>
              <p className="text-xs text-slate-400">
                Uploaded PDF resumes used for auto-attachments and parsing
              </p>
            </div>

            <label className="flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-600/30 cursor-pointer transition-colors shrink-0">
              {uploading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Upload className="w-3.5 h-3.5" />}
              Upload New PDF
              <input type="file" accept=".pdf" onChange={handleFileUpload} className="hidden" />
            </label>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
            {resumes.map((r) => (
              <div
                key={r.id}
                className="bg-slate-900 border border-slate-800 rounded-lg p-4 flex items-start justify-between gap-3"
              >
                <div className="space-y-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-xs text-white truncate">{r.label}</span>
                    {r.is_default && (
                      <span className="text-[10px] bg-emerald-500/10 text-emerald-400 px-1.5 py-0.5 rounded border border-emerald-500/20 font-medium">
                        Default
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] text-slate-500 truncate">{r.filename}</p>
                  <p className="text-[10px] text-slate-600">
                    {(r.file_size / 1024).toFixed(1)} KB • v{r.version}
                  </p>
                </div>

                {!r.is_default && (
                  <button
                    onClick={() => handleSetDefault(r)}
                    className="text-[11px] text-indigo-400 hover:text-indigo-300 font-medium shrink-0"
                  >
                    Set Default
                  </button>
                )}
              </div>
            ))}

            {resumes.length === 0 && (
              <div className="md:col-span-3 p-6 text-center text-xs text-slate-500 italic bg-slate-900/40 rounded-lg border border-slate-800">
                No custom resumes uploaded yet. Default candidate profile (Sarthak Singh Tomar) is active.
              </div>
            )}
          </div>
        </div>

        {/* Target Job Selector Bar */}
        <div className="glass-panel p-4 rounded-xl border border-indigo-500/30 bg-gradient-to-r from-indigo-950/40 to-slate-900 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-indigo-500/20 text-indigo-400 flex items-center justify-center shrink-0">
              <Briefcase className="w-5 h-5" />
            </div>
            <div>
              <h4 className="text-sm font-bold text-white">Target Job Context for AI Tailoring</h4>
              <p className="text-xs text-slate-400">
                Select a job from your pipeline to generate customized bullets & portal answers
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <select
              value={selectedJobId || ''}
              onChange={(e) => setSelectedJobId(Number(e.target.value))}
              className="bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 max-w-xs truncate"
            >
              {jobs.map((j) => (
                <option key={j.id} value={j.id}>
                  {j.company} — {j.title}
                </option>
              ))}
            </select>

            <button
              onClick={handleRunTailor}
              disabled={tailoring || !selectedJobId}
              className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-600/30 transition-colors shrink-0 disabled:opacity-60"
            >
              {tailoring ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
              Tailor Resume
            </button>
          </div>
        </div>

        {/* Section 2: Tailoring Output */}
        {tailorResult && (
          <div className="glass-panel p-6 rounded-xl border border-slate-800 space-y-6 animate-in fade-in">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h3 className="font-bold text-white text-base">
                  Resume Tailoring for {tailorResult.target_role}
                </h3>
                <p className="text-xs text-slate-400">
                  Recommended bullet points & summary statement designed to maximize ATS match
                </p>
              </div>
            </div>

            {/* Professional Summary */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-300">Customized Professional Summary</span>
                <button
                  onClick={() => copyToClipboard(tailorResult.summary_suggestion, 'summary')}
                  className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1"
                >
                  {copiedIndex === 'summary' ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                  {copiedIndex === 'summary' ? 'Copied' : 'Copy'}
                </button>
              </div>
              <p className="bg-slate-950 p-3.5 rounded-lg border border-slate-800 text-xs text-slate-300 leading-relaxed font-sans">
                {tailorResult.summary_suggestion}
              </p>
            </div>

            {/* Highlighted Projects */}
            <div className="space-y-2">
              <span className="text-xs font-semibold text-slate-300">Projects to Prioritize</span>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {tailorResult.highlighted_projects?.map((p: any, idx: number) => (
                  <div key={idx} className="bg-slate-950 p-3.5 rounded-lg border border-slate-800 space-y-1">
                    <span className="font-bold text-xs text-indigo-300">{p.name}</span>
                    <p className="text-xs text-slate-400 leading-relaxed">{p.focus}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Tailored Bullet Points */}
            <div className="space-y-2">
              <span className="text-xs font-semibold text-slate-300">Tailored Impact Bullet Points</span>
              <div className="space-y-2">
                {tailorResult.tailored_bullet_points?.map((bullet: string, idx: number) => (
                  <div
                    key={idx}
                    className="bg-slate-950 p-3 rounded-lg border border-slate-800 flex items-start justify-between gap-3 text-xs text-slate-300"
                  >
                    <span className="leading-relaxed">• {bullet}</span>
                    <button
                      onClick={() => copyToClipboard(bullet, `bullet-${idx}`)}
                      className="text-slate-500 hover:text-indigo-400 shrink-0"
                    >
                      {copiedIndex === `bullet-${idx}` ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* ATS Keywords */}
            <div className="space-y-2">
              <span className="text-xs font-semibold text-slate-300">Target Keywords for ATS Scoring</span>
              <div className="flex flex-wrap gap-1.5">
                {tailorResult.keywords_to_emphasize?.map((k: string, idx: number) => (
                  <span
                    key={idx}
                    className="px-2.5 py-1 rounded-md text-xs font-mono font-medium bg-indigo-500/10 text-indigo-300 border border-indigo-500/20"
                  >
                    {k}
                  </span>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Section 3: Application Portal QA Copilot */}
        <div className="glass-panel p-6 rounded-xl border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-bold text-white text-base flex items-center gap-2">
                <HelpCircle className="w-4 h-4 text-purple-400" />
                Portal Application QA Copilot
              </h3>
              <p className="text-xs text-slate-400">
                Paste any questions from Workday / Greenhouse application forms to generate tailored responses
              </p>
            </div>
            <button
              onClick={handleRunAnswerQuestions}
              disabled={answering || !selectedJobId}
              className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold shadow-md shadow-purple-600/30 transition-colors disabled:opacity-60"
            >
              {answering ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
              Generate Answers
            </button>
          </div>

          <textarea
            rows={3}
            value={questionsInput}
            onChange={(e) => setQuestionsInput(e.target.value)}
            placeholder="Type one question per line..."
            className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
          />

          {answersResult.length > 0 && (
            <div className="space-y-3 pt-3">
              {answersResult.map((a, idx) => (
                <div key={idx} className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-xs text-slate-200">Q: {a.question}</span>
                    <button
                      onClick={() => copyToClipboard(a.suggested_answer, `qa-${idx}`)}
                      className="text-xs text-purple-400 hover:text-purple-300 flex items-center gap-1"
                    >
                      {copiedIndex === `qa-${idx}` ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                      {copiedIndex === `qa-${idx}` ? 'Copied' : 'Copy Answer'}
                    </button>
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed font-sans whitespace-pre-line bg-slate-900/50 p-3 rounded-lg border border-slate-800/80">
                    {a.suggested_answer}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
};
