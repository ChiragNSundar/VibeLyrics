import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'react-hot-toast';
import { aiApi } from '../../services/api';
import { useSessionStore } from '../../store/sessionStore';
import { Button } from '../ui/Button';
import { HookGenerator } from './HookGenerator';
import { StructureBuilder } from './StructureBuilder';
import './AIHelpPanel.css';

interface AIHelpPanelProps {
    sessionId: number;
    onClose: () => void;
}

export const AIHelpPanel: React.FC<AIHelpPanelProps> = ({ sessionId, onClose }) => {
    const [question, setQuestion] = useState('');
    const [answer, setAnswer] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [improvementType, setImprovementType] = useState<'rhyme' | 'flow' | 'wordplay' | 'depth'>('rhyme');

    const [polishResult, setPolishResult] = useState('');
    const [isPolishing, setIsPolishing] = useState(false);
    const [isApplying, setIsApplying] = useState(false);

    // Local Polisher state
    const [localPolishLine, setLocalPolishLine] = useState('');
    const [localPolishSyl, setLocalPolishSyl] = useState<number | ''>('');
    const [localPolishMode, setLocalPolishMode] = useState<'cadence' | 'slang'>('cadence');
    const [localCandidates, setLocalCandidates] = useState<string[]>([]);
    const [isLocalPolishing, setIsLocalPolishing] = useState(false);

    const { currentSession, setLines, lines, selectedLineId } = useSessionStore();

    // Auto-populate local polish input from the selected line
    const selectedLine = useMemo(() => {
        if (selectedLineId) {
            return lines.find(l => l.id === selectedLineId);
        }
        return null;
    }, [selectedLineId, lines]);

    const handleAsk = async () => {
        if (!question.trim()) return;

        setIsLoading(true);
        setAnswer('');

        try {
            const response = await aiApi.ask(question, sessionId);
            if (response.success) {
                setAnswer(response.answer);
                setQuestion('');
            } else {
                toast.error('Failed to get answer');
            }
        } catch (error) {
            toast.error('Failed to ask AI');
        } finally {
            setIsLoading(false);
        }
    };

    const handlePolish = async () => {
        setIsPolishing(true);
        setPolishResult('');

        try {
            const response = await aiApi.improveSession(sessionId);
            if (response.success && response.improved) {
                setPolishResult(response.improved);
                toast.success('Song polished!');
            } else {
                toast.error(response.error || 'Failed to polish song');
            }
        } catch (error) {
            toast.error('Failed to polish song');
        } finally {
            setIsPolishing(false);
        }
    };

    const handleApplyPolish = async () => {
        if (!confirm('This will replace all current lyrics with the improved version. Continue?')) return;

        setIsApplying(true);
        try {
            const response = await aiApi.applyPolish(sessionId, polishResult);
            if (response.success && response.lines) {
                setLines(response.lines);
                setPolishResult('');
                toast.success('Lyrics updated!');
            } else {
                toast.error(response.error || 'Failed to apply lyrics');
            }
        } catch (error) {
            toast.error('Failed to apply lyrics');
        } finally {
            setIsApplying(false);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleAsk();
        }
    };

    // ── Local Polisher Logic ──
    const handleLocalPolish = async () => {
        const lineText = localPolishLine.trim() || (selectedLine?.final_version || selectedLine?.user_input || '');
        if (!lineText) {
            toast.error('Enter a line or select one from the editor');
            return;
        }

        setIsLocalPolishing(true);
        setLocalCandidates([]);

        try {
            const targetSyl = localPolishSyl ? Number(localPolishSyl) : undefined;
            const slangWords = localPolishMode === 'slang' ? [] : []; // backend merges from DB
            const response = await aiApi.polishLocal(lineText, targetSyl, slangWords);
            if (response.success && response.candidates.length > 0) {
                setLocalCandidates(response.candidates);
                toast.success(`${response.candidates.length} candidate(s) generated`);
            } else {
                toast.error('No candidates returned — try a different input');
            }
        } catch (error) {
            toast.error('Local polisher failed');
        } finally {
            setIsLocalPolishing(false);
        }
    };

    const handleUseLocalLine = (candidate: string) => {
        navigator.clipboard.writeText(candidate);
        toast.success(`Copied "${candidate.slice(0, 30)}..." to clipboard`);
    };

    return (
        <div className="aihelp-panel">
            <div className="panel-header">
                <h3>🤖 AI Help</h3>
                <Button variant="icon" onClick={onClose}>
                    ✕
                </Button>
            </div>

            <div className="panel-content">
                {/* Full Song Polish Section */}
                <div className="ai-section">
                    <h4>🚀 Full Song Polish</h4>
                    <p className="help-text">Restructure your whole song into Verses and a Chorus.</p>
                    <Button
                        variant="primary"
                        fullWidth
                        onClick={handlePolish}
                        disabled={isPolishing}
                        style={{ marginTop: '0.5rem' }}
                    >
                        {isPolishing ? '🪄 Polishing...' : '✨ Polish Entire Song'}
                    </Button>

                    {polishResult && (
                        <div className="polish-result">
                            <div className="result-header">
                                <span>Improved Version:</span>
                                <Button
                                    variant="secondary"
                                    size="sm"
                                    onClick={() => {
                                        navigator.clipboard.writeText(polishResult);
                                        toast.success('Copied to clipboard');
                                    }}
                                >
                                    📋 Copy
                                </Button>
                                <Button
                                    variant="primary"
                                    size="sm"
                                    onClick={handleApplyPolish}
                                    disabled={isApplying}
                                >
                                    {isApplying ? '...' : '✅ Apply to Session'}
                                </Button>
                            </div>
                            <pre className="result-text">{polishResult}</pre>
                        </div>
                    )}
                </div>

                {/* Improvement Section */}
                <div className="ai-section">
                    <h4>✨ Improve Line</h4>
                    <div className="improvement-types">
                        {(['rhyme', 'flow', 'wordplay', 'depth'] as const).map((type) => (
                            <button
                                key={type}
                                className={`chip ${improvementType === type ? 'active' : ''}`}
                                onClick={() => setImprovementType(type)}
                            >
                                {type === 'rhyme' && '🎯 Rhyme'}
                                {type === 'flow' && '🌊 Flow'}
                                {type === 'wordplay' && '🔤 Wordplay'}
                                {type === 'depth' && '💎 Depth'}
                            </button>
                        ))}
                    </div>
                    <p className="help-text">Click "✨" on any line to improve it with {improvementType}</p>
                </div>

                {/* ── Local Polisher Drawer ── */}
                <div className="ai-section local-polisher-section">
                    <h4>🎛️ Cadence Polisher</h4>
                    <p className="help-text">Rewrite a line to fit a target syllable count or inject your slang vocabulary.</p>

                    <div className="local-polish-controls">
                        <input
                            type="text"
                            className="ask-input"
                            placeholder={selectedLine
                                ? `Using: "${(selectedLine.final_version || selectedLine.user_input).slice(0, 40)}..."`
                                : 'Paste or type a lyric line...'
                            }
                            value={localPolishLine}
                            onChange={(e) => setLocalPolishLine(e.target.value)}
                        />

                        <div className="polish-options-row">
                            <div className="polish-syl-input">
                                <label>Target Syl</label>
                                <input
                                    type="number"
                                    min={2}
                                    max={24}
                                    value={localPolishSyl}
                                    onChange={(e) => setLocalPolishSyl(e.target.value ? parseInt(e.target.value) : '')}
                                    placeholder={selectedLine ? String(selectedLine.syllable_count) : '8'}
                                />
                            </div>
                            <div className="polish-mode-btns">
                                <button
                                    className={`chip ${localPolishMode === 'cadence' ? 'active' : ''}`}
                                    onClick={() => setLocalPolishMode('cadence')}
                                >
                                    🎵 Fit Cadence
                                </button>
                                <button
                                    className={`chip ${localPolishMode === 'slang' ? 'active' : ''}`}
                                    onClick={() => setLocalPolishMode('slang')}
                                >
                                    🗣️ Inject Slang
                                </button>
                            </div>
                        </div>

                        <Button
                            variant="primary"
                            fullWidth
                            onClick={handleLocalPolish}
                            disabled={isLocalPolishing}
                            style={{ marginTop: '0.5rem' }}
                        >
                            {isLocalPolishing ? '⏳ Polishing...' : '🎛️ Generate Alternatives'}
                        </Button>
                    </div>

                    {/* Candidates Display */}
                    <AnimatePresence>
                        {localCandidates.length > 0 && (
                            <motion.div
                                className="local-candidates"
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0 }}
                            >
                                {localCandidates.map((cand, idx) => (
                                    <motion.div
                                        key={idx}
                                        className="candidate-card glass-subcard"
                                        initial={{ opacity: 0, x: -10 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        transition={{ delay: idx * 0.1 }}
                                        onClick={() => handleUseLocalLine(cand)}
                                        title="Click to copy"
                                    >
                                        <span className="candidate-index">#{idx + 1}</span>
                                        <span className="candidate-text">{cand}</span>
                                        <span className="candidate-action">📋</span>
                                    </motion.div>
                                ))}
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>

                {/* Ask AI Section */}
                <div className="ai-section">
                    <h4>💬 Ask AI</h4>
                    <div className="ask-row">
                        <input
                            type="text"
                            className="ask-input"
                            placeholder="Ask about rhymes, flow..."
                            value={question}
                            onChange={(e) => setQuestion(e.target.value)}
                            onKeyDown={handleKeyDown}
                        />
                        <Button variant="primary" onClick={handleAsk} disabled={isLoading || !question.trim()}>
                            {isLoading ? '...' : 'Ask'}
                        </Button>
                    </div>

                    {answer && (
                        <div className="ai-answer">
                            {answer}
                        </div>
                    )}
                </div>

                {/* Song Structure & Hooks */}
                <div className="ai-section">
                    <h4>🏗️ Song Architecture</h4>
                    <StructureBuilder
                        sessionId={sessionId}
                        theme={currentSession?.theme}
                        mood={currentSession?.mood}
                        bpm={currentSession?.bpm}
                    />
                    <HookGenerator
                        sessionId={sessionId}
                        theme={currentSession?.theme}
                        mood={currentSession?.mood}
                    />
                </div>
            </div>
        </div>
    );
};
