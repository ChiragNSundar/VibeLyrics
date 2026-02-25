import React, { useState, useCallback } from 'react';
import { advancedApi } from '../../services/api';
import './PunchlinePanel.css';

interface PunchlinePanelProps {
    sessionId: number;
    mood?: string;
    onInsertLine?: (line: string) => void;
}

type TabType = 'punchlines' | 'metaphors' | 'adlibs';

interface ScoredPunchline {
    line: string;
    score: number;
    techniques: string[];
}

export const PunchlinePanel: React.FC<PunchlinePanelProps> = ({
    sessionId,
    mood,
    onInsertLine,
}) => {
    const [activeTab, setActiveTab] = useState<TabType>('punchlines');
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

    // Punchline state
    const [punchlines, setPunchlines] = useState<ScoredPunchline[]>([]);
    const [punchlineSource, setPunchlineSource] = useState('');

    // Metaphor/Simile state
    const [metaphors, setMetaphors] = useState<string[]>([]);
    const [metaphorSource, setMetaphorSource] = useState('');
    const [metaphorMode, setMetaphorMode] = useState<'metaphor' | 'simile'>('metaphor');

    // Adlib state
    const [adlibs, setAdlibs] = useState<string[]>([]);
    const [adlibTone, setAdlibTone] = useState('');
    const [adlibPlacements, setAdlibPlacements] = useState<Array<{
        position: number;
        after_word: string;
        suggested: string;
        type: string;
    }>>([]);
    const [artistStyle, setArtistStyle] = useState('');

    const handleCopy = useCallback((text: string, index: number) => {
        navigator.clipboard.writeText(text);
        setCopiedIndex(index);
        setTimeout(() => setCopiedIndex(null), 1500);
        if (onInsertLine) {
            onInsertLine(text);
        }
    }, [onInsertLine]);

    const generatePunchlines = async () => {
        if (!input.trim()) return;
        setLoading(true);

        try {
            const res = await advancedApi.generateAiPunchlines(input, sessionId, mood);
            if (res.success) {
                const scored = Array.isArray(res.punchlines)
                    ? res.punchlines.map((p) =>
                        typeof p === 'string'
                            ? { line: p, score: 0, techniques: [] }
                            : p
                    )
                    : [];
                setPunchlines(scored);
                setPunchlineSource(res.source || 'ai');
            }
        } catch (err) {
            console.error('Punchline generation failed:', err);
        } finally {
            setLoading(false);
        }
    };

    const generateMetaphors = async () => {
        if (!input.trim()) return;
        setLoading(true);

        try {
            if (metaphorMode === 'metaphor') {
                const res = await advancedApi.generateMetaphors(input, 5, sessionId);
                if (res.success) {
                    setMetaphors(res.metaphors);
                    setMetaphorSource(res.source || 'ai');
                }
            } else {
                const res = await advancedApi.generateSimiles(input, 5, sessionId);
                if (res.success) {
                    setMetaphors(res.similes);
                    setMetaphorSource(res.source || 'ai');
                }
            }
        } catch (err) {
            console.error('Metaphor generation failed:', err);
        } finally {
            setLoading(false);
        }
    };

    const generateAdlibs = async () => {
        if (!input.trim()) return;
        setLoading(true);

        try {
            const res = await advancedApi.generateContextualAdlibs(
                input, mood, artistStyle || undefined, [], false
            );
            if (res.success) {
                setAdlibs(res.adlibs);
                setAdlibTone(res.detected_tone);
                setAdlibPlacements(res.placements || []);
            }
        } catch (err) {
            console.error('Adlib generation failed:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleGenerate = () => {
        switch (activeTab) {
            case 'punchlines':
                generatePunchlines();
                break;
            case 'metaphors':
                generateMetaphors();
                break;
            case 'adlibs':
                generateAdlibs();
                break;
        }
    };

    const getPlaceholder = () => {
        switch (activeTab) {
            case 'punchlines': return 'Enter a theme... (e.g. "grinding", "loyalty")';
            case 'metaphors': return metaphorMode === 'metaphor' ? 'Enter a concept...' : 'Enter a word...';
            case 'adlibs': return 'Enter a bar to get adlib suggestions...';
        }
    };

    const getButtonLabel = () => {
        switch (activeTab) {
            case 'punchlines': return '🔥 Generate';
            case 'metaphors': return '💎 Generate';
            case 'adlibs': return '🎤 Suggest';
        }
    };

    return (
        <div className="punchline-panel">
            {/* Tabs */}
            <div className="punchline-tabs">
                <button
                    className={`punchline-tab ${activeTab === 'punchlines' ? 'active' : ''}`}
                    onClick={() => setActiveTab('punchlines')}
                >
                    🔥 Bars
                </button>
                <button
                    className={`punchline-tab ${activeTab === 'metaphors' ? 'active' : ''}`}
                    onClick={() => setActiveTab('metaphors')}
                >
                    💎 Metaphors
                </button>
                <button
                    className={`punchline-tab ${activeTab === 'adlibs' ? 'active' : ''}`}
                    onClick={() => setActiveTab('adlibs')}
                >
                    🎤 Adlibs
                </button>
            </div>

            {/* Metaphor mode toggle */}
            {activeTab === 'metaphors' && (
                <div className="punchline-tabs" style={{ gap: '0.15rem' }}>
                    <button
                        className={`punchline-tab ${metaphorMode === 'metaphor' ? 'active' : ''}`}
                        onClick={() => setMetaphorMode('metaphor')}
                        style={{ fontSize: '0.7rem' }}
                    >
                        Metaphors
                    </button>
                    <button
                        className={`punchline-tab ${metaphorMode === 'simile' ? 'active' : ''}`}
                        onClick={() => setMetaphorMode('simile')}
                        style={{ fontSize: '0.7rem' }}
                    >
                        Similes
                    </button>
                </div>
            )}

            {/* Artist style selector for adlibs */}
            {activeTab === 'adlibs' && (
                <select
                    className="adlib-style-select"
                    value={artistStyle}
                    onChange={(e) => setArtistStyle(e.target.value)}
                >
                    <option value="">Any Style</option>
                    <option value="travis_scott">Travis Scott</option>
                    <option value="drake">Drake</option>
                    <option value="kendrick">Kendrick Lamar</option>
                    <option value="future">Future</option>
                    <option value="migos">Migos</option>
                    <option value="21_savage">21 Savage</option>
                    <option value="j_cole">J. Cole</option>
                    <option value="kanye">Kanye West</option>
                </select>
            )}

            {/* Input */}
            <div className="punchline-input-row">
                <input
                    className="punchline-input"
                    placeholder={getPlaceholder()}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleGenerate()}
                />
                <button
                    className="punchline-generate-btn"
                    onClick={handleGenerate}
                    disabled={loading || !input.trim()}
                >
                    {loading ? '...' : getButtonLabel()}
                </button>
            </div>

            {/* Results */}
            <div className="punchline-results">
                {loading && (
                    <div className="punchline-loading">
                        <div className="punchline-loading-spinner" />
                        Generating...
                    </div>
                )}

                {!loading && activeTab === 'punchlines' && punchlines.length === 0 && (
                    <div className="punchline-empty">
                        <div className="punchline-empty-icon">🔥</div>
                        Enter a theme to generate AI-powered punchlines
                    </div>
                )}

                {!loading && activeTab === 'punchlines' &&
                    punchlines.map((p, i) => (
                        <div
                            key={i}
                            className={`punchline-card ${copiedIndex === i ? 'copied' : ''}`}
                            onClick={() => handleCopy(p.line, i)}
                            title="Click to copy & insert"
                        >
                            <div className="punchline-card-text">{p.line}</div>
                            <div className="punchline-card-meta">
                                {p.score > 0 && <span className="punchline-score">⚡ {p.score}</span>}
                                {p.techniques?.map((t, ti) => (
                                    <span key={ti} className="punchline-technique">{t}</span>
                                ))}
                                {punchlineSource && (
                                    <span className="punchline-technique">{punchlineSource}</span>
                                )}
                            </div>
                        </div>
                    ))}

                {!loading && activeTab === 'metaphors' && metaphors.length === 0 && (
                    <div className="punchline-empty">
                        <div className="punchline-empty-icon">💎</div>
                        Enter a concept to generate {metaphorMode === 'metaphor' ? 'metaphors' : 'similes'}
                    </div>
                )}

                {!loading && activeTab === 'metaphors' &&
                    metaphors.map((m, i) => (
                        <div
                            key={i}
                            className={`punchline-card ${copiedIndex === i + 100 ? 'copied' : ''}`}
                            onClick={() => handleCopy(m, i + 100)}
                            title="Click to copy & insert"
                        >
                            <div className="punchline-card-text">{m}</div>
                            <div className="punchline-card-meta">
                                <span className="punchline-technique">{metaphorMode}</span>
                                {metaphorSource && (
                                    <span className="punchline-technique">{metaphorSource}</span>
                                )}
                            </div>
                        </div>
                    ))}

                {!loading && activeTab === 'adlibs' && adlibs.length === 0 && (
                    <div className="punchline-empty">
                        <div className="punchline-empty-icon">🎤</div>
                        Enter a bar to get contextual adlib suggestions
                    </div>
                )}

                {!loading && activeTab === 'adlibs' && adlibs.length > 0 && (
                    <>
                        {adlibTone && (
                            <div style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.4)', marginBottom: '0.25rem' }}>
                                Detected tone: <strong style={{ color: '#c084fc' }}>{adlibTone}</strong>
                            </div>
                        )}
                        {adlibs.map((a, i) => (
                            <div
                                key={i}
                                className={`punchline-card ${copiedIndex === i + 200 ? 'copied' : ''}`}
                                onClick={() => handleCopy(a, i + 200)}
                                title="Click to copy"
                            >
                                <div className="punchline-card-text">{a}</div>
                            </div>
                        ))}
                        {adlibPlacements.length > 0 && (
                            <div className="adlib-placement">
                                <div style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.4)', marginBottom: '0.5rem' }}>
                                    Suggested placements:
                                </div>
                                {adlibPlacements.map((p, i) => (
                                    <div key={i} className="adlib-placement-item">
                                        <span className="adlib-placement-badge">{p.type}</span>
                                        after "{p.after_word}" → <strong style={{ color: '#67e8f9' }}>{p.suggested}</strong>
                                    </div>
                                ))}
                            </div>
                        )}
                    </>
                )}
            </div>

            {copiedIndex !== null && (
                <div className="copy-toast">✓ Copied to clipboard</div>
            )}
        </div>
    );
};
