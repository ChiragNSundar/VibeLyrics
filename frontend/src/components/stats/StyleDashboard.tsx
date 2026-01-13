import React, { useState, useEffect } from 'react';
import {
    RadarChart,
    Radar,
    PolarGrid,
    PolarAngleAxis,
    PolarRadiusAxis,
    ResponsiveContainer,
    Legend,
    BarChart,
    Bar,
    XAxis,
    YAxis,
    Tooltip,
    CartesianGrid,
} from 'recharts';
import { Card } from '../ui/Card';
import './StyleDashboard.css';

interface StyleDimensions {
    vocabulary: number;
    rhyme_density: number;
    flow: number;
    complexity: number;
    wordplay: number;
}

interface ArtistBenchmark {
    name: string;
    vocabulary: number;
    rhyme_density: number;
    flow: number;
    complexity: number;
    wordplay: number;
}

interface StyleData {
    dimensions: StyleDimensions;
    benchmarks: ArtistBenchmark[];
    total_lines: number;
    total_words: number;
    unique_words: number;
}

/**
 * Style Analysis Dashboard
 * Shows radar chart comparing user's writing style to famous artists
 */
export const StyleDashboard: React.FC = () => {
    const [styleData, setStyleData] = useState<StyleData | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [selectedArtists, setSelectedArtists] = useState<string[]>(['You', 'Eminem', 'Kendrick']);

    useEffect(() => {
        fetchStyleData();
    }, []);

    const fetchStyleData = async () => {
        try {
            const response = await fetch('/api/stats/style');
            const data = await response.json();
            if (data.success) {
                setStyleData(data.style);
            }
        } catch (error) {
            console.error('Failed to fetch style data:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const toggleArtist = (name: string) => {
        if (name === 'You') return; // Always show user
        setSelectedArtists((prev) =>
            prev.includes(name) ? prev.filter((a) => a !== name) : [...prev, name]
        );
    };

    if (isLoading) {
        return (
            <Card className="style-dashboard loading">
                <div className="loading-spinner">Loading style analysis...</div>
            </Card>
        );
    }

    if (!styleData) {
        return (
            <Card className="style-dashboard empty">
                <p>No data available. Start writing to see your style analysis!</p>
            </Card>
        );
    }

    // Transform data for radar chart
    const radarData = [
        { dimension: 'Vocabulary', ...getArtistValues('vocabulary') },
        { dimension: 'Rhyme Density', ...getArtistValues('rhyme_density') },
        { dimension: 'Flow', ...getArtistValues('flow') },
        { dimension: 'Complexity', ...getArtistValues('complexity') },
        { dimension: 'Wordplay', ...getArtistValues('wordplay') },
    ];

    function getArtistValues(key: keyof StyleDimensions) {
        const values: Record<string, number> = {};
        styleData?.benchmarks
            .filter((b) => selectedArtists.includes(b.name))
            .forEach((b) => {
                values[b.name] = b[key];
            });
        return values;
    }

    // Bar chart data for dimensions
    const barData = Object.entries(styleData.dimensions).map(([key, value]) => ({
        name: key.replace('_', ' ').replace(/\b\w/g, (l) => l.toUpperCase()),
        value: Math.round(value),
    }));

    // Color palette matching Dreamy theme
    const artistColors: Record<string, string> = {
        You: '#8b5cf6',
        Eminem: '#06b6d4',
        Kendrick: '#10b981',
        Drake: '#f59e0b',
        'J. Cole': '#ef4444',
    };

    return (
        <div className="style-dashboard">
            <Card className="style-card radar-card" glass>
                <h3 className="card-title">Style Comparison</h3>
                <p className="card-subtitle">Compare your style to legendary artists</p>

                <div className="artist-toggles">
                    {styleData.benchmarks.map((artist) => (
                        <button
                            key={artist.name}
                            className={`artist-toggle ${selectedArtists.includes(artist.name) ? 'active' : ''}`}
                            onClick={() => toggleArtist(artist.name)}
                            style={{
                                borderColor: selectedArtists.includes(artist.name)
                                    ? artistColors[artist.name]
                                    : undefined,
                            }}
                        >
                            {artist.name}
                        </button>
                    ))}
                </div>

                <div className="radar-container">
                    <ResponsiveContainer width="100%" height={350}>
                        <RadarChart data={radarData}>
                            <PolarGrid stroke="rgba(139, 92, 246, 0.2)" />
                            <PolarAngleAxis dataKey="dimension" tick={{ fill: '#94a3b8', fontSize: 12 }} />
                            <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: '#64748b' }} />
                            {selectedArtists.map((artist) => (
                                <Radar
                                    key={artist}
                                    name={artist}
                                    dataKey={artist}
                                    stroke={artistColors[artist]}
                                    fill={artistColors[artist]}
                                    fillOpacity={artist === 'You' ? 0.4 : 0.1}
                                    strokeWidth={artist === 'You' ? 2 : 1}
                                />
                            ))}
                            <Legend />
                        </RadarChart>
                    </ResponsiveContainer>
                </div>
            </Card>

            <Card className="style-card bar-card" glass>
                <h3 className="card-title">Your Dimensions</h3>
                <p className="card-subtitle">Breakdown of your writing style</p>

                <div className="bar-container">
                    <ResponsiveContainer width="100%" height={250}>
                        <BarChart data={barData} layout="vertical">
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(139, 92, 246, 0.1)" />
                            <XAxis type="number" domain={[0, 100]} tick={{ fill: '#64748b' }} />
                            <YAxis type="category" dataKey="name" tick={{ fill: '#94a3b8' }} width={100} />
                            <Tooltip
                                contentStyle={{
                                    background: 'rgba(15, 15, 25, 0.9)',
                                    border: '1px solid rgba(139, 92, 246, 0.3)',
                                    borderRadius: '8px',
                                }}
                            />
                            <Bar dataKey="value" fill="url(#barGradient)" radius={[0, 4, 4, 0]} />
                            <defs>
                                <linearGradient id="barGradient" x1="0" y1="0" x2="1" y2="0">
                                    <stop offset="0%" stopColor="#8b5cf6" />
                                    <stop offset="100%" stopColor="#06b6d4" />
                                </linearGradient>
                            </defs>
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </Card>

            <Card className="style-card stats-card" glass>
                <h3 className="card-title">Quick Stats</h3>
                <div className="quick-stats">
                    <div className="stat-item">
                        <span className="stat-value">{styleData.total_lines}</span>
                        <span className="stat-label">Total Lines</span>
                    </div>
                    <div className="stat-item">
                        <span className="stat-value">{styleData.total_words}</span>
                        <span className="stat-label">Total Words</span>
                    </div>
                    <div className="stat-item">
                        <span className="stat-value">{styleData.unique_words}</span>
                        <span className="stat-label">Unique Words</span>
                    </div>
                    <div className="stat-item">
                        <span className="stat-value">
                            {Math.round((styleData.unique_words / styleData.total_words) * 100) || 0}%
                        </span>
                        <span className="stat-label">Vocabulary Density</span>
                    </div>
                </div>
            </Card>
        </div>
    );
};
