import React, { Suspense, lazy } from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';
import { Navbar } from './components/layout/Navbar';
import { ErrorBoundary } from './components/ui/ErrorBoundary';
import { Skeleton } from './components/ui/Skeleton';
import './styles/global.css';

// Lazy load pages for code splitting
const WorkspacePage = lazy(() => import('./pages/WorkspacePage').then(m => ({ default: m.WorkspacePage })));
const SessionPage = lazy(() => import('./pages/SessionPage').then(m => ({ default: m.SessionPage })));
const JournalPage = lazy(() => import('./pages/JournalPage').then(m => ({ default: m.JournalPage })));
const StatsPage = lazy(() => import('./pages/StatsPage').then(m => ({ default: m.StatsPage })));
const SettingsPage = lazy(() => import('./pages/SettingsPage').then(m => ({ default: m.SettingsPage })));
const LearningPage = lazy(() => import('./pages/LearningPage').then(m => ({ default: m.LearningPage })));
const LearningCenter = lazy(() => import('./pages/LearningCenter').then(m => ({ default: m.default })));
const NotFoundPage = lazy(() => import('./pages/NotFoundPage').then(m => ({ default: m.NotFoundPage })));

// Loading fallback component
const PageLoader: React.FC = () => (
  <div className="page-loader">
    <div className="page-loader-content">
      <Skeleton variant="text" width="200px" height="2rem" />
      <Skeleton variant="text" width="300px" height="1rem" />
      <div style={{ marginTop: '2rem' }}>
        <Skeleton variant="card" width="100%" height="200px" />
      </div>
    </div>
  </div>
);

// Animated routes component
const AnimatedRoutes: React.FC = () => {
  const location = useLocation();

  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        <Route path="/" element={<WorkspacePage />} />
        <Route path="/learning" element={<LearningPage />} />
        <Route path="/ai-brain" element={<LearningCenter />} />
        <Route path="/session/:id" element={<SessionPage />} />
        <Route path="/journal" element={<JournalPage />} />
        <Route path="/stats" element={<StatsPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </AnimatePresence>
  );
};

function App() {
  return (
    <ErrorBoundary>
      <Router>
        <Navbar />
        <main className="main-content">
          <Suspense fallback={<PageLoader />}>
            <AnimatedRoutes />
          </Suspense>
        </main>
      </Router>
    </ErrorBoundary>
  );
}

export default App;
