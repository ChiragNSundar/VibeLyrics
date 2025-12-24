"""
Indian Rhyme Finder
Comprehensive rhyme dictionary for Hindi and Kannada (romanized)
Returns rhyming words for any input word
"""
from typing import List, Dict


class IndianRhymeFinder:
    """
    Finds rhyming words for Hindi and Kannada (romanized).
    Unlike English, Indian rhymes are primarily based on vowel endings.
    """
    
    def __init__(self):
        # Build rhyme groups - words that rhyme with each other
        self.kannada_rhyme_groups = {
            # Pronoun rhymes
            "aanu_group": ["naanu", "nane", "neenu", "naavu", "neevu", "avanu", "avalu"],
            "anu_group": ["naanu", "avanu", "huduganu", "maganu", "devaru"],
            "alu_group": ["avalu", "magalu", "hudugalu", "hennu"],
            
            # Verb rhymes (present/future)
            "odu_group": ["maadodu", "hogodu", "barodu", "nododu", "helodu", "kelodu"],
            "ona_group": ["maadona", "hogona", "barona", "nodona", "helona", "kelona"],
            "ali_group": ["maadali", "hogali", "barali", "nodali", "helali"],
            
            # Verb rhymes (past)
            "adu_group": ["hogadu", "maadadu", "nodadu", "heladu", "keladu", "aagadu"],
            "itu_group": ["hogitu", "maaditu", "noditu", "helitu", "banditu"],
            "ide_group": ["ide", "hogide", "bandide", "madide", "nodide", "helide"],
            
            # Noun rhymes
            "asu_group": ["manasu", "hanasu", "samayasu"],
            "eeti_group": ["preeti", "preethi", "reethi", "neeti"],
            "ema_group": ["prema", "sneha", "leha"],
            "osha_group": ["santhosha", "harsha", "kosha"],
            "ukha_group": ["dukha", "sukha", "mukha"],
            
            # Family rhymes
            "amma_group": ["amma", "ajamma", "tamma", "akka"],
            "appa_group": ["appa", "thatha", "anna"],
            
            # Nature rhymes
            "aali_group": ["gaali", "maali", "jaali", "thaali"],
            "eeru_group": ["neeru", "beeru", "veeru"],
            "ara_group": ["mara", "tara", "hara", "sara"],
            
            # Adjective rhymes
            "odda_group": ["dodda", "gadda", "hodda"],
            "ikka_group": ["chikka", "tikka", "dikka"],
            "osa_group": ["hosa", "dosa", "kosa"],
            
            # Action rhymes  
            "ogi_group": ["hogi", "nogi", "yogi"],
            "odi_group": ["nodi", "hodi", "kodi"],
            "odu_group2": ["haadu", "aadu", "kaadu", "naadu"],
        }
        
        self.hindi_rhyme_groups = {
            # Love/Emotion
            "yaar_group": ["yaar", "pyaar", "ikraar", "intezaar", "sitaar", "bahaar"],
            "ishq_group": ["ishq", "dil", "pal", "hal", "mahal"],
            "aan_group": ["jaan", "maan", "shaan", "armaan", "meherbaan", "jahan"],
            "aat_group": ["raat", "baat", "saat", "mulaqaat", "barsat", "jazbaat"],
            
            # People
            "ost_group": ["dost", "dushmani", "zindagi"],
            "ai_group": ["bhai", "hai", "mai", "shai", "khai"],
            
            # Nature
            "aand_group": ["chaand", "baand", "haand"],
            "aman_group": ["aasman", "jahan", "makaan", "imaan"],
            "een_group": ["zameen", "machine", "routine", "haseen"],
            
            # Actions
            "ana_group": ["jaana", "aana", "sunana", "banana", "khana", "gaana"],
            "na_group": ["bolna", "khona", "rona", "sona", "dona"],
            
            # Abstract
            "agi_group": ["zindagi", "aashiqi", "begunahi", "ruswaai"],
            "at_group": ["mohabbat", "izzat", "shohrat", "hikmat"],
        }
        
        # Build reverse lookup
        self.word_to_group = {}
        self._build_reverse_lookup()
    
    def _build_reverse_lookup(self):
        """Build word -> group mapping"""
        for group_name, words in self.kannada_rhyme_groups.items():
            for word in words:
                if word not in self.word_to_group:
                    self.word_to_group[word] = []
                self.word_to_group[word].append(("kannada", group_name))
        
        for group_name, words in self.hindi_rhyme_groups.items():
            for word in words:
                if word not in self.word_to_group:
                    self.word_to_group[word] = []
                self.word_to_group[word].append(("hindi", group_name))
    
    def find_rhymes(self, word: str, limit: int = 10) -> List[str]:
        """Find words that rhyme with the given word"""
        word = word.lower().strip()
        rhymes = set()
        
        # 1. Check if word is in our groups
        if word in self.word_to_group:
            for lang, group_name in self.word_to_group[word]:
                if lang == "kannada":
                    rhymes.update(self.kannada_rhyme_groups.get(group_name, []))
                else:
                    rhymes.update(self.hindi_rhyme_groups.get(group_name, []))
        
        # 2. Find by ending pattern
        rhymes.update(self._find_by_ending(word))
        
        # Remove the original word
        rhymes.discard(word)
        
        return list(rhymes)[:limit]
    
    def _find_by_ending(self, word: str) -> List[str]:
        """Find rhymes by matching ending patterns"""
        if len(word) < 2:
            return []
        
        ending = word[-2:]
        ending3 = word[-3:] if len(word) >= 3 else ""
        
        matches = []
        
        # Check all groups for ending matches
        for group_name, words in {**self.kannada_rhyme_groups, **self.hindi_rhyme_groups}.items():
            for w in words:
                if w != word and (w.endswith(ending) or (ending3 and w.endswith(ending3))):
                    matches.append(w)
        
        return matches
    
    def get_rhyme_suggestions(self, word: str) -> Dict:
        """Get comprehensive rhyme suggestions"""
        word = word.lower().strip()
        
        rhymes = self.find_rhymes(word, limit=15)
        
        # Detect language
        lang = "unknown"
        if word in self.word_to_group:
            lang = self.word_to_group[word][0][0]
        elif self._looks_kannada(word):
            lang = "kannada"
        elif self._looks_hindi(word):
            lang = "hindi"
        
        return {
            "word": word,
            "language": lang,
            "rhymes": rhymes,
            "ending_pattern": word[-2:] if len(word) >= 2 else word,
            "suggestions_count": len(rhymes)
        }
    
    def _looks_kannada(self, word: str) -> bool:
        """Heuristic to detect Kannada words"""
        kannada_endings = ['adu', 'idu', 'odu', 'anu', 'alu', 'ide', 'iddey', 'ona', 'ali']
        return any(word.endswith(e) for e in kannada_endings)
    
    def _looks_hindi(self, word: str) -> bool:
        """Heuristic to detect Hindi words"""
        hindi_endings = ['aan', 'een', 'aat', 'ana', 'agi', 'at']
        return any(word.endswith(e) for e in hindi_endings)


# Singleton
_indian_rhyme_finder = None

def get_indian_rhyme_finder() -> IndianRhymeFinder:
    global _indian_rhyme_finder
    if _indian_rhyme_finder is None:
        _indian_rhyme_finder = IndianRhymeFinder()
    return _indian_rhyme_finder
