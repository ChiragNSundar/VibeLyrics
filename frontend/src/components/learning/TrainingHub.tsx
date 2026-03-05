import React, { useState, useEffect, useCallback, useRef } from 'react';
import { trainingApi } from '../../services/api';
import './TrainingHub.css';

interface DatasetStats {
    total_pairs: number;
    dpo_pairs: number;
    generated_at: string | null;
    sources: Record<string, number>;
    quality_stats: {
        total_lines: number;
        quality_passed: number;
        quality_filtered: number;
    };
    quality_threshold: number;
    feedback_stats: Record<string, number>;
}

interface TrainingPair {
    instruction: string;
    input: string;
    output: string;
    source: string;
}

interface DpoPair {
    prompt: string;
    chosen: string;
    rejected: string;
    feedback_type: string;
}

interface ExportFormat {
    id: string;
    name: string;
    description: string;
    extension: string;
}

interface LMModel {
    id: string;
    object: string;
    owned_by: string;
}

interface TrainingConfig {
    base_model: string;
    lora_rank: number;
    lora_alpha: number;
    epochs: number;
    learning_rate: number;
    batch_size: number;
    max_seq_length: number;
    warmup_steps: number;
    weight_decay: number;
    gradient_accumulation_steps: number;
    quantization: string;
    dataset_format: string;
    active_profile: string | null;
    enable_dpo: boolean;
    dpo_beta: number;
    quality_threshold: number;
    enable_rag: boolean;
}

interface PipelineStatus {
    state: string;
    progress: number;
    message: string;
    started_at: string | null;
    script_path?: string;
}

interface LoRAProfile {
    id: string;
    name: string;
    mood_tags: string[];
    bpm_range: number[];
    description: string;
}

interface FeedbackStats {
    suggestion_feedback: Record<string, number>;
    total_suggestions: number;
    accepted: number;
    rejected: number;
    dpo_pairs: number;
}

const FEEDBACK_TYPES = [
    { id: 'more_complex', label: '🧠 More Complex', color: '#6c5ce7' },
    { id: 'change_rhyme', label: '🎵 Change Rhyme', color: '#00b894' },
    { id: 'more_aggressive', label: '🔥 More Aggressive', color: '#e17055' },
    { id: 'fix_syllables', label: '🎯 Fix Syllables', color: '#fdcb6e' },
    { id: 'too_generic', label: '💤 Too Generic', color: '#636e72' },
    { id: 'off_topic', label: '🚫 Off Topic', color: '#d63031' },
    { id: 'better_wordplay', label: '✨ Better Wordplay', color: '#a29bfe' },
];

const TrainingHub: React.FC = () => {
    // Dataset state
    const [stats, setStats] = useState<DatasetStats | null>(null);
    const [preview, setPreview] = useState<TrainingPair[]>([]);
    const [dpoPreview, setDpoPreview] = useState<DpoPair[]>([]);
    const [formats, setFormats] = useState<ExportFormat[]>([]);
    const [generating, setGenerating] = useState(false);
    const [statusMsg, setStatusMsg] = useState('');

    // Import state
    const [importFile, setImportFile] = useState<File | null>(null);
    const [importing, setImporting] = useState(false);
    const [importMsg, setImportMsg] = useState('');

    // LM Studio state
    const [models, setModels] = useState<LMModel[]>([]);
    const [serverAvailable, setServerAvailable] = useState(false);
    const [config, setConfig] = useState<TrainingConfig | null>(null);
    const [pipeline, setPipeline] = useState<PipelineStatus | null>(null);
    const [startingTraining, setStartingTraining] = useState(false);

    // LoRA profiles
    const [profiles, setProfiles] = useState<LoRAProfile[]>([]);
    const [generatingProfile, setGeneratingProfile] = useState<string | null>(null);

    // Feedback stats
    const [feedbackStats, setFeedbackStats] = useState<FeedbackStats | null>(null);

    // Sub-tab
    const [activeSection, setActiveSection] = useState<
        'overview' | 'export' | 'import' | 'dpo' | 'profiles' | 'lmstudio'
    >('overview');

    const fileInputRef = useRef<HTMLInputElement>(null);

    // ── Fetch data on mount ──
    useEffect(() => {
        fetchStats();
        fetchFormats();
        fetchLMStudioInfo();
        fetchProfiles();
        fetchFeedbackStats();
    }, []);

    const fetchStats = async () => {
        try {
            const data = await trainingApi.getStatus();
            setStats(data);
        } catch (e) {
            console.error('Failed to fetch training status:', e);
        }
    };

    const fetchFormats = async () => {
        try {
            const data = await trainingApi.getFormats();
            setFormats(data.formats || []);
        } catch (e) {
            console.error('Failed to fetch formats:', e);
        }
    };

    const fetchLMStudioInfo = async () => {
        try {
            const [modelData, configData, statusData] = await Promise.all([
                trainingApi.getLMStudioModels(),
                trainingApi.getTrainingConfig(),
                trainingApi.getTrainingStatus(),
            ]);
            setModels(modelData.models || []);
            setServerAvailable(modelData.server_available || false);
            setConfig(configData.config || null);
            setPipeline(statusData);
        } catch (e) {
            console.error('Failed to fetch LM Studio info:', e);
        }
    };

    const fetchProfiles = async () => {
        try {
            const data = await trainingApi.getProfiles();
            setProfiles(data.profiles || []);
        } catch (e) {
            console.error('Failed to fetch profiles:', e);
        }
    };

    const fetchFeedbackStats = async () => {
        try {
            const data = await trainingApi.getFeedbackStats();
            setFeedbackStats(data);
        } catch (e) {
            console.error('Failed to fetch feedback stats:', e);
        }
    };

    // ── Actions ──
    const handleGenerate = async () => {
        setGenerating(true);
        setStatusMsg('');
        try {
            const threshold = config?.quality_threshold || 0;
            const rag = config?.enable_rag !== false;
            const data = await trainingApi.generate(threshold, rag);
            setStats(data);
            setStatusMsg(`✅ Generated ${data.total_pairs} SFT pairs + ${data.dpo_pairs} DPO pairs!`);
            const prev = await trainingApi.preview(10);
            setPreview(prev.pairs || []);
        } catch (e) {
            setStatusMsg('❌ Generation failed. Check backend logs.');
        } finally {
            setGenerating(false);
        }
    };

    const handleExport = async (format: string) => {
        try {
            const url = `/api/training/export?format=${format}`;
            const link = document.createElement('a');
            link.href = url;
            const ext = format === 'zip' ? 'zip' : format === 'dpo' ? 'json' : format === 'alpaca' ? 'json' : format === 'jsonl' ? 'jsonl' : 'txt';
            link.download = `vibelyrics_training_data.${ext}`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        } catch (e) {
            console.error('Export failed:', e);
        }
    };

    const handleImport = async () => {
        if (!importFile) return;
        setImporting(true);
        setImportMsg('');
        try {
            const data = await trainingApi.importDataset(importFile);
            setImportMsg(`✅ Imported ${data.imported} pairs (total imported: ${data.total_imported})`);
            setImportFile(null);
            if (fileInputRef.current) fileInputRef.current.value = '';
            fetchStats();
        } catch (e) {
            setImportMsg('❌ Import failed. Check file format.');
        } finally {
            setImporting(false);
        }
    };

    const handlePreview = async () => {
        try {
            const data = await trainingApi.preview(10);
            setPreview(data.pairs || []);
        } catch (e) {
            console.error('Preview failed:', e);
        }
    };

    const handleDpoPreview = async () => {
        try {
            const data = await trainingApi.previewDpo(10);
            setDpoPreview(data.pairs || []);
        } catch (e) {
            console.error('DPO preview failed:', e);
        }
    };

    const handleStartTraining = async (autoRun: boolean = false) => {
        setStartingTraining(true);
        try {
            const data = await trainingApi.startTraining(autoRun);
            setPipeline(data);
        } catch (e) {
            console.error('Start training failed:', e);
        } finally {
            setStartingTraining(false);
        }
    };

    const handleConfigChange = async (key: string, value: string | number | boolean) => {
        if (!config) return;
        const updated = { ...config, [key]: value };
        setConfig(updated);
        try {
            await trainingApi.setTrainingConfig({ [key]: value });
        } catch (e) {
            console.error('Config update failed:', e);
        }
    };

    const handleGenerateProfile = async (profileId: string) => {
        setGeneratingProfile(profileId);
        try {
            const data = await trainingApi.generateProfileDataset(profileId);
            setStatusMsg(`✅ Generated ${data.total_pairs} pairs for "${profileId}" profile.`);
        } catch (e) {
            setStatusMsg('❌ Profile dataset generation failed.');
        } finally {
            setGeneratingProfile(null);
        }
    };

    const maxSourceCount = stats?.sources
        ? Math.max(...Object.values(stats.sources), 1)
        : 1;

    return (
        <div className="training-hub">
            {/* Sub-navigation */}
            <div className="training-tabs">
                <button className={`training-tab ${activeSection === 'overview' ? 'active' : ''}`}
                    onClick={() => setActiveSection('overview')}>📊 Overview</button>
                <button className={`training-tab ${activeSection === 'export' ? 'active' : ''}`}
                    onClick={() => { setActiveSection('export'); handlePreview(); }}>📤 Export</button>
                <button className={`training-tab ${activeSection === 'import' ? 'active' : ''}`}
                    onClick={() => setActiveSection('import')}>📥 Import</button>
                <button className={`training-tab ${activeSection === 'dpo' ? 'active' : ''}`}
                    onClick={() => { setActiveSection('dpo'); handleDpoPreview(); fetchFeedbackStats(); }}>⚖️ DPO</button>
                <button className={`training-tab ${activeSection === 'profiles' ? 'active' : ''}`}
                    onClick={() => { setActiveSection('profiles'); fetchProfiles(); }}>🎭 LoRA Profiles</button>
                <button className={`training-tab ${activeSection === 'lmstudio' ? 'active' : ''}`}
                    onClick={() => { setActiveSection('lmstudio'); fetchLMStudioInfo(); }}>🧪 LM Studio</button>
            </div>

            {/* ── Overview Section ── */}
            {activeSection === 'overview' && (
                <div className="training-section">
                    <div className="section-header">
                        <h3>🗂️ Dataset Overview</h3>
                        <button className="btn primary" onClick={handleGenerate} disabled={generating}>
                            {generating ? '⏳ Generating...' : '🔄 Generate Dataset'}
                        </button>
                    </div>

                    {statusMsg && (
                        <div className={`training-alert ${statusMsg.includes('❌') ? 'error' : 'success'}`}>
                            {statusMsg}
                        </div>
                    )}

                    <div className="stats-grid-training">
                        <div className="stat-card">
                            <div className="stat-number">{stats?.total_pairs ?? 0}</div>
                            <div className="stat-label-training">SFT Pairs</div>
                        </div>
                        <div className="stat-card accent">
                            <div className="stat-number">{stats?.dpo_pairs ?? 0}</div>
                            <div className="stat-label-training">DPO Pairs</div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-number">
                                {stats?.sources ? Object.keys(stats.sources).length : 0}
                            </div>
                            <div className="stat-label-training">Data Sources</div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-number">
                                {stats?.generated_at
                                    ? new Date(stats.generated_at).toLocaleDateString()
                                    : 'Never'}
                            </div>
                            <div className="stat-label-training">Last Generated</div>
                        </div>
                    </div>

                    {/* Quality gate info */}
                    {stats?.quality_stats && stats.quality_stats.total_lines > 0 && (
                        <div className="quality-gate-info">
                            <h4>🎯 Quality Gate</h4>
                            <div className="quality-row">
                                <span>Threshold: {stats.quality_threshold || 'None (all lines)'}</span>
                                <span>{stats.quality_stats.quality_passed} passed / {stats.quality_stats.quality_filtered} filtered / {stats.quality_stats.total_lines} total</span>
                            </div>
                            <div className="source-bar-bg">
                                <div className="source-bar-fill quality-bar"
                                    style={{ width: `${(stats.quality_stats.quality_passed / Math.max(stats.quality_stats.total_lines, 1)) * 100}%` }} />
                            </div>
                        </div>
                    )}

                    {/* Source breakdown */}
                    {stats?.sources && Object.keys(stats.sources).length > 0 && (
                        <div className="source-breakdown">
                            <h4>Sources Breakdown</h4>
                            {Object.entries(stats.sources).map(([source, count]) => (
                                <div key={source} className="source-row">
                                    <span className="source-name">{source.replace(/_/g, ' ')}</span>
                                    <div className="source-bar-bg">
                                        <div className="source-bar-fill"
                                            style={{ width: `${(count / maxSourceCount) * 100}%` }} />
                                    </div>
                                    <span className="source-count">{count}</span>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}

            {/* ── Export Section ── */}
            {activeSection === 'export' && (
                <div className="training-section">
                    <h3>📤 Export Training Data</h3>
                    <p className="hint">Download your training dataset in various formats for fine-tuning.</p>

                    <div className="format-grid">
                        {formats.map(fmt => (
                            <div key={fmt.id} className="format-card">
                                <div className="format-header">
                                    <span className="format-name">{fmt.name}</span>
                                    <span className="format-ext">{fmt.extension}</span>
                                </div>
                                <p className="format-desc">{fmt.description}</p>
                                <button className="btn primary btn-sm" onClick={() => handleExport(fmt.id)}
                                    disabled={!stats?.total_pairs}>Download</button>
                            </div>
                        ))}
                    </div>

                    {preview.length > 0 && (
                        <div className="preview-section">
                            <h4>Preview (First 10 Pairs)</h4>
                            <div className="preview-list">
                                {preview.map((pair, i) => (
                                    <div key={i} className="preview-pair">
                                        <div className="preview-badge">{pair.source?.replace(/_/g, ' ')}</div>
                                        <div className="preview-field">
                                            <span className="field-label">Instruction:</span>
                                            <span className="field-value">{pair.instruction}</span>
                                        </div>
                                        {pair.input && (
                                            <div className="preview-field">
                                                <span className="field-label">Input:</span>
                                                <span className="field-value">{pair.input}</span>
                                            </div>
                                        )}
                                        <div className="preview-field">
                                            <span className="field-label">Output:</span>
                                            <span className="field-value output">{pair.output}</span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            )}

            {/* ── Import Section ── */}
            {activeSection === 'import' && (
                <div className="training-section">
                    <h3>📥 Import Training Data</h3>
                    <p className="hint">Import an external dataset in Alpaca JSON or ChatML JSONL format.</p>

                    <div className="import-zone">
                        <div className="drop-area"
                            onDragOver={e => { e.preventDefault(); e.currentTarget.classList.add('drag-over'); }}
                            onDragLeave={e => e.currentTarget.classList.remove('drag-over')}
                            onDrop={e => {
                                e.preventDefault();
                                e.currentTarget.classList.remove('drag-over');
                                const file = e.dataTransfer.files[0];
                                if (file) setImportFile(file);
                            }}>
                            <div className="drop-icon">📁</div>
                            <p>Drag & drop a .json or .jsonl file here</p>
                            <p className="or-text">— or —</p>
                            <label className="file-picker-btn">
                                Choose File
                                <input ref={fileInputRef} type="file" accept=".json,.jsonl"
                                    onChange={e => setImportFile(e.target.files?.[0] || null)} hidden />
                            </label>
                            {importFile && (
                                <div className="selected-file">
                                    📄 {importFile.name} ({(importFile.size / 1024).toFixed(1)} KB)
                                </div>
                            )}
                        </div>

                        <button className="btn primary" onClick={handleImport}
                            disabled={!importFile || importing}>
                            {importing ? '⏳ Importing...' : '📥 Import Dataset'}
                        </button>

                        {importMsg && (
                            <div className={`training-alert ${importMsg.includes('❌') ? 'error' : 'success'}`}>
                                {importMsg}
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* ── DPO Section ── */}
            {activeSection === 'dpo' && (
                <div className="training-section">
                    <h3>⚖️ DPO Preference Training</h3>
                    <p className="hint">
                        DPO teaches the model what <strong>not</strong> to write.
                        Reject an AI suggestion and write your own — that creates a preference pair.
                    </p>

                    {/* Feedback Stats */}
                    {feedbackStats && (
                        <div className="dpo-stats-grid">
                            <div className="stat-card">
                                <div className="stat-number">{feedbackStats.total_suggestions}</div>
                                <div className="stat-label-training">Total Suggestions</div>
                            </div>
                            <div className="stat-card green">
                                <div className="stat-number">{feedbackStats.accepted}</div>
                                <div className="stat-label-training">Accepted</div>
                            </div>
                            <div className="stat-card red">
                                <div className="stat-number">{feedbackStats.rejected}</div>
                                <div className="stat-label-training">Rejected</div>
                            </div>
                            <div className="stat-card accent">
                                <div className="stat-number">{feedbackStats.dpo_pairs}</div>
                                <div className="stat-label-training">DPO Pairs</div>
                            </div>
                        </div>
                    )}

                    {/* Feedback type breakdown */}
                    {feedbackStats?.suggestion_feedback && Object.keys(feedbackStats.suggestion_feedback).length > 0 && (
                        <div className="feedback-breakdown">
                            <h4>Feedback Breakdown</h4>
                            <div className="feedback-chips">
                                {FEEDBACK_TYPES.map(ft => {
                                    const count = feedbackStats.suggestion_feedback[ft.id] || 0;
                                    if (count === 0) return null;
                                    return (
                                        <div key={ft.id} className="feedback-chip"
                                            style={{ borderColor: ft.color }}>
                                            <span>{ft.label}</span>
                                            <span className="feedback-count" style={{ background: ft.color }}>{count}</span>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    )}

                    {/* DPO Preview */}
                    {dpoPreview.length > 0 && (
                        <div className="preview-section">
                            <h4>DPO Pairs Preview</h4>
                            <div className="preview-list">
                                {dpoPreview.map((pair, i) => (
                                    <div key={i} className="preview-pair dpo-pair">
                                        <div className="preview-badge">{pair.feedback_type}</div>
                                        <div className="preview-field">
                                            <span className="field-label">Prompt:</span>
                                            <span className="field-value">{pair.prompt}</span>
                                        </div>
                                        <div className="preview-field">
                                            <span className="field-label">✅ Chosen:</span>
                                            <span className="field-value output">{pair.chosen}</span>
                                        </div>
                                        <div className="preview-field">
                                            <span className="field-label">❌ Rejected:</span>
                                            <span className="field-value rejected">{pair.rejected}</span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {dpoPreview.length === 0 && (
                        <div className="empty-state">
                            <p>No DPO pairs yet. Reject AI suggestions and write your own lines to build preference data.</p>
                        </div>
                    )}
                </div>
            )}

            {/* ── LoRA Profiles Section ── */}
            {activeSection === 'profiles' && (
                <div className="training-section">
                    <h3>🎭 Multi-LoRA Profiles</h3>
                    <p className="hint">
                        Train separate LoRA adapters for different moods and genres.
                        VibeLyrics auto-selects the best LoRA based on session mood and BPM.
                    </p>

                    <div className="profiles-grid">
                        {profiles.map(profile => (
                            <div key={profile.id} className={`profile-card ${config?.active_profile === profile.id ? 'active-profile' : ''}`}>
                                <div className="profile-header">
                                    <span className="profile-name">{profile.name}</span>
                                    {config?.active_profile === profile.id && (
                                        <span className="active-badge">ACTIVE</span>
                                    )}
                                </div>
                                <p className="profile-desc">{profile.description}</p>
                                <div className="profile-tags">
                                    {profile.mood_tags.map(tag => (
                                        <span key={tag} className="mood-tag">{tag}</span>
                                    ))}
                                </div>
                                <div className="profile-bpm">
                                    BPM: {profile.bpm_range[0]} – {profile.bpm_range[1]}
                                </div>
                                <div className="profile-actions">
                                    <button className="btn primary btn-sm"
                                        onClick={() => handleGenerateProfile(profile.id)}
                                        disabled={generatingProfile === profile.id}>
                                        {generatingProfile === profile.id ? '⏳...' : '📦 Generate'}
                                    </button>
                                    <button className="btn btn-sm"
                                        onClick={() => handleConfigChange('active_profile', profile.id)}>
                                        {config?.active_profile === profile.id ? '✓ Selected' : 'Select'}
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>

                    {statusMsg && (
                        <div className={`training-alert ${statusMsg.includes('❌') ? 'error' : 'success'}`}>
                            {statusMsg}
                        </div>
                    )}
                </div>
            )}

            {/* ── LM Studio Section ── */}
            {activeSection === 'lmstudio' && (
                <div className="training-section">
                    <h3>🧪 LM Studio Training Pipeline</h3>

                    <div className="lm-server-status">
                        <span className={`status-dot ${serverAvailable ? 'online' : 'offline'}`} />
                        <span>LM Studio Server: {serverAvailable ? 'Online' : 'Offline'}</span>
                        {serverAvailable && <span className="model-count">{models.length} model(s)</span>}
                    </div>

                    {models.length > 0 && (
                        <div className="models-list">
                            <h4>Loaded Models</h4>
                            {models.map(m => (
                                <div key={m.id} className="model-item">
                                    <span className="model-id">{m.id}</span>
                                    <span className="model-owner">{m.owned_by}</span>
                                </div>
                            ))}
                        </div>
                    )}

                    {/* Training Config */}
                    {config && (
                        <div className="training-config">
                            <h4>Training Configuration</h4>
                            <div className="config-grid">
                                <div className="config-field">
                                    <label>Base Model</label>
                                    <input type="text" value={config.base_model}
                                        onChange={e => handleConfigChange('base_model', e.target.value)} />
                                </div>
                                <div className="config-field">
                                    <label>LoRA Rank</label>
                                    <input type="number" value={config.lora_rank}
                                        onChange={e => handleConfigChange('lora_rank', parseInt(e.target.value))} />
                                </div>
                                <div className="config-field">
                                    <label>Epochs</label>
                                    <input type="number" value={config.epochs}
                                        onChange={e => handleConfigChange('epochs', parseInt(e.target.value))} />
                                </div>
                                <div className="config-field">
                                    <label>Learning Rate</label>
                                    <input type="number" step="0.0001" value={config.learning_rate}
                                        onChange={e => handleConfigChange('learning_rate', parseFloat(e.target.value))} />
                                </div>
                                <div className="config-field">
                                    <label>Batch Size</label>
                                    <input type="number" value={config.batch_size}
                                        onChange={e => handleConfigChange('batch_size', parseInt(e.target.value))} />
                                </div>
                                <div className="config-field">
                                    <label>Quality Threshold</label>
                                    <input type="number" step="5" value={config.quality_threshold}
                                        onChange={e => handleConfigChange('quality_threshold', parseFloat(e.target.value))} />
                                </div>
                                <div className="config-field">
                                    <label>Quantization</label>
                                    <select value={config.quantization}
                                        onChange={e => handleConfigChange('quantization', e.target.value)}>
                                        <option value="4bit">4-bit (QLoRA)</option>
                                        <option value="8bit">8-bit</option>
                                        <option value="none">None (Full)</option>
                                    </select>
                                </div>
                                <div className="config-field">
                                    <label>Gradient Accum</label>
                                    <input type="number" value={config.gradient_accumulation_steps}
                                        onChange={e => handleConfigChange('gradient_accumulation_steps', parseInt(e.target.value))} />
                                </div>
                            </div>

                            {/* Toggle switches */}
                            <div className="config-toggles">
                                <label className="toggle-row">
                                    <input type="checkbox" checked={config.enable_dpo}
                                        onChange={e => handleConfigChange('enable_dpo', e.target.checked)} />
                                    <span>Enable DPO Phase</span>
                                    <span className="toggle-hint">Adds preference training after SFT</span>
                                </label>
                                <label className="toggle-row">
                                    <input type="checkbox" checked={config.enable_rag}
                                        onChange={e => handleConfigChange('enable_rag', e.target.checked)} />
                                    <span>Enable RAG Callbacks</span>
                                    <span className="toggle-hint">Generate self-referential lyric pairs</span>
                                </label>
                            </div>
                        </div>
                    )}

                    {/* Pipeline Control */}
                    <div className="pipeline-control">
                        <h4>Fine-Tuning Pipeline</h4>
                        <p className="hint">
                            Generates a training script with SFT{config?.enable_dpo ? ' + DPO' : ''}.
                            Converts to GGUF for LM Studio.
                        </p>

                        <div className="pipeline-buttons">
                            <button className="btn primary" onClick={() => handleStartTraining(false)}
                                disabled={startingTraining || !stats?.total_pairs}>
                                {startingTraining ? '⏳...' : '📝 Generate Script'}
                            </button>
                            <button className="btn accent" onClick={() => handleStartTraining(true)}
                                disabled={startingTraining || !stats?.total_pairs}>
                                {startingTraining ? '⏳...' : '🚀 Auto-Train'}
                            </button>
                        </div>

                        {pipeline && pipeline.state !== 'idle' && (
                            <div className="pipeline-status">
                                <div className="pipeline-progress-bar">
                                    <div className="pipeline-progress-fill"
                                        style={{ width: `${pipeline.progress}%` }} />
                                </div>
                                <div className="pipeline-info">
                                    <span className="pipeline-state">{pipeline.state}</span>
                                    <span className="pipeline-msg">{pipeline.message}</span>
                                </div>
                                {pipeline.script_path && (
                                    <div className="script-path">
                                        <strong>Script:</strong> <code>{pipeline.script_path}</code>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};

export default TrainingHub;
