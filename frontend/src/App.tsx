import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Navbar } from './components/layout/Navbar';
import { WorkspacePage } from './pages/WorkspacePage';
import { SessionPage } from './pages/SessionPage';
import { JournalPage } from './pages/JournalPage';
import { StatsPage } from './pages/StatsPage';
import { SettingsPage } from './pages/SettingsPage';
import { LearningPage } from './pages/LearningPage';
import './styles/global.css';

function App() {
  return (
    <Router>
      <Navbar />
      <main className="main-content">
        <Routes>
          <Route path="/" element={<WorkspacePage />} />
          <Route path="/learning" element={<LearningPage />} />
          <Route path="/session/:id" element={<SessionPage />} />
          <Route path="/journal" element={<JournalPage />} />
          <Route path="/stats" element={<StatsPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </main>
    </Router>
  );
}

export default App;
