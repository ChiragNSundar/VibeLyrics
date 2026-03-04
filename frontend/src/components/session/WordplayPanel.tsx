import React, { useState, useCallback } from 'react';
import { nlpApi } from '../../services/api';
import type { WordplaySuggestion } from '../../services/api';
import './WordplayPanel.css';

interface WordplayPanelProps {
    sessionId: number;
    sessionTheme?: string;
    sessionMood?: string;
    onInsert?: (text: string) => void;
}

export const WordplayPanel: React.FC<WordplayPanelProps> = ({
    sessionId,
    sessionTheme = '',
    sessionMood,
    onInsert,
}) => {
    const [theme, setTheme] = useState(sessionTheme);
    const [suggestions, setSuggestions] = useState<WordplaySuggestion[]>([]);
    const [loading, setLoading] = useState(false);

    const fetchWordplay = useCallback(async () => {
        if (!theme.trim()) return;
        setLoading(true);
        try {
            const res = await nlpApi.getWordplaySuggestions(theme, sessionId, sessionMood);
            setSuggestions(res.suggestions || []);
        } catch (err) {
            console.error('Wordplay fetch failed:', err);
        } finally {
            setLoading(false);
        }
    }, [theme, sessionId, sessionMood]);

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') fetchWordplay();
    };

    return (
        <div className="wordplay-panel">
            <h3>
                <span>🎯</span> Wordplay Engine
            </h3>

            <div className="wordplay-input-row">
                <input
                    type="text"
                    value={theme}
                    onChange={(e) => setTheme(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Enter a theme (e.g., money, power, love)"
                />
                <button onClick={fetchWordplay} disabled={loading || !theme.trim()}>
                    {loading ? '...' : 'Generate'}
                </button>
            </div>

            <div className="wordplay-list">
                {suggestions.length === 0 && !loading && (
                    <div className="wordplay-empty">
                        Enter a theme and hit Generate to get wordplay suggestions
                    </div>
                )}
                {suggestions.map((s, i) => (
                    <div
                        key={i}
                        className="wordplay-item"
                        style={{ animationDelay: `${i * 0.08}s` }}
                        onClick={() => onInsert?.(s.text)}
                        title="Click to insert"
                    >
                        <div className="wp-type">{s.type}</div>
                        <div className="wp-text">{s.text}</div>
                        {s.explanation && (
                            <div className="wp-explanation">{s.explanation}</div>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
};

export default WordplayPanel;
