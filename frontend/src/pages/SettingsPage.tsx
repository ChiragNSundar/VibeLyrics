import React, { useState } from 'react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import './SettingsPage.css';

export const SettingsPage: React.FC = () => {
    const [provider, setProvider] = useState('gemini');
    const [artistName, setArtistName] = useState('');
    const [defaultBpm, setDefaultBpm] = useState(140);

    const handleSave = async () => {
        // Would call API to save settings
        console.log('Saving settings:', { provider, artistName, defaultBpm });
    };

    return (
        <div className="settings-page">
            <div className="page-header">
                <h1>⚙️ Settings</h1>
                <p className="subtitle">Customize your writing experience</p>
            </div>

            <Card className="settings-section" glass>
                <h3>🤖 AI Provider</h3>
                <div className="setting-row">
                    <label>Default Provider</label>
                    <select
                        className="input"
                        value={provider}
                        onChange={(e) => setProvider(e.target.value)}
                    >
                        <option value="gemini">Gemini (Recommended)</option>
                        <option value="openai">OpenAI</option>
                        <option value="lmstudio">LM Studio (Local)</option>
                    </select>
                </div>
            </Card>

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
                    <input
                        type="number"
                        className="input"
                        min="60"
                        max="200"
                        value={defaultBpm}
                        onChange={(e) => setDefaultBpm(parseInt(e.target.value))}
                    />
                </div>
            </Card>

            <Card className="settings-section" glass>
                <h3>🧠 Vocabulary & Style</h3>
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
                <div className="setting-row">
                    <label>Slang Preferences</label>
                    <p className="setting-sub">Regional slang to include.</p>
                    <textarea
                        className="input textarea-sm"
                        placeholder="finna, lit, bet, cap..."
                    />
                </div>
            </Card>

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
                <Button variant="primary" onClick={handleSave}>
                    Save Settings
                </Button>
            </div>
        </div>
    );
};
