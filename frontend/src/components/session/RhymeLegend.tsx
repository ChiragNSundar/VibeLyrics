import React, { useState } from 'react';
import './RhymeLegend.css';

export const RhymeLegend: React.FC = () => {
    const [isOpen, setIsOpen] = useState(false);

    return (
        <div>
            <button
                className="rhyme-legend-toggle"
                onClick={() => setIsOpen(!isOpen)}
            >
                {isOpen ? '▼' : '▶'} Rhyme Legend
            </button>

            {isOpen && (
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
            )}
        </div>
    );
};
