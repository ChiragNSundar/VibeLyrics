import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, Check, RefreshCw, Layers } from 'lucide-react';
import { aiApi } from '../../services/api';
import { Button } from '../ui/Button';
import { useSessionStore } from '../../store/sessionStore';
import { toast } from 'react-hot-toast';

interface HookGeneratorProps {
    sessionId: number;
    theme?: string;
    mood?: string;
}

export const HookGenerator: React.FC<HookGeneratorProps> = ({ sessionId, theme, mood }) => {
    const { lines, setLines, currentSession } = useSessionStore();
    const [isLoading, setIsLoading] = useState(false);
    const [hooks, setHooks] = useState<string[]>([]);
    const [customTheme, setCustomTheme] = useState(theme || '');

    const generateHooks = async () => {
        setIsLoading(true);
        try {
            // Get last 8 lines to give context
            const recentLines = lines.slice(-8).map(l => l.final_version || l.user_input);

            const res = await aiApi.generateHook(customTheme || 'general', mood, recentLines);
            if (res.success && res.hooks && res.hooks.length > 0) {
                setHooks(res.hooks);
                toast.success('Hooks generated!');
            } else {
                toast.error('Failed to generate hooks');
            }
        } catch (error) {
            toast.error('AI generation failed');
        } finally {
            setIsLoading(false);
        }
    };

    const applyHook = (hookText: string) => {
        const hookLines = hookText.split('\n').filter(l => l.trim() !== '');

        const newLines = hookLines.map((text, idx) => ({
            id: Date.now() + idx,
            line_number: lines.length + idx + 1,
            session_id: sessionId,
            user_input: text.trim(),
            final_version: text.trim(),
            section: 'Chorus',
            syllable_count: 0, // Simplified for immediate insertion
            has_internal_rhyme: false
        }));

        setLines([...lines, ...newLines as any]);
        toast.success('Hook added to session as Chorus');
    };

    return (
        <div className="hook-generator" style={{ background: 'var(--bg-elevated)', borderRadius: 'var(--radius-md)', padding: '1.25rem', border: '1px solid var(--border-color)', marginBottom: '1rem' }}>
            <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: 0, marginBottom: '1rem', fontSize: '1rem' }}>
                <Sparkles size={18} className="text-accent" />
                Auto-Hook Generator
            </h3>

            <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.5rem' }}>Theme/Topic (Optional)</label>
                <input
                    type="text"
                    value={customTheme}
                    onChange={(e) => setCustomTheme(e.target.value)}
                    placeholder="e.g. heartbreak, late night drive, winning..."
                    style={{ width: '100%', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)', background: 'var(--bg-input)', color: 'var(--text-color)' }}
                />
            </div>

            <Button
                variant="primary"
                onClick={generateHooks}
                disabled={isLoading}
                style={{ width: '100%', display: 'flex', justifyContent: 'center', gap: '0.5rem' }}
            >
                {isLoading ? <RefreshCw size={16} className="spin" /> : <Sparkles size={16} />}
                {isLoading ? 'Generating Hooks...' : 'Generate Hooks'}
            </Button>

            <AnimatePresence>
                {hooks.length > 0 && (
                    <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        style={{ marginTop: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}
                    >
                        <h4 style={{ fontSize: '0.85rem', color: 'var(--text-muted)', margin: 0 }}>Select a Hook:</h4>
                        {hooks.map((hook, idx) => (
                            <div key={idx} style={{
                                background: 'var(--bg-panel)',
                                padding: '1rem',
                                borderRadius: 'var(--radius-sm)',
                                border: '1px solid var(--primary-color)',
                                position: 'relative'
                            }}>
                                <pre style={{ fontFamily: 'var(--font-primary)', whiteSpace: 'pre-wrap', margin: 0, marginBottom: '1rem', fontSize: '0.9rem', lineHeight: 1.5 }}>
                                    {hook}
                                </pre>
                                <Button
                                    variant="secondary"
                                    size="sm"
                                    onClick={() => applyHook(hook)}
                                    style={{ width: '100%', display: 'flex', justifyContent: 'center', gap: '0.5rem' }}
                                >
                                    <Check size={14} /> Insert as Chorus
                                </Button>
                            </div>
                        ))}
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};
