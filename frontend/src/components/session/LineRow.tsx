import React, { useState } from 'react';
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
    const { lines, setLines } = useSessionStore();
    const [isEditing, setIsEditing] = useState(false);
    const [editValue, setEditValue] = useState(line.final_version || line.user_input);
    const [isImproving, setIsImproving] = useState(false);
    const [isSaving, setIsSaving] = useState(false);

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

    // Get heatmap class based on density
    const heatmapClass = line.heatmap_class || '';

    return (
        <div className={`line-row ${heatmapClass}`}>
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
                        className="line-text"
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
                    {line.stress_pattern && (
                        <div className="stress-viz" title="Stress pattern">
                            {line.stress_pattern.split('').map((char, i) => (
                                <span key={i} className={`stress-dot ${char === '/' ? 'primary' : 'unstressed'}`}>
                                    {char === '/' ? '●' : '○'}
                                </span>
                            ))}
                        </div>
                    )}
                </div>
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
