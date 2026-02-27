import React, { useEffect, useState } from 'react';
import { Card } from '../components/ui/Card';
import { vocabularyApi, statsApi } from '../services/api';
import type { VocabularyAgeResponse } from '../services/api';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { Flame, Calendar as CalendarIcon, Activity } from 'lucide-react';
import './StatsPage.css';

interface Stats {
    total_sessions: number;
    total_lines: number;
    avg_syllables: number;
    top_rhymes: string[];
}

export const StatsPage: React.FC = () => {
    // Basic stats
    const [stats, setStats] = useState<Stats | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    // Vocabulary Analytics
    const [vocabData, setVocabData] = useState<VocabularyAgeResponse | null>(null);
    const [vocabLoading, setVocabLoading] = useState(false);

    // Group C Analytics
    const [streakData, setStreakData] = useState<any>(null);
    const [growthData, setGrowthData] = useState<any[]>([]);
    const [calendarData, setCalendarData] = useState<any[]>([]);

    useEffect(() => {
        loadStats();
        loadVocabularyAge();
        loadGroupCStats();
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

    const loadGroupCStats = async () => {
        try {
            const [streakRes, growthRes, calendarRes] = await Promise.all([
                statsApi.getStreak().catch(() => ({ success: false })),
                statsApi.getVocabularyGrowth().catch(() => ({ success: false })),
                statsApi.getRhymeCalendar().catch(() => ({ success: false }))
            ]) as [any, any, any];

            if (streakRes.success) setStreakData(streakRes);
            if (growthRes.success) setGrowthData(growthRes.growth);
            if (calendarRes.success) setCalendarData(calendarRes.calendar);
        } catch (error) {
            console.warn('Failed to load advanced analytics');
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

    // Calendar Heatmap Helpers
    const getDaysInMonth = () => {
        const today = new Date();
        const year = today.getFullYear();
        const month = today.getMonth();
        const days = new Date(year, month + 1, 0).getDate();

        return Array.from({ length: days }, (_, i) => {
            const d = new Date(year, month, i + 1);
            return d.toISOString().split('T')[0];
        });
    };

    const getSchemeColor = (scheme: string) => {
        const map: Record<string, string> = {
            'AABB': '#3b82f6', // blue
            'ABAB': '#8b5cf6', // purple
            'AAAA': '#ef4444', // red
            'ABBA': '#10b981', // green
            'AABBCC': '#f59e0b' // yellow
        };
        return map[scheme] || 'var(--bg-hover)'; // default gray
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

            {/* ======= Group C: Analytics & Gamification ======= */}
            <div className="gamification-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem', marginBottom: '3rem' }}>

                {/* Writing Streak Tracker */}
                <Card className="streak-card" glass style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '2rem' }}>
                    <h3 style={{ margin: '0 0 1rem 0', display: 'flex', alignItems: 'center', gap: '0.5rem' }}><Flame size={20} className="text-accent" /> Writing Streak</h3>
                    <div style={{ fontSize: '4rem', fontWeight: 800, color: 'var(--accent-color)', lineHeight: 1, textShadow: '0 0 20px rgba(239, 68, 68, 0.4)' }}>
                        {streakData?.current_streak || 0}
                    </div>
                    <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginTop: '0.5rem' }}>Days in a row</div>
                    {streakData?.longest_streak && (
                        <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '1rem', background: 'var(--bg-elevated)', padding: '0.2rem 0.6rem', borderRadius: '20px' }}>
                            Longest: {streakData.longest_streak} days
                        </div>
                    )}
                </Card>

                {/* Vocabulary Growth Chart */}
                <Card className="growth-card" glass style={{ gridColumn: 'span 2' }}>
                    <h3 style={{ margin: '0 0 1rem 0', display: 'flex', alignItems: 'center', gap: '0.5rem' }}><Activity size={20} className="text-primary" /> Vocabulary Growth</h3>
                    {growthData.length > 0 ? (
                        <div style={{ height: '200px', width: '100%' }}>
                            <ResponsiveContainer width="100%" height="100%">
                                <AreaChart data={growthData}>
                                    <defs>
                                        <linearGradient id="colorVocab" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="var(--primary-color)" stopOpacity={0.8} />
                                            <stop offset="95%" stopColor="var(--primary-color)" stopOpacity={0} />
                                        </linearGradient>
                                    </defs>
                                    <XAxis dataKey="date" stroke="var(--text-muted)" fontSize={12} tickFormatter={(str) => str.substring(5)} />
                                    <YAxis stroke="var(--text-muted)" fontSize={12} />
                                    <Tooltip contentStyle={{ background: 'var(--bg-panel)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)' }} />
                                    <Area type="monotone" dataKey="unique_words" stroke="var(--primary-color)" fillOpacity={1} fill="url(#colorVocab)" />
                                </AreaChart>
                            </ResponsiveContainer>
                        </div>
                    ) : (
                        <div style={{ height: '200px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>Write songs to grow your vocabulary graph!</div>
                    )}
                </Card>

                {/* Rhyme Scheme Heatmap */}
                <Card className="heatmap-card" glass style={{ gridColumn: '1 / -1' }}>
                    <h3 style={{ margin: '0 0 1rem 0', display: 'flex', alignItems: 'center', gap: '0.5rem' }}><CalendarIcon size={20} /> Rhyme Scheme Heatmap</h3>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(30px, 1fr))', gap: '4px', maxWidth: '800px', margin: '0 auto' }}>
                        {getDaysInMonth().map((dateStr, i) => {
                            const dayData = calendarData.find(d => d.date === dateStr);
                            const scheme = dayData ? dayData.scheme : null;
                            const bgColor = scheme ? getSchemeColor(scheme) : 'var(--bg-hover)';

                            return (
                                <div
                                    key={i}
                                    title={`${dateStr}${scheme ? ` - ${scheme}` : ' - No sessions'}`}
                                    style={{
                                        aspectRatio: '1',
                                        background: bgColor,
                                        borderRadius: '3px',
                                        cursor: 'pointer',
                                        opacity: scheme ? 1 : 0.3
                                    }}
                                />
                            );
                        })}
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '1rem', marginTop: '1rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}><div style={{ width: 10, height: 10, background: '#3b82f6', borderRadius: 2 }} /> AABB</span>
                        <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}><div style={{ width: 10, height: 10, background: '#8b5cf6', borderRadius: 2 }} /> ABAB</span>
                        <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}><div style={{ width: 10, height: 10, background: '#10b981', borderRadius: 2 }} /> ABBA</span>
                    </div>
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
