"""
Shared Syllable Counting Utility
Canonical implementation used by all VibeLyrics services.
Always tries CMUDict first, then falls back to vowel-group heuristic.
"""
import re

try:
    import pronouncing
except ImportError:
    pronouncing = None


def count_syllables(word: str) -> int:
    """
    Count syllables in a single word.
    Strategy: CMUDict lookup → vowel-group heuristic fallback.
    """
    word = word.lower().strip().strip("'\".,!?;:-()[]")
    if not word:
        return 1

    # Try CMUDict first (most accurate)
    if pronouncing:
        clean = re.sub(r'[^a-z]', '', word)
        if clean:
            phones_list = pronouncing.phones_for_word(clean)
            if phones_list:
                return pronouncing.syllable_count(phones_list[0])

    # Fallback: vowel-group heuristic
    return _heuristic_syllables(word)


def _heuristic_syllables(word: str) -> int:
    """Estimate syllable count using vowel-group heuristic."""
    word = re.sub(r'[^a-z]', '', word.lower())
    if not word:
        return 1

    vowels = 'aeiouy'
    count = 0
    prev_vowel = False

    for char in word:
        is_vowel = char in vowels
        if is_vowel and not prev_vowel:
            count += 1
        prev_vowel = is_vowel

    # Adjust for silent 'e'
    if word.endswith('e') and count > 1:
        count -= 1

    return max(1, count)


def count_syllables_text(text: str) -> int:
    """Count total syllables across all words in a text string."""
    words = text.lower().split()
    total = 0
    for word in words:
        clean = re.sub(r'[^a-z]', '', word)
        if clean:
            total += count_syllables(clean)
    return total
