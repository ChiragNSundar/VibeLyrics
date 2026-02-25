import React, { useState, useEffect } from 'react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { request, journalApi } from '../services/api';
import './JournalPage.css';

interface JournalEntry {
    id: number;
    content: string;
    mood: string;
    created_at: string;
}

interface SearchResult {
    entry_id: number;
    content: string;
    similarity: number;
    match_type: string;
    mood?: string;
    created_at?: string;
    matched_words?: string[];
}

export const JournalPage: React.FC = () => {
    const [entries, setEntries] = useState<JournalEntry[]>([]);
    const [content, setContent] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const [searchMode, setSearchMode] = useState<'auto' | 'semantic' | 'keyword'>('auto');
    const [searchResults, setSearchResults] = useState<SearchResult[] | null>(null);
    const [isSearching, setIsSearching] = useState(false);

    useEffect(() => {
        loadEntries();
    }, []);

    const loadEntries = async () => {
        try {
            const res = await request<{ entries: JournalEntry[] }>('/api/journal?limit=20');
            setEntries(res.entries);
        } catch (err) {
            console.error('Failed to load journal', err);
        }
    };

    const handleSubmit = async () => {
        if (!content.trim()) return;
        setIsLoading(true);
        try {
            const res = await request<{ entry: JournalEntry }>('/api/journal', {
                method: 'POST',
                body: JSON.stringify({ content, mood: 'Neutral' })
            });
            setEntries([res.entry, ...entries]);
            setContent('');
        } catch (err) {
            console.error('Failed to save entry', err);
        } finally {
            setIsLoading(false);
        }
    };

    const handleSearch = async () => {
        if (!searchQuery.trim()) {
            setSearchResults(null);
            return;
        }
        setIsSearching(true);
        try {
            const res = await journalApi.search(searchQuery, searchMode, 10);
            if (res.success) {
                setSearchResults(res.results);
            }
        } catch (err) {
            console.error('Search failed', err);
        } finally {
            setIsSearching(false);
        }
    };

    const clearSearch = () => {
        setSearchQuery('');
        setSearchResults(null);
    };

    return (
        <div className="journal-page">
            <div className="page-header">
                <h1>📓 Journal</h1>
                <p className="subtitle">Write freely, capture ideas, process emotions</p>
            </div>

            {/* Semantic Search Bar */}
            <div className="journal-search-bar glass" style={{
                margin: '0 auto 1.5rem',
                maxWidth: '800px',
                padding: '0.75rem 1rem',
                borderRadius: '14px',
                display: 'flex',
                gap: '0.5rem',
                alignItems: 'center'
            }}>
                <input
                    type="text"
                    placeholder="Search your journal by meaning..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                    style={{
                        flex: 1,
                        background: 'rgba(255,255,255,0.06)',
                        border: '1px solid rgba(255,255,255,0.1)',
                        borderRadius: '10px',
                        padding: '0.5rem 0.75rem',
                        color: '#fff',
                        fontSize: '0.85rem',
                        outline: 'none'
                    }}
                />
                <select
                    value={searchMode}
                    onChange={(e) => setSearchMode(e.target.value as 'auto' | 'semantic' | 'keyword')}
                    style={{
                        background: 'rgba(255,255,255,0.06)',
                        border: '1px solid rgba(255,255,255,0.1)',
                        borderRadius: '10px',
                        padding: '0.5rem',
                        color: '#fff',
                        fontSize: '0.75rem',
                        cursor: 'pointer'
                    }}
                >
                    <option value="auto">Auto</option>
                    <option value="semantic">🧠 Semantic</option>
                    <option value="keyword">🔤 Keyword</option>
                </select>
                <Button variant="primary" size="sm" onClick={handleSearch} disabled={isSearching}>
                    {isSearching ? '...' : '🔍 Search'}
                </Button>
                {searchResults && (
                    <Button variant="secondary" size="sm" onClick={clearSearch}>✕</Button>
                )}
            </div>

            {/* Search Results */}
            {searchResults && (
                <div style={{ maxWidth: '800px', margin: '0 auto 1.5rem' }}>
                    <div style={{ fontSize: '0.8rem', color: 'rgba(255,255,255,0.4)', marginBottom: '0.5rem' }}>
                        {searchResults.length} result(s) for "{searchQuery}"
                    </div>
                    {searchResults.map((result, i) => (
                        <Card key={i} className="journal-entry" style={{ marginBottom: '0.5rem' }}>
                            <p className="entry-content">{result.content}</p>
                            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', marginTop: '0.5rem' }}>
                                <span style={{
                                    fontSize: '0.65rem',
                                    padding: '2px 8px',
                                    borderRadius: '10px',
                                    background: result.match_type === 'semantic' ? 'rgba(138,43,226,0.2)' : 'rgba(0,200,255,0.15)',
                                    color: result.match_type === 'semantic' ? '#c084fc' : '#67e8f9'
                                }}>
                                    {result.match_type === 'semantic' ? '🧠 Semantic' : '🔤 Keyword'}
                                </span>
                                <span style={{ fontSize: '0.65rem', color: 'rgba(255,255,255,0.3)' }}>
                                    {Math.round(result.similarity * 100)}% match
                                </span>
                                {result.created_at && (
                                    <span className="entry-meta">
                                        {new Date(result.created_at).toLocaleDateString()}
                                    </span>
                                )}
                            </div>
                        </Card>
                    ))}
                </div>
            )}

            <div className="journal-container">
                <div className="journal-sidebar">
                    <Card className="journal-tips" glass>
                        <h3>💡 Vibe Tips</h3>
                        <ul>
                            <li>Free-write without judgment</li>
                            <li>Capture conversations</li>
                            <li>Vent your raw emotions</li>
                            <li><strong>Vibe AI reads this</strong> to understand your style!</li>
                            <li>Use <strong>Semantic Search</strong> to find entries by meaning, not just words</li>
                        </ul>
                    </Card>
                </div>

                <div className="journal-main">
                    <Card className="composer-card" glass>
                        <textarea
                            className="journal-textarea"
                            placeholder="What's on your mind? (This helps AI learn your style)"
                            value={content}
                            onChange={(e) => setContent(e.target.value)}
                        />
                        <div className="composer-actions">
                            <Button variant="primary" onClick={handleSubmit} disabled={isLoading || !content.trim()}>
                                {isLoading ? 'Saving...' : 'Post Entry'}
                            </Button>
                        </div>
                    </Card>

                    {!searchResults && (
                        <div className="journal-feed">
                            {entries.map(entry => (
                                <Card key={entry.id} className="journal-entry">
                                    <p className="entry-content">{entry.content}</p>
                                    <span className="entry-meta">
                                        {new Date(entry.created_at).toLocaleString()}
                                    </span>
                                </Card>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
