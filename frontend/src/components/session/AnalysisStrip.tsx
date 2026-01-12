import React, { useMemo } from 'react';
import './AnalysisStrip.css';

interface AnalysisStripProps {
    text: string;
    rhymeScheme?: string;
}

export const AnalysisStrip: React.FC<AnalysisStripProps> = ({ text, rhymeScheme }) => {
    const analysis = useMemo(() => {
        if (!text.trim()) return null;

        const words = text.toLowerCase().split(/\s+/).filter(w => w);
        const syllables = words.reduce((acc, word) => {
            const vowels = word.match(/[aeiouy]+/g);
            return acc + (vowels ? vowels.length : 1);
        }, 0);

        // Simple figure of speech detection (client-side approximation)
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

    if (!analysis) return null;

    return (
        <div className="analysis-strip">
            <div className="analysis-pill">
                <span className="analysis-label">Syllables</span>
                <span className="analysis-value">{analysis.syllables}</span>
            </div>

            {rhymeScheme && (
                <div className="analysis-pill">
                    <span className="analysis-label">Scheme</span>
                    <span className="analysis-value">{rhymeScheme}</span>
                </div>
            )}

            {!rhymeScheme && (
                <div className="analysis-pill">
                    <span className="analysis-label">Flow</span>
                    <span className="analysis-value">
                        {analysis.syllables % 2 === 0 ? 'Even' : 'Odd'}
                    </span>
                </div>
            )}

            {analysis.figures.map(fig => (
                <div key={fig} className="analysis-pill figure">
                    <span className="analysis-icon">✨</span>
                    <span className="analysis-value">{fig}</span>
                </div>
            ))}
        </div>
    );
};
