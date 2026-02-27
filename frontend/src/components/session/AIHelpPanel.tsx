import React, { useState } from 'react';
import { toast } from 'react-hot-toast';
import { aiApi } from '../../services/api';
import { Button } from '../ui/Button';
import { HookGenerator } from './HookGenerator';
import { StructureBuilder } from './StructureBuilder';
import { useSessionStore } from '../../store/sessionStore';
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
    const { currentSession } = useSessionStore();

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
