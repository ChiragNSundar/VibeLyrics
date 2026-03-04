import React, { useEffect, useState, useRef } from 'react';
import { nlpApi } from '../../services/api';
import type { SemanticDriftResponse } from '../../services/api';
import './DriftIndicator.css';

interface DriftIndicatorProps {
    sessionId: number;
    lineCount: number;
    debounceMs?: number;
}

export const DriftIndicator: React.FC<DriftIndicatorProps> = ({
    sessionId,
    lineCount,
    debounceMs = 2000,
}) => {
    const [drift, setDrift] = useState<SemanticDriftResponse | null>(null);
    const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

    useEffect(() => {
        if (timerRef.current) clearTimeout(timerRef.current);

        if (lineCount < 6) {
            setDrift(null);
            return;
        }

        timerRef.current = setTimeout(async () => {
            try {
                const res = await nlpApi.getSemanticDrift(sessionId);
                setDrift(res);
            } catch (err) {
                console.error('Drift detection failed:', err);
            }
        }, debounceMs);

        return () => {
            if (timerRef.current) clearTimeout(timerRef.current);
        };
    }, [sessionId, lineCount, debounceMs]);

    if (!drift || drift.status === 'stable') {
        if (!drift) return null;
        // Show a subtle "on track" indicator
    }

    const score = drift?.drift_score ?? 0;
    const status = drift?.status ?? 'stable';
    const warning = drift?.warning ?? '';

    const getBarColor = () => {
        if (score < 0.4) return 'linear-gradient(90deg, #34d399, #6ee7b7)';
        if (score < 0.65) return 'linear-gradient(90deg, #f59e0b, #fbbf24)';
        return 'linear-gradient(90deg, #ef4444, #f87171)';
    };

    return (
        <div className={`drift-indicator ${status}`}>
            <span className={`drift-label ${status}`}>
                {status === 'stable' ? '✓ On Track' : status === 'drifting' ? '⚠ Drifting' : '🔴 Off Topic'}
            </span>
            <div className="drift-bar-track">
                <div
                    className="drift-bar-fill"
                    style={{
                        width: `${Math.min(100, score * 100)}%`,
                        background: getBarColor(),
                    }}
                />
            </div>
            {warning && (
                <div className={`drift-warning ${status === 'off-topic' ? 'severe' : ''}`}>
                    {warning}
                </div>
            )}
        </div>
    );
};

export default DriftIndicator;
