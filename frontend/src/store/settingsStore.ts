/**
 * Settings Store - Zustand
 * Global settings state shared across the entire app
 */
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type AIProvider = 'lmstudio' | 'gemini' | 'openai';

interface SettingsState {
    aiProvider: AIProvider;
    setAiProvider: (provider: AIProvider) => void;
    artistName: string;
    setArtistName: (name: string) => void;
    defaultBpm: number;
    setDefaultBpm: (bpm: number) => void;
}

export const useSettingsStore = create<SettingsState>()(
    persist(
        (set) => ({
            aiProvider: 'lmstudio',
            setAiProvider: (provider) => set({ aiProvider: provider }),
            artistName: '',
            setArtistName: (name) => set({ artistName: name }),
            defaultBpm: 140,
            setDefaultBpm: (bpm) => set({ defaultBpm: bpm }),
        }),
        {
            name: 'vibelyrics-settings', // persisted in localStorage
        }
    )
);
