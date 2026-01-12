import React, { useState } from 'react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { toolApi } from '../services/api';
import { toast } from 'react-hot-toast';
import './LearningPage.css';

export const LearningPage: React.FC = () => {
    const [word, setWord] = useState('');
    const [results, setResults] = useState<{
        perfect?: string[];
        near?: string[];
        synonyms?: string[];
    } | null>(null);
    const [isLoading, setIsLoading] = useState(false);

    const handleLookup = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!word.trim()) return;

        setIsLoading(true);
        try {
            // Parallel requests for rhymes and synonyms
            const [rhymes, synonyms] = await Promise.all([
                toolApi.lookup(word, 'rhyme'),
                toolApi.lookup(word, 'synonym')
            ]);

            setResults({
                perfect: rhymes.results.perfect || [],
                near: rhymes.results.near || [],
                synonyms: synonyms.results.synonyms || []
            });
        } catch (error) {
            console.error('Lookup failed:', error);
            toast.error('Failed to look up word');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="learning-page">
            <header className="page-header">
                <h1>Learning Center</h1>
                <p className="subtitle">Expand your vocabulary and master rhyme schemes</p>
            </header>

            <div className="learning-content">
                <Card className="lookup-card" glass>
                    <h2>Word Explorer</h2>
                    <form onSubmit={handleLookup} className="lookup-form">
                        <input
                            type="text"
                            value={word}
                            onChange={(e) => setWord(e.target.value)}
                            placeholder="Type a word to explore..."
                            className="input"
                        />
                        <Button type="submit" variant="primary" disabled={isLoading}>
                            {isLoading ? 'Searching...' : 'Explore'}
                        </Button>
                    </form>

                    {results && (
                        <div className="results-grid">
                            <div className="result-column">
                                <h3>Perfect Rhymes</h3>
                                <div className="tags">
                                    {results.perfect?.length ? (
                                        results.perfect.slice(0, 15).map(r => <span key={r} className="tag perfect">{r}</span>)
                                    ) : <p className="empty-text">No perfect rhymes</p>}
                                </div>
                            </div>
                            <div className="result-column">
                                <h3>Near Rhymes</h3>
                                <div className="tags">
                                    {results.near?.length ? (
                                        results.near.slice(0, 15).map(r => <span key={r} className="tag near">{r}</span>)
                                    ) : <p className="empty-text">No near rhymes</p>}
                                </div>
                            </div>
                            <div className="result-column">
                                <h3>Synonyms</h3>
                                <div className="tags">
                                    {results.synonyms?.length ? (
                                        results.synonyms.slice(0, 15).map(r => <span key={r} className="tag synonym">{r}</span>)
                                    ) : <p className="empty-text">No synonyms</p>}
                                </div>
                            </div>
                        </div>
                    )}
                </Card>

                <div className="tips-grid">
                    <Card className="tip-card" hover>
                        <h3>📚 Rhyme Schemes</h3>
                        <p className="tip-desc">The blueprint of your verse.</p>
                        <div className="scheme-examples">
                            <div className="scheme-item">
                                <span className="scheme-label">AABB</span>
                                <span className="scheme-expl">Couplets. Simple, punchy.</span>
                            </div>
                            <div className="scheme-item">
                                <span className="scheme-label">ABAB</span>
                                <span className="scheme-expl">Cross rhyme. Storytelling flow.</span>
                            </div>
                            <div className="scheme-item">
                                <span className="scheme-label">AAAA</span>
                                <span className="scheme-expl">Monorhyme. Intense buildup.</span>
                            </div>
                        </div>
                    </Card>

                    <Card className="tip-card" hover>
                        <h3>🎼 Rhythm & Flow</h3>
                        <div className="flow-content">
                            <p><strong>Stressed (/) vs Unstressed (x)</strong></p>
                            <p className="example-text">
                                "To <strong className="stress">be</strong> or <strong className="stress">not</strong> to <strong className="stress">be</strong>"
                                <br />
                                <span className="pattern">x / x / x /</span>
                            </p>
                            <p className="tip-sub">Match your beat's kick/snare pattern for maximum impact.</p>
                        </div>
                    </Card>

                    <Card className="tip-card" hover>
                        <h3>✍️ Metaphors & Similes</h3>
                        <div className="device-content">
                            <div className="device-item">
                                <strong>Simile (like/as)</strong>
                                <p>"Cold as ice"</p>
                            </div>
                            <div className="device-item">
                                <strong>Metaphor (is)</strong>
                                <p>"My heart is a ghost town"</p>
                            </div>
                            <div className="device-item">
                                <strong>Double Entendre</strong>
                                <p>Two meanings, one line.</p>
                            </div>
                        </div>
                    </Card>

                    <Card className="tip-card" hover>
                        <h3>🏗️ Song Structure</h3>
                        <div className="structure-content">
                            <div className="struct-item">
                                <strong>Verse</strong>
                                <p>Sets the scene, tells the story. Lower energy.</p>
                            </div>
                            <div className="struct-item">
                                <strong>Chorus (Hook)</strong>
                                <p>The main message. Catchy, repetitive, high energy.</p>
                            </div>
                            <div className="struct-item">
                                <strong>Bridge</strong>
                                <p>The twist or peak emotion. Connects last chorus.</p>
                            </div>
                        </div>
                    </Card>

                    <Card className="tip-card" hover>
                        <h3>📖 Storytelling</h3>
                        <div className="story-content">
                            <p className="rule"><strong>"Show, Don't Tell"</strong></p>
                            <div className="comparison">
                                <div className="bad">
                                    <span>❌ Tell:</span> "I was sad."
                                </div>
                                <div className="good">
                                    <span>✅ Show:</span> "Staring at the ceiling, waiting for the rain to stop."
                                </div>
                            </div>
                            <p className="tip-sub">Use sensory details: minor chords, cold coffee, visuals.</p>
                        </div>
                    </Card>

                    <Card className="tip-card" hover>
                        <h3>🎤 Performance & Delivery</h3>
                        <div className="perf-content">
                            <ul className="perf-list">
                                <li><strong>Cadence:</strong> Switch up your speeds (fast triplets vs slow drag).</li>
                                <li><strong>Breath Control:</strong> Write pauses into your bars.</li>
                                <li><strong>Inflection:</strong> Pitch up for questions, down for statements.</li>
                            </ul>
                        </div>
                    </Card>
                </div>
            </div>
        </div>
    );
};
