import React, { useState } from 'react';
import { aiApi } from '../../services/api';
import { Zap } from 'lucide-react';
import { Button } from '../ui/Button';
import { toast } from 'react-hot-toast';
import { motion, AnimatePresence } from 'framer-motion';

interface AdlibChipProps {
    sessionId: number;
    recentLines: string[];
    mood?: string;
}

export const AdlibChip: React.FC<AdlibChipProps> = ({ sessionId, recentLines, mood }) => {
    const [isLoading, setIsLoading] = useState(false);
    const [adlibs, setAdlibs] = useState<string[]>([]);
    const [isOpen, setIsOpen] = useState(false);

    const generateAdlibs = async () => {
        setIsLoading(true);
        try {
            const res = await aiApi.generateAdlibs(recentLines.slice(-4), mood);
            if (res.success && res.adlibs.length > 0) {
                setAdlibs(res.adlibs);
                setIsOpen(true);
            } else {
                toast.error('Could not generate adlibs');
            }
        } catch (error) {
            toast.error('Failed to suggest adlibs');
        } finally {
            setIsLoading(false);
        }
    };

    const copyAdlib = (text: string) => {
        navigator.clipboard.writeText(`(${text})`);
        toast.success(`Copied: (${text})`);
        setIsOpen(false);
    };

    return (
        <div style={{ position: 'relative', display: 'inline-flex' }}>
            <Button
                variant="secondary"
                size="sm"
                onClick={generateAdlibs}
                disabled={isLoading || recentLines.length === 0}
                style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', padding: '0.25rem 0.5rem', fontSize: '0.75rem', borderRadius: 'var(--radius-full)' }}
            >
                {isLoading ? <span className="spin">⏳</span> : <Zap size={14} className="text-accent" />}
                Adlibs
            </Button>

            <AnimatePresence>
                {isOpen && adlibs.length > 0 && (
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95, y: -10 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95, y: -10 }}
                        style={{
                            position: 'absolute',
                            bottom: '120%',
                            right: 0,
                            background: 'var(--bg-panel)',
                            border: '1px solid var(--border-color)',
                            borderRadius: 'var(--radius-md)',
                            padding: '0.5rem',
                            display: 'flex',
                            flexDirection: 'column',
                            gap: '0.25rem',
                            boxShadow: '0 4px 12px rgba(0,0,0,0.2)',
                            zIndex: 100,
                            minWidth: '120px'
                        }}
                    >
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: '0.25rem', textAlign: 'center' }}>
                            Click to copy
                        </div>
                        {adlibs.map((adlib, idx) => (
                            <button
                                key={idx}
                                onClick={() => copyAdlib(adlib)}
                                style={{
                                    background: 'var(--bg-hover)',
                                    color: 'var(--text-color)',
                                    border: 'none',
                                    padding: '0.4rem',
                                    borderRadius: 'var(--radius-sm)',
                                    fontSize: '0.8rem',
                                    cursor: 'pointer',
                                    textAlign: 'left',
                                    whiteSpace: 'nowrap'
                                }}
                                onMouseOver={(e) => e.currentTarget.style.background = 'var(--primary-color)'}
                                onMouseOut={(e) => e.currentTarget.style.background = 'var(--bg-hover)'}
                            >
                                ({adlib})
                            </button>
                        ))}
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};
