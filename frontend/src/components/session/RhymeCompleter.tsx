import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import './RhymeCompleter.css';

interface RhymeCompleterProps {
    sessionId: number;
    partialLine: string;
    onSelect: (completion: string) => void;
    isVisible: boolean;
}

/**
 * AI-powered rhyme completer panel
 * Shows 3 rhyming suggestions for the current line
 */
export const RhymeCompleter: React.FC<RhymeCompleterProps> = ({
    sessionId,
    partialLine,
    onSelect,
    isVisible,
}) => {
    const [completions, setCompletions] = useState<string[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchCompletions = useCallback(async (text: string) => {
        if (text.length < 5) {
            setCompletions([]);
            return;
        }

        setIsLoading(true);
        setError(null);

        try {
            const response = await fetch('/api/ai/complete-rhyme', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: sessionId,
                    partial_line: text,
                    count: 3,
                }),
            });

            const data = await response.json();

            if (data.success && data.completions) {
                setCompletions(data.completions);
            } else {
                setCompletions([]);
                if (data.error) setError(data.error);
            }
        } catch (err) {
            console.error('Failed to fetch completions:', err);
            setCompletions([]);
        } finally {
            setIsLoading(false);
        }
    }, [sessionId]);

    useEffect(() => {
        if (!isVisible || !partialLine) {
            setCompletions([]);
            return;
        }

        const timeout = setTimeout(() => {
            fetchCompletions(partialLine);
        }, 500);

        return () => clearTimeout(timeout);
    }, [partialLine, isVisible, fetchCompletions]);

    if (!isVisible) return null;

    return (
        <AnimatePresence>
            <motion.div
                className="rhyme-completer"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 10 }}
            >
                <div className="completer-header">
                    <span className="completer-icon">✨</span>
                    <span className="completer-title">Rhyme Suggestions</span>
                </div>

                <div className="completions-list">
                    {isLoading ? (
                        <div className="completions-loading">
                            <span className="loading-dot" />
                            <span className="loading-dot" />
                            <span className="loading-dot" />
                        </div>
                    ) : completions.length > 0 ? (
                        completions.map((completion, index) => (
                            <motion.button
                                key={index}
                                className="completion-item"
                                onClick={() => onSelect(completion)}
                                initial={{ opacity: 0, x: -10 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ delay: index * 0.1 }}
                            >
                                <span className="completion-number">{index + 1}</span>
                                <span className="completion-text">{completion}</span>
                            </motion.button>
                        ))
                    ) : partialLine.length >= 5 ? (
                        <div className="completions-empty">
                            {error || 'Type more to get suggestions...'}
                        </div>
                    ) : (
                        <div className="completions-hint">
                            Start typing to see rhyme suggestions
                        </div>
                    )}
                </div>
            </motion.div>
        </AnimatePresence>
    );
};
