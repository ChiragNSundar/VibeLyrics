import React, { useState, useEffect } from 'react';
import { learningApi } from '../services/api';
import type { LearningStatusResponse } from '../services/api';
import './LearningCenter.css';

const LearningCenter: React.FC = () => {
    const [status, setStatus] = useState<LearningStatusResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [artistInput, setArtistInput] = useState('');
    const [scraping, setScraping] = useState(false);
    const [message, setMessage] = useState('');

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

    const handleScrape = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!artistInput.trim()) return;

        try {
            setScraping(true);
            setMessage('');
            const res = await learningApi.scrapeArtist(artistInput.trim(), 3);
            setMessage(res.message);
            setArtistInput('');

            // Re-fetch status after a delay to show new learned data
            setTimeout(fetchStatus, 5000);
        } catch (error: any) {
            console.error('Failed to scrape artist:', error);
            setMessage(error.message || 'Scraping failed');
        } finally {
            setScraping(false);
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
            </header>

            <main className="learning-content">
                {/* ── Scraper Section ── */}
                <section className="learning-card scrape-section">
                    <h2>Feed the AI</h2>
                    <p>Enter an artist name to scrape their latest lyrics and teach Vibe their style.</p>

                    <form onSubmit={handleScrape} className="scrape-form">
                        <div className="input-group">
                            <input
                                type="text"
                                value={artistInput}
                                onChange={(e) => setArtistInput(e.target.value)}
                                placeholder="e.g. Kendrick Lamar, Taylor Swift..."
                                disabled={scraping}
                                className="search-input"
                            />
                            <button
                                type="submit"
                                className="btn primary scrape-btn"
                                disabled={scraping || !artistInput.trim()}
                            >
                                {scraping ? (
                                    <>
                                        <span className="spinner-small"></span>
                                        Learning...
                                    </>
                                ) : (
                                    'Start Learning'
                                )}
                            </button>
                        </div>
                    </form>

                    {message && (
                        <div className={`status-message ${message.includes('failed') ? 'error' : 'success'}`}>
                            {message}
                        </div>
                    )}
                </section>

                {/* ── Knowledge Base Dashboard ── */}
                {status && (
                    <div className="knowledge-dashboard">
                        <section className="learning-card">
                            <h3>Learned Style</h3>
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
                            <h3>Vocabulary Profile</h3>

                            <div className="tag-section">
                                <h4>Signature Words (Most Used)</h4>
                                <div className="tag-list">
                                    {status.vocabulary.most_used.length > 0 ? (
                                        status.vocabulary.most_used.map((word, i) => (
                                            <span key={i} className="tag word-tag">{word}</span>
                                        ))
                                    ) : (
                                        <span className="no-data">No words tracking yet.</span>
                                    )}
                                </div>
                            </div>

                            <div className="vocab-split">
                                <div className="tag-section">
                                    <h4>Favorite Slangs</h4>
                                    <div className="tag-list">
                                        {status.vocabulary.slangs.length > 0 ? (
                                            status.vocabulary.slangs.map((word, i) => (
                                                <span key={i} className="tag slang-tag">{word}</span>
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
                                                <span key={i} className="tag avoid-tag">{word}</span>
                                            ))
                                        ) : (
                                            <span className="no-data">None specified</span>
                                        )}
                                    </div>
                                </div>
                            </div>
                        </section>
                    </div>
                )}
            </main>
        </div>
    );
};

export default LearningCenter;
