"""
Rhyme Detection Service
Ported from Flask app with CMU dictionary and Indian language support
"""
import pronouncing
import re
from typing import List, Dict, Optional
from functools import lru_cache


class SyllableCounter:
    """Count syllables in text"""
    
    def count(self, text: str) -> int:
        """Count syllables in text"""
        words = text.lower().split()
        total = 0
        
        for word in words:
            word = re.sub(r'[^a-z]', '', word)
            if not word:
                continue
            
            # Try CMU dictionary first
            phones = pronouncing.phones_for_word(word)
            if phones:
                total += pronouncing.syllable_count(phones[0])
            else:
                # Fallback: count vowel groups
                vowels = re.findall(r'[aeiouy]+', word)
                total += max(1, len(vowels))
        
        return total

    def get_stress_pattern(self, text: str) -> str:
        """Get stress pattern (1=primary, 2=secondary, 0=unstressed)"""
        words = text.lower().split()
        pattern = []
        
        for word in words:
            word = re.sub(r'[^a-z]', '', word)
            if not word:
                continue
                
            phones = pronouncing.phones_for_word(word)
            if phones:
                # Get first pronunciation's stresses
                stress = pronouncing.stresses(phones[0])
                # Convert to simple representation (x=unstressed, /=stressed)
                simple = stress.replace('1', '/').replace('2', '/').replace('0', 'x')
                pattern.append(simple)
            else:
                # Guess based on length (simplified)
                length = len(re.findall(r'[aeiouy]+', word))
                pattern.append('x' * max(1, length))
        
        return " ".join(pattern)


class RhymeDetector:
    """Detect rhymes with multi-language support"""
    
    # Hip-hop rhyme families
    RHYME_FAMILIES = [
        ['ow', 'oh', 'o', 'oe'],
        ['ay', 'ey', 'ai', 'ei'],
        ['ee', 'ea', 'ie', 'y'],
        ['oo', 'ue', 'ew', 'ou'],
        ['ar', 'ah', 'a'],
        ['er', 'ir', 'ur'],
        ['in', 'en', 'an'],
        ['ight', 'ite', 'yte'],
        ['ack', 'ak', 'ac'],
        ['ame', 'aim', 'aym'],
    ]
    
    # Indian language rhyme families (Hindi/Kannada)
    INDIAN_FAMILIES = [
        ['aa', 'a'],
        ['ee', 'i', 'ii'],
        ['oo', 'u', 'uu'],
        ['ai', 'ay', 'ae', 'ey'],
        ['au', 'aw', 'ao', 'ow'],
        ['odu', 'edu', 'idu', 'adu', 'udu'],
        ['ona', 'ena', 'ina', 'ana', 'una'],
        ['ali', 'eli', 'ili', 'oli', 'uli'],
        ['ana', 'ena', 'ina', 'ona', 'una'],
        ['ata', 'eta', 'ita', 'ota', 'uta'],
    ]
    
    # Slang categories
    SLANG = {
        "money": ["bands", "racks", "stacks", "guap", "cheese", "bread", "cheddar", "paper"],
        "success": ["winning", "bossin", "shining", "grinding", "hustling"],
        "confidence": ["drip", "sauce", "swag", "fly", "icy", "cold"],
        "negative": ["cap", "fake", "lame", "wack", "trash"],
    }
    
    def __init__(self):
        self.syllable_counter = SyllableCounter()
    
    @lru_cache(maxsize=1000)
    def find_rhymes(self, word: str, max_results: int = 20) -> List[str]:
        """Find rhyming words"""
        word = word.lower().strip()
        if not word:
            return []
        
        rhymes = set()
        
        # CMU dictionary rhymes
        try:
            cmu_rhymes = pronouncing.rhymes(word)
            rhymes.update(cmu_rhymes[:max_results])
        except Exception:
            pass
        
        # Hip-hop family rhymes
        ending = self._get_ending(word)
        for family in self.RHYME_FAMILIES + self.INDIAN_FAMILIES:
            if ending in family:
                for other_ending in family:
                    if other_ending != ending:
                        # Generate potential rhymes
                        base = word[:-len(ending)] if word.endswith(ending) else word
                        rhymes.add(base + other_ending)
        
        return list(rhymes)[:max_results]
    
    def _get_ending(self, word: str) -> str:
        """Get the rhyme-relevant ending of a word"""
        vowels = 'aeiouy'
        word = word.lower()
        
        # Find last vowel position
        last_vowel_pos = -1
        for i, char in enumerate(word):
            if char in vowels:
                last_vowel_pos = i
        
        if last_vowel_pos >= 0:
            return word[last_vowel_pos:]
        return word[-2:] if len(word) >= 2 else word
    
    def get_rhyme_ending(self, word: str) -> str:
        """Get the phonetic rhyme ending"""
        word = word.lower().strip()
        word = re.sub(r'[^a-z]', '', word)
        
        phones = pronouncing.phones_for_word(word)
        if phones:
            # Get rhyme part (from last stressed vowel)
            return pronouncing.rhyming_part(phones[0])
        
        return self._get_ending(word)
    
    def find_multi_syllable_rhymes(self, word: str) -> List[str]:
        """Find multi-syllable rhymes"""
        word = word.lower().strip()
        rhymes = []
        
        phones = pronouncing.phones_for_word(word)
        if phones:
            syllable_count = pronouncing.syllable_count(phones[0])
            
            # Find words with similar syllable count that rhyme
            base_rhymes = self.find_rhymes(word, max_results=50)
            for rhyme in base_rhymes:
                r_phones = pronouncing.phones_for_word(rhyme)
                if r_phones and pronouncing.syllable_count(r_phones[0]) >= syllable_count:
                    rhymes.append(rhyme)
        
        return rhymes[:20]
    
    def get_synonyms(self, word: str) -> List[str]:
        """Get synonyms (simplified version)"""
        # Would integrate with NLTK WordNet in full version
        return []
    
    def highlight_lyrics(self, lines: List[str]) -> List[str]:
        """
        Multi-color rhyme highlighting.
        Groups words by their full rhyming part (from last stressed vowel onward)
        so that each rhyme family gets a distinct color — like a professional
        lyric breakdown. Only highlights groups that span 2+ lines.
        """
        if not lines:
            return []

        # 1. Tokenize all words, tracking (line_idx, word_idx)
        all_words = []     # flat list of clean words
        word_line = []     # which line each word belongs to
        word_map = []      # per-line list of flat indices (or -1 for non-alpha tokens)

        for i, line in enumerate(lines):
            words = line.split()
            word_map_line = []
            for j, word in enumerate(words):
                clean = re.sub(r'[^a-z]', '', word.lower())
                if clean:
                    all_words.append(clean)
                    word_line.append(i)
                    word_map_line.append(len(all_words) - 1)
                else:
                    word_map_line.append(-1)
            word_map.append(word_map_line)

        # 2. Get the full rhyming part for each word
        rhyme_parts = []
        for word in all_words:
            phones_list = pronouncing.phones_for_word(word)
            if phones_list:
                rp = pronouncing.rhyming_part(phones_list[0])
                rhyme_parts.append(rp)
            else:
                # Fallback: use the orthographic ending from last vowel
                rhyme_parts.append(self._get_ending(word))

        # 3. Group words that share the same rhyming part
        sound_groups: Dict[str, List[int]] = {}
        for idx, rp in enumerate(rhyme_parts):
            if not rp:
                continue
            if rp not in sound_groups:
                sound_groups[rp] = []
            sound_groups[rp].append(idx)

        # 4. Filter: keep only groups with 2+ words that appear across 2+ different lines
        #    This prevents trivial highlights (single word or all on same line)
        qualified_groups = {}
        for rp, indices in sound_groups.items():
            if len(indices) < 2:
                continue
            lines_involved = set(word_line[idx] for idx in indices)
            if len(lines_involved) >= 2:
                qualified_groups[rp] = indices

        # 5. Assign colors — most frequent group first for visual prominence
        group_colors: Dict[str, str] = {}
        color_idx = 0
        sorted_groups = sorted(qualified_groups.items(), key=lambda x: len(x[1]), reverse=True)

        for rp, indices in sorted_groups:
            group_colors[rp] = f"rhyme-group-{color_idx % 12 + 1}"
            color_idx += 1

        # Build a per-word color lookup
        word_color: Dict[int, str] = {}
        for rp, indices in qualified_groups.items():
            css_class = group_colors[rp]
            for idx in indices:
                word_color[idx] = css_class

        # 6. Build HTML
        highlighted_lines = []
        for i, line in enumerate(lines):
            words = line.split()
            if not words:
                highlighted_lines.append(line)
                continue

            line_html_parts = []
            for j, word in enumerate(words):
                flat_idx = word_map[i][j]
                classes = []

                # Rhyme color
                if flat_idx != -1 and flat_idx in word_color:
                    classes.append(word_color[flat_idx])
                    classes.append("rhyme-word")

                # Alliteration (same starting consonant with another word in the line)
                clean_word = re.sub(r'[^a-z]', '', word.lower())
                if clean_word:
                    first_char = clean_word[0]
                    siblings = [re.sub(r'[^a-z]', '', w.lower()) for k, w in enumerate(words) if k != j]
                    siblings = [w for w in siblings if w]
                    if any(s.startswith(first_char) for s in siblings):
                        classes.append("alliteration")

                if classes:
                    line_html_parts.append(f"<span class='{' '.join(classes)}'>{word}</span>")
                else:
                    line_html_parts.append(word)

            highlighted_lines.append(" ".join(line_html_parts))

        return highlighted_lines

    def _find_alliterations(self, lines: List[str]) -> List[List[str]]:
        """Find words that alliterate in each line"""
        result = []
        for line in lines:
            words = line.split()
            if not words:
                result.append([])
                continue
                
            # Get first letters
            firsts = {}
            for word in words:
                clean = re.sub(r'[^a-z]', '', word.lower())
                if clean:
                    f = clean[0]
                    if f not in firsts:
                        firsts[f] = []
                    firsts[f].append(clean)
            
            # Keep only those with 2+ count
            line_allits = []
            for chars in firsts.values():
                if len(chars) >= 2:
                    line_allits.extend(chars)
            result.append(line_allits)
        return result
    
    def _endings_rhyme(self, e1: str, e2: str) -> bool:
        """Check if two endings rhyme"""
        if e1 == e2:
            return True
        
        # Check family matches
        for family in self.RHYME_FAMILIES + self.INDIAN_FAMILIES:
            if e1 in family and e2 in family:
                return True
        
        return False
    
    def get_density_heatmap(self, lines: List[str]) -> List[Dict]:
        """Calculate rhyme density for heatmap"""
        result = []
        
        for line in lines:
            words = line.split()
            rhyme_count = 0
            
            for i, word in enumerate(words):
                for j, other in enumerate(words):
                    if i != j:
                        e1 = self.get_rhyme_ending(word)
                        e2 = self.get_rhyme_ending(other)
                        if self._endings_rhyme(e1, e2):
                            rhyme_count += 1
            
            density = rhyme_count / max(1, len(words))
            
            if density > 0.5:
                color = "high"
            elif density > 0.2:
                color = "medium"
            else:
                color = "low"
            
            result.append({"density": density, "color": color})
        
        return result
    
    def get_slang_by_category(self, category: str) -> List[str]:
        """Get slang words for a category"""
        return self.SLANG.get(category.lower(), [])
    
    def get_slang_categories(self) -> List[str]:
        """Get all slang categories"""
        return list(self.SLANG.keys())
    
    def get_rhyme_scheme_string(self, lines: List[str]) -> str:
        """
        Identify common 4-line rhyme schemes (ABAB, AABB, etc.)
        Returns the specific name of the scheme if matched, otherwise the raw pattern (e.g., 'ABCA').
        """
        if not lines:
            return ""
        
        # We only care about the last 4 lines for identifying specific stanzas
        # If fewer than 4, just return standard ABC
        target_lines = lines[-4:]
        if len(target_lines) < 4:
            return self._generate_raw_scheme(target_lines)

        endings = [self.get_rhyme_ending(line.split()[-1] if line.split() else "") for line in target_lines]
        
        # Generate generic pattern (A, B, C...)
        scheme = []
        seen = {}
        current_char = 'A'
        
        for end in endings:
            if not end:
                scheme.append('X')
                continue
                
            found = None
            for known_end, char in seen.items():
                if self._endings_rhyme(end, known_end):
                    found = char
                    break
            
            if found:
                scheme.append(found)
            else:
                scheme.append(current_char)
                seen[end] = current_char
                current_char = chr(ord(current_char) + 1)
        
        raw_pattern = "".join(scheme)
        
        # Map common patterns to user-friendly names
        patterns = {
            "AABB": "AABB (Couplets)",
            "ABAB": "ABAB (Alternating)",
            "AAAA": "AAAA (Monorhyme)",
            "XAXA": "XAXA (Simple 4-line)",
            "ABBA": "ABBA (Enclosed)",
            "AXAA": "AXAA",
            "AAXA": "AAXA",
            "AAAX": "AAAX",
            "AXXA": "AXXA"
        }
        
        # Normalize pattern to always start with A (handled by logic above), 
        # but handling 'X' requires care.
        # The above logic generates ABC... 
        # We need to map 'unrhymed' to X if the user prefers that specific notation for non-rhymes?
        # Standard notation usually allows C, D, etc. 
        # However, specifically for "XAXA", that implies line 1 and 3 DO NOT rhyme with anything.
        
        # Let's do a strict check against the requested patterns using the generated ABC form.
        # The generated form will maximize rhyme matching.
        # e.g. XAXA in standard form is ABCB (where A!=C and B=B).
        
        # Let's convert our ABC form to the user's requested "X" form if unique.
        
        # Check specific known mappings from ABC format
        if raw_pattern == "ABCB": return "XAXA" # Popular ballad meter often called this
        if raw_pattern == "ABAC": return "AXXA" # Not quite standard but fits
        
        return patterns.get(raw_pattern, raw_pattern)

    def _generate_raw_scheme(self, lines: List[str]) -> str:
        """Generate standard ABCD rhyme scheme string"""
        endings = [self.get_rhyme_ending(line.split()[-1] if line.split() else "") for line in lines]
        scheme = []
        seen = {}
        current_char = 'A'
        
        for end in endings:
            if not end:
                scheme.append('X')
                continue
            found = None
            for known_end, char in seen.items():
                if self._endings_rhyme(end, known_end):
                    found = char
                    break
            if found:
                scheme.append(found)
            else:
                scheme.append(current_char)
                seen[end] = current_char
                current_char = chr(ord(current_char) + 1)
        return "".join(scheme)
