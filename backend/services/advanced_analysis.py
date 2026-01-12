"""
Advanced Analysis Services
- Punchline scoring
- Metaphor/Simile generation
- Complexity scoring
- Imagery analysis
"""
from typing import List, Dict, Optional
import re


class PunchlineEngine:
    """Score and generate punchlines"""
    
    # Punchline techniques
    TECHNIQUES = {
        "contrast": ["but", "yet", "although", "however", "while"],
        "wordplay": ["like", "as", "ain't", "get it", "you know"],
        "callback": ["remember", "told you", "said"],
        "reversal": ["flip", "switch", "turn", "reverse"],
    }
    
    def score_punchline(self, line: str) -> Dict:
        """Score a line's punchline potential (0-100)"""
        line_lower = line.lower()
        score = 0
        techniques_used = []
        
        # Check for contrast
        for word in self.TECHNIQUES["contrast"]:
            if word in line_lower:
                score += 15
                techniques_used.append("contrast")
                break
        
        # Check for wordplay indicators
        for word in self.TECHNIQUES["wordplay"]:
            if word in line_lower:
                score += 20
                techniques_used.append("wordplay")
                break
        
        # Check for callback
        for word in self.TECHNIQUES["callback"]:
            if word in line_lower:
                score += 10
                techniques_used.append("callback")
                break
        
        # Check for reversal
        for word in self.TECHNIQUES["reversal"]:
            if word in line_lower:
                score += 15
                techniques_used.append("reversal")
                break
        
        # Word count bonus (optimal 8-12 words)
        word_count = len(line.split())
        if 8 <= word_count <= 12:
            score += 15
        elif 6 <= word_count <= 14:
            score += 10
        
        # Rhyme density bonus
        words = line.split()
        rhyme_pairs = self._count_internal_rhymes(words)
        score += min(20, rhyme_pairs * 5)
        
        return {
            "score": min(100, score),
            "techniques": techniques_used,
            "word_count": word_count,
            "internal_rhymes": rhyme_pairs
        }
    
    def _count_internal_rhymes(self, words: List[str]) -> int:
        """Count internal rhyme pairs"""
        endings = [self._get_ending(w) for w in words if len(w) > 2]
        seen = {}
        pairs = 0
        for ending in endings:
            if ending in seen:
                pairs += 1
            seen[ending] = True
        return pairs
    
    def _get_ending(self, word: str) -> str:
        """Get word ending for rhyme matching"""
        word = word.lower().strip(".,!?;:'\"")
        vowels = 'aeiouy'
        for i, char in enumerate(word):
            if char in vowels:
                return word[i:]
        return word[-2:] if len(word) >= 2 else word
    
    def detect_contrast(self, line: str) -> bool:
        """Check if line contains contrast"""
        line_lower = line.lower()
        for word in self.TECHNIQUES["contrast"]:
            if word in line_lower:
                return True
        return False
    
    def generate_punchline_starters(self, theme: str) -> List[str]:
        """Generate punchline starter phrases"""
        starters = [
            f"They say {theme}, but I...",
            f"You thought {theme}? Nah...",
            f"Every time {theme}, I just...",
            f"While they {theme}, I'm...",
            f"Flip the {theme}, now watch me...",
        ]
        return starters


class MetaphorGenerator:
    """Generate metaphors and similes"""
    
    # Common metaphor frames
    FRAMES = {
        "success": ["mountain", "throne", "crown", "diamond", "gold"],
        "struggle": ["storm", "battle", "war", "fire", "darkness"],
        "money": ["paper", "bread", "trees", "ocean", "rain"],
        "time": ["river", "thief", "healer", "clock", "sand"],
        "love": ["drug", "fire", "game", "maze", "ocean"],
    }
    
    def generate_metaphors(self, concept: str, count: int = 5) -> List[str]:
        """Generate metaphors for a concept"""
        concept_lower = concept.lower()
        
        # Find matching frame
        frame = None
        for key, values in self.FRAMES.items():
            if key in concept_lower or concept_lower in key:
                frame = values
                break
        
        if not frame:
            frame = self.FRAMES["success"]  # Default
        
        metaphors = []
        for item in frame[:count]:
            metaphors.append(f"{concept} is a {item}")
            metaphors.append(f"My {concept}'s like a {item}")
        
        return metaphors[:count]
    
    def generate_similes(self, word: str, count: int = 5) -> List[str]:
        """Generate similes for a word"""
        comparisons = [
            "lion", "king", "rocket", "diamond", "storm",
            "fire", "ice", "blade", "wave", "legend"
        ]
        
        similes = []
        for comp in comparisons[:count]:
            similes.append(f"{word} like a {comp}")
            similes.append(f"Cold as {comp}")
        
        return similes[:count]
    
    def complete_simile(self, starter: str) -> str:
        """Complete a simile starter"""
        if "like a" in starter.lower():
            return starter + " on a mission"
        return starter + " like a boss"


class ComplexityScorer:
    """Score lyric complexity"""
    
    def score_verse(self, lines: List[str]) -> Dict:
        """Score verse complexity (0-100)"""
        if not lines:
            return {"score": 0, "breakdown": {}}
        
        total_words = 0
        long_words = 0  # 3+ syllables
        unique_words = set()
        
        for line in lines:
            words = line.lower().split()
            total_words += len(words)
            
            for word in words:
                word = re.sub(r'[^a-z]', '', word)
                if len(word) > 2:
                    unique_words.add(word)
                    if self._count_syllables(word) >= 3:
                        long_words += 1
        
        # Calculate metrics
        vocab_diversity = len(unique_words) / max(1, total_words)
        multi_syllable_ratio = long_words / max(1, total_words)
        
        score = int(
            vocab_diversity * 40 + 
            multi_syllable_ratio * 30 + 
            min(30, len(lines) * 3)
        )
        
        return {
            "score": min(100, score),
            "breakdown": {
                "vocabulary_diversity": round(vocab_diversity, 2),
                "multi_syllable_ratio": round(multi_syllable_ratio, 2),
                "unique_words": len(unique_words),
                "total_words": total_words
            }
        }
    
    def _count_syllables(self, word: str) -> int:
        """Count syllables in a word"""
        vowels = 'aeiouy'
        count = 0
        prev_vowel = False
        
        for char in word.lower():
            is_vowel = char in vowels
            if is_vowel and not prev_vowel:
                count += 1
            prev_vowel = is_vowel
        
        return max(1, count)


class ImageryAnalyzer:
    """Analyze imagery density in lyrics"""
    
    # Imagery categories
    IMAGERY_WORDS = {
        "visual": ["see", "look", "watch", "shine", "bright", "dark", "color", "gold", "silver"],
        "auditory": ["hear", "sound", "loud", "quiet", "ring", "beat", "bass"],
        "tactile": ["feel", "touch", "cold", "hot", "smooth", "rough"],
        "olfactory": ["smell", "scent", "fresh", "stink"],
        "gustatory": ["taste", "sweet", "bitter", "sour"],
    }
    
    def analyze_imagery(self, lines: List[str]) -> Dict:
        """Analyze imagery density"""
        text = " ".join(lines).lower()
        words = text.split()
        
        counts = {cat: 0 for cat in self.IMAGERY_WORDS}
        
        for word in words:
            word = re.sub(r'[^a-z]', '', word)
            for category, keywords in self.IMAGERY_WORDS.items():
                if word in keywords:
                    counts[category] += 1
        
        total = sum(counts.values())
        density = total / max(1, len(words))
        
        return {
            "total_imagery_words": total,
            "density": round(density, 3),
            "by_category": counts,
            "dominant_sense": max(counts, key=counts.get) if total > 0 else None
        }
