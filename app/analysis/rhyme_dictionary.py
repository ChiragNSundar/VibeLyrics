"""
Rhyme Dictionary
Provides rhyme suggestions, slant rhymes, and hip-hop vocabulary
"""
import pronouncing
import re
from typing import List, Dict, Set


class RhymeDictionary:
    """Dictionary for finding rhymes, near-rhymes, and hip-hop vocabulary"""
    
    # Common hip-hop slang and terms
    HIP_HOP_VOCAB = {
        "money": ["bread", "cheddar", "cheese", "paper", "bands", "racks", "stacks", "guap", "mula", "dough", "cabbage", "cake"],
        "car": ["whip", "ride", "foreign", "coupe", "drop-top", "slab", "bucket", "hooptie"],
        "gun": ["strap", "piece", "heat", "burner", "blicky", "pole", "iron", "tool"],
        "police": ["ops", "feds", "pigs", "12", "boys", "one-time", "jake"],
        "friends": ["squad", "gang", "crew", "homies", "bros", "day-ones", "dawgs"],
        "enemies": ["opps", "haters", "snakes", "rats", "fakes"],
        "drugs": ["pack", "work", "bricks", "loud", "gas", "za"],
        "jewelry": ["ice", "drip", "flooded", "bust-down", "chains", "rocks"],
        "success": ["winning", "up", "lit", "blessed", "eatin", "goated"],
        "work": ["grind", "hustle", "chase", "stack", "flip"],
        "girl": ["shorty", "shawty", "baddie", "queen", "wifey", "bae"],
        "neighborhood": ["hood", "block", "turf", "ends", "streets", "trenches"],
        "real": ["solid", "100", "valid", "certified", "official", "facts"],
        "fake": ["cap", "fraud", "phony", "lame", "goofy", "clown"]
    }
    
    # Multisyllabic rhyme patterns
    MULTI_SYLLABLE_GROUPS = {
        "ation": ["nation", "station", "patient", "relation", "creation", "vacation", "sensation"],
        "ology": ["apology", "technology", "psychology", "ideology"],
        "icious": ["delicious", "suspicious", "malicious", "nutritious", "ambitious"],
        "ential": ["essential", "potential", "credential", "residential", "presidential"],
    }
    
    def __init__(self):
        self.cache = {}
    
    def find_rhymes(self, word: str, max_results: int = 20) -> List[str]:
        """Find exact rhymes for a word"""
        word = word.lower().strip()
        
        if word in self.cache:
            return self.cache[word][:max_results]
        
        rhymes = pronouncing.rhymes(word)
        self.cache[word] = rhymes
        return rhymes[:max_results]
    
    def find_near_rhymes(self, word: str, max_results: int = 15) -> List[str]:
        """Find slant/near rhymes (similar but not exact)"""
        word = word.lower().strip()
        near_rhymes = []
        
        # Get phonemes
        phones = pronouncing.phones_for_word(word)
        if not phones:
            return []
        
        # Get last vowel sound
        primary_phones = phones[0]
        vowel_sounds = re.findall(r'[AEIOU]+[A-Z]*\d?', primary_phones)
        
        if vowel_sounds:
            # Find words with similar vowel patterns
            last_vowel = vowel_sounds[-1] if vowel_sounds else None
            if last_vowel:
                # This is simplified - a full implementation would use phoneme matching
                pass
        
        # Fallback: use ending similarity
        ending = word[-2:] if len(word) > 2 else word
        near_rhymes = [r for r in self.find_rhymes(word, 50) if r.endswith(ending)]
        
        return near_rhymes[:max_results]
    
    def get_synonyms(self, category: str) -> List[str]:
        """Get hip-hop slang synonyms for a category"""
        category = category.lower()
        return self.HIP_HOP_VOCAB.get(category, [])
    
    def get_all_categories(self) -> List[str]:
        """Get all available slang categories"""
        return list(self.HIP_HOP_VOCAB.keys())
    
    def find_multisyllabic_rhymes(self, word: str) -> List[str]:
        """Find multisyllabic rhyme matches"""
        word = word.lower()
        matches = []
        
        for pattern, words in self.MULTI_SYLLABLE_GROUPS.items():
            if word.endswith(pattern) or word in words:
                matches.extend([w for w in words if w != word])
        
        return matches
    
    def suggest_rhyme_words(self, line: str, max_per_word: int = 5) -> Dict[str, List[str]]:
        """Suggest rhymes for key words in a line"""
        words = re.findall(r'\b[a-zA-Z]+\b', line)
        suggestions = {}
        
        # Focus on last word (most important for end rhyme)
        if words:
            last_word = words[-1].lower()
            rhymes = self.find_rhymes(last_word, max_per_word * 2)
            if rhymes:
                suggestions[last_word] = rhymes[:max_per_word]
        
        # Also suggest for important words (nouns, verbs)
        for word in words[:-1]:
            if len(word) > 4:  # Skip short words
                rhymes = self.find_rhymes(word.lower(), max_per_word)
                if rhymes:
                    suggestions[word.lower()] = rhymes
        
        return suggestions
    
    def get_rhyme_info(self, word: str) -> Dict:
        """Get comprehensive rhyme information for a word"""
        word = word.lower().strip()
        
        phones = pronouncing.phones_for_word(word)
        
        return {
            "word": word,
            "phonemes": phones[0] if phones else None,
            "syllables": pronouncing.syllable_count(phones[0]) if phones else 0,
            "exact_rhymes": self.find_rhymes(word, 10),
            "multisyllabic": self.find_multisyllabic_rhymes(word),
            "stresses": pronouncing.stresses(phones[0]) if phones else None
        }

    def find_pocket_rhymes(self, word: str, source_syllables: int = None, source_stresses: str = None, max_results: int = 15) -> List[str]:
        """Find rhymes that fit the same 'pocket' (syllable count and stress pattern)"""
        word = word.lower().strip()
        
        # If no target pattern provided, get from the word itself
        if source_syllables is None or source_stresses is None:
            phones = pronouncing.phones_for_word(word)
            if not phones:
                return []
            source_syllables = pronouncing.syllable_count(phones[0])
            source_stresses = pronouncing.stresses(phones[0])

        all_rhymes = pronouncing.rhymes(word)
        pocket_rhymes = []
        
        for r_word in all_rhymes:
            r_phones = pronouncing.phones_for_word(r_word)
            if not r_phones:
                continue
            
            # Check if any variant matches the pocket
            for variant in r_phones:
                r_syl = pronouncing.syllable_count(variant)
                r_stress = pronouncing.stresses(variant)
                
                if r_syl == source_syllables and r_stress == source_stresses:
                    pocket_rhymes.append(r_word)
                    break
            
            if len(pocket_rhymes) >= max_results:
                break
        
        return pocket_rhymes
