"""
Advanced Analysis Services
- AI-Powered Punchline Engine
- AI-Powered Metaphor/Simile Generator
- Complexity scoring
- Imagery analysis
"""
from typing import List, Dict, Optional
import re


class PunchlineEngine:
    """Score and generate punchlines — rule-based scoring + AI generation"""
    
    # Punchline techniques for scoring
    TECHNIQUES = {
        "contrast": ["but", "yet", "although", "however", "while", "though", "still"],
        "wordplay": ["like", "as", "ain't", "get it", "you know", "no pun", "literally"],
        "callback": ["remember", "told you", "said", "back when", "used to"],
        "reversal": ["flip", "switch", "turn", "reverse", "opposite", "plot twist"],
        "double_entendre": ["two ways", "both", "either", "mean"],
        "homophone": [],  # Detected dynamically
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
        
        # Double entendre detection — words with multiple meanings
        for word in self.TECHNIQUES["double_entendre"]:
            if word in line_lower:
                score += 20
                techniques_used.append("double_entendre")
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
        if rhyme_pairs >= 2:
            techniques_used.append("internal_rhyme")
        
        # Alliteration bonus
        alliteration_count = self._count_alliteration(words)
        if alliteration_count >= 2:
            score += 10
            techniques_used.append("alliteration")
        
        return {
            "score": min(100, score),
            "techniques": techniques_used,
            "word_count": word_count,
            "internal_rhymes": rhyme_pairs,
            "alliteration": alliteration_count
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
    
    def _count_alliteration(self, words: List[str]) -> int:
        """Count alliterative pairs"""
        clean = [w.lower().strip(".,!?;:'\"") for w in words if len(w) > 1]
        count = 0
        for i in range(len(clean) - 1):
            if clean[i][0] == clean[i + 1][0] and clean[i][0].isalpha():
                count += 1
        return count
    
    def detect_contrast(self, line: str) -> bool:
        """Check if line contains contrast"""
        line_lower = line.lower()
        for word in self.TECHNIQUES["contrast"]:
            if word in line_lower:
                return True
        return False
    
    def generate_punchline_starters(self, theme: str) -> List[str]:
        """Generate punchline starter phrases (rule-based fallback)"""
        starters = [
            f"They say {theme}, but I...",
            f"You thought {theme}? Nah...",
            f"Every time {theme}, I just...",
            f"While they {theme}, I'm...",
            f"Flip the {theme}, now watch me...",
        ]
        return starters
    
    async def generate_ai_punchlines(
        self, theme: str, lines: List[str] = None,
        mood: str = None, count: int = 5
    ) -> Dict:
        """Generate punchlines using AI provider"""
        from .ai_provider import get_ai_provider
        
        provider = get_ai_provider()
        if not provider.is_available():
            return {
                "punchlines": self.generate_punchline_starters(theme),
                "source": "rule-based"
            }
        
        context_lines = "\n".join(lines[-5:]) if lines else "None yet"
        mood_str = mood or "confident"
        
        prompt = f"""You are a master hip-hop lyricist and punchline writer. Generate {count} hard-hitting punchlines about the theme: "{theme}".

Mood/energy: {mood_str}
Recent bars for context:
{context_lines}

Rules:
- Each punchline should be a COMPLETE bar (one line)
- Use wordplay, double entendres, metaphors, or contrasts
- Make them clever — the kind that makes the crowd go "ohhh!"
- Match the mood/energy
- No generic filler — every word should hit

Return ONLY the punchlines, one per line, no numbering or bullets."""

        try:
            response = await provider.answer_question(prompt, None)
            punchlines = [
                line.strip("- •").strip()
                for line in response.strip().split('\n')
                if line.strip() and len(line.strip()) > 5
            ][:count]
            
            # Score each generated punchline
            scored = []
            for p in punchlines:
                score_data = self.score_punchline(p)
                scored.append({
                    "line": p,
                    "score": score_data["score"],
                    "techniques": score_data["techniques"]
                })
            
            return {
                "punchlines": scored,
                "source": "ai",
                "theme": theme,
                "mood": mood_str
            }
        except Exception as e:
            return {
                "punchlines": self.generate_punchline_starters(theme),
                "source": "rule-based",
                "error": str(e)
            }


class MetaphorGenerator:
    """Generate metaphors and similes — static fallback + AI generation"""
    
    # Common metaphor frames (fallback)
    FRAMES = {
        "success": ["mountain", "throne", "crown", "diamond", "gold", "summit", "peak"],
        "struggle": ["storm", "battle", "war", "fire", "darkness", "maze", "quicksand"],
        "money": ["paper", "bread", "trees", "ocean", "rain", "river", "waterfall"],
        "time": ["river", "thief", "healer", "clock", "sand", "ghost", "shadow"],
        "love": ["drug", "fire", "game", "maze", "ocean", "rollercoaster", "gravity"],
        "power": ["lion", "thunder", "earthquake", "volcano", "hurricane", "titan"],
        "loyalty": ["anchor", "chain", "root", "pillar", "shield", "rock"],
        "ambition": ["rocket", "arrow", "eagle", "flame", "engine", "bullet"],
    }
    
    def generate_metaphors(self, concept: str, count: int = 5) -> List[str]:
        """Generate metaphors for a concept (rule-based fallback)"""
        concept_lower = concept.lower()
        
        # Find matching frame
        frame = None
        for key, values in self.FRAMES.items():
            if key in concept_lower or concept_lower in key:
                frame = values
                break
        
        if not frame:
            frame = self.FRAMES["success"]
        
        metaphors = []
        for item in frame[:count]:
            metaphors.append(f"{concept} is a {item}")
        
        return metaphors[:count]
    
    def generate_similes(self, word: str, count: int = 5) -> List[str]:
        """Generate similes for a word (rule-based fallback)"""
        comparisons = [
            "lion on the hunt", "king without a crown", "rocket breaking through",
            "diamond in the rough", "storm rolling in", "fire nobody can tame",
            "blade cutting deep", "wave crashing down", "legend in the making",
            "shadow in the dark"
        ]
        
        similes = []
        for comp in comparisons[:count]:
            similes.append(f"{word} like a {comp}")
        
        return similes[:count]
    
    def complete_simile(self, starter: str) -> str:
        """Complete a simile starter (rule-based fallback)"""
        if "like a" in starter.lower():
            return starter + " on a mission, no intermission"
        return starter + " like a boss, never taking a loss"
    
    async def generate_ai_metaphors(
        self, concept: str, context: List[str] = None, count: int = 5
    ) -> Dict:
        """Generate metaphors using AI"""
        from .ai_provider import get_ai_provider
        
        provider = get_ai_provider()
        if not provider.is_available():
            return {
                "metaphors": self.generate_metaphors(concept, count),
                "source": "rule-based"
            }
        
        context_str = "\n".join(context[-3:]) if context else "None"
        
        prompt = f"""You are a creative hip-hop lyricist. Generate {count} powerful, original METAPHORS for the concept: "{concept}".

Recent bars for context:
{context_str}

Rules:
- Each metaphor should be a vivid, original comparison (NOT cliché)
- Format: "[concept] is [metaphor]" or weave it into a bar
- Think abstract, cinematic, emotionally resonant
- Avoid overused comparisons like "life is a journey"
- Make them suitable for hip-hop — gritty, real, impactful

Return ONLY the metaphors, one per line, no numbering."""

        try:
            response = await provider.answer_question(prompt, None)
            metaphors = [
                line.strip("- •").strip()
                for line in response.strip().split('\n')
                if line.strip() and len(line.strip()) > 5
            ][:count]
            
            return {
                "metaphors": metaphors,
                "source": "ai",
                "concept": concept
            }
        except Exception as e:
            return {
                "metaphors": self.generate_metaphors(concept, count),
                "source": "rule-based",
                "error": str(e)
            }
    
    async def generate_ai_similes(
        self, word: str, context: List[str] = None, count: int = 5
    ) -> Dict:
        """Generate similes using AI"""
        from .ai_provider import get_ai_provider
        
        provider = get_ai_provider()
        if not provider.is_available():
            return {
                "similes": self.generate_similes(word, count),
                "source": "rule-based"
            }
        
        context_str = "\n".join(context[-3:]) if context else "None"
        
        prompt = f"""You are a creative hip-hop lyricist. Generate {count} fire SIMILES using the word/concept: "{word}".

Recent context:
{context_str}

Rules:
- Format: "[word] like [comparison]" or "Cold as [comparison]"
- Each simile should paint a vivid picture
- Keep them hip-hop appropriate — street-smart, clever
- Avoid generic comparisons

Return ONLY the similes, one per line, no numbering."""

        try:
            response = await provider.answer_question(prompt, None)
            similes = [
                line.strip("- •").strip()
                for line in response.strip().split('\n')
                if line.strip() and len(line.strip()) > 5
            ][:count]
            
            return {
                "similes": similes,
                "source": "ai",
                "word": word
            }
        except Exception as e:
            return {
                "similes": self.generate_similes(word, count),
                "source": "rule-based",
                "error": str(e)
            }


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
