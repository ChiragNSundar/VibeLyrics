import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Clock, RotateCcw } from 'lucide-react';
import type { LineVersion } from '../../services/api';

interface VersionHistoryProps {
    isOpen: boolean;
    onClose: () => void;
    versions: LineVersion[];
    onRestore: (versionId: number) => void;
    currentContent: string;
}

export const VersionHistory: React.FC<VersionHistoryProps> = ({
    isOpen,
    onClose,
    versions,
    onRestore,
    currentContent
}) => {
    return (
        <AnimatePresence>
            {isOpen && (
                <motion.div
                    className="version-history-panel"
                    initial={{ x: '100%', opacity: 0 }}
                    animate={{ x: 0, opacity: 1 }}
                    exit={{ x: '100%', opacity: 0 }}
                    transition={{ type: 'spring', damping: 25, stiffness: 200 }}
                    style={{
                        position: 'fixed',
                        right: 0,
                        top: 0,
                        bottom: 0,
                        width: '350px',
                        backgroundColor: 'var(--bg-panel)',
                        borderLeft: '1px solid var(--border-color)',
                        zIndex: 100,
                        padding: '1.5rem',
                        display: 'flex',
                        flexDirection: 'column',
                        boxShadow: '-4px 0 15px rgba(0,0,0,0.5)',
                        overflowY: 'auto'
                    }}
                >
                    <div className="panel-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                        <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', margin: 0 }}>
                            <Clock size={18} />
                            Line History
                        </h3>
                        <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
                            <X size={20} />
                        </button>
                    </div>

                    <div className="current-version" style={{ marginBottom: '2rem', padding: '1rem', background: 'var(--bg-elevated)', borderRadius: 'var(--radius-md)', border: '1px solid var(--primary-color)' }}>
                        <div style={{ fontSize: '0.75rem', color: 'var(--primary-color)', marginBottom: '0.5rem', fontWeight: 600 }}>CURRENT</div>
                        <div style={{ fontFamily: 'var(--font-mono)' }}>{currentContent || <em>Empty line</em>}</div>
                    </div>

                    <div className="versions-list" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                        {versions.length === 0 ? (
                            <div style={{ color: 'var(--text-muted)', textAlign: 'center', margin: '2rem 0' }}>
                                No previous versions found.
                            </div>
                        ) : (
                            versions.map((ver) => {
                                const date = new Date(ver.created_at);
                                const timeString = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
                                const dateString = date.toLocaleDateString();

                                return (
                                    <div key={ver.id} className="version-card" style={{
                                        padding: '1rem',
                                        background: 'var(--bg-hover)',
                                        borderRadius: 'var(--radius-md)',
                                        border: '1px solid var(--border-color)',
                                        position: 'relative'
                                    }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                                            <span>v{ver.version_number}</span>
                                            <span>{dateString} {timeString}</span>
                                        </div>
                                        <div style={{ fontFamily: 'var(--font-mono)', marginBottom: '1rem', textDecoration: 'line-through', opacity: 0.8 }}>
                                            {ver.content}
                                        </div>
                                        <button
                                            onClick={() => onRestore(ver.id)}
                                            className="btn btn-secondary"
                                            style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', padding: '0.4rem' }}
                                        >
                                            <RotateCcw size={14} /> Restore
                                        </button>
                                    </div>
                                );
                            })
                        )}
                    </div>
                </motion.div>
            )}
        </AnimatePresence>
    );
};
