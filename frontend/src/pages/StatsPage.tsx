import React, { useEffect, useState } from 'react';
import { Card } from '../components/ui/Card';
import './StatsPage.css';

interface Stats {
    total_sessions: number;
    total_lines: number;
    avg_syllables: number;
    top_rhymes: string[];
}

export const StatsPage: React.FC = () => {
    const [stats, setStats] = useState<Stats | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        loadStats();
    }, []);

    const loadStats = async () => {
        try {
            // Placeholder - would call API
            setStats({
                total_sessions: 12,
                total_lines: 248,
                avg_syllables: 11.4,
                top_rhymes: ['flow', 'go', 'know']
            });
        } catch (error) {
            console.error('Failed to load stats:', error);
        } finally {
            setIsLoading(false);
        }
    };

    if (isLoading) {
        return (
            <div className="stats-loading">
                <div className="spinner" />
                <p>Loading stats...</p>
            </div>
        );
    }

    return (
        <div className="stats-page">
            <div className="page-header">
                <h1>📊 Your Stats</h1>
                <p className="subtitle">Track your writing progress</p>
            </div>

            <div className="stats-grid">
                <Card className="stat-card" glass>
                    <div className="stat-icon">📝</div>
                    <div className="stat-value">{stats?.total_sessions || 0}</div>
                    <div className="stat-label">Sessions</div>
                </Card>

                <Card className="stat-card" glass>
                    <div className="stat-icon">🎤</div>
                    <div className="stat-value">{stats?.total_lines || 0}</div>
                    <div className="stat-label">Lines Written</div>
                </Card>

                <Card className="stat-card" glass>
                    <div className="stat-icon">🎵</div>
                    <div className="stat-value">{stats?.avg_syllables?.toFixed(1) || 0}</div>
                    <div className="stat-label">Avg Syllables</div>
                </Card>

                <Card className="stat-card" glass>
                    <div className="stat-icon">🔗</div>
                    <div className="stat-value">{stats?.top_rhymes?.length || 0}</div>
                    <div className="stat-label">Rhyme Patterns</div>
                </Card>
            </div>

            <Card className="coming-soon" glass>
                <h3>🚀 More Stats Coming Soon</h3>
                <p>Artist DNA analysis, vocabulary growth, writing streaks...</p>
            </Card>
        </div>
    );
};
