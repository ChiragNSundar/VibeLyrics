"""
Correction Analyzer
Analyzes user corrections to AI suggestions to learn preferences
"""
from typing import Dict, List, Optional, Tuple
from collections import Counter
import re


class CorrectionAnalyzer:
    """
    Analyzes the difference between AI suggestions and user's final versions
    to extract learning signals for adaptive prompting.
    """
    
    # Reason codes for categorizing corrections
    REASON_SHORTER = "prefers_shorter"
    REASON_LONGER = "prefers_longer"
    REASON_SIMPLER = "prefers_simpler_words"
    REASON_COMPLEX = "prefers_complex_words"
    REASON_DIFFERENT_RHYME = "changed_rhyme"
    REASON_DIFFERENT_TOPIC = "changed_topic"
    REASON_STYLE_SHIFT = "style_shift"
    
    def __init__(self):
        # Word complexity heuristic (syllable count as proxy)
        self.simple_word_max_syllables = 2
    
    def analyze_correction(self, ai_suggestion: str, final_version: str) -> Dict:
        """
        Compare AI suggestion to user's final version and extract learning signals.
        
        Returns dict with:
        - correction_type: list of reason codes
        - word_replacements: dict of {old_word: new_word}
        - length_change: int (positive = longer, negative = shorter)
        - rhyme_changed: bool
        - insights: human-readable summary
        """
        if not ai_suggestion or not final_version:
            return {"correction_type": [], "insights": []}
        
        ai_words = self._extract_words(ai_suggestion)
        final_words = self._extract_words(final_version)
        
        correction_types = []
        insights = []
        
        # 1. Length preference
        length_diff = len(final_words) - len(ai_words)
        if length_diff <= -2:
            correction_types.append(self.REASON_SHORTER)
            insights.append(f"User shortened by {abs(length_diff)} words")
        elif length_diff >= 2:
            correction_types.append(self.REASON_LONGER)
            insights.append(f"User extended by {length_diff} words")
        
        # 2. Word complexity shift
        ai_complexity = self._avg_word_complexity(ai_words)
        final_complexity = self._avg_word_complexity(final_words)
        
        if final_complexity < ai_complexity - 0.5:
            correction_types.append(self.REASON_SIMPLER)
            insights.append("User prefers simpler vocabulary")
        elif final_complexity > ai_complexity + 0.5:
            correction_types.append(self.REASON_COMPLEX)
            insights.append("User prefers complex vocabulary")
        
        # 3. Detect word replacements (semantic shifts)
        replacements = self._find_replacements(ai_words, final_words)
        if replacements:
            correction_types.append(self.REASON_STYLE_SHIFT)
            for old, new in list(replacements.items())[:3]:
                insights.append(f"Replaced '{old}' → '{new}'")
        
        # 4. Rhyme change detection
        ai_end = ai_words[-1].lower() if ai_words else ""
        final_end = final_words[-1].lower() if final_words else ""
        rhyme_changed = ai_end != final_end and len(ai_end) > 2 and len(final_end) > 2
        
        if rhyme_changed:
            correction_types.append(self.REASON_DIFFERENT_RHYME)
            insights.append(f"Changed end rhyme: '{ai_end}' → '{final_end}'")
        
        return {
            "correction_type": correction_types,
            "word_replacements": replacements,
            "length_change": length_diff,
            "rhyme_changed": rhyme_changed,
            "ai_complexity": round(ai_complexity, 2),
            "final_complexity": round(final_complexity, 2),
            "insights": insights
        }
    
    def aggregate_learnings(self, corrections: List[Dict]) -> Dict:
        """
        Aggregate multiple correction analyses into actionable preferences.
        
        Returns preferences that should influence future prompts.
        """
        if not corrections:
            return {}
        
        type_counts = Counter()
        all_replacements = {}
        total_length_change = 0
        
        for c in corrections:
            for t in c.get("correction_type", []):
                type_counts[t] += 1
            all_replacements.update(c.get("word_replacements", {}))
            total_length_change += c.get("length_change", 0)
        
        # Build preferences based on patterns (need 3+ occurrences)
        preferences = []
        
        if type_counts.get(self.REASON_SHORTER, 0) >= 3:
            preferences.append("User prefers CONCISE lines. Keep suggestions under 10 words.")
        
        if type_counts.get(self.REASON_LONGER, 0) >= 3:
            preferences.append("User prefers DETAILED lines. Expand suggestions with imagery.")
        
        if type_counts.get(self.REASON_SIMPLER, 0) >= 3:
            preferences.append("User prefers SIMPLE vocabulary. Avoid complex/obscure words.")
        
        if type_counts.get(self.REASON_COMPLEX, 0) >= 3:
            preferences.append("User prefers ELEVATED vocabulary. Use sophisticated words.")
        
        # Track specific word avoidances
        avoided_words = list(all_replacements.keys())[:10]
        preferred_words = list(all_replacements.values())[:10]
        
        return {
            "preferences": preferences,
            "avoided_words": avoided_words,
            "preferred_words": preferred_words,
            "avg_length_preference": "shorter" if total_length_change < -5 else "longer" if total_length_change > 5 else "neutral"
        }
    
    def _extract_words(self, text: str) -> List[str]:
        """Extract words from text"""
        return [w for w in re.findall(r'\b\w+\b', text.lower()) if len(w) > 1]
    
    def _avg_word_complexity(self, words: List[str]) -> float:
        """Calculate average word complexity (syllable count as proxy)"""
        if not words:
            return 0
        
        def syllable_count(word):
            word = word.lower()
            count = len(re.findall(r'[aeiouy]+', word))
            return max(1, count)
        
        return sum(syllable_count(w) for w in words) / len(words)
    
    def _find_replacements(self, ai_words: List[str], final_words: List[str]) -> Dict[str, str]:
        """
        Find words that were replaced (simple positional heuristic).
        """
        replacements = {}
        ai_set = set(ai_words)
        final_set = set(final_words)
        
        removed = ai_set - final_set
        added = final_set - ai_set
        
        # Try to pair removed words with added words by position
        # This is a heuristic - not perfect but captures intent
        for old in list(removed)[:5]:
            for new in list(added)[:5]:
                # If they're similar length, might be a replacement
                if abs(len(old) - len(new)) <= 3:
                    replacements[old] = new
                    added.discard(new)
                    break
        
        return replacements


# Singleton instance
_correction_analyzer = None

def get_correction_analyzer() -> CorrectionAnalyzer:
    global _correction_analyzer
    if _correction_analyzer is None:
        _correction_analyzer = CorrectionAnalyzer()
    return _correction_analyzer
