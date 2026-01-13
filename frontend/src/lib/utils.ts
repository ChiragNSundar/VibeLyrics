import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Merge Tailwind CSS classes with proper conflict resolution
 * @param inputs - Class names to merge
 * @returns Merged class string
 */
export function cn(...inputs: ClassValue[]): string {
    return twMerge(clsx(inputs));
}

/**
 * Generate staggered animation delay classes
 * @param index - Item index
 * @param baseDelay - Base delay in ms (default: 100)
 * @returns CSS delay style object
 */
export function staggerDelay(index: number, baseDelay = 100): React.CSSProperties {
    return { animationDelay: `${index * baseDelay}ms` };
}
