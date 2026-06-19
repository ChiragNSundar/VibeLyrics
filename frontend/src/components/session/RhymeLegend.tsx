import React from 'react';
import './RhymeLegend.css';

export const RhymeLegend: React.FC = () => {
    return (
        <div className="rhyme-legend">
            <div className="legend-item">
                <span className="legend-swatch perfect" />
                Perfect Rhyme
            </div>
            <div className="legend-item">
                <span className="legend-swatch near" />
                Near / Slant
            </div>
            <div className="legend-item">
                <span className="legend-swatch assonance" />
                Assonance (Vowel)
            </div>
            <div className="legend-item">
                <span className="legend-swatch consonance" />
                Consonance
            </div>
            <div className="legend-item">
                <span className="legend-swatch internal" />
                Internal Rhyme
            </div>
            <div className="legend-item">
                <span className="legend-swatch multisyl" />
                Multi-syllable ✨
            </div>
            <div className="legend-item">
                <span className="legend-swatch alliteration">Aa</span>
                Alliteration
            </div>
        </div>
    );
};

