import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Toaster, toast } from 'react-hot-toast';
import { useSessionStore } from '../store/sessionStore';
import { useSettingsStore } from '../store/settingsStore';
import { useKeyboardShortcuts } from '../hooks/useKeyboardShortcuts';
import { LyricsEditor } from '../components/session/LyricsEditor';
import { RhymeWavePanel } from '../components/session/RhymeWavePanel.tsx';
import { AIHelpPanel } from '../components/session/AIHelpPanel.tsx';
import { PunchlinePanel } from '../components/session/PunchlinePanel';
import { RhymeLegend } from '../components/session/RhymeLegend';
import { BeatTimer } from '../components/session/BeatTimer';
import { WordplayPanel } from '../components/session/WordplayPanel';
import { ComplexityMeter } from '../components/session/ComplexityMeter';
import { DriftIndicator } from '../components/session/DriftIndicator';
import { AudioInfoCard } from '../components/session/AudioInfoCard';
import { Button } from '../components/ui/Button';
import { sessionApi, aiApi } from '../services/api';
import './SessionPage.css';

export const SessionPage: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const sessionId = parseInt(id || '0');

    const { currentSession, setSession, lines, setLines, reset, undo, redo } = useSessionStore();
    const { aiProvider } = useSettingsStore(); // global provider from Settings
    const [isLoading, setIsLoading] = useState(true);
    const [activePanel, setActivePanel] = useState<'none' | 'rhymewave' | 'aihelp' | 'punchline' | 'wordplay' | 'audio'>('none');

    useEffect(() => {
        loadSession();
        return () => reset();
    }, [sessionId]);

    // Sync the global provider setting to the backend whenever it changes
    useEffect(() => {
        aiApi.switchProvider(aiProvider).catch(() => { });
    }, [aiProvider]);

    // ── Session Time Tracker (Heartbeat) ─────────────────────
    useEffect(() => {
        if (!currentSession) return;
        const interval = setInterval(() => {
            if (document.hasFocus()) {
                sessionApi.heartbeat(sessionId).catch(console.error);
            }
        }, 30000); // 30 seconds
        return () => clearInterval(interval);
    }, [sessionId, currentSession]);

    // Keyboard shortcuts: Ctrl+Z undo, Ctrl+Y / Ctrl+Shift+Z redo
    useKeyboardShortcuts([
        { key: 'z', ctrlKey: true, action: () => undo(), description: 'Undo' },
        { key: 'y', ctrlKey: true, action: () => redo(), description: 'Redo' },
        { key: 'z', ctrlKey: true, shiftKey: true, action: () => redo(), description: 'Redo (Shift)' },
    ]);

    const loadSession = async () => {
        try {
            const response = await fetch(`/api/sessions/${sessionId}`);
            const data = await response.json();
            if (data.success) {
                setSession(data.session);
                setLines(data.lines || []);
            }
        } catch (error) {
            console.error('Failed to load session:', error);
            toast.error('Failed to load session');
        } finally {
            setIsLoading(false);
        }
    };



    const togglePanel = (panel: 'rhymewave' | 'aihelp' | 'punchline' | 'wordplay' | 'audio') => {
        setActivePanel(activePanel === panel ? 'none' : panel);
    };

    if (isLoading) {
        return (
            <div className="session-loading">
                <div className="spinner" />
                <p>Loading session...</p>
            </div>
        );
    }

    if (!currentSession) {
        return (
            <div className="session-error">
                <h2>Session not found</h2>
                <Link to="/">
                    <Button variant="primary">Back to Workspace</Button>
                </Link>
            </div>
        );
    }

    return (
        <div className="session-page">
            <Toaster
                position="bottom-right"
                toastOptions={{
                    style: {
                        background: 'var(--bg-card)',
                        color: 'var(--text-primary)',
                        border: '1px solid var(--border-color)',
                    },
                }}
            />

            {/* Header Bar */}
            <header className="session-header glass">
                <div className="session-info">
                    <Link to="/" className="back-link">
                        ← Back
                    </Link>
                    <h1 className="session-title">{currentSession.title}</h1>
                    <div className="session-badges">
                        <span className="bpm-badge">{currentSession.bpm} BPM</span>
                        {currentSession.mood && <span className="mood-tag">{currentSession.mood}</span>}
                    </div>
                </div>

                <div className="session-actions">
                    <Link to="/settings" className="provider-badge" title="Change AI provider in Settings">
                        🤖 {aiProvider}
                    </Link>
                    <Button variant="secondary" size="sm">
                        📊 Analyze
                    </Button>
                    <div className="writing-time" style={{ fontSize: '0.85rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '0.4rem', borderLeft: '1px solid var(--border-color)', paddingLeft: '1rem', marginLeft: '0.5rem' }}>
                        ⏱️ {currentSession.total_writing_seconds ? Math.floor(currentSession.total_writing_seconds / 60) : 0}m
                    </div>
                    <Button variant="secondary" size="sm">
                        📄 Export
                    </Button>
                </div>
            </header>

            {/* Main Content */}
            <div className={`session-content ${activePanel !== 'none' ? 'with-panel' : ''}`}>
                {/* Left Toggle Buttons */}
                <div className="panel-toggles">
                    <button
                        className={`panel-toggle ${activePanel === 'rhymewave' ? 'active' : ''}`}
                        onClick={() => togglePanel('rhymewave')}
                        title="RhymeWave"
                    >
                        🌊
                    </button>
                    <button
                        className={`panel-toggle ${activePanel === 'aihelp' ? 'active' : ''}`}
                        onClick={() => togglePanel('aihelp')}
                        title="AI Help"
                    >
                        🤖
                    </button>
                    <button
                        className={`panel-toggle ${activePanel === 'punchline' ? 'active' : ''}`}
                        onClick={() => togglePanel('punchline')}
                        title="Punchlines & Metaphors"
                    >
                        🔥
                    </button>
                    <button
                        className={`panel-toggle ${activePanel === 'wordplay' ? 'active' : ''}`}
                        onClick={() => togglePanel('wordplay')}
                        title="Wordplay Engine"
                    >
                        🎯
                    </button>
                    <button
                        className={`panel-toggle ${activePanel === 'audio' ? 'active' : ''}`}
                        onClick={() => togglePanel('audio')}
                        title="Beat Analysis"
                    >
                        🎵
                    </button>
                </div>

                {/* Left Panel */}
                <AnimatePresence>
                    {activePanel === 'rhymewave' && (
                        <motion.div
                            className="side-panel"
                            initial={{ width: 0, opacity: 0 }}
                            animate={{ width: 400, opacity: 1 }}
                            exit={{ width: 0, opacity: 0 }}
                            transition={{ duration: 0.3 }}
                        >
                            <RhymeWavePanel onClose={() => setActivePanel('none')} />
                        </motion.div>
                    )}
                    {activePanel === 'aihelp' && (
                        <motion.div
                            className="side-panel"
                            initial={{ width: 0, opacity: 0 }}
                            animate={{ width: 400, opacity: 1 }}
                            exit={{ width: 0, opacity: 0 }}
                            transition={{ duration: 0.3 }}
                        >
                            <AIHelpPanel sessionId={sessionId} onClose={() => setActivePanel('none')} />
                        </motion.div>
                    )}
                    {activePanel === 'punchline' && (
                        <motion.div
                            className="side-panel"
                            initial={{ width: 0, opacity: 0 }}
                            animate={{ width: 400, opacity: 1 }}
                            exit={{ width: 0, opacity: 0 }}
                            transition={{ duration: 0.3 }}
                        >
                            <PunchlinePanel sessionId={sessionId} mood={currentSession?.mood} />
                        </motion.div>
                    )}
                    {activePanel === 'wordplay' && (
                        <motion.div
                            className="side-panel"
                            initial={{ width: 0, opacity: 0 }}
                            animate={{ width: 400, opacity: 1 }}
                            exit={{ width: 0, opacity: 0 }}
                            transition={{ duration: 0.3 }}
                        >
                            <WordplayPanel
                                sessionId={sessionId}
                                sessionTheme={currentSession?.theme}
                                sessionMood={currentSession?.mood}
                            />
                        </motion.div>
                    )}
                    {activePanel === 'audio' && (
                        <motion.div
                            className="side-panel"
                            initial={{ width: 0, opacity: 0 }}
                            animate={{ width: 400, opacity: 1 }}
                            exit={{ width: 0, opacity: 0 }}
                            transition={{ duration: 0.3 }}
                        >
                            <AudioInfoCard sessionId={sessionId} />
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* Main Editor */}
                <div className="editor-container">
                    <div className="editor-top-bar">
                        <BeatTimer bpm={currentSession.bpm} />
                        <ComplexityMeter
                            lines={lines.map(l => l.final_version || l.user_input)}
                        />
                    </div>
                    <LyricsEditor sessionId={sessionId} lines={lines} bpm={currentSession.bpm} rhymeScheme={currentSession.rhyme_scheme} />
                    <DriftIndicator sessionId={sessionId} lineCount={lines.length} />
                    <RhymeLegend />
                </div>
            </div>
        </div>
    );
};
