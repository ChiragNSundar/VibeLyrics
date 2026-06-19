import React, { useEffect, useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
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
    const [isCollapsed, setIsCollapsed] = useState(true);
    const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    const containerRef = useRef<HTMLDivElement | null>(null);

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

    // Close dropdown when clicking outside
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
                setIsCollapsed(true);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, []);

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
        <div className="complexity-meter-container" ref={containerRef}>
            {/* The circular mini gauge which is always visible and clickable */}
            <div 
                className="complexity-meter-trigger" 
                onClick={() => setIsCollapsed(!isCollapsed)}
                title="Click to toggle complexity details"
            >
                <div className="complexity-gauge mini">
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
                    </div>
                </div>
            </div>

            {/* The absolute-positioned expanded dropdown card */}
            <AnimatePresence>
                {!isCollapsed && (
                    <motion.div 
                        className="complexity-dropdown-card glass"
                        initial={{ opacity: 0, y: -8 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -8 }}
                        transition={{ duration: 0.15, ease: 'easeOut' }}
                    >
                        <button 
                            className="complexity-collapse-btn" 
                            onClick={(e) => {
                                e.stopPropagation();
                                setIsCollapsed(true);
                            }}
                            title="Collapse"
                        >
                            ✕
                        </button>
                        
                        <div className="complexity-header-info">
                            <span className="complexity-card-title">Complexity</span>
                            <span className="complexity-grade-badge" style={{ color: gaugeColor, borderColor: `${gaugeColor}30`, background: `${gaugeColor}15` }}>
                                {grade}
                            </span>
                        </div>

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
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default ComplexityMeter;
