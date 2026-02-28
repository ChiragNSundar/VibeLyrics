import React, { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import { motion, AnimatePresence, Reorder } from 'framer-motion';
import { toast } from 'react-hot-toast';
import { FixedSizeList as List } from 'react-window';
import type { LyricLine } from '../../services/api';
import { lineApi } from '../../services/api';
import { useSessionStore } from '../../store/sessionStore';
import { LineRow } from './LineRow.tsx';
import { VirtualLineRow } from './VirtualLineRow';
import { AnalysisStrip } from './AnalysisStrip';
import { Button } from '../ui/Button';
import { VersionHistory } from './VersionHistory';
import { Autocomplete } from './Autocomplete';
import { AdlibChip } from './AdlibChip';
import { flowApi, statsApi } from '../../services/api';
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

// ── Syllable target based on BPM ────────────────────────────
function getSyllableTarget(bpm: number): { min: number; max: number; label: string } {
    // Rough mapping: faster BPM = fewer syllables per line
    if (bpm >= 160) return { min: 4, max: 8, label: 'Fast' };
    if (bpm >= 130) return { min: 6, max: 10, label: 'Upbeat' };
    if (bpm >= 100) return { min: 8, max: 14, label: 'Mid' };
    if (bpm >= 70) return { min: 10, max: 18, label: 'Slow' };
    return { min: 12, max: 20, label: 'Ballad' };
}

export const LyricsEditor: React.FC<LyricsEditorProps> = ({ sessionId, lines, bpm, rhymeScheme }) => {
    const { setLines, setGhostText, ghostText, currentSection, setCurrentSection } =
        useSessionStore();

    const [inputValue, setInputValue] = useState('');
    const [isStreaming, setIsStreaming] = useState(false);
    const [syllableCount, setSyllableCount] = useState(0);
    const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved'>('idle');
    const [historyPanelConfig, setHistoryPanelConfig] = useState<{ isOpen: boolean; lineId: number | null }>({ isOpen: false, lineId: null });
    const [historyVersions, setHistoryVersions] = useState<any[]>([]);

    // Flow Templates
    const [flowTemplates, setFlowTemplates] = useState<any[]>([]);
    const [selectedFlow, setSelectedFlow] = useState<string>('free');

    const inputRef = useRef<HTMLInputElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);
    const eventSourceRef = useRef<EventSource | null>(null);
    const saveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

    const syllableTarget = useMemo(() => {
        const baseTargetObj = getSyllableTarget(bpm);
        // We use the midpoint of the suggested min/max as the "ideal" base target for math
        const baseTarget = Math.floor((baseTargetObj.min + baseTargetObj.max) / 2);
        const minBase = baseTargetObj.min;
        const maxBase = baseTargetObj.max;

        let flowTarget = baseTarget;
        let flowLabel = `${bpm} BPM (${baseTargetObj.label})`;

        if (selectedFlow !== 'free') {
            const template = flowTemplates.find(t => t.id === selectedFlow);
            if (template) {
                flowTarget = template.syllable_target;
                flowLabel = template.name;
                return {
                    min: Math.floor(flowTarget * 0.9), // Tighter constraint
                    max: Math.ceil(flowTarget * 1.1),
                    ideal: flowTarget,
                    label: flowLabel
                };
            }
        }

        return { min: minBase, max: maxBase, ideal: baseTarget, label: flowLabel };
    }, [bpm, selectedFlow, flowTemplates]);

    // ── Stats ────────────────────────────────────────────────
    const stats = useMemo(() => {
        const totalLines = lines.length;
        const totalWords = lines.reduce((acc, l) => {
            const text = l.final_version || l.user_input;
            return acc + (text ? text.split(/\s+/).filter(w => w).length : 0);
        }, 0);
        const totalSyllables = lines.reduce((acc, l) => acc + (l.syllable_count || 0), 0);
        return { totalLines, totalWords, totalSyllables };
    }, [lines]);

    // ── Load Flow Templates ──────────────────────────────────
    useEffect(() => {
        const fetchTemplates = async () => {
            try {
                const res = await flowApi.getTemplates();
                if (res.success) setFlowTemplates(res.templates);
            } catch (err) {
                console.warn('Failed to fetch flow templates');
            }
        };
        fetchTemplates();
    }, []);

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

    // ── Auto-save indicator ──────────────────────────────────
    const showSaved = () => {
        setSaveStatus('saved');
        if (saveTimerRef.current) clearTimeout(saveTimerRef.current);
        saveTimerRef.current = setTimeout(() => setSaveStatus('idle'), 2000);
    };

    // Add new line
    const handleAddLine = async () => {
        const content = inputValue.trim();
        if (!content) return;

        setSaveStatus('saving');

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
                if (response.all_lines && response.all_lines.length > 0) {
                    setLines(response.all_lines);
                } else {
                    setLines(
                        lines
                            .filter((l) => l.id !== tempLine.id)
                            .concat(response.line)
                    );
                }
                showSaved();

                // Track streak in the background
                statsApi.checkInStreak().catch(() => { });
            }
        } catch (error) {
            toast.error('Failed to add line');
            setLines(lines.filter((l) => l.id !== tempLine.id));
            setSaveStatus('idle');
        }
    };

    // ── Export lyrics ─────────────────────────────────────────
    const exportAsText = () => {
        const text = lines
            .map((l) => {
                const content = l.final_version || l.user_input;
                return content;
            })
            .join('\n');

        if (!text.trim()) {
            toast.error('No lyrics to export');
            return;
        }

        // Download as .txt file
        const blob = new Blob([text], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `lyrics-${sessionId}.txt`;
        a.click();
        URL.revokeObjectURL(url);
        toast.success('Lyrics exported!');
    };

    const copyToClipboard = async () => {
        const text = lines
            .map((l) => l.final_version || l.user_input)
            .join('\n');

        if (!text.trim()) {
            toast.error('No lyrics to copy');
            return;
        }

        try {
            await navigator.clipboard.writeText(text);
            toast.success('Copied to clipboard!');
        } catch {
            toast.error('Failed to copy');
        }
    };

    const handleReorder = async (newOrder: LyricLine[]) => {
        // Optimistically update local state
        const reordered = newOrder.map((line, idx) => ({
            ...line,
            line_number: idx + 1,
        }));
        setLines(reordered);

        // Persist to backend
        try {
            const order = reordered.map((l) => ({
                id: l.id,
                line_number: l.line_number,
            }));
            const response = await lineApi.reorder(sessionId, order);
            if (response.all_lines && response.all_lines.length > 0) {
                setLines(response.all_lines);
            }
            showSaved();
        } catch {
            toast.error('Reorder failed');
        }
    };

    // ── Version History ───────────────────────────────────────
    const handleOpenHistory = async (lineId: number) => {
        setHistoryPanelConfig({ isOpen: true, lineId });
        try {
            const res = await lineApi.getHistory(lineId);
            if (res.success) {
                setHistoryVersions(res.versions);
            }
        } catch (error) {
            toast.error('Failed to load version history');
        }
    };

    const handleRestoreVersion = async (versionId: number) => {
        if (!historyPanelConfig.lineId) return;
        try {
            const res = await lineApi.restoreVersion(historyPanelConfig.lineId, versionId);
            if (res.success) {
                // Update local state
                setLines(lines.map(l => l.id === res.line.id ? res.line : l));
                toast.success('Version restored!');
                setHistoryPanelConfig({ isOpen: false, lineId: null });
                showSaved();
            }
        } catch (error) {
            toast.error('Failed to restore version');
        }
    };

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            if (eventSourceRef.current) {
                eventSourceRef.current.close();
            }
            if (saveTimerRef.current) {
                clearTimeout(saveTimerRef.current);
            }
        };
    }, []);

    // ── Syllable target indicator ────────────────────────────
    const syllableStatus = useMemo(() => {
        if (!inputValue.trim()) return 'empty';
        if (syllableCount < syllableTarget.min) return 'under';
        if (syllableCount > syllableTarget.max) return 'over';
        return 'good';
    }, [syllableCount, syllableTarget, inputValue]);

    const useReorder = lines.length < VIRTUALIZATION_THRESHOLD && lines.length > 1;

    return (
        <div className="lyrics-editor">
            {/* ── Stats Bar ──────────────────────────────────── */}
            <div className="editor-stats-bar">
                <div className="stats-left">
                    <span className="stat-item">📝 {stats.totalLines} lines</span>
                    <span className="stat-item">💬 {stats.totalWords} words</span>
                    <span className="stat-item">🎵 {stats.totalSyllables} syllables</span>
                </div>
                <div className="stats-right">
                    {saveStatus === 'saving' && (
                        <span className="save-status saving">⏳ Saving...</span>
                    )}
                    {saveStatus === 'saved' && (
                        <span className="save-status saved">✅ Saved</span>
                    )}
                    <button
                        className="export-btn"
                        onClick={copyToClipboard}
                        title="Copy lyrics to clipboard"
                    >
                        📋 Copy
                    </button>
                    <button
                        className="export-btn"
                        onClick={exportAsText}
                        title="Download as .txt"
                    >
                        ⬇️ Export
                    </button>
                </div>
            </div>

            {/* ── Lines Container ────────────────────────────── */}
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
            ) : useReorder ? (
                <Reorder.Group
                    axis="y"
                    values={lines}
                    onReorder={handleReorder}
                    className="lines-container"
                >
                    {lines.map((line, index) => (
                        <Reorder.Item
                            key={line.id}
                            value={line}
                            className="reorder-item"
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            exit={{ opacity: 0, x: 20 }}
                            transition={{ duration: 0.2 }}
                            whileDrag={{
                                scale: 1.02,
                                boxShadow: '0 8px 25px rgba(0,0,0,0.15)',
                                zIndex: 50,
                            }}
                        >
                            <LineRow
                                line={line}
                                index={index}
                                sessionId={sessionId}
                                onOpenHistory={() => handleOpenHistory(line.id)}
                            />
                        </Reorder.Item>
                    ))}
                </Reorder.Group>
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
                                <LineRow
                                    line={line}
                                    index={index}
                                    sessionId={sessionId}
                                    onOpenHistory={() => handleOpenHistory(line.id)}
                                />
                            </motion.div>
                        ))}
                    </AnimatePresence>
                </div>
            )}

            {/* ── Input Area ─────────────────────────────────── */}
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

                {/* ── Syllable target guide ───────────────────── */}
                <div className="input-hints">
                    <div className="hints-left">
                        {ghostText && (
                            <span className="tab-hint">
                                Press <kbd>Tab</kbd> to accept
                            </span>
                        )}
                        {inputValue.trim() && (
                            <span className={`syllable-guide ${syllableStatus}`}>
                                {syllableCount} / {syllableTarget.min}–{syllableTarget.max} syl
                                {syllableStatus === 'good' && ' ✓'}
                                {syllableStatus === 'under' && ' (short)'}
                                {syllableStatus === 'over' && ' (long)'}
                            </span>
                        )}
                    </div>
                    <div className="hints-right" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <AdlibChip
                            sessionId={sessionId}
                            recentLines={lines.map(l => l.final_version || l.user_input)}
                            mood={lines.length > 5 ? 'energetic' : undefined}
                        />
                        <select
                            value={selectedFlow}
                            onChange={(e) => setSelectedFlow(e.target.value)}
                            style={{ background: 'var(--bg-panel)', color: 'var(--text-muted)', border: '1px solid var(--border-color)', borderRadius: 'var(--radius-sm)', padding: '0.2rem', fontSize: '0.75rem' }}
                        >
                            <option value="free">Free Flow</option>
                            {flowTemplates.map(t => (
                                <option key={t.id} value={t.id}>{t.name}</option>
                            ))}
                        </select>
                        <span className="bpm-hint">{bpm} BPM · {syllableTarget.label}</span>
                    </div>
                </div>

                <AnalysisStrip text={inputValue} rhymeScheme={rhymeScheme} />
            </div>

            <VersionHistory
                isOpen={historyPanelConfig.isOpen}
                onClose={() => setHistoryPanelConfig({ isOpen: false, lineId: null })}
                versions={historyVersions}
                onRestore={handleRestoreVersion}
                currentContent={lines.find(l => l.id === historyPanelConfig.lineId)?.user_input || ''}
            />
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
