import React, { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'react-hot-toast';
import type { LyricLine, AddLineResponse } from '../../services/api';
import { lineApi } from '../../services/api';
import { useSessionStore } from '../../store/sessionStore';
import { Button } from '../ui/Button';
import './LineRow.css';

interface LineRowProps {
    line: LyricLine;
    index: number;
    sessionId: number;
    onOpenHistory?: () => void;
}

export const LineRow: React.FC<LineRowProps> = ({ line, onOpenHistory }) => {
    const { lines, setLines, setActiveRhymeWord, setActivePanel } = useSessionStore();
    const [isEditing, setIsEditing] = useState(false);
    const [editValue, setEditValue] = useState(line.final_version || line.user_input);
    const [isImproving, setIsImproving] = useState(false);
    const [isSaving, setIsSaving] = useState(false);
    const [showTimeline, setShowTimeline] = useState(false);

    // Local stress overrides: user can toggle individual syllable nodes
    const [stressOverrides, setStressOverrides] = useState<Record<number, string>>({});

    const handleTextClick = (e: React.MouseEvent<HTMLSpanElement>) => {
        const target = e.target as HTMLElement;
        let word = '';
        
        // If clicked target is a highlighting span inside the text
        if (target && target.tagName === 'SPAN' && target !== e.currentTarget) {
            word = target.textContent || '';
        } else {
            // Fallback: use getSelection range to extract clicked word
            const selection = window.getSelection();
            if (selection && selection.rangeCount > 0) {
                const range = selection.getRangeAt(0);
                const node = range.startContainer;
                const offset = range.startOffset;
                if (node.nodeType === Node.TEXT_NODE && node.textContent) {
                    const text = node.textContent;
                    let start = offset;
                    while (start > 0 && /[\w\u0900-\u097F\u0C80-\u0CFF]/.test(text[start - 1])) {
                        start--;
                    }
                    let end = offset;
                    while (end < text.length && /[\w\u0900-\u097F\u0C80-\u0CFF]/.test(text[end])) {
                        end++;
                    }
                    word = text.slice(start, end);
                }
            }
        }
        
        // Clean word from non-alpha characters (keeping Devanagari/Kannada letters)
        const cleanWord = word.replace(/[^\w\u0900-\u097F\u0C80-\u0CFF]/g, '').trim();
        if (cleanWord) {
            setActiveRhymeWord(cleanWord);
            setActivePanel('doppelreim');
        }
    };

    const handleEdit = () => {
        setIsEditing(true);
        setEditValue(line.final_version || line.user_input);
    };

    const handleSave = async () => {
        if (!editValue.trim()) return;

        setIsSaving(true);
        try {
            const response = await lineApi.update(line.id, editValue) as AddLineResponse;
            // Use all_lines if available for proper cross-line highlighting
            if (response.all_lines && response.all_lines.length > 0) {
                setLines(response.all_lines);
            } else {
                setLines(
                    lines.map((l) =>
                        l.id === line.id ? { ...l, user_input: editValue, final_version: editValue } : l
                    )
                );
            }
            setIsEditing(false);
            // Reset overrides on save since stress pattern may change
            setStressOverrides({});
            toast.success('Line updated');
        } catch (error) {
            toast.error('Failed to update line');
        } finally {
            setIsSaving(false);
        }
    };

    const handleCancel = () => {
        setIsEditing(false);
        setEditValue(line.final_version || line.user_input);
    };

    const handleDelete = async () => {
        if (!confirm('Delete this line?')) return;

        try {
            await lineApi.delete(line.id);
            setLines(lines.filter((l) => l.id !== line.id));
            toast.success('Line deleted');
        } catch (error) {
            toast.error('Failed to delete line');
        }
    };

    const handleImprove = async () => {
        setIsImproving(true);
        try {
            const response = await lineApi.improve(line.id, 'enhance');
            if (response.success && response.improved) {
                // Auto-save the improved version directly
                const saveResponse = await lineApi.update(line.id, response.improved) as AddLineResponse;
                if (saveResponse.all_lines && saveResponse.all_lines.length > 0) {
                    setLines(saveResponse.all_lines);
                } else {
                    setLines(
                        lines.map((l) =>
                            l.id === line.id
                                ? { ...l, user_input: response.improved!, final_version: response.improved }
                                : l
                        )
                    );
                }
                toast.success('✨ Lyric improved!');
            } else {
                toast.error(response.error || 'AI could not improve this line');
            }
        } catch (error) {
            toast.error('AI improvement failed');
        } finally {
            setIsImproving(false);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') {
            handleSave();
        } else if (e.key === 'Escape') {
            handleCancel();
        }
    };

    // ── Stress & Flow Timeline ──────────────────────────────────
    const rawPattern = line.stress_pattern || '';
    // Parse pattern into individual chars (strip spaces)
    const stressChars = rawPattern.replace(/\s/g, '').split('');

    const getDisplayChar = useCallback((idx: number, original: string) => {
        return stressOverrides[idx] || original;
    }, [stressOverrides]);

    const toggleStress = (idx: number) => {
        const current = getDisplayChar(idx, stressChars[idx] || 'x');
        const toggled = current === '/' ? 'x' : '/';
        setStressOverrides(prev => ({ ...prev, [idx]: toggled }));
    };

    // Get heatmap class based on density
    const heatmapClass = line.heatmap_class || '';

    return (
        <div
            className={`line-row ${heatmapClass}`}
            onMouseEnter={() => setShowTimeline(true)}
            onMouseLeave={() => setShowTimeline(false)}
        >
            <span className="line-number">{line.line_number}</span>

            <div className="line-content">
                {isEditing ? (
                    <input
                        type="text"
                        className="line-edit-input"
                        value={editValue}
                        onChange={(e) => setEditValue(e.target.value)}
                        onKeyDown={handleKeyDown}
                        autoFocus
                        disabled={isSaving}
                    />
                ) : (
                    <span
                        className="line-text highlightable-word"
                        onClick={handleTextClick}
                        style={{ cursor: 'pointer' }}
                        dangerouslySetInnerHTML={{
                            __html: line.highlighted_html || line.final_version || line.user_input,
                        }}
                    />
                )}

                <div className="line-meta">
                    <span className="syllable-count">{line.syllable_count} syl</span>
                    {line.has_internal_rhyme && (
                        <span className="rhyme-badge" title="Has internal rhyme">
                            🔗
                        </span>
                    )}
                    {line.complexity_score != null && line.complexity_score > 0 && (
                        <span
                            className={`complexity-badge ${line.complexity_score >= 60 ? 'high' : line.complexity_score >= 30 ? 'mid' : 'low'}`}
                            title={`Complexity: ${line.complexity_score}/100`}
                        >
                            {line.complexity_score >= 60 ? '🔥' : line.complexity_score >= 30 ? '📝' : '💡'}
                        </span>
                    )}
                    {rawPattern && (
                        <div className="stress-viz" title="Stress pattern">
                            {stressChars.map((char, i) => (
                                <span key={i} className={`stress-dot ${char === '/' ? 'primary' : 'unstressed'}`}>
                                    {char === '/' ? '●' : '○'}
                                </span>
                            ))}
                        </div>
                    )}
                </div>

                {/* ── Stress & Flow Timeline (appears on hover/focus) ── */}
                <AnimatePresence>
                    {showTimeline && stressChars.length > 0 && !isEditing && (
                        <motion.div
                            className="stress-flow-timeline"
                            initial={{ opacity: 0, height: 0, marginTop: 0 }}
                            animate={{ opacity: 1, height: 'auto', marginTop: 6 }}
                            exit={{ opacity: 0, height: 0, marginTop: 0 }}
                            transition={{ duration: 0.2, ease: 'easeOut' }}
                        >
                            <span className="timeline-label">Flow</span>
                            <div className="timeline-nodes">
                                {stressChars.map((char, idx) => {
                                    const display = getDisplayChar(idx, char);
                                    const isStressed = display === '/';
                                    const isOverridden = stressOverrides[idx] !== undefined;
                                    return (
                                        <motion.button
                                            key={idx}
                                            className={`timeline-node ${isStressed ? 'stressed' : 'unstressed'} ${isOverridden ? 'overridden' : ''}`}
                                            onClick={() => toggleStress(idx)}
                                            title={`Syllable ${idx + 1}: ${isStressed ? 'Stressed (Guru / /)' : 'Unstressed (Lagu / x)'} — click to toggle`}
                                            whileHover={{ scale: 1.2 }}
                                            whileTap={{ scale: 0.9 }}
                                        >
                                            {display}
                                        </motion.button>
                                    );
                                })}
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>

            <div className="line-actions">
                {isEditing ? (
                    <>
                        <Button variant="icon" onClick={handleSave} title="Save" disabled={isSaving}>
                            {isSaving ? '⏳' : '✓'}
                        </Button>
                        <Button variant="icon" onClick={handleCancel} title="Cancel">
                            ✕
                        </Button>
                    </>
                ) : (
                    <>
                        <Button variant="icon" onClick={handleEdit} title="Edit">
                            ✏️
                        </Button>
                        <Button variant="icon" onClick={handleImprove} title="AI Improve" disabled={isImproving}>
                            {isImproving ? '⏳' : '✨'}
                        </Button>
                        {onOpenHistory && (
                            <Button variant="icon" onClick={onOpenHistory} title="View History">
                                🕒
                            </Button>
                        )}
                        <Button variant="icon" className="delete-btn" onClick={handleDelete} title="Delete">
                            🗑️
                        </Button>
                    </>
                )}
            </div>
        </div>
    );
};
