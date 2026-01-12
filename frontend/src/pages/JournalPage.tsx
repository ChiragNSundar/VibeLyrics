import React, { useState, useEffect } from 'react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { request } from '../services/api';
import './JournalPage.css';

interface JournalEntry {
    id: number;
    content: string;
    mood: string;
    created_at: string;
}

export const JournalPage: React.FC = () => {
    const [entries, setEntries] = useState<JournalEntry[]>([]);
    const [content, setContent] = useState('');
    const [isLoading, setIsLoading] = useState(false);

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

    return (
        <div className="journal-page">
            <div className="page-header">
                <h1>📓 Journal</h1>
                <p className="subtitle">Write freely, capture ideas, process emotions</p>
            </div>

            <div className="journal-container">
                <div className="journal-sidebar">
                    <Card className="journal-tips" glass>
                        <h3>💡 Vibe Tips</h3>
                        <ul>
                            <li>Free-write without judgment</li>
                            <li>Capture conversations</li>
                            <li>Vent your raw emotions</li>
                            <li><strong>Vibe AI reads this</strong> to understand your style!</li>
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
                </div>
            </div>
        </div>
    );
};
