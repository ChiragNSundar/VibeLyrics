/**
 * Autocomplete Component
 * Displays AI-suggested text completion that appears as you type.
 * Press Tab to accept the suggestion.
 */
import React from 'react';
import './Autocomplete.css';

interface AutocompleteProps {
    /** The AI-suggested completion text */
    suggestion: string;
    /** Current user input value */
    inputValue: string;
    /** Whether the AI is currently streaming a suggestion */
    isStreaming: boolean;
}

export const Autocomplete: React.FC<AutocompleteProps> = ({
    suggestion,
    inputValue,
    isStreaming,
}) => {
    if (!suggestion && !isStreaming) return null;

    // Calculate the display text - shows the full line with user input + remaining suggestion
    let displayText = '';

    if (suggestion) {
        if (inputValue.length === 0) {
            // Show full suggestion when input is empty
            displayText = suggestion;
        } else if (suggestion.toLowerCase().startsWith(inputValue.toLowerCase())) {
            // Show user input + remaining suggestion (appears as inline completion)
            displayText = inputValue + suggestion.slice(inputValue.length);
        } else {
            // Suggestion doesn't match input - hide it
            return null;
        }
    }

    return (
        <span className={`autocomplete ${isStreaming ? 'streaming' : ''}`}>
            {isStreaming && !suggestion ? (
                <span className="autocomplete-loading">thinking...</span>
            ) : (
                displayText
            )}
        </span>
    );
};

// Re-export as GhostText for backwards compatibility
export { Autocomplete as GhostText };
