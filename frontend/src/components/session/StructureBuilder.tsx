import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Layers, Map, CheckCircle2 } from 'lucide-react';
import { aiApi } from '../../services/api';
import { Button } from '../ui/Button';
import { useSessionStore } from '../../store/sessionStore';
import { toast } from 'react-hot-toast';

interface StructureBuilderProps {
    sessionId: number;
    theme?: string;
    mood?: string;
    bpm?: number;
}

export const StructureBuilder: React.FC<StructureBuilderProps> = ({ sessionId, theme, mood, bpm }) => {
    const { lines, setLines } = useSessionStore();
    const [isLoading, setIsLoading] = useState(false);
    const [structure, setStructure] = useState<Array<{ section: string; bars: number; description: string; energy: string }> | null>(null);

    const generateStructure = async () => {
        setIsLoading(true);
        try {
            const res = await aiApi.generateStructure(theme || 'general', mood, bpm);
            if (res.success && res.sections) {
                setStructure(res.sections);
                toast.success(res.fallback ? 'Loaded default structure blueprint' : 'AI generated a custom blueprint!');
            } else {
                toast.error('Failed to generate structure');
            }
        } catch (error) {
            toast.error('AI generation failed');
        } finally {
            setIsLoading(false);
        }
    };

    const applyStructure = () => {
        if (!structure) return;

        if (lines.length > 0) {
            if (!confirm('This will append empty section headers to your current lyrics. Proceed?')) return;
        }

        const scaffoldLines: any[] = [];
        let currentLineNum = lines.length + 1;

        structure.forEach((block) => {
            // Add a header/marker line for the section
            scaffoldLines.push({
                id: Date.now() + currentLineNum,
                line_number: currentLineNum,
                session_id: sessionId,
                user_input: `[${block.section} - ${block.bars} Bars]`,
                final_version: `[${block.section} - ${block.bars} Bars]`,
                section: block.section,
                syllable_count: 0,
                has_internal_rhyme: false,
                heatmap_class: 'scaffold-marker'
            });
            currentLineNum++;

            // Add one empty line under it to start writing
            scaffoldLines.push({
                id: Date.now() + currentLineNum + 100,
                line_number: currentLineNum,
                session_id: sessionId,
                user_input: '',
                final_version: '',
                section: block.section,
                syllable_count: 0,
                has_internal_rhyme: false
            });
            currentLineNum++;
        });

        setLines([...lines, ...scaffoldLines]);
        toast.success('Structure scaffolded in editor');
    };

    const getEnergyColor = (energy: string) => {
        switch (energy.toLowerCase()) {
            case 'low': return 'var(--text-muted)';
            case 'medium': return 'var(--primary-color)';
            case 'high': return 'var(--accent-color)';
            case 'peak': return '#ff0000';
            default: return 'var(--primary-color)';
        }
    };

    return (
        <div className="structure-builder" style={{ background: 'var(--bg-elevated)', borderRadius: 'var(--radius-md)', padding: '1.25rem', border: '1px solid var(--border-color)', marginBottom: '1rem' }}>
            <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: 0, marginBottom: '1rem', fontSize: '1rem' }}>
                <Map size={18} className="text-primary" />
                Song Structure Blueprint
            </h3>

            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1.5rem' }}>
                Generate a full song arrangement tailored to your {bpm ? `${bpm} BPM` : ''} track.
            </p>

            {!structure ? (
                <Button
                    variant="primary"
                    onClick={generateStructure}
                    disabled={isLoading}
                    style={{ width: '100%' }}
                >
                    {isLoading ? 'Architecting...' : 'Build Blueprint'}
                </Button>
            ) : (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginBottom: '1.5rem' }}>
                        {structure.map((block, idx) => (
                            <div key={idx} style={{
                                display: 'flex',
                                borderLeft: `3px solid ${getEnergyColor(block.energy)}`,
                                background: 'var(--bg-panel)',
                                padding: '0.75rem 1rem',
                                borderRadius: '0 var(--radius-sm) var(--radius-sm) 0',
                            }}>
                                <div style={{ flex: 1 }}>
                                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                                        <strong style={{ fontSize: '0.9rem' }}>{block.section}</strong>
                                        <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', background: 'var(--bg-hover)', padding: '0.1rem 0.5rem', borderRadius: '10px' }}>
                                            {block.bars} Bars
                                        </span>
                                    </div>
                                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                                        {block.description}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>

                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                        <Button variant="secondary" onClick={generateStructure} disabled={isLoading} style={{ flex: 1 }}>
                            Regenerate
                        </Button>
                        <Button variant="primary" onClick={applyStructure} style={{ flex: 2, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
                            <Layers size={16} /> Scaffold in Editor
                        </Button>
                    </div>
                </motion.div>
            )}
        </div>
    );
};
