import React, { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'react-hot-toast';
import { FixedSizeList as List } from 'react-window';
import type { LyricLine } from '../../services/api';
import { lineApi } from '../../services/api';
import { useSessionStore } from '../../store/sessionStore';
import { LineRow } from './LineRow.tsx';
import { VirtualLineRow } from './VirtualLineRow';
import { Autocomplete } from './Autocomplete';
import { AnalysisStrip } from './AnalysisStrip';
import { Button } from '../ui/Button';
import './LyricsEditor.css';

// Threshold for switching to virtualized rendering
const VIRTUALIZATION_THRESHOLD = 50;
const LINE_HEIGHT = 72; // px per line row

interface LyricsEditorProps {
    sessionId: number;
    lines: LyricLine[];
    bpm: number;
    rhymeScheme?: string;
}

export const LyricsEditor: React.FC<LyricsEditorProps> = ({ sessionId, lines, rhymeScheme }) => {
    const { setLines, setGhostText, ghostText, currentSection, setCurrentSection } =
        useSessionStore();

    const [inputValue, setInputValue] = useState('');
    const [isStreaming, setIsStreaming] = useState(false);
    const [syllableCount, setSyllableCount] = useState(0);
    const inputRef = useRef<HTMLInputElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);
    const eventSourceRef = useRef<EventSource | null>(null);

    // Count syllables (simple client-side approximation)
    const countSyllables = (text: string): number => {
        const words = text.toLowerCase().split(/\s+/);
        let count = 0;
        for (const word of words) {
            if (!word) continue;
            const vowels = word.match(/[aeiouy]+/g);
            count += vowels ? vowels.length : 1;
        }
        return count;
    };

    // Debounced suggestion fetching
    const fetchSuggestion = useCallback(
        debounce(async (text: string) => {
            if (!text.trim() || text.length < 3) {
                setGhostText('');
                return;
            }

            // Cancel previous stream
            if (eventSourceRef.current) {
                eventSourceRef.current.close();
            }

            setIsStreaming(true);
            let accumulated = '';

            try {
                const es = lineApi.streamSuggestion(sessionId, text);
                eventSourceRef.current = es;

                es.onmessage = (e) => {
                    if (e.data === '[DONE]') {
                        es.close();
                        setIsStreaming(false);
                        return;
                    }

                    if (e.data.startsWith('[ERROR]')) {
                        console.error(e.data);
                        es.close();
                        setIsStreaming(false);
                        setGhostText('');
                        return;
                    }

                    // Filter error messages
                    const errorPatterns = ['429', 'error', 'exceeded', 'quota'];
                    const isError = errorPatterns.some((p) =>
                        e.data.toLowerCase().includes(p)
                    );

                    if (isError) {
                        es.close();
                        setIsStreaming(false);
                        setGhostText('');
                        return;
                    }

                    accumulated += e.data;
                    setGhostText(accumulated);
                };

                es.onerror = () => {
                    es.close();
                    setIsStreaming(false);
                };
            } catch (error) {
                console.error('Stream error:', error);
                setIsStreaming(false);
            }
        }, 400),
        [sessionId]
    );

    // Handle input change
    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const value = e.target.value;
        setInputValue(value);
        setSyllableCount(countSyllables(value));
        fetchSuggestion(value);
    };

    // Handle key press
    const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
        if (e.key === 'Tab' && ghostText) {
            e.preventDefault();
            setInputValue(ghostText);
            setSyllableCount(countSyllables(ghostText));
            setGhostText('');
        } else if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleAddLine();
        } else if (e.key === 'Escape') {
            setGhostText('');
        }
    };

    // Add new line
    const handleAddLine = async () => {
        const content = inputValue.trim();
        if (!content) return;

        // Optimistic update
        const tempLine: LyricLine = {
            id: Date.now(),
            line_number: lines.length + 1,
            user_input: content,
            section: currentSection,
            syllable_count: syllableCount,
            has_internal_rhyme: false,
        };

        setLines([...lines, tempLine]);
        setInputValue('');
        setSyllableCount(0);
        setGhostText('');

        // Scroll to bottom
        setTimeout(() => {
            containerRef.current?.scrollTo({
                top: containerRef.current.scrollHeight,
                behavior: 'smooth',
            });
        }, 100);

        // API call
        try {
            const response = await lineApi.add(sessionId, content, currentSection);
            if (response.success) {
                // Use all_lines (with full cross-line highlighting) if available
                if (response.all_lines && response.all_lines.length > 0) {
                    setLines(response.all_lines);
                } else {
                    // Fallback: replace temp line with real data
                    setLines(
                        lines
                            .filter((l) => l.id !== tempLine.id)
                            .concat(response.line)
                    );
                }
            }
        } catch (error) {
            toast.error('Failed to add line');
            // Rollback
            setLines(lines.filter((l) => l.id !== tempLine.id));
        }
    };

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            if (eventSourceRef.current) {
                eventSourceRef.current.close();
            }
        };
    }, []);

    return (
        <div className="lyrics-editor">
            {/* Lines Container - Virtualized for 50+ lines */}
            {lines.length >= VIRTUALIZATION_THRESHOLD ? (
                <div className="lines-container virtualized" ref={containerRef}>
                    <List
                        height={500}
                        itemCount={lines.length}
                        itemSize={LINE_HEIGHT}
                        width="100%"
                        itemData={{ lines, sessionId }}
                    >
                        {VirtualLineRow}
                    </List>
                </div>
            ) : (
                <div className="lines-container" ref={containerRef}>
                    <AnimatePresence>
                        {lines.map((line, index) => (
                            <motion.div
                                key={line.id}
                                initial={{ opacity: 0, x: -20 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: 20 }}
                                transition={{ duration: 0.2 }}
                            >
                                <LineRow line={line} index={index} sessionId={sessionId} />
                            </motion.div>
                        ))}
                    </AnimatePresence>
                </div>
            )}

            {/* Input Area */}
            <div className="input-area glass">
                <div className="section-select">
                    <select
                        value={currentSection}
                        onChange={(e) => setCurrentSection(e.target.value)}
                        className="section-dropdown"
                    >
                        <option value="Verse">Verse</option>
                        <option value="Chorus">Chorus</option>
                        <option value="Bridge">Bridge</option>
                        <option value="Intro">Intro</option>
                        <option value="Outro">Outro</option>
                    </select>
                </div>

                <div className="input-row">
                    <span className="line-number">{lines.length + 1}</span>
                    <div className="autocomplete-wrapper">
                        <input
                            ref={inputRef}
                            type="text"
                            className="line-input"
                            placeholder="Write your next bar..."
                            value={inputValue}
                            onChange={handleInputChange}
                            onKeyDown={handleKeyDown}
                            autoComplete="off"
                        />
                        <Autocomplete suggestion={ghostText} inputValue={inputValue} isStreaming={isStreaming} />
                    </div>
                    <Button variant="primary" onClick={handleAddLine} disabled={!inputValue.trim()}>
                        Add
                    </Button>
                </div>

                <div className="input-hints">
                    <div className="hints-left">
                        {ghostText && (
                            <span className="tab-hint">
                                Press <kbd>Tab</kbd> to accept
                            </span>
                        )}
                    </div>
                </div>

                <AnalysisStrip text={inputValue} rhymeScheme={rhymeScheme} />
            </div>
        </div>
    );
};

// Debounce utility
function debounce<T extends (...args: Parameters<T>) => void>(
    fn: T,
    delay: number
): (...args: Parameters<T>) => void {
    let timeout: ReturnType<typeof setTimeout>;
    return (...args: Parameters<T>) => {
        clearTimeout(timeout);
        timeout = setTimeout(() => fn(...args), delay);
    };
}
