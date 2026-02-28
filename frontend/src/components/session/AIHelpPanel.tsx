import React, { useState } from 'react';
import { toast } from 'react-hot-toast';
import { aiApi, type LyricLine } from '../../services/api';
import { useSessionStore } from '../../store/sessionStore';
import { Button } from '../ui/Button';
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
    const { setLines } = useSessionStore();

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
            </div>
        </div>
    );
};
