import { memo } from 'react';
import type { LyricLine } from '../../services/api';
import { LineRow } from './LineRow';

interface VirtualLineRowData {
    lines: LyricLine[];
    sessionId: number;
}

interface VirtualLineRowProps {
    index: number;
    style: React.CSSProperties;
    data: VirtualLineRowData;
}

/**
 * Virtualized wrapper for LineRow - used with react-window
 * Memoized for performance optimization
 */
export const VirtualLineRow = memo(({ index, style, data }: VirtualLineRowProps) => {
    const { lines, sessionId } = data;
    const line = lines[index];

    if (!line) return null;

    return (
        <div style={style}>
            <LineRow
                line={line}
                index={index}
                sessionId={sessionId}
            />
        </div>
    );
});

VirtualLineRow.displayName = 'VirtualLineRow';
