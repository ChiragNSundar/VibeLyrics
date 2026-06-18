import React, { useState, useEffect } from 'react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { toolApi, settingsApi, learningApi } from '../services/api';
import { toast } from 'react-hot-toast';
import { 
    BookOpen, BrainCircuit, Search, Plus, Trash2, 
    Sliders, Music, Upload, RefreshCw 
} from 'lucide-react';
import './LearningPage.css';

type TabId = 'vocabulary' | 'sandbox' | 'importer' | 'explorer';

export const LearningPage: React.FC = () => {
    const [activeTab, setActiveTab] = useState<TabId>('vocabulary');

    // === Tab 1: Vocabulary & Slang ===
    const [vocab, setVocab] = useState<{
        favorites: string[];
        banned: string[];
        slangs: string[];
    }>({ favorites: [], banned: [], slangs: [] });
    const [newWord, setNewWord] = useState('');
    const [wordCategory, setWordCategory] = useState<'favorite' | 'banned' | 'slang'>('favorite');
    const [vocabLoading, setVocabLoading] = useState(false);

    // === Tab 2: Phonetic Sandbox ===
    const [sandboxWord, setSandboxWord] = useState('');
    const [sandboxLang, setSandboxLang] = useState<'en' | 'hi' | 'kn'>('en');
    const [sandboxVowels, setSandboxVowels] = useState('');
    const [sandboxKey, setSandboxKey] = useState('');
    const [sandboxSyllables, setSandboxSyllables] = useState(1);
    const [sandboxIsSlang, setSandboxIsSlang] = useState(false);
    const [sandboxExtracted, setSandboxExtracted] = useState(false);
    const [sandboxLoading, setSandboxLoading] = useState(false);
    const [sandboxSaving, setSandboxSaving] = useState(false);

    // === Tab 3: Brain Feed & Importer ===
    const [docText, setDocText] = useState('');
    const [docFile, setDocFile] = useState<File | null>(null);
    const [audioFile, setAudioFile] = useState<File | null>(null);
    const [feedLoading, setFeedLoading] = useState(false);
    const [audioLoading, setAudioLoading] = useState(false);
    const [audioResult, setAudioResult] = useState<{ bpm: number; key: string; energy: string } | null>(null);

    // === Tab 4: Word Explorer ===
    const [explorerWord, setExplorerWord] = useState('');
    const [explorerResults, setExplorerResults] = useState<{
        perfect?: string[];
        near?: string[];
        synonyms?: string[];
    } | null>(null);
    const [explorerLoading, setExplorerLoading] = useState(false);

    // Load vocab lists on mount and tab switch
    const loadVocabulary = async () => {
        setVocabLoading(true);
        try {
            const res = await settingsApi.getSettings();
            if (res.success && res.profile) {
                // Parse database settings lists safely
                const favs = JSON.parse(res.profile.favorite_words || '[]');
                const bans = JSON.parse(res.profile.banned_words || '[]');
                const slgs = JSON.parse(res.profile.slang_preferences || '[]');
                setVocab({ favorites: favs, banned: bans, slangs: slgs });
            }
        } catch (err) {
            console.error('Failed to load vocabulary preferences:', err);
            toast.error('Failed to load vocabulary lists.');
        } finally {
            setVocabLoading(false);
        }
    };

    useEffect(() => {
        if (activeTab === 'vocabulary') {
            loadVocabulary();
        }
    }, [activeTab]);

    // Add vocabulary handler
    const handleAddVocab = async (e: React.FormEvent) => {
        e.preventDefault();
        const term = newWord.trim().toLowerCase();
        if (!term) return;

        try {
            const res = await settingsApi.addVocabulary(term, wordCategory);
            if (res.success) {
                toast.success(`Added "${term}" to ${wordCategory} list`);
                setNewWord('');
                loadVocabulary();
            } else {
                toast.error(res.error || 'Failed to add word');
            }
        } catch {
            toast.error('Network error. Failed to add word.');
        }
    };

    // Remove vocabulary handler
    const handleRemoveVocab = async (word: string, category: 'favorite' | 'banned' | 'slang') => {
        try {
            const res = await settingsApi.removeVocabulary(word, category);
            if (res.success) {
                toast.success(`Removed "${word}"`);
                loadVocabulary();
            }
        } catch {
            toast.error('Failed to delete word.');
        }
    };

    // Reset learning preferences handler
    const handleResetBrain = async () => {
        if (!window.confirm("Are you SURE you want to clear all learning preferences? Favorite/Banned/Slang words will be cleared.")) {
            return;
        }
        try {
            const res = await settingsApi.resetSettings();
            if (res.success) {
                toast.success("Vocabulary lists reset successfully.");
                loadVocabulary();
            }
        } catch {
            toast.error("Failed to reset vocabulary databases.");
        }
    };

    // === Tab 2 Handlers ===
    const handleSandboxExtract = async (e: React.FormEvent) => {
        e.preventDefault();
        const term = sandboxWord.trim();
        if (!term) return;

        setSandboxLoading(true);
        try {
            const res = await toolApi.extractPhonetics(term, sandboxLang);
            if (res.success) {
                setSandboxVowels(res.vowel_sequence);
                setSandboxKey(res.exact_key);
                setSandboxSyllables(res.syllable_count);
                setSandboxExtracted(true);
                toast.success('Phonetics extracted successfully.');
            } else {
                toast.error('Could not extract phonetics.');
            }
        } catch {
            toast.error('Failed to communicate with phonetic extractor.');
        } finally {
            setSandboxLoading(false);
        }
    };

    const handleSandboxSave = async () => {
        const term = sandboxWord.trim();
        if (!term || !sandboxVowels.trim() || !sandboxKey.trim()) {
            toast.error('Please lookup and fill all phonetic parameters.');
            return;
        }

        setSandboxSaving(true);
        try {
            const res = await toolApi.registerPhonetics({
                word: term,
                language: sandboxLang,
                vowel_sequence: sandboxVowels.trim(),
                exact_key: sandboxKey.trim(),
                syllable_count: sandboxSyllables,
                is_slang: sandboxIsSlang
            });
            if (res.success) {
                toast.success(res.message || `Saved overrides for "${term}"`);
                setSandboxWord('');
                setSandboxExtracted(false);
            } else {
                toast.error(res.error || 'Failed to save dictionary entry');
            }
        } catch {
            toast.error('Error saving overrides.');
        } finally {
            setSandboxSaving(false);
        }
    };

    // === Tab 3 Handlers ===
    const handleDocumentSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!docText.trim() && !docFile) {
            toast.error('Please paste text or select a file to import.');
            return;
        }

        setFeedLoading(true);
        try {
            const res = await learningApi.uploadDocument(docFile || undefined, docText || undefined);
            if (res.success) {
                toast.success(res.message || 'Brain learned document context successfully.');
                setDocText('');
                setDocFile(null);
            } else {
                toast.error('Failed to import document.');
            }
        } catch (err) {
            toast.error('Failed to feed document to AI brain.');
        } finally {
            setFeedLoading(false);
        }
    };

    const handleAudioSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!audioFile) {
            toast.error('Please drag & drop or select an audio beat.');
            return;
        }

        setAudioLoading(true);
        setAudioResult(null);
        try {
            const res = await learningApi.uploadAudio(audioFile);
            if (res.success) {
                setAudioResult({ bpm: res.bpm, key: res.key, energy: res.energy });
                toast.success(`Extracted BPM: ${res.bpm} | Key: ${res.key}`);
                setAudioFile(null);
            }
        } catch (err) {
            toast.error('Audio analysis failed. Ensure librosa is installed in global python.');
        } finally {
            setAudioLoading(false);
        }
    };

    // === Tab 4 Handlers ===
    const handleExplorerLookup = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!explorerWord.trim()) return;

        setExplorerLoading(true);
        try {
            const [rhymes, synonyms] = await Promise.all([
                toolApi.lookup(explorerWord, 'rhyme'),
                toolApi.lookup(explorerWord, 'synonym')
            ]);
            setExplorerResults({
                perfect: rhymes.results.perfect || [],
                near: rhymes.results.near || [],
                synonyms: synonyms.results.synonyms || []
            });
        } catch (error) {
            toast.error('Failed to look up word.');
        } finally {
            setExplorerLoading(false);
        }
    };

    return (
        <div className="learning-page">
            <header className="page-header">
                <h1>🧠 Interactive Seeding Center</h1>
                <p className="subtitle">Feed dictionaries, sandbox custom phonetics, and upload training materials to enhance the AI's learning.</p>
            </header>

            {/* Premium Tab Bar Selector */}
            <div className="cockpit-tabs-bar glass-card border border-white/5">
                <button
                    className={`tab-btn ${activeTab === 'vocabulary' ? 'active' : ''}`}
                    onClick={() => setActiveTab('vocabulary')}
                >
                    <BookOpen size={16} /> Vocabulary &amp; Slang
                </button>
                <button
                    className={`tab-btn ${activeTab === 'sandbox' ? 'active' : ''}`}
                    onClick={() => setActiveTab('sandbox')}
                >
                    <Sliders size={16} /> Phonetic Sandbox
                </button>
                <button
                    className={`tab-btn ${activeTab === 'importer' ? 'active' : ''}`}
                    onClick={() => setActiveTab('importer')}
                >
                    <BrainCircuit size={16} /> Brain Feed &amp; Importer
                </button>
                <button
                    className={`tab-btn ${activeTab === 'explorer' ? 'active' : ''}`}
                    onClick={() => setActiveTab('explorer')}
                >
                    <Search size={16} /> Word Explorer
                </button>
            </div>

            <div className="learning-content">
                {/* ==================== TAB 1: VOCABULARY & SLANG BUILDER ==================== */}
                {activeTab === 'vocabulary' && (
                    <Card className="cockpit-card glass" hover={false}>
                        <div className="cockpit-card-header">
                            <h2>🧠 Vocabulary &amp; Slang Preferences</h2>
                            <p className="description-text">Instruct the AI ghostwriter on terms to actively use (Favorites), avoid (Banned), or treat as hip-hop slangs.</p>
                        </div>

                        {/* Inline word adder */}
                        <form onSubmit={handleAddVocab} className="vocab-add-form">
                            <input
                                type="text"
                                className="input glass-input"
                                value={newWord}
                                onChange={(e) => setNewWord(e.target.value)}
                                placeholder="Type a word..."
                                required
                            />
                            <select
                                className="glass-select"
                                value={wordCategory}
                                onChange={(e) => setWordCategory(e.target.value as any)}
                            >
                                <option value="favorite">Favorite Word</option>
                                <option value="banned">Banned Word</option>
                                <option value="slang">Slang Word</option>
                            </select>
                            <Button type="submit" variant="primary">
                                <Plus size={16} /> Feed Word
                            </Button>
                        </form>

                        {vocabLoading ? (
                            <div className="loading-container">
                                <span className="pulse-dot"></span> Loading vocabulary data...
                            </div>
                        ) : (
                            <div className="vocabulary-columns">
                                {/* Favorites Column */}
                                <div className="vocab-col border border-white/5">
                                    <div className="col-header favorite">⭐️ Favorite Words</div>
                                    <div className="vocab-items-list">
                                        {vocab.favorites.length === 0 ? (
                                            <p className="empty-text">No favorites added</p>
                                        ) : (
                                            vocab.favorites.map((w) => (
                                                <div key={w} className="vocab-item glass-subcard">
                                                    <span>{w}</span>
                                                    <button onClick={() => handleRemoveVocab(w, 'favorite')} className="trash-btn" title="Delete">
                                                        <Trash2 size={13} />
                                                    </button>
                                                </div>
                                            ))
                                        )}
                                    </div>
                                </div>

                                {/* Banned Column */}
                                <div className="vocab-col border border-white/5">
                                    <div className="col-header banned">🚫 Banned Words</div>
                                    <div className="vocab-items-list">
                                        {vocab.banned.length === 0 ? (
                                            <p className="empty-text">No banned words</p>
                                        ) : (
                                            vocab.banned.map((w) => (
                                                <div key={w} className="vocab-item glass-subcard">
                                                    <span>{w}</span>
                                                    <button onClick={() => handleRemoveVocab(w, 'banned')} className="trash-btn" title="Delete">
                                                        <Trash2 size={13} />
                                                    </button>
                                                </div>
                                            ))
                                        )}
                                    </div>
                                </div>

                                {/* Slang Column */}
                                <div className="vocab-col border border-white/5">
                                    <div className="col-header slang">🔥 Slang Words</div>
                                    <div className="vocab-items-list">
                                        {vocab.slangs.length === 0 ? (
                                            <p className="empty-text">No slang preferences</p>
                                        ) : (
                                            vocab.slangs.map((w) => (
                                                <div key={w} className="vocab-item glass-subcard">
                                                    <span>{w}</span>
                                                    <button onClick={() => handleRemoveVocab(w, 'slang')} className="trash-btn" title="Delete">
                                                        <Trash2 size={13} />
                                                    </button>
                                                </div>
                                            ))
                                        )}
                                    </div>
                                </div>
                            </div>
                        )}

                        <div className="cockpit-footer border-t border-white/5">
                            <button onClick={handleResetBrain} className="reset-btn hover-glow">
                                <RefreshCw size={14} /> Reset Vocabulary Configuration
                            </button>
                        </div>
                    </Card>
                )}

                {/* ==================== TAB 2: PHONETIC SANDBOX ==================== */}
                {activeTab === 'sandbox' && (
                    <Card className="cockpit-card glass" hover={false}>
                        <div className="cockpit-card-header">
                            <h2>🎙️ Phonetic Dictionary Sandbox</h2>
                            <p className="description-text">Test the spelling rules of the G2P phonetic engine. If syllables or vowel mappings are incorrect, edit them here and save directly to local SQLite database.</p>
                        </div>

                        {/* Lookup Form */}
                        <form onSubmit={handleSandboxExtract} className="vocab-add-form font-sandbox">
                            <input
                                type="text"
                                className="input glass-input"
                                value={sandboxWord}
                                onChange={(e) => setSandboxWord(e.target.value)}
                                placeholder="Type a word (e.g., 'सपना', 'lyrics')..."
                                required
                            />
                            <select
                                className="glass-select"
                                value={sandboxLang}
                                onChange={(e) => setSandboxLang(e.target.value as any)}
                            >
                                <option value="en">English (EN)</option>
                                <option value="hi">Devanagari (Hindi)</option>
                                <option value="kn">Kannada (ಕನ್ನಡ)</option>
                            </select>
                            <Button type="submit" variant="primary" disabled={sandboxLoading}>
                                {sandboxLoading ? 'Analyzing...' : 'Analyze'}
                            </Button>
                        </form>

                        {sandboxExtracted && (
                            <div className="sandbox-results-panel glass-subcard border border-white/10">
                                <h3>📝 Phonetic Override for "{sandboxWord}"</h3>
                                
                                <div className="sandbox-grid">
                                    <div className="sandbox-field">
                                        <label>Syllable Count</label>
                                        <input
                                            type="number"
                                            className="input glass-input"
                                            value={sandboxSyllables}
                                            onChange={(e) => setSandboxSyllables(Math.max(1, parseInt(e.target.value) || 1))}
                                            min="1"
                                            max="20"
                                        />
                                    </div>

                                    <div className="sandbox-field">
                                        <label>Vowel Phonemes (hyphenated)</label>
                                        <input
                                            type="text"
                                            className="input glass-input"
                                            value={sandboxVowels}
                                            onChange={(e) => setSandboxVowels(e.target.value)}
                                            placeholder="e.g. aa-aa or EY1-OW0"
                                        />
                                    </div>

                                    <div className="sandbox-field">
                                        <label>Rhyme Key (Ending suffix)</label>
                                        <input
                                            type="text"
                                            className="input glass-input"
                                            value={sandboxKey}
                                            onChange={(e) => setSandboxKey(e.target.value)}
                                            placeholder="e.g. na or ow"
                                        />
                                    </div>

                                    <div className="sandbox-field checkbox-row">
                                        <label className="switch">
                                            <input
                                                type="checkbox"
                                                checked={sandboxIsSlang}
                                                onChange={(e) => setSandboxIsSlang(e.target.checked)}
                                            />
                                            <span className="slider round"></span>
                                        </label>
                                        <span className="checkbox-label">Treat as Slang Word</span>
                                    </div>
                                </div>

                                <div className="sandbox-actions">
                                    <Button onClick={handleSandboxSave} variant="primary" disabled={sandboxSaving}>
                                        {sandboxSaving ? 'Saving...' : '💾 Save to Local Dictionary'}
                                    </Button>
                                </div>
                            </div>
                        )}
                    </Card>
                )}

                {/* ==================== TAB 3: BRAIN FEED & IMPORTER ==================== */}
                {activeTab === 'importer' && (
                    <div className="cockpit-two-column">
                        {/* Document Importer */}
                        <Card className="cockpit-card glass" hover={false}>
                            <div className="cockpit-card-header">
                                <h2>📄 Document Importer</h2>
                                <p className="description-text">Upload lyrics sheets or past compositions in **PDF, DOCX, or TXT** format. VibeLyrics will parse the text and train the AI brain on your vocabulary usage.</p>
                            </div>

                            <form onSubmit={handleDocumentSubmit} className="feed-form">
                                <div className="text-area-section">
                                    <label>Paste Lyrics Text Directly</label>
                                    <textarea
                                        className="input textarea-lg"
                                        value={docText}
                                        onChange={(e) => setDocText(e.target.value)}
                                        placeholder="Paste your lyrics or notes here..."
                                    />
                                </div>

                                <div className="file-upload-section border border-dashed border-white/10">
                                    <Upload size={24} className="upload-icon" />
                                    <span className="upload-title">Or Choose a File (.txt, .pdf, .docx)</span>
                                    <input
                                        type="file"
                                        className="file-input-hidden"
                                        onChange={(e) => setDocFile(e.target.files ? e.target.files[0] : null)}
                                        accept=".txt,.pdf,.docx"
                                        id="doc-file-picker"
                                    />
                                    <label htmlFor="doc-file-picker" className="btn secondary-btn upload-btn">
                                        Select File
                                    </label>
                                    {docFile && <div className="selected-filename">Selected: {docFile.name}</div>}
                                </div>

                                <Button type="submit" variant="primary" disabled={feedLoading}>
                                    {feedLoading ? 'Processing file/text...' : '🚀 Train Brain from Document'}
                                </Button>
                            </form>
                        </Card>

                        {/* Beat Audio Analyzer */}
                        <Card className="cockpit-card glass" hover={false}>
                            <div className="cockpit-card-header">
                                <h2>🎵 Beat Audio Analyzer</h2>
                                <p className="description-text">Drag &amp; drop beat audio stems (.mp3 or .wav). VibeLyrics will extract BPM, musical keys, and register the optimal syllables for your metronome.</p>
                            </div>

                            <form onSubmit={handleAudioSubmit} className="feed-form">
                                <div className="file-upload-section border border-dashed border-white/10 select-audio">
                                    <Music size={24} className="upload-icon" />
                                    <span className="upload-title">Select Beat File (.mp3, .wav)</span>
                                    <input
                                        type="file"
                                        className="file-input-hidden"
                                        onChange={(e) => setAudioFile(e.target.files ? e.target.files[0] : null)}
                                        accept=".mp3,.wav"
                                        id="audio-file-picker"
                                    />
                                    <label htmlFor="audio-file-picker" className="btn secondary-btn upload-btn">
                                        Select Audio
                                    </label>
                                    {audioFile && <div className="selected-filename">Selected: {audioFile.name}</div>}
                                </div>

                                <Button type="submit" variant="primary" disabled={audioLoading}>
                                    {audioLoading ? 'Extracting BPM & Key...' : '⚡ Analyze Beat Audio'}
                                </Button>
                            </form>

                            {audioResult && (
                                <div className="audio-results-display glass-subcard border border-emerald-500/20">
                                    <h4>⚡ Beat Analysis Complete</h4>
                                    <div className="audio-metrics-grid">
                                        <div className="metric-cell">
                                            <span className="m-lbl">BPM</span>
                                            <span className="m-val text-primary">{audioResult.bpm}</span>
                                        </div>
                                        <div className="metric-cell">
                                            <span className="m-lbl">Estimated Key</span>
                                            <span className="m-val text-emerald">{audioResult.key}</span>
                                        </div>
                                        <div className="metric-cell">
                                            <span className="m-lbl">Energy Level</span>
                                            <span className="m-val text-purple">{audioResult.energy}</span>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </Card>
                    </div>
                )}

                {/* ==================== TAB 4: WORD EXPLORER ==================== */}
                {activeTab === 'explorer' && (
                    <Card className="lookup-card glass" hover={false}>
                        <div className="cockpit-card-header">
                            <h2>🔍 Offline Word Explorer</h2>
                            <p className="description-text">Enter any word to discover perfect rhymes, near rhymes, and semantic synonyms from the offline thesaurus dictionary.</p>
                        </div>

                        <form onSubmit={handleExplorerLookup} className="lookup-form">
                            <input
                                type="text"
                                value={explorerWord}
                                onChange={(e) => setExplorerWord(e.target.value)}
                                placeholder="Type a word to explore..."
                                className="input glass-input"
                            />
                            <Button type="submit" variant="primary" disabled={explorerLoading}>
                                {explorerLoading ? 'Searching...' : 'Explore'}
                            </Button>
                        </form>

                        {explorerResults && (
                            <div className="results-grid">
                                <div className="result-column glass-subcard">
                                    <h3>Perfect Rhymes</h3>
                                    <div className="tags">
                                        {explorerResults.perfect?.length ? (
                                            explorerResults.perfect.slice(0, 15).map(r => <span key={r} className="tag perfect">{r}</span>)
                                        ) : <p className="empty-text">No perfect rhymes</p>}
                                    </div>
                                </div>
                                <div className="result-column glass-subcard">
                                    <h3>Near Rhymes</h3>
                                    <div className="tags">
                                        {explorerResults.near?.length ? (
                                            explorerResults.near.slice(0, 15).map(r => <span key={r} className="tag near">{r}</span>)
                                        ) : <p className="empty-text">No near rhymes</p>}
                                    </div>
                                </div>
                                <div className="result-column glass-subcard">
                                    <h3>Synonyms</h3>
                                    <div className="tags">
                                        {explorerResults.synonyms?.length ? (
                                            explorerResults.synonyms.slice(0, 15).map(r => <span key={r} className="tag synonym">{r}</span>)
                                        ) : <p className="empty-text">No synonyms</p>}
                                    </div>
                                </div>
                            </div>
                        )}
                    </Card>
                )}
            </div>
        </div>
    );
};
