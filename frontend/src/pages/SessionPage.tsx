import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Toaster, toast } from 'react-hot-toast';
import { useSessionStore } from '../store/sessionStore';
import { LyricsEditor } from '../components/session/LyricsEditor';
import { RhymeWavePanel } from '../components/session/RhymeWavePanel.tsx';
import { AIHelpPanel } from '../components/session/AIHelpPanel.tsx';
import { PunchlinePanel } from '../components/session/PunchlinePanel';
import { RhymeLegend } from '../components/session/RhymeLegend';
import { Button } from '../components/ui/Button';
import './SessionPage.css';

export const SessionPage: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const sessionId = parseInt(id || '0');

    const { currentSession, setSession, lines, setLines, reset } = useSessionStore();
    const [isLoading, setIsLoading] = useState(true);
    const [activePanel, setActivePanel] = useState<'none' | 'rhymewave' | 'aihelp' | 'punchline'>('none');
    const [provider, setProvider] = useState('gemini');

    useEffect(() => {
        loadSession();
        return () => reset();
    }, [sessionId]);

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

    const handleProviderChange = async (newProvider: string) => {
        try {
            await fetch('/api/provider/switch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ provider: newProvider }),
            });
            setProvider(newProvider);
            toast.success(`Switched to ${newProvider}`);
        } catch (error) {
            toast.error('Failed to switch provider');
        }
    };

    const togglePanel = (panel: 'rhymewave' | 'aihelp' | 'punchline') => {
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
                    <select
                        className="provider-select"
                        value={provider}
                        onChange={(e) => handleProviderChange(e.target.value)}
                    >
                        <option value="gemini">Gemini</option>
                        <option value="openai">OpenAI</option>
                        <option value="lmstudio">LM Studio</option>
                    </select>
                    <Button variant="secondary" size="sm">
                        📊 Analyze
                    </Button>
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
                </AnimatePresence>

                {/* Main Editor */}
                <div className="editor-container">
                    <LyricsEditor sessionId={sessionId} lines={lines} bpm={currentSession.bpm} />
                    <RhymeLegend />
                </div>
            </div>
        </div>
    );
};
