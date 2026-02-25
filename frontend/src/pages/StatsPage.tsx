import React, { useEffect, useState } from 'react';
import { Card } from '../components/ui/Card';
import { vocabularyApi } from '../services/api';
import type { VocabularyAgeResponse } from '../services/api';
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
    const [vocabData, setVocabData] = useState<VocabularyAgeResponse | null>(null);
    const [vocabLoading, setVocabLoading] = useState(false);

    useEffect(() => {
        loadStats();
        loadVocabularyAge();
    }, []);

    const loadStats = async () => {
        try {
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

    const loadVocabularyAge = async () => {
        setVocabLoading(true);
        try {
            const res = await vocabularyApi.getAge();
            if (res.success) {
                setVocabData(res);
            }
        } catch (error) {
            console.error('Failed to load vocabulary age:', error);
        } finally {
            setVocabLoading(false);
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

    // Get max grade for chart scaling
    const maxGrade = vocabData?.evolution?.length
        ? Math.max(...vocabData.evolution.map(e => e.grade_level), 12)
        : 12;

    const getTrendEmoji = (trend: string) => {
        switch (trend) {
            case 'improving': return '📈';
            case 'declining': return '📉';
            default: return '➡️';
        }
    };

    const getLevelColor = (level: string) => {
        switch (level) {
            case 'Elementary': return '#4ade80';
            case 'Middle School': return '#60a5fa';
            case 'High School': return '#a78bfa';
            case 'College': return '#f472b6';
            case 'Graduate+': return '#f59e0b';
            default: return '#94a3b8';
        }
    };

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

            {/* ======= Vocabulary Age Section ======= */}
            <div className="vocab-age-section">
                <h2 className="section-title">
                    📚 Vocabulary Age
                </h2>

                {vocabLoading && (
                    <Card className="vocab-loading" glass>
                        <div className="spinner" style={{ width: '24px', height: '24px' }} />
                        <span>Analyzing vocabulary...</span>
                    </Card>
                )}

                {vocabData && vocabData.summary && (
                    <>
                        {/* Summary Cards */}
                        <div className="vocab-summary-grid">
                            <Card className="vocab-card" glass>
                                <div className="vocab-level-badge" style={{
                                    background: `${getLevelColor(vocabData.summary.current_level)}22`,
                                    color: getLevelColor(vocabData.summary.current_level),
                                    border: `1px solid ${getLevelColor(vocabData.summary.current_level)}44`
                                }}>
                                    {vocabData.summary.current_level}
                                </div>
                                <div className="vocab-grade">Grade {vocabData.summary.current_grade}</div>
                                <div className="vocab-card-label">Current Reading Level</div>
                            </Card>

                            <Card className="vocab-card" glass>
                                <div className="vocab-trend-icon">{getTrendEmoji(vocabData.summary.grade_trend)}</div>
                                <div className="vocab-grade">
                                    {vocabData.summary.grade_change > 0 ? '+' : ''}{vocabData.summary.grade_change}
                                </div>
                                <div className="vocab-card-label">Grade Trend</div>
                            </Card>

                            <Card className="vocab-card" glass>
                                <div className="vocab-trend-icon">📖</div>
                                <div className="vocab-grade">{vocabData.summary.total_unique_words}</div>
                                <div className="vocab-card-label">Unique Words</div>
                            </Card>

                            <Card className="vocab-card" glass>
                                <div className="vocab-trend-icon">📋</div>
                                <div className="vocab-grade">{vocabData.summary.sessions_analyzed}</div>
                                <div className="vocab-card-label">Sessions Analyzed</div>
                            </Card>
                        </div>

                        {/* Evolution Chart */}
                        {vocabData.evolution && vocabData.evolution.length > 0 && (
                            <Card className="vocab-chart-card" glass>
                                <h3 style={{ marginBottom: '1rem', fontSize: '0.9rem', color: 'rgba(255,255,255,0.7)' }}>
                                    Grade Level Over Time
                                </h3>
                                <div className="vocab-chart">
                                    {vocabData.evolution.map((point, i) => (
                                        <div key={i} className="vocab-chart-bar-container" title={
                                            `Session ${point.session_id}\nGrade: ${point.grade_level}\nLevel: ${point.reading_level}\nUnique words: ${point.unique_words}\nNew words: ${point.new_words_introduced}`
                                        }>
                                            <div
                                                className="vocab-chart-bar"
                                                style={{
                                                    height: `${(point.grade_level / maxGrade) * 100}%`,
                                                    background: `linear-gradient(to top, ${getLevelColor(point.reading_level)}88, ${getLevelColor(point.reading_level)})`,
                                                }}
                                            />
                                            <div className="vocab-chart-label">
                                                {point.grade_level.toFixed(1)}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                                <div className="vocab-chart-legend">
                                    {['Elementary', 'Middle School', 'High School', 'College', 'Graduate+'].map(level => (
                                        <span key={level} className="vocab-legend-item">
                                            <span className="vocab-legend-dot" style={{ background: getLevelColor(level) }} />
                                            {level}
                                        </span>
                                    ))}
                                </div>
                            </Card>
                        )}

                        {vocabData.evolution.length === 0 && (
                            <Card className="vocab-empty" glass>
                                <p>Write some lyrics first to see your vocabulary evolution!</p>
                            </Card>
                        )}
                    </>
                )}

                {!vocabLoading && !vocabData && (
                    <Card className="vocab-empty" glass>
                        <p>Could not load vocabulary data. Try refreshing.</p>
                    </Card>
                )}
            </div>
        </div>
    );
};
