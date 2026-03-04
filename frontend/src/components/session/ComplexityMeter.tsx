import React, { useEffect, useState, useRef } from 'react';
import { nlpApi } from '../../services/api';
import type { ComplexityScoreResponse } from '../../services/api';
import './ComplexityMeter.css';

interface ComplexityMeterProps {
    lines: string[];
    debounceMs?: number;
}

export const ComplexityMeter: React.FC<ComplexityMeterProps> = ({
    lines,
    debounceMs = 1500,
}) => {
    const [data, setData] = useState<ComplexityScoreResponse | null>(null);
    const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

    useEffect(() => {
        if (timerRef.current) clearTimeout(timerRef.current);

        const validLines = lines.filter((l) => l.trim());
        if (validLines.length < 2) {
            setData(null);
            return;
        }

        timerRef.current = setTimeout(async () => {
            try {
                const res = await nlpApi.getComplexityScore(validLines);
                setData(res);
            } catch (err) {
                console.error('Complexity score failed:', err);
            }
        }, debounceMs);

        return () => {
            if (timerRef.current) clearTimeout(timerRef.current);
        };
    }, [lines, debounceMs]);

    const score = data?.score ?? 0;
    const grade = data?.grade ?? '—';
    const dims = data?.dimensions;

    // SVG circle params
    const radius = 38;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (score / 100) * circumference;

    // Color based on score
    const getColor = (s: number) => {
        if (s >= 75) return '#34d399'; // emerald
        if (s >= 50) return '#f59e0b'; // amber
        if (s >= 25) return '#f97316'; // orange
        return '#ef4444'; // red
    };
    const gaugeColor = getColor(score);

    return (
        <div className="complexity-meter">
            <div className="complexity-gauge">
                <svg viewBox="0 0 90 90">
                    <circle className="gauge-bg" cx="45" cy="45" r={radius} />
                    <circle
                        className="gauge-fill"
                        cx="45"
                        cy="45"
                        r={radius}
                        stroke={gaugeColor}
                        strokeDasharray={circumference}
                        strokeDashoffset={offset}
                        style={{ '--gauge-color': gaugeColor } as React.CSSProperties}
                    />
                </svg>
                <div className="complexity-score-label">
                    <span className="complexity-score-number">{score}</span>
                    <span className="complexity-score-max">/100</span>
                </div>
            </div>

            <span className="complexity-grade-badge" style={{ color: gaugeColor }}>
                {grade}
            </span>

            {dims && (
                <div className="complexity-dimensions">
                    <div className="complexity-dim">
                        <span className="dim-label">Rhyme</span>
                        <span className="dim-value">{dims.internal_rhyme}</span>
                    </div>
                    <div className="complexity-dim">
                        <span className="dim-label">Multi</span>
                        <span className="dim-value">{dims.multisyllabic}</span>
                    </div>
                    <div className="complexity-dim">
                        <span className="dim-label">Asson</span>
                        <span className="dim-value">{dims.assonance}</span>
                    </div>
                    <div className="complexity-dim">
                        <span className="dim-label">Vocab</span>
                        <span className="dim-value">{dims.vocabulary}</span>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ComplexityMeter;
