import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { toolApi } from '../../services/api';
import type { DoppelreimResult } from '../../services/api';
import { toast } from 'react-hot-toast';
import './DoppelreimPanel.css';

interface DoppelreimPanelProps {
    sessionId: number;
    initialWord?: string;
    onInsert?: (text: string) => void;
}

export const DoppelreimPanel: React.FC<DoppelreimPanelProps> = ({
    sessionId,
    initialWord = '',
    onInsert,
}) => {
    const [searchTerm, setSearchTerm] = useState(initialWord);
    const [language, setLanguage] = useState<'en' | 'hi' | 'kn'>('en');
    const [mode, setMode] = useState<'classic' | 'vowel' | 'multi' | 'inspiration'>('vowel');
    const [allowSlang, setAllowSlang] = useState(true);
    const [results, setResults] = useState<DoppelreimResult[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [votedItems, setVotedItems] = useState<Record<string, 'up' | 'down'>>({});

    const handleSearch = useCallback(async () => {
        const cleanTerm = searchTerm.trim();
        if (!cleanTerm) return;

        setLoading(true);
        setError(null);
        try {
            const res = await toolApi.lookupDoppelreim({
                word: cleanTerm,
                language,
                mode,
                allow_slang: allowSlang,
                max_results: 30,
            });

            if (res.success && res.results) {
                setResults(res.results);
            } else {
                setResults([]);
                setError('No rhymes found for this search configuration.');
            }
        } catch (err) {
            console.error('Doppelreim lookup failed:', err);
            setError('Failed to connect to offline rhyme engine.');
            setResults([]);
        } finally {
            setLoading(false);
        }
    }, [searchTerm, language, mode, allowSlang]);

    useEffect(() => {
        if (initialWord) {
            setSearchTerm(initialWord);
        }
    }, [initialWord]);

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') handleSearch();
    };

    const handleVote = async (targetWord: string, isValid: boolean) => {
        const key = targetWord.toLowerCase();
        if (votedItems[key]) return; // prevent double voting in session

        try {
            const res = await toolApi.voteRhyme(searchTerm, targetWord, isValid);
            if (res.success) {
                setVotedItems((prev) => ({
                    ...prev,
                    [key]: isValid ? 'up' : 'down',
                }));
                // Update local votes count for visual feedback
                setResults((prevResults) =>
                    prevResults.map((r) => {
                        if (r.word.toLowerCase() === key) {
                            return {
                                ...r,
                                upvotes: r.upvotes + (isValid ? 1 : -1),
                            };
                        }
                        return r;
                    })
                );
            }
        } catch (err) {
            console.error('Failed to register vote:', err);
        }
    };

    const handleInsert = (word: string) => {
        if (onInsert) {
            onInsert(word);
        } else {
            navigator.clipboard.writeText(word);
            toast.success(`Copied "${word}" to clipboard!`);
        }
    };

    return (
        <div className="doppelreim-panel glass-card">
            <div className="panel-header">
                <h3>
                    <span className="panel-icon">🎙️</span> Doppelreim Engine
                </h3>
                <span className="subtitle-tag">Offline Phonetics</span>
            </div>

            {/* Language Selector */}
            <div className="control-group">
                <label className="group-label">Language</label>
                <div className="toggle-buttons select-lang">
                    <button
                        className={`toggle-btn ${language === 'en' ? 'active' : ''}`}
                        onClick={() => setLanguage('en')}
                    >
                        English
                    </button>
                    <button
                        className={`toggle-btn ${language === 'hi' ? 'active' : ''}`}
                        onClick={() => setLanguage('hi')}
                    >
                        हिंदी
                    </button>
                    <button
                        className={`toggle-btn ${language === 'kn' ? 'active' : ''}`}
                        onClick={() => setLanguage('kn')}
                    >
                        ಕನ್ನಡ
                    </button>
                </div>
            </div>

            {/* Search Input Row */}
            <div className="search-input-row">
                <input
                    type="text"
                    className="glass-input"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder={`Enter a word (e.g., ${
                        language === 'en' ? 'lyrics' : language === 'hi' ? 'सपना' : 'ಬಂಗಾರ'
                    })`}
                />
                <button
                    className="search-submit-btn hover-glow"
                    onClick={handleSearch}
                    disabled={loading || !searchTerm.trim()}
                >
                    {loading ? (
                        <div className="spinner-small"></div>
                    ) : (
                        'Rhyme'
                    )}
                </button>
            </div>

            {/* Rhyme Modes */}
            <div className="control-group">
                <label className="group-label">Rhyme Style</label>
                <div className="toggle-buttons grid-modes">
                    <button
                        className={`toggle-btn ${mode === 'vowel' ? 'active' : ''}`}
                        onClick={() => setMode('vowel')}
                        title="Doppelreim: Vowel sounds only (slant rhyming)"
                    >
                        Slant Vowel
                    </button>
                    <button
                        className={`toggle-btn ${mode === 'classic' ? 'active' : ''}`}
                        onClick={() => setMode('classic')}
                        title="Classic: Standard, perfect end-rhymes"
                    >
                        Perfect
                    </button>
                    <button
                        className={`toggle-btn ${mode === 'multi' ? 'active' : ''}`}
                        onClick={() => setMode('multi')}
                        title="Multi-Word: Pairs shorter words together"
                    >
                        Multi-Word
                    </button>
                    <button
                        className={`toggle-btn ${mode === 'inspiration' ? 'active' : ''}`}
                        onClick={() => setMode('inspiration')}
                        title="Inspiration: Rich assonance structures"
                    >
                        Inspiration
                    </button>
                </div>
            </div>

            {/* Slang Filter Toggle */}
            <div className="filter-row">
                <span className="filter-label">Include Slang Dictionary</span>
                <label className="switch">
                    <input
                        type="checkbox"
                        checked={allowSlang}
                        onChange={(e) => setAllowSlang(e.target.checked)}
                    />
                    <span className="slider round"></span>
                </label>
            </div>

            {/* Results Section */}
            <div className="results-scroll-area">
                {loading && (
                    <div className="results-status">
                        <span className="pulse-dot"></span> Analyzing phonetics...
                    </div>
                )}

                {error && <div className="results-error">{error}</div>}

                {!loading && !error && results.length === 0 && (
                    <div className="results-empty">
                        Enter a search term and click Rhyme to load offline matches.
                    </div>
                )}

                <AnimatePresence>
                    {!loading &&
                        results.map((item, index) => {
                            const voteState = votedItems[item.word.toLowerCase()];
                            return (
                                <motion.div
                                    key={item.word + index}
                                    className="rhyme-result-card glass-subcard"
                                    initial={{ opacity: 0, y: 15 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    exit={{ opacity: 0 }}
                                    transition={{ delay: Math.min(index * 0.04, 0.4) }}
                                >
                                    <div
                                        className="result-main"
                                        onClick={() => handleInsert(item.word)}
                                        title="Click to insert / copy"
                                    >
                                        <div className="result-text">{item.word}</div>
                                        <div className="result-meta">
                                            <span className="syl-badge">
                                                {item.syllable_count} {item.syllable_count === 1 ? 'Syllable' : 'Syllables'}
                                            </span>
                                            {item.is_slang && <span className="slang-badge">Slang</span>}
                                        </div>

                                        {/* Vowel Sequence Badges */}
                                        <div className="vowel-sequence">
                                            {item.vowel_sequence.split('-').map((v, i) => (
                                                <span key={i} className="vowel-badge">
                                                    {v}
                                                </span>
                                            ))}
                                        </div>
                                    </div>

                                    {/* Voting & Ranking Weights */}
                                    <div className="result-voting">
                                        <button
                                            className={`vote-btn up ${voteState === 'up' ? 'voted' : ''}`}
                                            onClick={() => handleVote(item.word, true)}
                                            title="Rhymes well"
                                            disabled={!!voteState}
                                        >
                                            👍
                                        </button>
                                        <span className="vote-count">{item.upvotes}</span>
                                        <button
                                            className={`vote-btn down ${voteState === 'down' ? 'voted' : ''}`}
                                            onClick={() => handleVote(item.word, false)}
                                            title="Does not rhyme well"
                                            disabled={!!voteState}
                                        >
                                            👎
                                        </button>
                                    </div>
                                </motion.div>
                            );
                        })}
                </AnimatePresence>
            </div>
        </div>
    );
};

export default DoppelreimPanel;
