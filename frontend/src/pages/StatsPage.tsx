import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card } from '../components/ui/Card';
import { statsApi, type StatsOverview } from '../services/api';
import './StatsPage.css';

export const StatsPage: React.FC = () => {
    const [stats, setStats] = useState<StatsOverview | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        loadStats();
    }, []);

    const loadStats = async () => {
        setIsLoading(true);
        try {
            const response = await statsApi.getOverview();
            if (response.success) {
                setStats(response.stats);
            }
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

    // Empty state if no sessions
    if (!stats || stats.total_sessions === 0) {
        return (
            <div className="stats-page empty-stats">
                <div className="page-header">
                    <h1>📊 Your Stats</h1>
                    <p className="subtitle">Track your writing progress</p>
                </div>

                <Card className="empty-state-card" glass>
                    <div className="empty-icon">📈</div>
                    <h3>No Stats Yet</h3>
                    <p>Start writing lyrics to see your progress, vocabulary growth, and rhyme density analysis.</p>
                    <button
                        className="btn-primary"
                        onClick={() => navigate('/')}
                    >
                        Start Your First Session
                    </button>
                </Card>
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
                    <div className="stat-value">{stats.total_sessions}</div>
                    <div className="stat-label">Sessions</div>
                </Card>

                <Card className="stat-card" glass>
                    <div className="stat-icon">🎤</div>
                    <div className="stat-value">{stats.total_lines}</div>
                    <div className="stat-label">Lines Written</div>
                </Card>

                <Card className="stat-card" glass>
                    <div className="stat-icon">🎵</div>
                    <div className="stat-value">{stats.avg_syllables.toFixed(1)}</div>
                    <div className="stat-label">Avg Syllables</div>
                </Card>

                <Card className="stat-card" glass>
                    <div className="stat-icon">🔗</div>
                    <div className="stat-value">{stats.top_rhymes.length}</div>
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
