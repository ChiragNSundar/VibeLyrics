import React, { useEffect, useState } from 'react';
import {
    Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
    ResponsiveContainer, Tooltip
} from 'recharts';
import { learningApi } from '../../services/api';
import './DnaMatcher.css';

interface DnaAxis {
    axis: string;
    value: number;
}

const DnaMatcher: React.FC = () => {
    const [axes, setAxes] = useState<DnaAxis[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const load = async () => {
            try {
                const res = await learningApi.getDna();
                setAxes(res.axes);
            } catch (err) {
                console.error('Failed to load DNA:', err);
            } finally {
                setLoading(false);
            }
        };
        load();
    }, []);

    if (loading) {
        return <div className="dna-loading">Analyzing lyrical DNA...</div>;
    }

    if (axes.length === 0) {
        return <div className="dna-empty">Not enough data to compute DNA. Scrape some lyrics first.</div>;
    }

    return (
        <div className="dna-container">
            <ResponsiveContainer width="100%" height={350}>
                <RadarChart cx="50%" cy="50%" outerRadius="75%" data={axes}>
                    <PolarGrid stroke="rgba(148, 163, 184, 0.15)" />
                    <PolarAngleAxis
                        dataKey="axis"
                        tick={{ fill: '#94a3b8', fontSize: 11 }}
                    />
                    <PolarRadiusAxis
                        angle={30}
                        domain={[0, 100]}
                        tick={{ fill: '#475569', fontSize: 10 }}
                        axisLine={false}
                    />
                    <Radar
                        name="Your DNA"
                        dataKey="value"
                        stroke="#a78bfa"
                        fill="#a78bfa"
                        fillOpacity={0.25}
                        strokeWidth={2}
                    />
                    <Tooltip
                        contentStyle={{
                            background: '#1e293b',
                            border: '1px solid #475569',
                            borderRadius: '8px',
                            color: '#e2e8f0',
                            fontSize: '0.85rem',
                        }}
                        formatter={(value?: number) => [`${value ?? 0}/100`, 'Score']}
                    />
                </RadarChart>
            </ResponsiveContainer>

            <div className="dna-scores">
                {axes.map((a, i) => (
                    <div key={i} className="dna-score-row">
                        <span className="dna-axis-name">{a.axis}</span>
                        <div className="dna-bar-bg">
                            <div
                                className="dna-bar-fill"
                                style={{ width: `${a.value}%` }}
                            />
                        </div>
                        <span className="dna-value">{a.value}</span>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default DnaMatcher;
