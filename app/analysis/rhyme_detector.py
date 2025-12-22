"""
Rhyme Detector
Detects internal rhymes, end rhymes, multisyllabic rhymes, and slant rhymes
Uses CMU Pronouncing Dictionary for phonetic analysis
"""
import re
from typing import List, Dict, Tuple, Optional
import pronouncing


class RhymeDetector:
    """Detects various types of rhymes in lyrics"""
    
    def __init__(self):
        # Common slang/hip-hop words not in CMU dict with approximate pronunciations
        self.custom_pronunciations = {
            "finna": ["F IH1 N AH0"],
            "gonna": ["G AH1 N AH0"],
            "wanna": ["W AA1 N AH0"],
            "gotta": ["G AA1 T AH0"],
            "tryna": ["T R AY1 N AH0"],
            "ima": ["AY1 M AH0"],
            "wassup": ["W AH0 S AH1 P"],
            "aight": ["AY1 T"],
            "dope": ["D OW1 P"],
            "drip": ["D R IH1 P"],
            "lit": ["L IH1 T"],
            "flex": ["F L EH1 K S"],
            "vibe": ["V AY1 B"],
            "vibin": ["V AY1 B IH0 N"],
        }
    
    def get_pronunciation(self, word: str) -> List[str]:
        """Get phonetic pronunciation(s) for a word"""
        word = word.lower().strip()
        
        # Check custom dict first
        if word in self.custom_pronunciations:
            return self.custom_pronunciations[word]
        
        # Try CMU dictionary
        phones = pronouncing.phones_for_word(word)
        return phones if phones else []
    
    def get_rhyme_part(self, pronunciation: str) -> str:
        """Extract the rhyming part (from last stressed vowel to end)"""
        phones = pronunciation.split()
        
        # Find last stressed vowel (marked with 1 or 2)
        for i in range(len(phones) - 1, -1, -1):
            if any(c.isdigit() for c in phones[i]):
                return ' '.join(phones[i:])
        
        # Fallback: use last two phonemes
        return ' '.join(phones[-2:]) if len(phones) >= 2 else pronunciation
    
    def words_rhyme(self, word1: str, word2: str, strict: bool = True) -> bool:
        """Check if two words rhyme"""
        if word1.lower() == word2.lower():
            return False  # Same word doesn't count
        
        pron1_list = self.get_pronunciation(word1)
        pron2_list = self.get_pronunciation(word2)
        
        if not pron1_list or not pron2_list:
            # Fallback to suffix matching if no pronunciation
            return self._suffix_rhyme(word1, word2)
        
        for pron1 in pron1_list:
            for pron2 in pron2_list:
                rhyme1 = self.get_rhyme_part(pron1)
                rhyme2 = self.get_rhyme_part(pron2)
                
                if rhyme1 == rhyme2:
                    return True
                
                if not strict and self._slant_rhyme(rhyme1, rhyme2):
                    return True
        
        return False
    
    def _suffix_rhyme(self, word1: str, word2: str, min_match: int = 2) -> bool:
        """Fallback rhyme check based on suffix matching - more lenient for rap"""
        w1, w2 = word1.lower().strip(), word2.lower().strip()
        
        # Clean words
        w1 = re.sub(r"[^a-z]", "", w1)
        w2 = re.sub(r"[^a-z]", "", w2)
        
        if not w1 or not w2:
            return False
        
        # Exact suffix match
        for length in range(min(len(w1), len(w2)), min_match - 1, -1):
            if w1[-length:] == w2[-length:]:
                return True
        
        # Common rhyming endings (hip-hop focused)
        rhyme_families = [
            ['ay', 'ey', 'eigh', 'a'],
            ['ow', 'oe', 'o'],
            ['ight', 'ite', 'yte'],
            ['ough', 'uff', 'uf'],
            ['ation', 'asion', 'ition'],
            ['ine', 'ign', 'yn'],
            ['ear', 'eer', 'ere', 'eir'],
            ['ound', 'ownd'],
            ['ough', 'ow', 'o'],
            ['ack', 'ak'],
            ['ing', 'in'],
            ['ame', 'aim'],
            ['ane', 'ain', 'ayn'],
            ['eal', 'eel', 'iel'],
        ]
        
        for family in rhyme_families:
            w1_match = any(w1.endswith(ending) for ending in family)
            w2_match = any(w2.endswith(ending) for ending in family)
            if w1_match and w2_match:
                return True
        
        return False
    
    def _slant_rhyme(self, rhyme1: str, rhyme2: str) -> bool:
        """Check for slant/near rhymes (vowel or consonant similarity)"""
        phones1 = rhyme1.split()
        phones2 = rhyme2.split()
        
        if not phones1 or not phones2:
            return False
        
        # Check if vowels match (ignore stress markers)
        def get_vowel(phone):
            return ''.join(c for c in phone if not c.isdigit())
        
        vowels1 = [get_vowel(p) for p in phones1 if any(c.isdigit() for c in p)]
        vowels2 = [get_vowel(p) for p in phones2 if any(c.isdigit() for c in p)]
        
        # Match if same vowel sounds
        if vowels1 and vowels2 and vowels1[-1] == vowels2[-1]:
            return True
        
        return False
    
    def detect_end_rhymes(self, lines: List[str]) -> Dict[str, List[int]]:
        """
        Detect end rhymes and return rhyme scheme
        Returns: {"A": [0, 2], "B": [1, 3]} format
        """
        if not lines:
            return {}
        
        rhyme_groups = {}
        line_labels = {}
        current_label = 0
        
        for i, line in enumerate(lines):
            words = self._extract_words(line)
            if not words:
                continue
            
            last_word = words[-1]
            found_group = None
            
            # Check if rhymes with any existing group
            for label, indices in rhyme_groups.items():
                ref_line = lines[indices[0]]
                ref_words = self._extract_words(ref_line)
                if ref_words and self.words_rhyme(last_word, ref_words[-1], strict=False):
                    found_group = label
                    break
            
            if found_group:
                rhyme_groups[found_group].append(i)
                line_labels[i] = found_group
            else:
                new_label = chr(ord('A') + current_label)
                rhyme_groups[new_label] = [i]
                line_labels[i] = new_label
                current_label += 1
        
        return rhyme_groups
    
    def detect_internal_rhymes(self, line: str) -> List[Tuple[str, str, int, int]]:
        """
        Detect rhymes within a single line
        Returns: List of (word1, word2, pos1, pos2) tuples
        """
        words = self._extract_words(line)
        internal_rhymes = []
        
        for i in range(len(words)):
            for j in range(i + 2, len(words)):  # Skip adjacent words
                if self.words_rhyme(words[i], words[j], strict=False):
                    internal_rhymes.append((words[i], words[j], i, j))
        
        return internal_rhymes
    
    def detect_multisyllabic_rhymes(self, line1: str, line2: str) -> List[Dict]:
        """
        Detect complex multi-word rhyme patterns between two lines
        Example: "hollow tips" / "follow ships"
        """
        words1 = self._extract_words(line1)
        words2 = self._extract_words(line2)
        
        multisyllabic = []
        
        # Check last 2-3 words for compound rhymes
        for length in [3, 2]:
            if len(words1) >= length and len(words2) >= length:
                phrase1 = words1[-length:]
                phrase2 = words2[-length:]
                
                # Check if phrases rhyme phonetically
                if self._phrases_rhyme(phrase1, phrase2):
                    multisyllabic.append({
                        "phrase1": " ".join(phrase1),
                        "phrase2": " ".join(phrase2),
                        "length": length
                    })
        
        return multisyllabic
    
    def _phrases_rhyme(self, phrase1: List[str], phrase2: List[str]) -> bool:
        """Check if two phrases have rhyming patterns"""
        # Simple: check if at least half the words rhyme
        rhyme_count = 0
        for w1, w2 in zip(phrase1, phrase2):
            if self.words_rhyme(w1, w2, strict=False):
                rhyme_count += 1
        
        return rhyme_count >= len(phrase1) // 2 + 1
    
    def get_rhyme_scheme_string(self, lines: List[str]) -> str:
        """Get rhyme scheme as a string like 'AABB' or 'ABAB'"""
        rhyme_groups = self.detect_end_rhymes(lines)
        
        # Build scheme string
        scheme = []
        for i in range(len(lines)):
            found = False
            for label, indices in rhyme_groups.items():
                if i in indices:
                    scheme.append(label)
                    found = True
                    break
            if not found:
                scheme.append('X')
        
        return ''.join(scheme)
    
    def _extract_words(self, line: str) -> List[str]:
        """Extract words from a line, cleaning punctuation"""
        # Remove punctuation but keep apostrophes in contractions
        cleaned = re.sub(r"[^\w\s']", "", line)
        words = cleaned.split()
        # Clean leading/trailing apostrophes
        return [w.strip("'") for w in words if w.strip("'")]
    
    def analyze_line(self, line: str, previous_lines: List[str] = None) -> Dict:
        """
        Complete rhyme analysis for a line
        """
        result = {
            "line": line,
            "internal_rhymes": self.detect_internal_rhymes(line),
            "end_word": None,
            "rhymes_with_previous": []
        }
        
        words = self._extract_words(line)
        if words:
            result["end_word"] = words[-1]
        
        if previous_lines:
            for i, prev_line in enumerate(previous_lines):
                prev_words = self._extract_words(prev_line)
                if prev_words and words:
                    if self.words_rhyme(words[-1], prev_words[-1], strict=False):
                        result["rhymes_with_previous"].append(i)
        
        return result
