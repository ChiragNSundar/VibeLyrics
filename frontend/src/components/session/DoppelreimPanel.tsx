import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { SlidersHorizontal } from 'lucide-react';
import { toolApi, vocabularyApi } from '../../services/api';
import type { DoppelreimResult, DictionaryEntry } from '../../services/api';
import { toast } from 'react-hot-toast';
import { useSessionStore } from '../../store/sessionStore';
import { RhymeMap3D } from './RhymeMap3D';
import './DoppelreimPanel.css';

interface DoppelreimPanelProps {
    sessionId: number;
    initialWord?: string;
    onInsert?: (text: string) => void;
}

export const DoppelreimPanel: React.FC<DoppelreimPanelProps> = ({
    sessionId: _sessionId,
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
    const [showOptions, setShowOptions] = useState(false);
    const [viewMode, setViewMode] = useState<'list' | 'map'>('list');

    // Flow-Aligned Sorting state
    const [flowAligned, setFlowAligned] = useState(false);
    const [targetSyllables, setTargetSyllables] = useState<number | undefined>(undefined);
    const [targetStress, setTargetStress] = useState<string>('');

    const { activeRhymeWord, setActiveRhymeWord, lines, selectedLineId } = useSessionStore();

    // Kannada Dictionary search states
    const [activeTab, setActiveTab] = useState<'rhymes' | 'dict'>('rhymes');
    const [dictSearchTerm, setDictSearchTerm] = useState('');
    const [dictResults, setDictResults] = useState<DictionaryEntry[]>([]);
    const [dictLoading, setDictLoading] = useState(false);
    const [dictError, setDictError] = useState<string | null>(null);

    const handleDictSearch = async () => {
        const query = dictSearchTerm.trim();
        if (!query) return;

        setDictLoading(true);
        setDictError(null);
        try {
            const res = await vocabularyApi.searchDictionary(query);
            if (res.success && res.results) {
                setDictResults(res.results);
                if (res.results.length === 0) {
                    setDictError('No entries found in the Kannada dictionary.');
                }
            } else {
                setDictResults([]);
                setDictError('No entries found in the Kannada dictionary.');
            }
        } catch (err) {
            console.error('Dictionary search failed:', err);
            setDictError('Failed to query local dictionary.');
            setDictResults([]);
        } finally {
            setDictLoading(false);
        }
    };

    const handleDictKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') handleDictSearch();
    };

    const handleFindRhymesFromDict = (word: string) => {
        setLanguage('kn');
        setActiveTab('rhymes');
        setActiveRhymeWord(word);
    };

    // Derive target cadence from the selected/active line
    useEffect(() => {
        if (flowAligned && selectedLineId) {
            const activeLine = lines.find(l => l.id === selectedLineId);
            if (activeLine) {
                setTargetSyllables(activeLine.syllable_count || undefined);
                setTargetStress(activeLine.stress_pattern || '');
            }
        } else if (!flowAligned) {
            setTargetSyllables(undefined);
            setTargetStress('');
        }
    }, [flowAligned, selectedLineId, lines]);

    const buildLookupPayload = useCallback(() => {
        const payload: any = {
            word: searchTerm.trim(),
            language,
            mode,
            allow_slang: allowSlang,
            max_results: 30,
        };
        if (flowAligned && targetSyllables) {
            payload.target_syllables = targetSyllables;
        }
        if (flowAligned && targetStress) {
            payload.target_stress = targetStress;
        }
        return payload;
    }, [searchTerm, language, mode, allowSlang, flowAligned, targetSyllables, targetStress]);

    const handleSearch = useCallback(async () => {
        const cleanTerm = searchTerm.trim();
        if (!cleanTerm) return;

        setLoading(true);
        setError(null);
        try {
            const res = await toolApi.lookupDoppelreim(buildLookupPayload());

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
    }, [searchTerm, buildLookupPayload]);

    useEffect(() => {
        if (initialWord) {
            setSearchTerm(initialWord);
        }
    }, [initialWord]);

    useEffect(() => {
        if (activeRhymeWord) {
            setSearchTerm(activeRhymeWord);
            const triggerSearch = async () => {
                setLoading(true);
                setError(null);
                try {
                    const payload: any = {
                        word: activeRhymeWord,
                        language,
                        mode,
                        allow_slang: allowSlang,
                        max_results: 30,
                    };
                    if (flowAligned && targetSyllables) {
                        payload.target_syllables = targetSyllables;
                    }
                    if (flowAligned && targetStress) {
                        payload.target_stress = targetStress;
                    }
                    const res = await toolApi.lookupDoppelreim(payload);
                    if (res.success && res.results) {
                        setResults(res.results);
                    } else {
                        setResults([]);
                        setError('No rhymes found for this search configuration.');
                    }
                } catch (err) {
                    setError('Failed to connect to offline rhyme engine.');
                    setResults([]);
                } finally {
                    setLoading(false);
                }
            };
            triggerSearch();
            setActiveRhymeWord(null);
        }
    }, [activeRhymeWord, language, mode, allowSlang, setActiveRhymeWord, flowAligned, targetSyllables, targetStress]);

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

            {/* Tabs */}
            <div className="panel-tabs">
                <button
                    className={`panel-tab-btn ${activeTab === 'rhymes' ? 'active' : ''}`}
                    onClick={() => setActiveTab('rhymes')}
                >
                    🎙️ Rhymes
                </button>
                <button
                    className={`panel-tab-btn ${activeTab === 'dict' ? 'active' : ''}`}
                    onClick={() => setActiveTab('dict')}
                >
                    📖 Dictionary
                </button>
            </div>

            {activeTab === 'rhymes' ? (
                <>
                    {/* Search Input Row */}
                    <div className="search-input-row">
                        <input
                            type="text"
                            className="glass-input"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder={`Enter a word (e.g., ${
                                language === 'en' ? 'lyrics' : language === 'hi' ? 'sapna' : 'bangaara'
                            })`}
                        />
                        <button
                            type="button"
                            className={`options-toggle-btn ${showOptions ? 'active' : ''}`}
                            onClick={() => setShowOptions(!showOptions)}
                            title="Toggle Search Settings"
                        >
                            <SlidersHorizontal size={15} />
                        </button>
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

                    {/* Collapsible Search Options */}
                    <AnimatePresence initial={false}>
                        {showOptions && (
                            <motion.div
                                className="doppelreim-options-drawer"
                                initial={{ height: 0, opacity: 0 }}
                                animate={{ height: 'auto', opacity: 1 }}
                                exit={{ height: 0, opacity: 0 }}
                                transition={{ duration: 0.25, ease: 'easeInOut' }}
                                style={{ overflow: 'hidden' }}
                            >
                                <div className="drawer-inner" style={{ display: 'flex', flexDirection: 'column', gap: '1rem', paddingBottom: '0.5rem', paddingTop: '0.25rem' }}>
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
                                                Hinglish
                                            </button>
                                            <button
                                                className={`toggle-btn ${language === 'kn' ? 'active' : ''}`}
                                                onClick={() => setLanguage('kn')}
                                            >
                                                Kanglish
                                            </button>
                                        </div>
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

                                    {/* Flow-Aligned Sorting Toggle */}
                                    <div className="filter-row flow-aligned-row">
                                        <div className="filter-label-group">
                                            <span className="filter-label">🎵 Flow-Aligned Sorting</span>
                                            <span className="filter-hint">
                                                {flowAligned
                                                    ? targetSyllables
                                                        ? `Targeting ${targetSyllables} syl · ${targetStress || 'auto'}`
                                                        : 'Select a line to set target'
                                                    : 'Rank by rhythmic match'
                                                }
                                            </span>
                                        </div>
                                        <label className="switch">
                                            <input
                                                type="checkbox"
                                                checked={flowAligned}
                                                onChange={(e) => setFlowAligned(e.target.checked)}
                                            />
                                            <span className="slider round"></span>
                                        </label>
                                    </div>
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </>
            ) : (
                <div className="search-input-row">
                    <input
                        type="text"
                        className="glass-input"
                        value={dictSearchTerm}
                        onChange={(e) => setDictSearchTerm(e.target.value)}
                        onKeyDown={handleDictKeyDown}
                        placeholder="Search dictionary (e.g. dew or ibbaru)..."
                    />
                    <button
                        className="search-submit-btn hover-glow"
                        onClick={handleDictSearch}
                        disabled={dictLoading || !dictSearchTerm.trim()}
                        style={{ minWidth: '80px' }}
                    >
                        {dictLoading ? (
                            <div className="spinner-small"></div>
                        ) : (
                            'Search'
                        )}
                    </button>
                </div>
            )}

            {/* View Mode Toggle */}
            {activeTab === 'rhymes' && results.length > 0 && !loading && !error && (
                <div className="view-mode-toggle">
                    <button
                        className={`mode-toggle-btn ${viewMode === 'list' ? 'active' : ''}`}
                        onClick={() => setViewMode('list')}
                    >
                        List View
                    </button>
                    <button
                        className={`mode-toggle-btn ${viewMode === 'map' ? 'active' : ''}`}
                        onClick={() => setViewMode('map')}
                    >
                        🌐 3D Rhyme Map
                    </button>
                </div>
            )}

            {/* Results Section */}
            <div className="results-scroll-area">
                {activeTab === 'rhymes' ? (
                    <>
                        {loading && (
                            <div className="results-status">
                                <span className="pulse-dot"></span> Analyzing phonetics...
                            </div>
                        )}

                        {error && <div className="results-error">{error}</div>}

                        {!loading && !error && results.length === 0 && (
                            <div className="results-empty">
                                Enter a search term and click Rhyme to load matches.
                            </div>
                        )}

                        {viewMode === 'map' && results.length > 0 && !loading && !error ? (
                            <RhymeMap3D
                                searchWord={searchTerm}
                                results={results}
                                onWordClick={handleInsert}
                            />
                        ) : (
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
                                                        {flowAligned && item.rhythmic_score !== undefined && (
                                                            <span className={`rhythm-score-badge ${item.rhythmic_score >= 0 ? 'good' : 'weak'}`}>
                                                                ♪ {item.rhythmic_score >= 0 ? '+' : ''}{item.rhythmic_score.toFixed(1)}
                                                            </span>
                                                        )}
                                                    </div>

                                                    {/* Vowel Sequence Badges */}
                                                    <div className="vowel-sequence">
                                                        {item.vowel_sequence.split('-').map((v, i) => (
                                                            <span key={i} className="vowel-badge">
                                                                {v}
                                                            </span>
                                                        ))}
                                                    </div>

                                                    {/* Stress Pattern Display */}
                                                    {item.stress_pattern && (
                                                        <div className="result-stress-pattern">
                                                            {item.stress_pattern.replace(/\s/g, '').split('').map((c, i) => (
                                                                <span key={i} className={`mini-stress ${c === '/' ? 'str' : 'unstr'}`}>
                                                                    {c}
                                                                </span>
                                                            ))}
                                                        </div>
                                                    )}
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
                        )}
                    </>
                ) : (
                    <>
                        {dictLoading && (
                            <div className="results-status">
                                <span className="pulse-dot"></span> Searching dictionary...
                            </div>
                        )}

                        {dictError && <div className="results-error">{dictError}</div>}

                        {!dictLoading && !dictError && dictResults.length === 0 && (
                            <div className="results-empty">
                                Search Romanized Kannada words or English translation terms to query the dictionary.
                            </div>
                        )}

                        <AnimatePresence>
                            {!dictLoading &&
                                dictResults.map((entry, index) => (
                                    <motion.div
                                        key={entry.word + index}
                                        className="dict-result-card glass-subcard"
                                        initial={{ opacity: 0, y: 15 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        exit={{ opacity: 0 }}
                                        transition={{ delay: Math.min(index * 0.04, 0.4) }}
                                    >
                                        <div className="dict-header-row">
                                            <span className="dict-word-text">{entry.word}</span>
                                            {entry.ipa && <span className="dict-ipa-text">[{entry.ipa}]</span>}
                                        </div>
                                        <div className="dict-definitions-list">
                                            {entry.definitions.map((def, dIdx) => (
                                                <div key={dIdx} className="dict-def-item">
                                                    {def}
                                                </div>
                                            ))}
                                        </div>
                                        <div className="dict-actions-row">
                                            <button
                                                className="dict-action-btn primary"
                                                onClick={() => handleFindRhymesFromDict(entry.word)}
                                                title="Find rhymes for this Kannada word"
                                            >
                                                🎙️ Rhymes
                                            </button>
                                            <button
                                                className="dict-action-btn"
                                                onClick={() => handleInsert(entry.word)}
                                                title="Insert word into lyrics"
                                            >
                                                ✍️ Insert
                                            </button>
                                            <button
                                                className="dict-action-btn"
                                                onClick={() => {
                                                    navigator.clipboard.writeText(entry.word);
                                                    toast.success(`Copied "${entry.word}" to clipboard!`);
                                                }}
                                                title="Copy word"
                                            >
                                                📋 Copy
                                            </button>
                                        </div>
                                    </motion.div>
                                ))
                            }
                        </AnimatePresence>
                    </>
                )}
            </div>
        </div>
    );
};

export default DoppelreimPanel;

