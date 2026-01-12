/**
 * Session Store - Zustand
 * Global state management for the writing session
 */
import { create } from 'zustand';
import type { Session, LyricLine } from '../services/api';
import { lineApi } from '../services/api';

interface HistoryAction {
    type: 'add' | 'update' | 'delete';
    lineId: number | null;
    data: {
        text: string;
        oldText?: string;
        newText?: string;
        section?: string;
    };
}

interface SessionStore {
    // Session state
    currentSession: Session | null;
    lines: LyricLine[];
    isLoading: boolean;
    error: string | null;

    // UI state
    selectedLineId: number | null;
    ghostText: string;
    currentSection: string;

    // History for undo/redo
    history: HistoryAction[];
    future: HistoryAction[];
    maxHistorySize: number;

    // Actions
    setSession: (session: Session) => void;
    setLines: (lines: LyricLine[]) => void;
    addLine: (content: string, section?: string) => Promise<void>;
    updateLine: (lineId: number, content: string) => Promise<void>;
    deleteLine: (lineId: number) => Promise<void>;
    setGhostText: (text: string) => void;
    setSelectedLine: (lineId: number | null) => void;
    setCurrentSection: (section: string) => void;

    // History actions
    pushHistory: (action: HistoryAction) => void;
    undo: () => Promise<void>;
    redo: () => Promise<void>;

    // Reset
    reset: () => void;
}

export const useSessionStore = create<SessionStore>((set, get) => ({
    // Initial state
    currentSession: null,
    lines: [],
    isLoading: false,
    error: null,
    selectedLineId: null,
    ghostText: '',
    currentSection: 'Verse',
    history: [],
    future: [],
    maxHistorySize: 10,

    setSession: (session) => set({ currentSession: session }),

    setLines: (lines) => set({ lines }),

    addLine: async (content, section = 'Verse') => {
        const { currentSession, lines, pushHistory } = get();
        if (!currentSession) return;

        set({ isLoading: true });
        try {
            const response = await lineApi.add(currentSession.id, content, section);
            if (response.success) {
                set({ lines: [...lines, response.line] });
                pushHistory({
                    type: 'add',
                    lineId: response.line.id,
                    data: { text: content, section },
                });
            }
        } catch (error) {
            set({ error: (error as Error).message });
        } finally {
            set({ isLoading: false });
        }
    },

    updateLine: async (lineId, content) => {
        const { lines, pushHistory } = get();
        const oldLine = lines.find((l) => l.id === lineId);
        if (!oldLine) return;

        set({ isLoading: true });
        try {
            await lineApi.update(lineId, content);
            set({
                lines: lines.map((l) =>
                    l.id === lineId ? { ...l, user_input: content, final_version: content } : l
                ),
            });
            pushHistory({
                type: 'update',
                lineId,
                data: {
                    text: content,
                    oldText: oldLine.final_version || oldLine.user_input,
                    newText: content,
                },
            });
        } catch (error) {
            set({ error: (error as Error).message });
        } finally {
            set({ isLoading: false });
        }
    },

    deleteLine: async (lineId) => {
        const { lines, pushHistory } = get();
        const lineToDelete = lines.find((l) => l.id === lineId);
        if (!lineToDelete) return;

        set({ isLoading: true });
        try {
            await lineApi.delete(lineId);
            set({ lines: lines.filter((l) => l.id !== lineId) });
            pushHistory({
                type: 'delete',
                lineId,
                data: {
                    text: lineToDelete.final_version || lineToDelete.user_input,
                    section: lineToDelete.section,
                },
            });
        } catch (error) {
            set({ error: (error as Error).message });
        } finally {
            set({ isLoading: false });
        }
    },

    setGhostText: (text) => set({ ghostText: text }),

    setSelectedLine: (lineId) => set({ selectedLineId: lineId }),

    setCurrentSection: (section) => set({ currentSection: section }),

    pushHistory: (action) => {
        const { history, maxHistorySize } = get();
        const newHistory = [...history, action];
        if (newHistory.length > maxHistorySize) {
            newHistory.shift();
        }
        set({ history: newHistory, future: [] });
    },

    undo: async () => {
        const { history, future, lines, currentSession } = get();
        if (history.length === 0 || !currentSession) return;

        const action = history[history.length - 1];
        const newHistory = history.slice(0, -1);
        const newFuture = [...future, action];

        set({ history: newHistory, future: newFuture });

        // Perform undo action
        if (action.type === 'add' && action.lineId) {
            await lineApi.delete(action.lineId);
            set({ lines: lines.filter((l) => l.id !== action.lineId) });
        } else if (action.type === 'delete' && action.data.text) {
            const response = await lineApi.add(
                currentSession.id,
                action.data.text,
                action.data.section || 'Verse'
            );
            if (response.success) {
                set({ lines: [...lines, response.line] });
            }
        } else if (action.type === 'update' && action.lineId && action.data.oldText) {
            await lineApi.update(action.lineId, action.data.oldText);
            set({
                lines: lines.map((l) =>
                    l.id === action.lineId
                        ? { ...l, user_input: action.data.oldText!, final_version: action.data.oldText }
                        : l
                ),
            });
        }
    },

    redo: async () => {
        const { history, future, lines, currentSession } = get();
        if (future.length === 0 || !currentSession) return;

        const action = future[future.length - 1];
        const newFuture = future.slice(0, -1);
        const newHistory = [...history, action];

        set({ history: newHistory, future: newFuture });

        // Perform redo action
        if (action.type === 'add' && action.data.text) {
            const response = await lineApi.add(
                currentSession.id,
                action.data.text,
                action.data.section || 'Verse'
            );
            if (response.success) {
                set({ lines: [...lines, response.line] });
            }
        } else if (action.type === 'delete' && action.lineId) {
            await lineApi.delete(action.lineId);
            set({ lines: lines.filter((l) => l.id !== action.lineId) });
        } else if (action.type === 'update' && action.lineId && action.data.newText) {
            await lineApi.update(action.lineId, action.data.newText);
            set({
                lines: lines.map((l) =>
                    l.id === action.lineId
                        ? { ...l, user_input: action.data.newText!, final_version: action.data.newText }
                        : l
                ),
            });
        }
    },

    reset: () =>
        set({
            currentSession: null,
            lines: [],
            isLoading: false,
            error: null,
            selectedLineId: null,
            ghostText: '',
            currentSection: 'Verse',
            history: [],
            future: [],
        }),
}));
