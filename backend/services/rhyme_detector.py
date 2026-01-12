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
        """Add HTML highlighting for rhymes"""
        if not lines:
            return []
        
        # Get rhyme endings
        endings = []
        for line in lines:
            words = line.split()
            if words:
                ending = self.get_rhyme_ending(words[-1])
                endings.append(ending)
            else:
                endings.append("")
        
        # Assign colors to rhyme groups
        color_map = {}
        colors = ['rhyme-a', 'rhyme-b', 'rhyme-c', 'rhyme-d', 'rhyme-e']
        color_idx = 0
        
        for ending in endings:
            if ending and ending not in color_map:
                # Check if it rhymes with any existing
                found_match = False
                for existing, color in color_map.items():
                    if self._endings_rhyme(ending, existing):
                        color_map[ending] = color
                        found_match = True
                        break
                
                if not found_match:
                    color_map[ending] = colors[color_idx % len(colors)]
                    color_idx += 1
        
        # Generate highlighted HTML
        highlighted = []
        # Prepare alliteration groups
        alliterations = self._find_alliterations(lines)
        
        # Generate highlighted HTML
        highlighted = []
        for i, (line, ending) in enumerate(zip(lines, endings)):
            words = line.split()
            if not words:
                highlighted.append(line)
                continue
                
            # Apply alliteration first (simplified)
            line_html_parts = []
            for word in words:
                word_clean = re.sub(r'[^a-z]', '', word.lower())
                if len(word_clean) > 0 and i < len(alliterations) and word_clean in alliterations[i]:
                     line_html_parts.append(f"<span class='alliteration'>{word}</span>")
                else:
                    line_html_parts.append(word)
            
            # Apply rhyme to last word
            if ending and ending in color_map:
                last_word = line_html_parts[-1] # This might be already wrapped in alliteration span
                # If wrapped, we need to be careful. For now, let's just wrap the whole thing or strip
                # To be safe and simple: just wrap the last word for rhyme, ignoring internal alliteration of that specific word if conflict
                # Better: Re-construct the last word wrapper
                
                raw_last = words[-1]
                # If it was alliterated
                is_alliterated = len(re.sub(r'[^a-z]', '', raw_last.lower())) > 0 and i < len(alliterations) and re.sub(r'[^a-z]', '', raw_last.lower()) in alliterations[i]
                
                classes = f"rhyme-word {color_map[ending]}"
                if is_alliterated:
                    classes += " alliteration"
                    
                line_html_parts[-1] = f"<span class='{classes}'>{raw_last}</span>"
            
            highlighted.append(" ".join(line_html_parts))
        
        return highlighted

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
        """Get rhyme scheme as string (e.g., AABB, ABAB)"""
        if not lines:
            return ""
        
        endings = []
        for line in lines:
            words = line.split()
            if words:
                endings.append(self.get_rhyme_ending(words[-1]))
            else:
                endings.append("")
        
        scheme = []
        seen = {}
        current = 'A'
        
        for ending in endings:
            if not ending:
                scheme.append('X')
                continue
            
            found = None
            for known, letter in seen.items():
                if self._endings_rhyme(ending, known):
                    found = letter
                    break
            
            if found:
                scheme.append(found)
            else:
                scheme.append(current)
                seen[ending] = current
                current = chr(ord(current) + 1)
        
        return ''.join(scheme)
