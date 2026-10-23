import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Sidebar } from './components/Sidebar';
import { DashboardPage } from './pages/DashboardPage';
import { JobsPage } from './pages/JobsPage';
import { EmailsPage } from './pages/EmailsPage';
import { ApplicationsTrackerPage } from './pages/ApplicationsTrackerPage';
import { ResumeStudioPage } from './pages/ResumeStudioPage';
import { RecruitersPage } from './pages/RecruitersPage';
import { ProfilePage } from './pages/ProfilePage';
import { SettingsPage } from './pages/SettingsPage';

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-slate-950 text-slate-100 flex">
        {/* Left Fixed Sidebar */}
        <Sidebar />

        {/* Main Content Area */}
        <div className="flex-1 ml-64 min-h-screen flex flex-col bg-slate-950">
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/jobs" element={<JobsPage />} />
            <Route path="/emails" element={<EmailsPage />} />
            <Route path="/applications" element={<ApplicationsTrackerPage />} />
            <Route path="/resume-studio" element={<ResumeStudioPage />} />
            <Route path="/recruiters" element={<RecruitersPage />} />
            <Route path="/profile" element={<ProfilePage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  );
}
