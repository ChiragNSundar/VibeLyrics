/**
 * VibeLyrics API Service
 * Centralized API calls to Flask backend
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
        request<ApiResponse>(`/api/session/${id}/delete`, { method: 'POST' }),

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
        request<ApiResponse>(`/api/lines/${lineId}`, {
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

// Types
export interface Session {
    id: number;
    title: string;
    bpm: number;
    mood?: string;
    theme?: string;
    line_count: number;
    audio_path?: string;
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
