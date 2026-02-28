import React, { useState, useEffect } from 'react';
import { toast } from 'react-hot-toast';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { aiApi } from '../services/api';
import { useSettingsStore, type AIProvider } from '../store/settingsStore';
import './SettingsPage.css';

const PROVIDERS: { value: AIProvider; label: string; description: string; icon: string }[] = [
    { value: 'lmstudio', label: 'LM Studio (Local)', description: 'Run AI locally, fully private. Requires LM Studio running on port 1234.', icon: '🖥️' },
    { value: 'gemini', label: 'Google Gemini', description: 'Google\'s Gemini model. Requires a GEMINI_API_KEY in .env.', icon: '✨' },
    { value: 'openai', label: 'OpenAI GPT', description: 'OpenAI GPT-4o-mini. Requires an OPENAI_API_KEY in .env.', icon: '🤖' },
];

export const SettingsPage: React.FC = () => {
    const { aiProvider, setAiProvider, artistName, setArtistName, defaultBpm, setDefaultBpm } = useSettingsStore();
    const [isSaving, setIsSaving] = useState(false);
    const [currentProviderName, setCurrentProviderName] = useState<string>('');

    // Load the current active provider from backend on mount
    useEffect(() => {
        aiApi.ask('__ping__', 0).catch(() => { }); // warm up
        fetch('/api/ai/provider')
            .then(r => r.json())
            .then(data => {
                if (data.provider) {
                    setCurrentProviderName(data.provider);
                }
            })
            .catch(() => { });
    }, []);

    const handleProviderChange = async (newProvider: AIProvider) => {
        setAiProvider(newProvider); // update local store immediately (optimistic)
        try {
            const res = await aiApi.switchProvider(newProvider);
            if (res.success) {
                setCurrentProviderName(newProvider);
                toast.success(`✅ AI provider switched to ${newProvider}`);
            } else {
                toast.error('Failed to switch provider on backend');
            }
        } catch {
            toast.error('Failed to reach backend');
        }
    };

    const handleSave = async () => {
        setIsSaving(true);
        try {
            // Switch provider on backend
            await aiApi.switchProvider(aiProvider);
            toast.success('✅ Settings saved!');
        } catch {
            toast.error('Failed to save settings');
        } finally {
            setIsSaving(false);
        }
    };

    return (
        <div className="settings-page">
            <div className="page-header">
                <h1>⚙️ Settings</h1>
                <p className="subtitle">Customize your writing experience</p>
            </div>

            {/* AI Provider */}
            <Card className="settings-section" glass>
                <h3>🤖 AI Provider</h3>
                <p className="setting-description">
                    Choose which AI engine powers your lyric improvements, suggestions, and polish features.
                    This setting applies globally to the whole app immediately.
                </p>

                {currentProviderName && (
                    <div className="provider-status">
                        <span className="status-dot active" />
                        Backend is using: <strong>{currentProviderName}</strong>
                    </div>
                )}

                <div className="provider-cards">
                    {PROVIDERS.map(p => (
                        <div
                            key={p.value}
                            className={`provider-card ${aiProvider === p.value ? 'selected' : ''}`}
                            onClick={() => handleProviderChange(p.value)}
                        >
                            <div className="provider-icon">{p.icon}</div>
                            <div className="provider-info">
                                <div className="provider-name">{p.label}</div>
                                <div className="provider-desc">{p.description}</div>
                            </div>
                            {aiProvider === p.value && (
                                <div className="provider-check">✓</div>
                            )}
                        </div>
                    ))}
                </div>
            </Card>

            {/* Artist Profile */}
            <Card className="settings-section" glass>
                <h3>🎤 Artist Profile</h3>
                <div className="setting-row">
                    <label>Artist Name</label>
                    <input
                        type="text"
                        className="input"
                        placeholder="Your stage name..."
                        value={artistName}
                        onChange={(e) => setArtistName(e.target.value)}
                    />
                </div>
                <div className="setting-row">
                    <label>Default BPM</label>
                    <div className="bpm-row">
                        <input
                            type="range"
                            min="60"
                            max="200"
                            value={defaultBpm}
                            onChange={(e) => setDefaultBpm(parseInt(e.target.value))}
                            className="bpm-slider"
                        />
                        <span className="bpm-value">{defaultBpm} BPM</span>
                    </div>
                </div>
            </Card>

            {/* Vocabulary */}
            <Card className="settings-section" glass>
                <h3>🧠 Vocabulary &amp; Style</h3>
                <div className="setting-row">
                    <label>Favorite Words</label>
                    <p className="setting-sub">Comma-separated words you love to use.</p>
                    <textarea
                        className="input textarea-sm"
                        placeholder="eternal, soul, vibe, nebula..."
                    />
                </div>
                <div className="setting-row">
                    <label>Banned Words</label>
                    <p className="setting-sub">Words the AI should avoid.</p>
                    <textarea
                        className="input textarea-sm"
                        placeholder="cliche, baby, yeah..."
                    />
                </div>
            </Card>

            {/* Learning */}
            <Card className="settings-section" glass>
                <h3>📚 Learning</h3>
                <div className="setting-row">
                    <label>Style Learning</label>
                    <p className="setting-description">
                        VibeLyrics learns from your corrections and preferences to provide
                        better suggestions over time.
                    </p>
                </div>
            </Card>

            <div className="settings-actions">
                <Button variant="primary" onClick={handleSave} disabled={isSaving}>
                    {isSaving ? '⏳ Saving...' : '💾 Save Settings'}
                </Button>
            </div>
        </div>
    );
};
