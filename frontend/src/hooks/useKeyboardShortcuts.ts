import { useEffect, useCallback } from 'react';

interface ShortcutConfig {
    key: string;
    ctrlKey?: boolean;
    metaKey?: boolean;
    shiftKey?: boolean;
    action: () => void;
    description?: string;
}

export function useKeyboardShortcuts(shortcuts: ShortcutConfig[]) {
    const handleKeyDown = useCallback((event: KeyboardEvent) => {
        // Don't trigger shortcuts when typing in inputs
        const target = event.target as HTMLElement;
        if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.isContentEditable) {
            // Allow Escape in inputs
            if (event.key !== 'Escape') {
                return;
            }
        }

        for (const shortcut of shortcuts) {
            const ctrlOrMeta = shortcut.ctrlKey || shortcut.metaKey;
            const modifierMatch = ctrlOrMeta
                ? (event.ctrlKey || event.metaKey)
                : (!event.ctrlKey && !event.metaKey);

            const shiftMatch = shortcut.shiftKey ? event.shiftKey : !event.shiftKey;

            if (
                event.key.toLowerCase() === shortcut.key.toLowerCase() &&
                modifierMatch &&
                shiftMatch
            ) {
                event.preventDefault();
                shortcut.action();
                break;
            }
        }
    }, [shortcuts]);

    useEffect(() => {
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [handleKeyDown]);
}

// Common shortcut patterns
export const createNewSessionShortcut = (action: () => void): ShortcutConfig => ({
    key: 'n',
    ctrlKey: true,
    action,
    description: 'Create new session',
});

export const saveShortcut = (action: () => void): ShortcutConfig => ({
    key: 's',
    ctrlKey: true,
    action,
    description: 'Save',
});

export const escapeShortcut = (action: () => void): ShortcutConfig => ({
    key: 'Escape',
    action,
    description: 'Close / Cancel',
});
