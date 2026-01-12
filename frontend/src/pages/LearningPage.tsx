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
                        <p>AABB, ABAB, and more. Learn how to structure your verses.</p>
                        <Button variant="secondary" size="sm">Coming Soon</Button>
                    </Card>
                    <Card className="tip-card" hover>
                        <h3>🎼 Rhythm & Flow</h3>
                        <p>Mastering syllable counts and stress patterns.</p>
                        <Button variant="secondary" size="sm">Coming Soon</Button>
                    </Card>
                    <Card className="tip-card" hover>
                        <h3>✍️ Metaphors</h3>
                        <p>Advanced literary devices to elevate your lyrics.</p>
                        <Button variant="secondary" size="sm">Coming Soon</Button>
                    </Card>
                </div>
            </div>
        </div>
    );
};
