
export interface ApiResponse<T = unknown> {
    success?: boolean;
    error?: string;
    [key: string]: T | boolean | string | undefined;
}

export interface Session {
    id: number;
    title: string;
    bpm: number;
    mood?: string;
    theme?: string;
    line_count: number;
    audio_path?: string;
    total_writing_seconds?: number;
    rhyme_scheme?: string;
    created_at: string;
    updated_at: string;
}

export interface LineVersion {
    id: number;
    line_id: number;
    content: string;
    version_number: number;
    created_at: string;
}

export interface LyricLine {
    id: number;
    line_number: number;
    user_input: string;
    final_version?: string;
    section: string;
    syllable_count: number;
    stress_pattern?: string;
    has_internal_rhyme: boolean;
    complexity_score?: number;
    highlighted_html?: string;
    heatmap_class?: string;
}

export interface CreateSessionData {
    title: string;
    bpm: number;
    mood?: string;
    theme?: string;
}

export interface AddLineResponse {
    success: boolean;
    line: LyricLine;
    all_lines?: LyricLine[];
}

export interface SuggestionResponse {
    success: boolean;
    result?: {
        suggestion?: string;
        improved?: string;
        explanation?: string;
        changes_made?: string[];
    };
    error?: string;
}

export interface AnalysisResult {
    complexity: {
        overall: number;
        dimensions: {
            internal_rhyme: number;
            vocabulary: number;
            diversity_score: number;
            vocabulary_diversity: number;
            rhyme_scheme: number;
        };
    };
    rhyme_scheme: string;
    improvement_suggestions: string[];
}

export interface LookupResponse {
    success: boolean;
    results: {
        perfect?: string[];
        near?: string[];
        synonyms?: string[];
    };
}

export interface ConceptRhymesResponse {
    success: boolean;
    results: Array<{ word: string; score: number }>;
}

export interface MultiRhymesResponse {
    success: boolean;
    results: string[];
}

// Advanced Feature Types
export interface PunchlineScoreResponse {
    success: boolean;
    score: number;
    techniques: string[];
    word_count: number;
    internal_rhymes: number;
    alliteration: number;
}

export interface AiPunchlineResponse {
    success: boolean;
    punchlines: Array<{ line: string; score: number; techniques: string[] }> | string[];
    source: string;
    theme?: string;
    mood?: string;
}

export interface MetaphorResponse {
    success: boolean;
    metaphors: string[];
    source: string;
    concept?: string;
}

export interface SimileResponse {
    success: boolean;
    similes: string[];
    source: string;
    word?: string;
}

export interface ContextualAdlibResponse {
    success: boolean;
    adlibs: string[];
    detected_tone: string;
    source: string;
    placements: Array<{
        position: number;
        after_word: string;
        suggested: string;
        type: string;
    }>;
}

export interface AudioSectionsResponse {
    success: boolean;
    bpm: number;
    key: { key: string; mode: string; confidence: number; label: string };
    sections: Array<{
        label: string;
        start_sec: number;
        end_sec: number;
        bars: number;
        energy: string;
    }>;
    total_sections: number;
}

export interface AudioAnalysisResponse {
    success: boolean;
    bpm: number;
    key: { key: string; mode: string; confidence: number; label: string };
    sections: Array<{ section: number; energy: number; level: string }>;
    waveform: number[];
}

export interface JournalEntry {
    id: number;
    content: string;
    mood: string;
    tags?: string[];
    themes?: string[];
    keywords?: string[];
    created_at: string;
}

export interface JournalSearchResponse {
    success: boolean;
    query: string;
    mode: string;
    results: Array<{
        entry_id: number;
        content: string;
        similarity: number;
        match_type: string;
        mood?: string;
        created_at?: string;
        matched_words?: string[];
    }>;
    total: number;
}

export interface VocabularyAgeResponse {
    success: boolean;
    evolution: Array<{
        session_id: number;
        date: string;
        grade_level: number;
        reading_level: string;
        unique_words: number;
        multisyllabic_pct: number;
        vocabulary_density: number;
        cumulative_unique_words: number;
        new_words_introduced: number;
        avg_syllables_per_word: number;
    }>;
    summary: {
        current_grade: number;
        current_level: string;
        average_grade: number;
        grade_trend: string;
        grade_change: number;
        total_unique_words: number;
        sessions_analyzed: number;
    };
}

export interface VocabularySessionResponse {
    success: boolean;
    session_id: number;
    session_title: string;
    total_words: number;
    unique_words: number;
    vocabulary_density: number;
    avg_word_length: number;
    avg_syllables_per_word: number;
    multisyllabic_count: number;
    multisyllabic_pct: number;
    flesch_kincaid_grade: number;
    reading_level: string;
}

export interface LearningStatusResponse {
    success: boolean;
    vocabulary: {
        favorites: string[];
        slangs: string[];
        most_used: string[];
        avoided: string[];
    };
    style: {
        themes: string[];
        rhyme_preference: string;
        avg_line_length: number;
    };
}
