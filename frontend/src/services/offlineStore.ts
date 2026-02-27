import { openDB, DBSchema, IDBPDatabase } from 'idb';
import { LyricLine, Session } from './api';

interface VibeLyricsDB extends DBSchema {
    sessions: {
        key: number;
        value: Session;
    };
    lines: {
        key: number;
        value: LyricLine;
        indexes: { 'by-session': number };
    };
    syncQueue: {
        key: number;
        value: {
            id?: number;
            type: 'ADD_LINE' | 'UPDATE_LINE' | 'DELETE_LINE' | 'UPDATE_SESSION';
            payload: any;
            timestamp: number;
        };
    };
}

let dbPromise: Promise<IDBPDatabase<VibeLyricsDB>> | null = null;

export const initDB = () => {
    if (!dbPromise) {
        dbPromise = openDB<VibeLyricsDB>('vibelyrics-store', 1, {
            upgrade(db) {
                db.createObjectStore('sessions', { keyPath: 'id' });

                const linesStore = db.createObjectStore('lines', { keyPath: 'id' });
                linesStore.createIndex('by-session', 'session_id');

                db.createObjectStore('syncQueue', { keyPath: 'id', autoIncrement: true });
            },
        });
    }
    return dbPromise;
};

export const offlineStore = {
    // ---- Sessions ----
    async saveSession(session: Session) {
        const db = await initDB();
        await db.put('sessions', session);
    },

    async getSession(id: number) {
        const db = await initDB();
        return db.get('sessions', id);
    },

    async getAllSessions() {
        const db = await initDB();
        return db.getAll('sessions');
    },

    // ---- Lines ----
    async saveLine(line: LyricLine) {
        const db = await initDB();
        await db.put('lines', line);
    },

    async getLinesForSession(sessionId: number) {
        const db = await initDB();
        return db.getAllFromIndex('lines', 'by-session', sessionId);
    },

    async deleteLine(id: number) {
        const db = await initDB();
        await db.delete('lines', id);
    },

    // ---- Sync Queue ----
    async enqueueSync(type: 'ADD_LINE' | 'UPDATE_LINE' | 'DELETE_LINE' | 'UPDATE_SESSION', payload: any) {
        const db = await initDB();
        await db.put('syncQueue', {
            type,
            payload,
            timestamp: Date.now()
        });

        // Try to trigger background sync if supported
        if ('serviceWorker' in navigator && 'SyncManager' in window) {
            try {
                const registration = await navigator.serviceWorker.ready;
                // @ts-ignore
                await registration.sync.register('sync-vibelyrics');
            } catch (err) {
                console.log('Background Sync not supported:', err);
            }
        }
    },

    async getSyncQueue() {
        const db = await initDB();
        return db.getAll('syncQueue');
    },

    async clearSyncItem(id: number) {
        const db = await initDB();
        await db.delete('syncQueue', id);
    }
};
