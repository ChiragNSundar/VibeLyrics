import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import type { Session } from '../services/api';
import { sessionApi } from '../services/api';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import './WorkspacePage.css';

export const WorkspacePage: React.FC = () => {
    const navigate = useNavigate();
    const [sessions, setSessions] = useState<Session[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [showNewForm, setShowNewForm] = useState(false);
    const [newSession, setNewSession] = useState({
        title: '',
        bpm: 140,
        mood: '',
        theme: '',
    });

    useEffect(() => {
        loadSessions();
    }, []);

    const loadSessions = async () => {
        try {
            const data = await sessionApi.getAll();
            setSessions(data.sessions || []);
        } catch (error) {
            console.error('Failed to load sessions:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleCreateSession = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newSession.title.trim()) return;

        try {
            const response = await sessionApi.create(newSession);
            if (response.success) {
                setSessions([response.session, ...sessions]);
                setShowNewForm(false);
                setNewSession({ title: '', bpm: 140, mood: '', theme: '' });
                navigate(`/session/${response.session.id}`);
            }
        } catch (error) {
            console.error('Failed to create session:', error);
        }
    };

    const handleDeleteSession = async (id: number, e: React.MouseEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (!confirm('Delete this session?')) return;

        try {
            await sessionApi.delete(id);
            setSessions(sessions.filter((s) => s.id !== id));
        } catch (error) {
            console.error('Failed to delete session:', error);
        }
    };

    return (
        <div className="workspace-page">
            <div className="page-header">
                <div>
                    <h1>Your Sessions</h1>
                    <p className="subtitle">Continue writing or start something new</p>
                </div>
                <Button variant="primary" onClick={() => setShowNewForm(!showNewForm)}>
                    {showNewForm ? '✕ Cancel' : '+ New Session'}
                </Button>
            </div>

            {showNewForm && (
                <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                >
                    <Card className="new-session-form" glass>
                        <form onSubmit={handleCreateSession}>
                            <div className="form-row">
                                <div className="form-group">
                                    <label>Title</label>
                                    <input
                                        type="text"
                                        className="input"
                                        placeholder="Untitled Track"
                                        value={newSession.title}
                                        onChange={(e) => setNewSession({ ...newSession, title: e.target.value })}
                                        autoFocus
                                    />
                                </div>
                                <div className="form-group">
                                    <label>BPM</label>
                                    <input
                                        type="number"
                                        className="input"
                                        min="60"
                                        max="200"
                                        value={newSession.bpm}
                                        onChange={(e) => setNewSession({ ...newSession, bpm: parseInt(e.target.value) })}
                                    />
                                </div>
                            </div>
                            <div className="form-row">
                                <div className="form-group">
                                    <label>Mood (optional)</label>
                                    <select
                                        className="input"
                                        value={newSession.mood}
                                        onChange={(e) => setNewSession({ ...newSession, mood: e.target.value })}
                                    >
                                        <option value="">Select mood...</option>
                                        <option value="confident">🔥 Confident</option>
                                        <option value="melancholic">💔 Melancholic</option>
                                        <option value="aggressive">😤 Aggressive</option>
                                        <option value="chill">😎 Chill</option>
                                        <option value="introspective">🤔 Introspective</option>
                                    </select>
                                </div>
                                <div className="form-group">
                                    <label>Theme (optional)</label>
                                    <input
                                        type="text"
                                        className="input"
                                        placeholder="Success, struggle, love..."
                                        value={newSession.theme}
                                        onChange={(e) => setNewSession({ ...newSession, theme: e.target.value })}
                                    />
                                </div>
                            </div>
                            <div className="form-actions">
                                <Button type="submit" variant="primary">
                                    Create Session
                                </Button>
                            </div>
                        </form>
                    </Card>
                </motion.div>
            )}

            {isLoading ? (
                <div className="loading-state">
                    <div className="spinner" />
                    <p>Loading sessions...</p>
                </div>
            ) : sessions.length === 0 ? (
                <Card className="empty-state" glass>
                    <div className="empty-icon">🎤</div>
                    <h3>No sessions yet</h3>
                    <p>Create your first writing session to get started</p>
                </Card>
            ) : (
                <motion.div className="sessions-grid" layout>
                    {sessions.map((session, index) => (
                        <motion.div
                            key={session.id}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: index * 0.05 }}
                        >
                            <Link to={`/session/${session.id}`}>
                                <Card className="session-card" hover glow>
                                    <div className="session-header">
                                        <h3>{session.title}</h3>
                                        <Button
                                            variant="icon"
                                            className="delete-btn"
                                            onClick={(e) => handleDeleteSession(session.id, e)}
                                        >
                                            🗑️
                                        </Button>
                                    </div>
                                    <div className="session-meta">
                                        <span className="bpm-badge">{session.bpm} BPM</span>
                                        {session.mood && <span className="mood-tag">{session.mood}</span>}
                                        {session.theme && <span className="theme-tag">{session.theme}</span>}
                                    </div>
                                    <div className="session-stats">
                                        <span>{session.line_count || 0} lines</span>
                                        <span className="session-date">
                                            {new Date(session.updated_at).toLocaleDateString()}
                                        </span>
                                    </div>
                                </Card>
                            </Link>
                        </motion.div>
                    ))}
                </motion.div>
            )}
        </div>
    );
};
