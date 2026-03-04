import React, { useState, useCallback, useRef } from 'react';
import { nlpApi } from '../../services/api';
import type { AudioUploadAnalysisResponse } from '../../services/api';
import './AudioInfoCard.css';

interface AudioInfoCardProps {
    sessionId: number;
    onAnalysisComplete?: (data: AudioUploadAnalysisResponse) => void;
}

export const AudioInfoCard: React.FC<AudioInfoCardProps> = ({
    sessionId,
    onAnalysisComplete,
}) => {
    const [analysis, setAnalysis] = useState<AudioUploadAnalysisResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [dragging, setDragging] = useState(false);
    const fileRef = useRef<HTMLInputElement>(null);

    const handleFile = useCallback(async (file: File) => {
        if (!file) return;
        setLoading(true);
        try {
            const res = await nlpApi.uploadAndAnalyzeAudio(file, sessionId);
            setAnalysis(res);
            onAnalysisComplete?.(res);
        } catch (err) {
            console.error('Audio analysis failed:', err);
        } finally {
            setLoading(false);
        }
    }, [sessionId, onAnalysisComplete]);

    const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) handleFile(file);
    };

    const onDrop = (e: React.DragEvent) => {
        e.preventDefault();
        setDragging(false);
        const file = e.dataTransfer.files?.[0];
        if (file) handleFile(file);
    };

    const formatTime = (sec: number) => {
        const m = Math.floor(sec / 60);
        const s = Math.floor(sec % 60);
        return `${m}:${s.toString().padStart(2, '0')}`;
    };

    return (
        <div className="audio-info-card">
            <h3>🎵 Beat Analysis</h3>

            {!analysis && !loading && (
                <div
                    className={`audio-drop-zone ${dragging ? 'dragging' : ''}`}
                    onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
                    onDragLeave={() => setDragging(false)}
                    onDrop={onDrop}
                >
                    <input
                        ref={fileRef}
                        type="file"
                        accept="audio/*"
                        onChange={onFileChange}
                    />
                    <div className="drop-icon">🎧</div>
                    <div className="drop-text">Drop a beat or click to upload</div>
                    <div className="drop-hint">.wav, .mp3, .flac — auto-detects BPM & key</div>
                </div>
            )}

            {loading && (
                <div className="audio-loading">
                    <span className="spinner" />
                    Analyzing beat... detecting BPM, key, and structure
                </div>
            )}

            {analysis && (
                <>
                    <div className="audio-stats-grid">
                        <div className="audio-stat-item">
                            <div className="audio-stat-value">{Math.round(analysis.bpm)}</div>
                            <div className="audio-stat-label">BPM</div>
                        </div>
                        <div className="audio-stat-item">
                            <div className="audio-stat-value">
                                {analysis.key?.key}{analysis.key?.mode === 'minor' ? 'm' : ''}
                            </div>
                            <div className="audio-stat-label">
                                Key ({Math.round((analysis.key?.confidence ?? 0) * 100)}%)
                            </div>
                        </div>
                        <div className="audio-stat-item">
                            <div className="audio-stat-value">{analysis.syllables_per_bar}</div>
                            <div className="audio-stat-label">Syl / Bar</div>
                        </div>
                        <div className="audio-stat-item">
                            <div className="audio-stat-value">{analysis.sections?.length ?? 0}</div>
                            <div className="audio-stat-label">Sections</div>
                        </div>
                    </div>

                    {analysis.sections && analysis.sections.length > 0 && (
                        <div className="audio-sections-list">
                            {analysis.sections.map((sec, i) => (
                                <div key={i} className="audio-section-row">
                                    <span className="section-label">{sec.label}</span>
                                    <span className="section-time">
                                        {formatTime(sec.start_sec)} — {formatTime(sec.end_sec)}
                                    </span>
                                    <span className={`section-energy ${sec.energy}`}>
                                        {sec.energy}
                                    </span>
                                </div>
                            ))}
                        </div>
                    )}

                    <div
                        className="audio-drop-zone"
                        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
                        onDragLeave={() => setDragging(false)}
                        onDrop={onDrop}
                        style={{ padding: '0.75rem' }}
                    >
                        <input
                            ref={fileRef}
                            type="file"
                            accept="audio/*"
                            onChange={onFileChange}
                        />
                        <div className="drop-text" style={{ fontSize: '0.75rem' }}>
                            Drop another beat to re-analyze
                        </div>
                    </div>
                </>
            )}
        </div>
    );
};

export default AudioInfoCard;
