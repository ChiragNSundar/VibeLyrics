import React, { useState } from 'react';
import { toast } from 'react-hot-toast';
import type { LyricLine } from '../../services/api';
import { lineApi } from '../../services/api';
import { useSessionStore } from '../../store/sessionStore';
import { Button } from '../ui/Button';
import './LineRow.css';

interface LineRowProps {
    line: LyricLine;
    index: number;
    sessionId: number;
}

export const LineRow: React.FC<LineRowProps> = ({ line }) => {
    const { lines, setLines } = useSessionStore();
    const [isEditing, setIsEditing] = useState(false);
    const [editValue, setEditValue] = useState(line.final_version || line.user_input);

    const handleEdit = () => {
        setIsEditing(true);
        setEditValue(line.final_version || line.user_input);
    };

    const handleSave = async () => {
        if (!editValue.trim()) return;

        try {
            await lineApi.update(line.id, editValue);
            setLines(
                lines.map((l) =>
                    l.id === line.id ? { ...l, user_input: editValue, final_version: editValue } : l
                )
            );
            setIsEditing(false);
            toast.success('Line updated');
        } catch (error) {
            toast.error('Failed to update line');
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
                        <Button variant="icon" onClick={handleSave} title="Save">
                            ✓
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
                        <Button variant="icon" onClick={() => { }} title="Improve">
                            ✨
                        </Button>
                        <Button variant="icon" className="delete-btn" onClick={handleDelete} title="Delete">
                            🗑️
                        </Button>
                    </>
                )}
            </div>
        </div>
    );
};
