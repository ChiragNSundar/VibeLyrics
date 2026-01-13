/**
 * VibeLyrics - Shared TypeScript Types
 */

// ═══════════════════════════════════════════════════════════
// 📦 API RESPONSE TYPES
// ═══════════════════════════════════════════════════════════

export interface ApiResponse<T = unknown> {
    success: boolean;
    message?: string;
    error?: string;
    data?: T;
}

// ═══════════════════════════════════════════════════════════
// 🎵 SESSION TYPES
// ═══════════════════════════════════════════════════════════

export interface Session {
    id: number;
    title: string;
    bpm: number;
    mood?: string;
    theme?: string;
    beat_path?: string;
    line_count?: number;
    created_at: string;
    updated_at: string;
}

export interface CreateSessionRequest {
    title: string;
    bpm: number;
    mood?: string;
    theme?: string;
}

export interface SessionListResponse extends ApiResponse {
    sessions: Session[];
}

export interface SessionResponse extends ApiResponse {
    session: Session;
    lines: LyricLine[];
}

// ═══════════════════════════════════════════════════════════
// 📝 LYRIC LINE TYPES
// ═══════════════════════════════════════════════════════════

export interface LyricLine {
    id: number;
    session_id?: number;
    line_number: number;
    user_input: string;
    section: string;
    syllable_count?: number;
    stress_pattern?: string;
    rhyme_end?: string;
    has_internal_rhyme?: boolean;
    complexity_score?: number;
    created_at?: string;
}

export interface LineAddRequest {
    content: string;
    section?: string;
}

export interface LineResponse extends ApiResponse {
    line: LyricLine;
}

// ═══════════════════════════════════════════════════════════
// 🔍 RHYME & ANALYSIS TYPES
// ═══════════════════════════════════════════════════════════

export interface RhymeResult {
    perfect: string[];
    near: string[];
    slant: string[];
}

export interface ThesaurusResult {
    synonyms: string[];
    antonyms: string[];
    related: string[];
}

export interface StressAnalysis {
    pattern: string;
    syllables: number;
    stressed: number[];
    unstressed: number[];
}

// ═══════════════════════════════════════════════════════════
// 🤖 AI TYPES
// ═══════════════════════════════════════════════════════════

export type AIProvider = 'gemini' | 'openai' | 'lmstudio';

export interface AIHelpRequest {
    prompt: string;
    context?: string;
    session_id?: number;
}

export interface AIHelpResponse extends ApiResponse {
    response: string;
    provider: AIProvider;
}

export interface SuggestionRequest {
    session_id: number;
    current_line: string;
    context_lines?: string[];
}

// ═══════════════════════════════════════════════════════════
// 📓 JOURNAL TYPES
// ═══════════════════════════════════════════════════════════

export interface JournalEntry {
    id: number;
    content: string;
    mood?: string;
    created_at: string;
}

export interface JournalListResponse extends ApiResponse {
    entries: JournalEntry[];
}

// ═══════════════════════════════════════════════════════════
// ⚙️ USER SETTINGS TYPES
// ═══════════════════════════════════════════════════════════

export interface UserProfile {
    id: number;
    username: string;
    preferred_language: string;
    favorite_words: string[];
    banned_words: string[];
    slang_preferences: string[];
    created_at: string;
}

export interface UserSettingsResponse extends ApiResponse {
    profile: UserProfile;
}

// ═══════════════════════════════════════════════════════════
// 🎨 UI COMPONENT TYPES
// ═══════════════════════════════════════════════════════════

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger' | 'icon' | 'dreamy';
export type ButtonSize = 'sm' | 'md' | 'lg';

export type CardVariant = 'default' | 'glass' | 'glow' | 'holographic';

export interface AnimationConfig {
    duration?: number;
    delay?: number;
    easing?: string;
}
