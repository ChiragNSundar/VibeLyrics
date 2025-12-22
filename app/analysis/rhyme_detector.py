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
    
    def _guess_pronunciation(self, word: str) -> List[str]:
        """
        Heuristic G2P (Grapheme-to-Phoneme) for unknown slang words.
        Very basic rule-based approximation for hip-hop slang.
        """
        word = word.lower()
        phones = []
        
        # 1. Handle common endings
        if word.endswith("ing"):
            phones = ["IH", "NG"]
            stem = word[:-3]
        elif word.endswith("er"):
            phones = ["ER"]
            stem = word[:-2]
        else:
            stem = word
            
        # 2. Map vowel groups to likely sounds
        # This is primitive but handles many cases better than raw spelling
        vowel_map = {
            "ee": "IY", "ea": "IY", "oo": "UW", "oa": "OW",
            "ai": "EY", "ay": "EY", "ei": "EY",
            "ie": "AY", "uy": "AY", "y": "AY", # at end usually
            "ou": "AW", "ow": "AW",
            "oi": "OY", "oy": "OY",
            "a": "AE", "e": "EH", "i": "IH", "o": "AA", "u": "AH"
        }
        
        # Simple scan (not perfect, but a safety net)
        # Check double vowels first
        found_vowel = False
        i = 0
        while i < len(stem):
            char = stem[i]
            next_char = stem[i+1] if i+1 < len(stem) else ""
            bigram = char + next_char
            
            if bigram in vowel_map:
                phones.append(vowel_map[bigram] + "1") # Assume stress
                found_vowel = True
                i += 2
                continue
                
            if char in vowel_map:
                # Magic E rule (simple version): "ite" -> AY T
                if char in ['a','e','i','o','u'] and next_char not in ['a','e','i','o','u'] and (i+2 < len(stem) and stem[i+2] == 'e'):
                     long_vowels = {'a':'EY', 'e':'IY', 'i':'AY', 'o':'OW', 'u':'UW'}
                     if char in long_vowels:
                         phones.append(long_vowels[char] + "1")
                         found_vowel = True
                         phones.append(next_char.upper()) # The consonant
                         i += 3 # Skip vowel, consonant, E
                         continue
                
                phones.append(vowel_map[char] + "1")
                found_vowel = True
                i += 1
                continue
            
            # Consonants
            if char.isalpha() and char not in ['a','e','i','o','u']:
                # Map some easy ones, ignore hard ones for now or map 1:1
                c_map = {'c': 'K', 'q': 'K', 'x': 'K S', 'j': 'JH'}
                phones.append(c_map.get(char, char.upper()))
            
            i += 1
            
        if not found_vowel:
             return []
             
        return [" ".join(phones)]

    def get_pronunciation(self, word: str) -> List[str]:
        """Get list of possible pronunciations for a word"""
        word = word.lower().strip()
        word = re.sub(r"[^a-z']", "", word)
        
        # Try CMU dictionary directly
        phones = pronouncing.phones_for_word(word)
        if phones:
            return phones
            
        # Fallback 1: Plural handling (s, es)
        if word.endswith('s'):
            # Try removing 's' (Cornflakes -> Cornflake)
            sing_phones = pronouncing.phones_for_word(word[:-1])
            if sing_phones:
                return [p + " Z" for p in sing_phones]
                
            if word.endswith('es'):
                sing_phones = pronouncing.phones_for_word(word[:-2])
                if sing_phones:
                    return [p + " IH0 Z" for p in sing_phones]
        
        # Fallback 2: Heuristic Guessing (Slang)
        # If we still know nothing, try to guess the sounds
        guessed = self._guess_pronunciation(word)
        if guessed:
            return guessed
            
        return []
    
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
            # Fallback to suffix matching ONLY if strictly necessary
            # and verify it's not a weak suffix match
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
            
        # Avoid weak suffix detection (just 's', 'es', 'ed', 'd')
        # If the match length is small, ensure it's not a common grammatical suffix
        # that doesn't carry the rhyme sound (Trees / Flakes)
        
        match_len = 0
        max_len = min(len(w1), len(w2))
        for length in range(1, max_len + 1):
            if w1[-length:] == w2[-length:]:
                match_len = length
            else:
                break
                
        if match_len >= min_match:
            suffix = w1[-match_len:]
            # Blacklist weak suffixes if that's ALL that matches
            weak_suffixes = ['s', 'es', 'ed', 'ly', 'y'] 
            # Note: 'ing' rhymes usually involve the vowel (Sing/Ring), so suffix='ing' is actually OK.
            # But 'es' is bad (Trees/Cakes). 
            
            if suffix in ['s', 'es', 'ed', 'd', 'ly', 'y']:
                # Require more context (longer match) to confirm rhyme
                # e.g. "happiness" vs "sadness" (ness) is ok?
                if match_len < 3: 
                    return False
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
    
    def _get_coda(self, phones: List[str]) -> str:
        """Get the consonant sounds after the last vowel"""
        coda = []
        found_vowel = False
        for p in reversed(phones):
            if any(c.isdigit() for c in p):
                found_vowel = True
                break
            coda.insert(0, p)
        return " ".join(coda) if found_vowel else ""

    def _coda_compatible(self, coda1: str, coda2: str) -> bool:
        """Check if two codas are phonetically compatible for slant rhyme"""
        if coda1 == coda2:
            return True
            
        # Clean numeric stress if any leaking (shouldn't be in coda)
        # We need to keep spaces to split individual phonemes
        def clean_coda(c):
            return "".join(char for char in c if char.isalpha() or char.isspace())

        c1_phones = set(clean_coda(coda1).split())
        c2_phones = set(clean_coda(coda2).split())
        
        # Empty coda matches S/Z (very common: rhyme / rhymes)
        if not c1_phones and any(p in ['Z', 'S'] for p in c2_phones): return True
        if not c2_phones and any(p in ['Z', 'S'] for p in c1_phones): return True
            
        # Phonetic families
        families = [
            {'M', 'N', 'NG'}, # Nasals
            {'S', 'Z', 'SH', 'ZH'}, # Sibilants
            {'T', 'D', 'K', 'G', 'P', 'B'}, # Plosives
            {'F', 'V', 'TH', 'DH'}, # Fricatives
            {'L', 'R'} # Liquids
        ]
        
        # 1. If any sound matches exactly
        if not c1_phones.isdisjoint(c2_phones):
            return True
            
        # 2. Check if any phones from c1 match a family that any phones from c2 also match
        for fam in families:
            if not c1_phones.isdisjoint(fam) and not c2_phones.isdisjoint(fam):
                return True
                
        return False

    def _slant_rhyme(self, rhyme1: str, rhyme2: str) -> bool:
        """Check for slant/near rhymes (vowel match + compatible coda)"""
        phones1 = rhyme1.split()
        phones2 = rhyme2.split()
        
        if not phones1 or not phones2:
             return False
        
        # Check vowels
        def get_vowel_sound(phone):
            return ''.join(c for c in phone if not c.isdigit())
        
        vowels1 = [get_vowel_sound(p) for p in phones1 if any(c.isdigit() for c in p)]
        vowels2 = [get_vowel_sound(p) for p in phones2 if any(c.isdigit() for c in p)]
        
        # Must match last vowel
        if not vowels1 or not vowels2 or vowels1[-1] != vowels2[-1]:
            return False
            
        # Get vowel stresses
        def get_stress(phone):
            return ''.join(c for c in phone if c.isdigit())
            
        stress1 = [get_stress(p) for p in phones1 if any(c.isdigit() for c in p)]
        stress2 = [get_stress(p) for p in phones2 if any(c.isdigit() for c in p)]
        
        last_stress1 = stress1[-1] if stress1 else '1'
        last_stress2 = stress2[-1] if stress2 else '1'
        
        # Check Coda compatibility
        coda1 = self._get_coda(phones1)
        coda2 = self._get_coda(phones2)
        
        # Stricter check for Open vs Closed rhymes involving S/Z
        # REMOVED: In hip-hop, unstressed endings (Whitney) often rhyme with stressed (Trees)
        # "Pay" (1) vs "Days" (1) -> OK
        # "Whitney" (0) vs "Trees" (1) -> OK (Relaxes previous constraint)
        # is_open_closed_mix = (not coda1 and coda2) or (not coda2 and coda1)
        # if is_open_closed_mix and last_stress1 != last_stress2:
        #     return False
        
        # Allow match if codas are compatible
        if self._coda_compatible(coda1, coda2):
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
    
    def highlight_lyrics(self, lines: List[str]) -> List[str]:
        """
        Takes a list of lyric lines and returns HTML strings with rhyming words highlighted.
        Example: "I like <span class='rhyme-word rhyme-a'>cats</span>"
        """
        if not lines:
            return []
            
        rhyme_groups = self.detect_end_rhymes(lines)
        highlighted_lines = []
        
        # Flatten groups to map line_index -> label
        line_to_label = {}
        for label, indices in rhyme_groups.items():
            for idx in indices:
                line_to_label[idx] = label.lower() # rhyme-a, rhyme-b
                
        for i, line in enumerate(lines):
            words = self._extract_words(line)
            if not words:
                highlighted_lines.append(line)
                continue
                
            label = line_to_label.get(i)
            if label:
                last_word = words[-1]
                # Replace the LAST occurrence of the word to avoid false positives early in line
                # This is a simple regex replacement which might be safer
                pattern = re.compile(re.escape(last_word) + r"($|\W)", re.IGNORECASE)
                
                # Check for match at end of string
                match = None
                for m in pattern.finditer(line):
                    match = m
                
                if match:
                    # We have the last match, replace it
                    start, end = match.span()
                    # Keep the original casing from the line, but wrap it
                    # Note: match includes the trailing boundary char if present
                    original_text = line[start:end]
                    # Separate word and punctuation
                    word_part = original_text[:len(last_word)]
                    punct_part = original_text[len(last_word):]
                    
                    replacement = f"<span class='rhyme-word rhyme-{label}'>{word_part}</span>{punct_part}"
                    new_line = line[:start] + replacement + line[end:]
                    highlighted_lines.append(new_line)
                else:
                    highlighted_lines.append(line)
            else:
                highlighted_lines.append(line)
                
        return highlighted_lines

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

    def get_density_heatmap(self, lines: List[str]) -> List[Dict]:
        """
        Calculate rhyme density for each line to generate a heatmap.
        Density = (Syllables in rhyming words) / (Total Syllables)
        """
        heatmap = []
        # Local import to avoid circular dependency if any
        from app.analysis.syllable_counter import SyllableCounter
        counter = SyllableCounter()
        
        for line in lines:
            line_words = self._extract_words(line)
            if not line_words:
                heatmap.append({"density": 0, "color": "none"})
                continue
                
            total_syl = counter.count_syllables_phrase(line)
            if total_syl == 0:
                heatmap.append({"density": 0, "color": "none"})
                continue

            # 1. find internal rhymes
            internal = self.detect_internal_rhymes(line)
            rhyming_words = set()
            for w1, w2, _, _ in internal:
                rhyming_words.add(w1.lower())
                rhyming_words.add(w2.lower())
                
            # 2. check end rhyme (with ANY other line in the batch)
            # This is O(N^2) but N is small (lines in view)
            last_word = line_words[-1].lower()
            if last_word not in rhyming_words:
                for other_line in lines:
                    if other_line == line: continue
                    other_words = self._extract_words(other_line)
                    if other_words and self.words_rhyme(last_word, other_words[-1], strict=False):
                        rhyming_words.add(last_word)
                        break
            
            # Calculate rhyming syllables
            rhyme_syl = 0
            # To be accurate we must map words back to the line to avoid overcounting duplicates 
            # if they appear multiple times but only rhyme once? 
            # Simpler: just iterate the words in the line and check if they are in rhyming_words set
            for w in line_words:
                if w.lower() in rhyming_words:
                    rhyme_syl += counter.count_syllables(w)
            
            density = min(1.0, rhyme_syl / total_syl)
            
            # Color scale
            color = "none"
            if density > 0.6: color = "high"    # Red/Hot
            elif density > 0.4: color = "medium" # Orange
            elif density > 0.2: color = "low"    # Yellow
            
            heatmap.append({
                "density": round(density, 2),
                "color": color,
                "rhyme_syl": rhyme_syl,
                "total_syl": total_syl
            })
            
        return heatmap
