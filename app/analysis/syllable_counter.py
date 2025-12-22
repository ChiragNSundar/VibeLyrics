"""
Syllable Counter
Accurate syllable counting for BPM synchronization
Uses CMU dictionary with rule-based fallback for unknown words
"""
import re
from typing import List, Optional
import pronouncing


class SyllableCounter:
    """Counts syllables in words and lines for BPM sync"""
    
    def __init__(self):
        # Patterns that indicate syllable additions/reductions
        self.silent_e_pattern = re.compile(r'[^aeiou]e$', re.IGNORECASE)
        self.vowel_pattern = re.compile(r'[aeiouy]+', re.IGNORECASE)
        
        # Common slang with known syllable counts
        self.slang_syllables = {
            "finna": 2,
            "gonna": 2,
            "wanna": 2,
            "gotta": 2,
            "tryna": 2,
            "ima": 2,
            "wassup": 2,
            "aight": 1,
            "dope": 1,
            "drip": 1,
            "lit": 1,
            "flex": 1,
            "vibe": 1,
            "vibin": 2,
            "vibes": 1,
            "yo": 1,
            "bruh": 1,
            "dawg": 1,
            "homie": 2,
            "homies": 2,
            "hunnid": 2,
            "bussin": 2,
            "cap": 1,
            "nocap": 2,
            "deadass": 2,
            "lowkey": 2,
            "highkey": 2,
            "fire": 1,  # Often pronounced as one syllable in rap
            "real": 1,
            "yeah": 1,
            "nah": 1,
            "aye": 1,
            "ayy": 1,
        }
    
    def count_word_syllables(self, word: str) -> int:
        """Count syllables in a single word"""
        word = word.lower().strip().strip(".,!?;:'\"")
        
        if not word:
            return 0
        
        # Check slang dictionary
        if word in self.slang_syllables:
            return self.slang_syllables[word]
        
        # Try CMU dictionary
        phones = pronouncing.phones_for_word(word)
        if phones:
            # Count vowel sounds (marked with stress numbers)
            first_pron = phones[0]
            syllables = len([p for p in first_pron.split() if any(c.isdigit() for c in p)])
            return syllables if syllables > 0 else 1
        
        # Fallback to rule-based counting
        return self._rule_based_count(word)
    
    def _rule_based_count(self, word: str) -> int:
        """Rule-based syllable counting for words not in dictionary"""
        word = word.lower()
        
        # Handle common endings
        word = re.sub(r"(?:ed|es)$", "", word)  # Remove silent endings
        
        # Count vowel groups
        vowel_groups = self.vowel_pattern.findall(word)
        count = len(vowel_groups)
        
        # Adjust for silent 'e'
        if self.silent_e_pattern.search(word):
            count -= 1
        
        # Adjust for 'le' endings (like "little" = 2 syllables)
        if word.endswith('le') and len(word) > 2 and word[-3] not in 'aeiou':
            count += 1
        
        # Minimum 1 syllable
        return max(1, count)
    
    def count_line_syllables(self, line: str) -> int:
        """Count total syllables in a line"""
        words = self._extract_words(line)
        return sum(self.count_word_syllables(word) for word in words)
    
    def _extract_words(self, line: str) -> List[str]:
        """Extract words from a line"""
        # Remove punctuation but keep apostrophes
        cleaned = re.sub(r"[^\w\s']", " ", line)
        words = cleaned.split()
        return [w.strip("'") for w in words if w.strip("'")]
    
    def get_line_breakdown(self, line: str) -> List[dict]:
        """Get syllable breakdown for each word in a line"""
        words = self._extract_words(line)
        return [
            {"word": word, "syllables": self.count_word_syllables(word)}
            for word in words
        ]
    
    def analyze_flow(self, line: str, target_syllables: Optional[int] = None) -> dict:
        """
        Analyze line flow based on syllables
        """
        breakdown = self.get_line_breakdown(line)
        total = sum(w["syllables"] for w in breakdown)
        
        result = {
            "total_syllables": total,
            "word_count": len(breakdown),
            "breakdown": breakdown,
            "avg_syllables_per_word": total / len(breakdown) if breakdown else 0
        }
        
        if target_syllables:
            diff = total - target_syllables
            result["target"] = target_syllables
            result["difference"] = diff
            if diff > 2:
                result["suggestion"] = "Line may be too dense for the beat, consider cutting words"
            elif diff < -2:
                result["suggestion"] = "Line has room for more content or longer words"
            else:
                result["suggestion"] = "Syllable count is on target"
        
        return result
    
    def suggest_syllable_target(self, bpm: int, flow_style: str = "regular") -> int:
        """
        Suggest target syllables per bar based on BPM and flow style
        
        Flow styles:
        - regular: Standard flow
        - double: Double time (twice as many syllables)
        - half: Half time (half as many)
        - triplet: Triplet flow (1.5x)
        """
        # Base calculation: syllables that fit in one bar (4 beats)
        # Average speaking rate: ~4-5 syllables per second
        bar_duration = (60 / bpm) * 4  # Duration of 1 bar in seconds
        base_syllables = int(bar_duration * 4.5)  # 4.5 syllables per second base
        
        multipliers = {
            "regular": 1.0,
            "double": 2.0,
            "half": 0.5,
            "triplet": 1.5
        }
        
        multiplier = multipliers.get(flow_style, 1.0)
        return int(base_syllables * multiplier)
