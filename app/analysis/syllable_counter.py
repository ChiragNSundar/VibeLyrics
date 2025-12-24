"""
Syllable Counter
Accurate syllable counting for BPM synchronization
Uses CMU dictionary with rule-based fallback for unknown words
Supports romanized Hindi/Kannada (typed in English)
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
        
        # Romanized Indian language vowel patterns
        # Long vowels: aa, ee, ii, oo, uu, ai, au, ei, ou
        # Short vowels: a, e, i, o, u
        self.indian_vowel_pattern = re.compile(
            r'(aa|ee|ii|oo|uu|ai|au|ei|ou|ae|a|e|i|o|u)', 
            re.IGNORECASE
        )
        
        # Common slang with known syllable counts (English)
        self.slang_syllables = {
            "finna": 2, "gonna": 2, "wanna": 2, "gotta": 2,
            "tryna": 2, "ima": 2, "wassup": 2, "aight": 1,
            "dope": 1, "drip": 1, "lit": 1, "flex": 1,
            "vibe": 1, "vibin": 2, "vibes": 1, "yo": 1,
            "bruh": 1, "dawg": 1, "homie": 2, "homies": 2,
            "hunnid": 2, "bussin": 2, "cap": 1, "nocap": 2,
            "deadass": 2, "lowkey": 2, "highkey": 2, "fire": 1,
            "real": 1, "yeah": 1, "nah": 1, "aye": 1, "ayy": 1,
        }
        
        # Common Hindi words (romanized) with syllable counts
        self.hindi_syllables = {
            # Pronouns and basics
            "mera": 2, "meri": 2, "tera": 2, "teri": 2,
            "uska": 2, "uski": 2, "hamara": 3, "tumhara": 3,
            "main": 1, "mai": 1, "tu": 1, "tum": 1, "hum": 1, "aap": 1,
            "yeh": 1, "woh": 1, "kya": 1, "kaun": 1, "kahan": 2,
            # Common words
            "hai": 1, "hain": 1, "tha": 1, "thi": 1, "the": 1,
            "ho": 1, "hona": 2, "karna": 2, "bolna": 2,
            "naam": 1, "kaam": 1, "daam": 1, "shaam": 1,
            "din": 1, "raat": 1, "subah": 2, "dopahar": 3,
            "pyaar": 1, "pyar": 1, "ishq": 1, "mohabbat": 3,
            "dil": 1, "jaan": 1, "zindagi": 3, "duniya": 3,
            "sapna": 2, "khwab": 1, "aankh": 1, "aankhein": 2,
            "aasman": 3, "zameen": 2, "sitara": 3, "chaand": 1,
            "paisa": 2, "rupaya": 3, "sona": 2, "heera": 2,
            # Verbs
            "bolo": 2, "suno": 2, "dekho": 2, "jao": 2, "aao": 2,
            "karo": 2, "chalo": 2, "ruko": 2, "socho": 2,
            # Adjectives
            "accha": 2, "bura": 2, "bara": 2, "chota": 2,
            "naya": 2, "purana": 3, "sundar": 2, "behtareen": 3,
            # Slang/Hip-hop Hindi
            "bhai": 1, "yaar": 1, "dost": 1, "pagle": 2,
            "banda": 2, "bandi": 2, "scene": 1, "game": 1,
        }
        
        # Common Kannada words (romanized)
        self.kannada_syllables = {
            # Pronouns and basics
            "naanu": 2, "ninna": 2, "avanu": 3, "avalu": 3,
            "naavu": 2, "neevu": 2, "avaru": 3,
            "idu": 2, "adu": 2, "yenu": 2, "yaaru": 2, "elli": 2,
            # Common words
            "ide": 2, "illa": 2, "beku": 2, "maadu": 2,
            "hesaru": 3, "kelsa": 2, "bele": 2, "haadu": 2,
            "dina": 2, "raatri": 2, "beligge": 3,
            "preeti": 2, "prema": 2, "snehaa": 2,
            "manasu": 3, "jeeva": 2, "jagat": 2, "bhoomi": 2,
            "aakasha": 3, "nakshatra": 3, "chandra": 2,
            "hana": 2, "belli": 2, "chinna": 2,
            # Slang
            "guru": 2, "maga": 2, "maccha": 2, "thala": 2,
        }
        
        # Merge all dictionaries
        self.all_known_words = {
            **self.slang_syllables,
            **self.hindi_syllables,
            **self.kannada_syllables
        }

    def count_syllables(self, word: str) -> int:
        """Alias for count_word_syllables"""
        return self.count_word_syllables(word)

    def count_syllables_phrase(self, phrase: str) -> int:
        """Alias for count_line_syllables"""
        return self.count_line_syllables(phrase)
    
    def count_word_syllables(self, word: str) -> int:
        """Count syllables in a single word (supports English, Hindi, Kannada)"""
        word = word.lower().strip().strip(".,!?;:'\"")
        
        if not word:
            return 0
        
        # Check all known words (English slang + Hindi + Kannada)
        if word in self.all_known_words:
            return self.all_known_words[word]
        
        # Try CMU dictionary (English)
        phones = pronouncing.phones_for_word(word)
        if phones:
            first_pron = phones[0]
            syllables = len([p for p in first_pron.split() if any(c.isdigit() for c in p)])
            return syllables if syllables > 0 else 1
        
        # Detect if word looks like romanized Indian language
        # (not in CMU dict + contains common Indian patterns)
        if self._looks_indian(word):
            return self._indian_syllable_count(word)
        
        # Fallback to English rule-based counting
        return self._rule_based_count(word)
    
    def _looks_indian(self, word: str) -> bool:
        """Heuristic to detect if word might be romanized Hindi/Kannada"""
        # Common Indian language patterns
        indian_patterns = [
            'aa', 'ee', 'ii', 'oo', 'uu',  # Long vowels
            'bh', 'ch', 'dh', 'gh', 'jh', 'kh', 'ph', 'th',  # Aspirated consonants
            'sh', 'chh',  # Common sounds
        ]
        word_lower = word.lower()
        
        # If word contains multiple Indian patterns, likely Indian
        pattern_count = sum(1 for p in indian_patterns if p in word_lower)
        return pattern_count >= 1
    
    def _indian_syllable_count(self, word: str) -> int:
        """
        Count syllables for romanized Indian words.
        Indian languages have very regular syllable structure:
        - Each vowel (or vowel cluster) = 1 syllable
        - Consonant clusters don't create extra syllables
        """
        word = word.lower()
        
        # Find all vowel clusters (prioritize long vowels)
        vowels = self.indian_vowel_pattern.findall(word)
        count = len(vowels)
        
        return max(1, count)
    
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

    def get_stress_pattern(self, word: str) -> str:
        """Get stress pattern (0=unstressed, 1=primary, 2=secondary)"""
        word = word.lower().strip().strip(".,!?;:'\"")
        phones = pronouncing.phones_for_word(word)
        if phones:
            return pronouncing.stresses(phones[0])
        else:
            # Fallback: Guess 1 for 1-syl, 10 for 2-syl... very rough
            count = self.count_word_syllables(word)
            if count == 1: return "1"
            if count == 2: return "10" 
            return "1" + "0" * (count - 1)

    def analyze_flow(self, line: str, target_syllables: Optional[int] = None) -> dict:
        """
        Analyze line flow based on syllables
        """
        breakdown = self.get_line_breakdown(line)
        total = sum(w["syllables"] for w in breakdown)
        
        # Calculate stress pattern
        stress_pattern = ""
        for w in breakdown:
            stress_pattern += self.get_stress_pattern(w["word"])

        result = {
            "total_syllables": total,
            "word_count": len(breakdown),
            "breakdown": breakdown,
            "stress_pattern": stress_pattern,
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
