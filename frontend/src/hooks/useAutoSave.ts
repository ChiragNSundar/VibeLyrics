import { useState, useCallback, useRef, useEffect } from 'react';

interface AutoSaveOptions {
    delay?: number;
    onSave: (data: unknown) => Promise<void>;
    onError?: (error: Error) => void;
}

export function useAutoSave<T>({ delay = 2000, onSave, onError }: AutoSaveOptions) {
    const [isSaving, setIsSaving] = useState(false);
    const [lastSaved, setLastSaved] = useState<Date | null>(null);
    const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
    const timeoutRef = useRef<number | null>(null);

    const save = useCallback(async (data: T) => {
        if (timeoutRef.current) {
            clearTimeout(timeoutRef.current);
        }

        setHasUnsavedChanges(true);

        timeoutRef.current = setTimeout(async () => {
            try {
                setIsSaving(true);
                await onSave(data);
                setLastSaved(new Date());
                setHasUnsavedChanges(false);
            } catch (error) {
                if (onError) {
                    onError(error as Error);
                }
            } finally {
                setIsSaving(false);
            }
        }, delay);
    }, [delay, onSave, onError]);

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            if (timeoutRef.current) {
                clearTimeout(timeoutRef.current);
            }
        };
    }, []);

    // Save immediately without delay
    const saveNow = useCallback(async (data: T) => {
        if (timeoutRef.current) {
            clearTimeout(timeoutRef.current);
        }
        try {
            setIsSaving(true);
            await onSave(data);
            setLastSaved(new Date());
            setHasUnsavedChanges(false);
        } catch (error) {
            if (onError) {
                onError(error as Error);
            }
        } finally {
            setIsSaving(false);
        }
    }, [onSave, onError]);

    return {
        save,
        saveNow,
        isSaving,
        lastSaved,
        hasUnsavedChanges,
    };
}
