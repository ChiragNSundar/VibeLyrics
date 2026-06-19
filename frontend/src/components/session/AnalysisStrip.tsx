import React, { useMemo, useState, useEffect } from 'react';
import { learningApi } from '../../services/api';
import './AnalysisStrip.css';

interface AnalysisStripProps {
    text: string;
    rhymeScheme?: string;
}

interface BackendAnalysis {
    cliches: Array<{
        phrase: string;
        category: string;
        alternatives: string[];
        severity: string;
        reason: string;
    }>;
    imagery: {
        total_imagery_words: number;
        by_category: Record<string, number>;
        dominant_sense: string | null;
    };
    wordplay: Array<{
        category: string;
        trigger: string;
        text: string;
        explanation: string;
    }>;
}

export const AnalysisStrip: React.FC<AnalysisStripProps> = ({ text, rhymeScheme }) => {
    const [backendAnalysis, setBackendAnalysis] = useState<BackendAnalysis | null>(null);
    const [activeClicheIndex, setActiveClicheIndex] = useState<number | null>(null);

    // Client-side quick analysis
    const analysis = useMemo(() => {
        if (!text.trim()) return null;

        const words = text.toLowerCase().split(/\s+/).filter(w => w);
        const syllables = words.reduce((acc, word) => {
            const vowels = word.match(/[aeiouy]+/g);
            return acc + (vowels ? vowels.length : 1);
        }, 0);

        const figures: string[] = [];

        // Alliteration (3+ words with same start)
        if (words.length >= 3) {
            const starts = words.map(w => w[0]);
            for (let i = 0; i < starts.length - 2; i++) {
                if (starts[i] === starts[i + 1] && starts[i] === starts[i + 2]) {
                    figures.push('Alliteration');
                    break;
                }
            }
        }

        // Simile
        if (words.includes('like') || words.includes('as')) {
            figures.push('Simile');
        }

        return { syllables, figures };
    }, [text]);

    // Backend real-time analysis with 300ms debounce
    useEffect(() => {
        const trimmed = text.trim();
        if (!trimmed) {
            setBackendAnalysis(null);
            return;
        }

        const handler = setTimeout(async () => {
            try {
                const res = await learningApi.analyzeLine(trimmed);
                if (res.success) {
                    setBackendAnalysis(res);
                }
            } catch (err) {
                console.warn('Real-time analysis lookup failed', err);
            }
        }, 300);

        return () => clearTimeout(handler);
    }, [text]);

    if (!analysis) return null;

    // Helper for sensory icons
    const getSensoryIcon = (sense: string): string => {
        switch (sense.toLowerCase()) {
            case 'visual': return '👁️';
            case 'auditory': return '👂';
            case 'tactile': return '🔥';
            case 'olfactory': return '👃';
            case 'gustatory': return '👅';
            default: return '✨';
        }
    };

    return (
        <div className="analysis-strip">
            {/* Syllables */}
            <div className="analysis-pill">
                <span className="analysis-label">Syllables</span>
                <span className="analysis-value">{analysis.syllables}</span>
            </div>

            {/* Rhyme Scheme or Flow */}
            {rhymeScheme ? (
                <div className="analysis-pill">
                    <span className="analysis-label">Scheme</span>
                    <span className="analysis-value">{rhymeScheme}</span>
                </div>
            ) : (
                <div className="analysis-pill">
                    <span className="analysis-label">Flow</span>
                    <span className="analysis-value">
                        {analysis.syllables % 2 === 0 ? 'Even' : 'Odd'}
                    </span>
                </div>
            )}

            {/* Figures of speech (Client-side) */}
            {analysis.figures.map(fig => (
                <div key={fig} className="analysis-pill figure">
                    <span className="analysis-icon">✨</span>
                    <span className="analysis-value">{fig}</span>
                </div>
            ))}

            {/* Backend Imagery/Sensory Indicators */}
            {backendAnalysis?.imagery && backendAnalysis.imagery.total_imagery_words > 0 && (
                Object.entries(backendAnalysis.imagery.by_category)
                    .filter(([_, count]) => count > 0)
                    .map(([sense, _]) => (
                        <div key={sense} className="analysis-pill sense-indicator" title={`${sense} imagery detected`}>
                            <span className="analysis-icon">{getSensoryIcon(sense)}</span>
                            <span className="analysis-value">{sense}</span>
                        </div>
                    ))
            )}

            {/* Backend Wordplay Sparks */}
            {backendAnalysis?.wordplay && backendAnalysis.wordplay.map((wp, idx) => (
                <div key={idx} className="analysis-pill wordplay-spark" title={wp.explanation}>
                    <span className="analysis-icon">💡</span>
                    <span className="analysis-value">{wp.category}: "{wp.text}"</span>
                </div>
            ))}

            {/* Backend Clichés with Popover Suggestions */}
            {backendAnalysis?.cliches && backendAnalysis.cliches.map((cliche, idx) => (
                <div
                    key={idx}
                    className="analysis-pill cliche-warning interactive"
                    onClick={() => setActiveClicheIndex(activeClicheIndex === idx ? null : idx)}
                    onMouseEnter={() => setActiveClicheIndex(idx)}
                    onMouseLeave={() => setActiveClicheIndex(null)}
                >
                    <span className="analysis-icon">⚠️</span>
                    <span className="analysis-value">Cliché: "{cliche.phrase}"</span>
                    
                    {activeClicheIndex === idx && (
                        <div className="cliche-popover glass">
                            <div className="popover-header">
                                <strong>Category:</strong> {cliche.category}
                            </div>
                            <div className="popover-body">
                                <p className="popover-desc">Avoid overused terms. Try these poetic alternatives:</p>
                                <ul className="popover-alternatives">
                                    {cliche.alternatives.map((alt, aIdx) => (
                                        <li key={aIdx} className="alternative-item">
                                            "{alt}"
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        </div>
                    )}
                </div>
            ))}
        </div>
    );
};

