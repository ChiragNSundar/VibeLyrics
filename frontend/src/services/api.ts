/**
 * VibeLyrics API Service
 * Centralized API calls to FastAPI backend
 */

const BASE_URL = '';

interface ApiResponse<T = unknown> {
    success?: boolean;
    error?: string;
    [key: string]: T | boolean | string | undefined;
}

export async function request<T>(
    endpoint: string,
    options: RequestInit = {}
): Promise<T> {
    const response = await fetch(`${BASE_URL}${endpoint}`, {
        headers: {
            'Content-Type': 'application/json',
            ...options.headers,
        },
        ...options,
    });

    if (!response.ok) {
        throw new Error(`API Error: ${response.statusText}`);
    }

    return response.json();
}

// Session APIs
export const sessionApi = {
    getAll: () => request<{ sessions: Session[] }>('/api/sessions'),

    get: (id: number) => request<Session>(`/api/sessions/${id}`),

    create: (data: CreateSessionData) =>
        request<{ success: boolean; session: Session }>('/api/sessions', {
            method: 'POST',
            body: JSON.stringify(data),
        }),

    delete: (id: number) =>
        request<ApiResponse>(`/api/sessions/${id}`, { method: 'DELETE' }),

    analyze: (id: number) =>
        request<AnalysisResult>(`/api/session/${id}/analyze`),
};

// Line APIs
export const lineApi = {
    add: (sessionId: number, content: string, section: string = 'Verse') =>
        request<AddLineResponse>('/api/lines', {
            method: 'POST',
            body: JSON.stringify({ session_id: sessionId, content, section }),
        }),

    update: (lineId: number, content: string) =>
        request<AddLineResponse>(`/api/lines/${lineId}`, {
            method: 'PUT',
            body: JSON.stringify({ content }),
        }),

    delete: (lineId: number) =>
        request<ApiResponse>(`/api/lines/${lineId}`, {
            method: 'DELETE',
        }),

    suggest: (sessionId: number, action: string, currentLine?: string, improvementType?: string) =>
        request<SuggestionResponse>('/api/ai/suggest', {
            method: 'POST',
            body: JSON.stringify({
                session_id: sessionId,
                action,
                current_line: currentLine,
                improvement_type: improvementType,
            }),
        }),

    streamSuggestion: (sessionId: number, currentLine: string = ''): EventSource => {
        const url = `/api/lines/stream?session_id=${sessionId}&partial=${encodeURIComponent(currentLine)}`;
        return new EventSource(url);
    },

    improve: (lineId: number, improvementType: string = 'enhance') =>
        request<{ success: boolean; improved?: string; original?: string; error?: string }>('/api/ai/improve', {
            method: 'POST',
            body: JSON.stringify({ line_id: lineId, improvement_type: improvementType }),
        }),

    reorder: (sessionId: number, order: { id: number; line_number: number }[]) =>
        request<AddLineResponse>('/api/lines/reorder', {
            method: 'POST',
            body: JSON.stringify({ session_id: sessionId, order }),
        }),
};

// Tool APIs
export const toolApi = {
    lookup: (word: string, type: 'rhyme' | 'synonym') =>
        request<LookupResponse>('/api/thesaurus/lookup', {
            method: 'POST',
            body: JSON.stringify({
                word,
                include_rhymes: type === 'rhyme',
                include_synonyms: type === 'synonym'
            })
        }),

    getConceptRhymes: (word: string) =>
        request<ConceptRhymesResponse>(`/api/concept-rhymes/${encodeURIComponent(word)}`),

    getMultiRhymes: (word: string) =>
        request<MultiRhymesResponse>(`/api/multi-rhymes/${encodeURIComponent(word)}`),
};

// AI APIs
export const aiApi = {
    ask: (question: string, sessionId: number) =>
        request<{ success: boolean; answer: string }>('/api/ask', {
            method: 'POST',
            body: JSON.stringify({ question, session_id: sessionId }),
        }),

    switchProvider: (provider: string) =>
        request<ApiResponse>('/api/provider/switch', {
            method: 'POST',
            body: JSON.stringify({ provider }),
        }),
};

// ============ Advanced Feature APIs ============

export const advancedApi = {
    // Punchlines
    scorePunchline: (line: string) =>
        request<PunchlineScoreResponse>('/api/punchline/score', {
            method: 'POST',
            body: JSON.stringify({ line }),
        }),

    generateAiPunchlines: (theme: string, sessionId?: number, mood?: string, count: number = 5) =>
        request<AiPunchlineResponse>('/api/punchline/ai-generate', {
            method: 'POST',
            body: JSON.stringify({ theme, session_id: sessionId, mood, count }),
        }),

    // Metaphors & Similes
    generateMetaphors: (concept: string, count: number = 5, sessionId?: number) =>
        request<MetaphorResponse>('/api/metaphor/generate', {
            method: 'POST',
            body: JSON.stringify({ concept, count, session_id: sessionId }),
        }),

    generateSimiles: (word: string, count: number = 5, sessionId?: number) =>
        request<SimileResponse>('/api/simile/generate', {
            method: 'POST',
            body: JSON.stringify({ word, count, session_id: sessionId }),
        }),

    // Contextual Adlibs
    generateContextualAdlibs: (line: string, mood?: string, artistStyle?: string, recentLines: string[] = [], useAi: boolean = false) =>
        request<ContextualAdlibResponse>('/api/adlibs/contextual', {
            method: 'POST',
            body: JSON.stringify({
                line,
                mood,
                artist_style: artistStyle,
                recent_lines: recentLines,
                use_ai: useAi
            }),
        }),

    getArtistStyles: () =>
        request<{ success: boolean; styles: string[] }>('/api/adlibs/artist-styles'),

    // Audio Analysis
    getAudioSections: (filename: string) =>
        request<AudioSectionsResponse>(`/api/audio/sections/${encodeURIComponent(filename)}`),

    analyzeAudio: (filename: string) =>
        request<AudioAnalysisResponse>(`/api/audio/analyze/${encodeURIComponent(filename)}`),

    getSectionWaveform: (filename: string, start: number, end: number) =>
        request<{ success: boolean; waveform: number[] }>(`/api/audio/section-waveform/${encodeURIComponent(filename)}?start=${start}&end=${end}`),
};

// Journal APIs
export const journalApi = {
    create: (content: string, mood: string = 'Neutral', tags: string[] = []) =>
        request<{ success: boolean; entry: JournalEntry }>('/api/journal', {
            method: 'POST',
            body: JSON.stringify({ content, mood, tags }),
        }),

    list: (limit: number = 10) =>
        request<{ success: boolean; entries: JournalEntry[] }>(`/api/journal?limit=${limit}`),

    search: (query: string, mode: string = 'auto', topK: number = 5) =>
        request<JournalSearchResponse>(`/api/journal/search?q=${encodeURIComponent(query)}&mode=${mode}&top_k=${topK}`),

    reindex: () =>
        request<{ success: boolean; total: number }>('/api/journal/reindex', { method: 'POST' }),
};

// Vocabulary APIs
export const vocabularyApi = {
    getAge: () =>
        request<VocabularyAgeResponse>('/api/vocabulary/age'),

    getSession: (sessionId: number) =>
        request<VocabularySessionResponse>(`/api/vocabulary/session/${sessionId}`),
};

export const learningApi = {
    getStatus: () =>
        request<LearningStatusResponse>('/api/learning/status'),

    // We no longer use POST for scrape because we stream it via SSE GET request.
    // However, if we needed a fallback:
    scrapeArtist: (artist: string, maxSongs: number = 3, era?: string) =>
        request<{ success: boolean; message: string }>('/api/learning/scrape', {
            method: 'POST',
            body: JSON.stringify({ artist, max_songs: maxSongs, era }),
        }),

    uploadDocument: (file?: File, text?: string) => {
        const formData = new FormData();
        if (file) formData.append('file', file);
        if (text) formData.append('text', text);

        return request<{ success: boolean; message: string; lines_parsed: number; words_parsed: number }>('/api/learning/upload', {
            method: 'POST',
            body: formData,
            // Don't set Content-Type header so browser sets it with appropriate boundary for FormData
        });
    },

    deleteVocabulary: (word: string, listType: 'favorites' | 'slangs' | 'avoided' | 'most_used') =>
        request<{ success: boolean; message: string }>(`/api/learning/vocabulary?word=${encodeURIComponent(word)}&list_type=${listType}`, {
            method: 'DELETE',
        }),

    resetBrain: () =>
        request<{ success: boolean; message: string }>('/api/learning/reset', {
            method: 'POST',
        }),

    getBrainMap: () =>
        request<{ success: boolean; nodes: Array<{ id: string; val: number; category: string; frequency: number }>; links: Array<{ source: string; target: string; value: number }> }>('/api/learning/brain-map'),

    getDna: () =>
        request<{ success: boolean; axes: Array<{ axis: string; value: number }> }>('/api/learning/dna'),

    getAnnotations: () =>
        request<{ success: boolean; annotations: Array<{ line: string; score: number; techniques: string[]; notes: string[] }>; message?: string }>('/api/learning/annotations'),

    uploadAudio: (file: File) => {
        const formData = new FormData();
        formData.append('file', file);
        return request<{ success: boolean; bpm: number; key: string; energy: string; avg_rms: number }>('/api/learning/audio', {
            method: 'POST',
            body: formData,
        });
    },
};

// ============ Types ============

export interface Session {
    id: number;
    title: string;
    bpm: number;
    mood?: string;
    theme?: string;
    line_count: number;
    audio_path?: string;
    rhyme_scheme?: string;
    created_at: string;
    updated_at: string;
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
