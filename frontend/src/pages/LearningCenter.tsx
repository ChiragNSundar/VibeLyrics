import React, { useState, useEffect, useRef } from 'react';
import { learningApi } from '../services/api';
import type { LearningStatusResponse } from '../services/api';
import BrainMap from '../components/learning/BrainMap';
import DnaMatcher from '../components/learning/DnaMatcher';
import './LearningCenter.css';

const LearningCenter: React.FC = () => {
    // Top Level State
    const [status, setStatus] = useState<LearningStatusResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<'scrape' | 'manual'>('scrape');

    // Scraper State
    const [artistInput, setArtistInput] = useState('');
    const [eraInput, setEraInput] = useState('');
    const [scraping, setScraping] = useState(false);
    const [terminalLogs, setTerminalLogs] = useState<string[]>([]);

    // Manual Upload State
    const [manualText, setManualText] = useState('');
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [uploading, setUploading] = useState(false);
    const [uploadMessage, setUploadMessage] = useState('');

    // Phase 4 State
    const [dashboardTab, setDashboardTab] = useState<'stats' | 'brainmap' | 'dna'>('stats');
    const [annotations, setAnnotations] = useState<Array<{ line: string; score: number; techniques: string[]; notes: string[] }>>([]);
    const [audioResult, setAudioResult] = useState<{ bpm: number; key: string; energy: string } | null>(null);
    const [audioUploading, setAudioUploading] = useState(false);

    const endOfLogsRef = useRef<HTMLDivElement>(null);

    const fetchStatus = async () => {
        try {
            setLoading(true);
            const data = await learningApi.getStatus();
            setStatus(data);
        } catch (error) {
            console.error('Failed to fetch learning status:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchStatus();
    }, []);

    useEffect(() => {
        // Auto-scroll terminal logs
        if (endOfLogsRef.current) {
            endOfLogsRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [terminalLogs]);

    const handleScrapeStream = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!artistInput.trim()) return;

        setScraping(true);
        setTerminalLogs([`> Initializing connection to AI Engine...`]);

        const url = new URL('/api/learning/scrape/stream', window.location.origin);
        url.searchParams.append('artist', artistInput.trim());
        url.searchParams.append('max_songs', '3');
        if (eraInput.trim()) {
            url.searchParams.append('era', eraInput.trim());
        }

        const eventSource = new EventSource(url.toString());

        eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);

            if (data.error) {
                setTerminalLogs(prev => [...prev, `[ERROR] ${data.error}`]);
                eventSource.close();
                setScraping(false);
            } else if (data.msg) {
                setTerminalLogs(prev => [...prev, `> ${data.msg}`]);
                if (data.done) {
                    eventSource.close();
                    setScraping(false);
                    setArtistInput('');
                    setEraInput('');
                    setTimeout(fetchStatus, 1000); // Refresh stats
                }
            }
        };

        eventSource.onerror = (err) => {
            console.error("SSE Error:", err);
            setTerminalLogs(prev => [...prev, `[ERROR] Connection lost formatting stream.`]);
            eventSource.close();
            setScraping(false);
        };
    };

    const handleUpload = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!manualText.trim() && !selectedFile) return;

        try {
            setUploading(true);
            setUploadMessage('');
            const res = await learningApi.uploadDocument(selectedFile || undefined, manualText.trim() || undefined);
            setUploadMessage(`Success: Extracted from ${res.lines_parsed} lines and ${res.words_parsed} words.`);
            setManualText('');
            setSelectedFile(null);
            setTimeout(fetchStatus, 500);
        } catch (error: unknown) {
            const err = error as Error;
            setUploadMessage(err.message || 'Upload failed');
        } finally {
            setUploading(false);
        }
    };

    const handleDeleteVocab = async (word: string, type: 'favorites' | 'slangs' | 'avoided' | 'most_used') => {
        try {
            await learningApi.deleteVocabulary(word, type);
            // Optimistically update UI
            if (status) {
                const newStatus = { ...status };
                newStatus.vocabulary[type] = newStatus.vocabulary[type].filter(w => w !== word);
                setStatus(newStatus);
            }
        } catch (error) {
            console.error("Failed to delete word", error);
        }
    };

    const handleWipeBrain = async () => {
        if (!confirm("Are you SURE you want to wipe the AI's memory? All learned styles and vocabulary will be lost forever.")) {
            return;
        }
        try {
            await learningApi.resetBrain();
            fetchStatus();
        } catch (error) {
            console.error("Failed to reset brain", error);
        }
    };

    const handleFetchAnnotations = async () => {
        try {
            const res = await learningApi.getAnnotations();
            setAnnotations(res.annotations || []);
        } catch (error) {
            console.error('Failed to fetch annotations:', error);
        }
    };

    const handleAudioUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;
        try {
            setAudioUploading(true);
            const res = await learningApi.uploadAudio(file);
            setAudioResult({ bpm: res.bpm, key: res.key, energy: res.energy });
            setTimeout(fetchStatus, 500);
        } catch (error) {
            console.error('Audio analysis failed:', error);
        } finally {
            setAudioUploading(false);
        }
    };

    if (loading && !status) {
        return <div className="learning-center loading">Loading AI Brain...</div>;
    }

    return (
        <div className="learning-center-container fade-in">
            <header className="page-header">
                <div className="title-group">
                    <h1>AI Learning Center 🧠</h1>
                    <p className="subtitle">Feed the ghostwriter and explore its learned style</p>
                </div>
                <button onClick={handleWipeBrain} className="btn danger wipe-btn" title="Reset all learned style and vocabulary">
                    Wipe Brain
                </button>
            </header>

            <main className="learning-content">
                {/* ── Training Controls ── */}
                <section className="learning-card train-section">
                    <div className="tab-header">
                        <button
                            className={`tab-btn ${activeTab === 'scrape' ? 'active' : ''}`}
                            onClick={() => setActiveTab('scrape')}
                        >
                            Web Scraper
                        </button>
                        <button
                            className={`tab-btn ${activeTab === 'manual' ? 'active' : ''}`}
                            onClick={() => setActiveTab('manual')}
                        >
                            Manual Upload
                        </button>
                    </div>

                    {activeTab === 'scrape' ? (
                        <div className="tab-pane">
                            <p className="instructions">Scrape AZLyrics automatically to train the AI on an artist.</p>
                            <form onSubmit={handleScrapeStream} className="scrape-form">
                                <div className="input-row">
                                    <div className="input-group">
                                        <label>Artist Name</label>
                                        <input
                                            type="text"
                                            value={artistInput}
                                            onChange={(e) => setArtistInput(e.target.value)}
                                            placeholder="e.g., Kendrick Lamar"
                                            disabled={scraping}
                                            required
                                        />
                                    </div>
                                    <div className="input-group">
                                        <label>Era / Album (Optional)</label>
                                        <input
                                            type="text"
                                            value={eraInput}
                                            onChange={(e) => setEraInput(e.target.value)}
                                            placeholder="e.g., DAMN"
                                            disabled={scraping}
                                        />
                                    </div>
                                    <button
                                        type="submit"
                                        className="btn primary scrape-btn"
                                        disabled={scraping || !artistInput.trim()}
                                    >
                                        {scraping ? <span className="spinner-small"></span> : 'Start Extraction'}
                                    </button>
                                </div>
                            </form>

                            {/* Terminal UI */}
                            {(terminalLogs.length > 0 || scraping) && (
                                <div className="terminal-ui">
                                    <div className="terminal-header">Extraction Feed</div>
                                    <div className="terminal-body">
                                        {terminalLogs.map((log, i) => (
                                            <div key={i} className={`log-line ${log.includes('[ERROR]') ? 'error' : ''}`}>
                                                {log}
                                            </div>
                                        ))}
                                        <div ref={endOfLogsRef} />
                                    </div>
                                </div>
                            )}
                        </div>
                    ) : (
                        <div className="tab-pane">
                            <p className="instructions">Paste raw text or upload a document (.txt, .pdf, .docx) to feed the AI directly.</p>
                            <form onSubmit={handleUpload} className="upload-form">
                                <textarea
                                    value={manualText}
                                    onChange={(e) => setManualText(e.target.value)}
                                    placeholder="Paste lyrics, poetry, or existing songs here..."
                                    rows={5}
                                    disabled={uploading}
                                />
                                <div className="upload-row">
                                    <div className="file-input-wrapper">
                                        <input
                                            type="file"
                                            accept=".txt,.pdf,.docx"
                                            onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                                            disabled={uploading}
                                            id="file-upload"
                                        />
                                        <label htmlFor="file-upload" className="file-label">
                                            {selectedFile ? selectedFile.name : '📄 Choose File (Optional)'}
                                        </label>
                                    </div>
                                    <button
                                        type="submit"
                                        className="btn primary"
                                        disabled={uploading || (!manualText.trim() && !selectedFile)}
                                    >
                                        {uploading ? 'Parsing...' : 'Analyze & Learn'}
                                    </button>
                                </div>
                                {uploadMessage && (
                                    <div className={`status-message ${uploadMessage.includes('failed') ? 'error' : 'success'}`}>
                                        {uploadMessage}
                                    </div>
                                )}
                            </form>
                        </div>
                    )}
                </section>

                {/* ── Audio Upload Zone ── */}
                <section className="learning-card audio-section">
                    <h3>🎧 Audio Rhythm Analysis</h3>
                    <p className="instructions">Upload an .mp3 or .wav beat to extract BPM, key, and energy.</p>
                    <div className="upload-row">
                        <div className="file-input-wrapper">
                            <input
                                type="file"
                                accept=".mp3,.wav"
                                onChange={handleAudioUpload}
                                disabled={audioUploading}
                                id="audio-upload"
                            />
                            <label htmlFor="audio-upload" className="file-label">
                                {audioUploading ? '⏳ Analyzing...' : '🎵 Drop a Beat File'}
                            </label>
                        </div>
                    </div>
                    {audioResult && (
                        <div className="audio-results">
                            <div className="stat-box"><div className="stat-label">BPM</div><div className="stat-value">{audioResult.bpm}</div></div>
                            <div className="stat-box"><div className="stat-label">Key</div><div className="stat-value">{audioResult.key}</div></div>
                            <div className="stat-box"><div className="stat-label">Energy</div><div className="stat-value">{audioResult.energy}</div></div>
                        </div>
                    )}
                </section>

                {/* ── Knowledge Base Dashboard ── */}
                {status && (
                    <div className="knowledge-dashboard">
                        {/* Dashboard Tabs */}
                        <div className="dash-tab-bar">
                            <button className={`dash-tab ${dashboardTab === 'stats' ? 'active' : ''}`} onClick={() => setDashboardTab('stats')}>📊 Stats</button>
                            <button className={`dash-tab ${dashboardTab === 'brainmap' ? 'active' : ''}`} onClick={() => setDashboardTab('brainmap')}>🕸️ Brain Map</button>
                            <button className={`dash-tab ${dashboardTab === 'dna' ? 'active' : ''}`} onClick={() => setDashboardTab('dna')}>🧬 Lyrical DNA</button>
                        </div>

                        {dashboardTab === 'stats' && (
                            <>
                                <section className="learning-card">
                                    <h3>Learned Style Profile</h3>
                                    <div className="stats-grid">
                                        <div className="stat-box">
                                            <div className="stat-label">Rhyme Preference</div>
                                            <div className="stat-value">{status.style.rhyme_preference || 'Not enough data'}</div>
                                        </div>
                                        <div className="stat-box">
                                            <div className="stat-label">Avg Line Length</div>
                                            <div className="stat-value">{status.style.avg_line_length ? `${status.style.avg_line_length} words` : 'N/A'}</div>
                                        </div>
                                    </div>

                                    <div className="tag-section">
                                        <h4>Dominant Themes</h4>
                                        <div className="tag-list">
                                            {status.style.themes.length > 0 ? (
                                                status.style.themes.map((theme, i) => (
                                                    <span key={i} className="tag theme-tag">{theme}</span>
                                                ))
                                            ) : (
                                                <span className="no-data">Need more lyrics to detect themes.</span>
                                            )}
                                        </div>
                                    </div>
                                </section>

                                <section className="learning-card">
                                    <h3>Vocabulary Matrix</h3>
                                    <p className="hint">Click the × to make the AI forget a specific word.</p>

                                    <div className="tag-section mt-1">
                                        <h4>Signature Words (Most Used)</h4>
                                        <div className="tag-list">
                                            {status.vocabulary.most_used.length > 0 ? (
                                                status.vocabulary.most_used.map((word, i) => (
                                                    <span key={i} className="tag word-tag">
                                                        {word}
                                                        <button onClick={() => handleDeleteVocab(word, 'most_used')} className="delete-tag">×</button>
                                                    </span>
                                                ))
                                            ) : (
                                                <span className="no-data">No words tracking yet.</span>
                                            )}
                                        </div>
                                    </div>

                                    <div className="vocab-split mt-2">
                                        <div className="tag-section">
                                            <h4>Favorite Slangs</h4>
                                            <div className="tag-list">
                                                {status.vocabulary.slangs.length > 0 ? (
                                                    status.vocabulary.slangs.map((word, i) => (
                                                        <span key={i} className="tag slang-tag">
                                                            {word}
                                                            <button onClick={() => handleDeleteVocab(word, 'slangs')} className="delete-tag">×</button>
                                                        </span>
                                                    ))
                                                ) : (
                                                    <span className="no-data">None detected</span>
                                                )}
                                            </div>
                                        </div>

                                        <div className="tag-section">
                                            <h4>Avoided Words</h4>
                                            <div className="tag-list">
                                                {status.vocabulary.avoided.length > 0 ? (
                                                    status.vocabulary.avoided.map((word, i) => (
                                                        <span key={i} className="tag avoid-tag">
                                                            {word}
                                                            <button onClick={() => handleDeleteVocab(word, 'avoided')} className="delete-tag">×</button>
                                                        </span>
                                                    ))
                                                ) : (
                                                    <span className="no-data">None specified</span>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                </section>

                                {/* ── Annotations Panel ── */}
                                <section className="learning-card">
                                    <div className="annotations-header">
                                        <h3>📝 Auto-Annotations</h3>
                                        <button onClick={handleFetchAnnotations} className="btn primary btn-sm">Analyze Last Scrape</button>
                                    </div>
                                    {annotations.length > 0 ? (
                                        <div className="annotations-list">
                                            {annotations.map((a, i) => (
                                                <div key={i} className="annotation-row">
                                                    <div className="annotation-line">"{a.line}"</div>
                                                    <div className="annotation-meta">
                                                        <span className="punch-score" data-score={a.score > 50 ? 'high' : a.score > 25 ? 'mid' : 'low'}>
                                                            🎯 {a.score}/100
                                                        </span>
                                                        {a.notes.map((note, j) => (
                                                            <span key={j} className="annotation-note">{note}</span>
                                                        ))}
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    ) : (
                                        <p className="no-data mt-1">Scrape an artist first, then click "Analyze" to auto-annotate their lyrics.</p>
                                    )}
                                </section>
                            </>
                        )}

                        {dashboardTab === 'brainmap' && (
                            <section className="learning-card brain-map-card">
                                <h3>🕸️ Neural Vocabulary Map</h3>
                                <p className="hint">Explore how the AI connects words. Node size = frequency. Lines = co-occurrence.</p>
                                <BrainMap />
                            </section>
                        )}

                        {dashboardTab === 'dna' && (
                            <section className="learning-card">
                                <h3>🧬 Your Lyrical DNA</h3>
                                <p className="hint">See how your writing measures across 6 key dimensions.</p>
                                <DnaMatcher />
                            </section>
                        )}
                    </div>
                )}
            </main>
        </div>
    );
};

export default LearningCenter;
