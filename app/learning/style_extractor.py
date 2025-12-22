"""
Style Extractor
Analyzes user's writing patterns to build a style profile
"""
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from collections import Counter

from app.config import Config
from app.analysis import RhymeDetector, SyllableCounter, ComplexityScorer


class StyleExtractor:
    """Extracts and maintains user's writing style profile"""
    
    def __init__(self):
        self.rhyme_detector = RhymeDetector()
        self.syllable_counter = SyllableCounter()
        self.complexity_scorer = ComplexityScorer()
        self.style_path = Config.USER_STYLE_PATH
        self._style_data = None
    
    @property
    def style_data(self) -> Dict:
        """Lazy load style data"""
        if self._style_data is None:
            self._style_data = self._load_style()
        return self._style_data
    
    def _load_style(self) -> Dict:
        """Load style data from JSON file"""
        if self.style_path.exists():
            try:
                with open(self.style_path, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return self._get_default_style()
    
    def _get_default_style(self) -> Dict:
        """Get default style structure"""
        return {
            "profile": {
                "name": "default",
                "created_at": None,
                "last_updated": None
            },
            "preferences": {
                "default_bpm": 140,
                "preferred_provider": "openai",
                "rhyme_style": "mixed",
                "complexity_level": "medium"
            },
            "vocabulary": {
                "favorite_words": [],
                "favorite_slangs": [],
                "avoided_words": []
            },
            "themes": {
                "preferred": [],
                "recent": []
            },
            "learned_patterns": {
                "rhyme_preferences": [],
                "flow_patterns": [],
                "avg_syllables_per_line": 0,
                "preferred_rhyme_schemes": [],
                "corrections_applied": 0
            },
            "statistics": {
                "total_lines_written": 0,
                "total_sessions": 0,
                "avg_complexity_score": 0.0
            }
        }
    
    def save_style(self):
        """Save current style data to JSON file"""
        from datetime import datetime
        self.style_data["profile"]["last_updated"] = datetime.now().isoformat()
        
        # Ensure directory exists
        self.style_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.style_path, 'w') as f:
            json.dump(self.style_data, f, indent=2)
    
    def analyze_lines(self, lines: List[str]) -> Dict:
        """
        Analyze a set of lines and extract style patterns
        """
        if not lines:
            return {}
        
        # Get complexity scores
        verse_score = self.complexity_scorer.score_verse(lines)
        
        # Get rhyme scheme
        rhyme_scheme = self.rhyme_detector.get_rhyme_scheme_string(lines)
        
        # Analyze syllable patterns
        syllables = [self.syllable_counter.count_line_syllables(line) for line in lines]
        avg_syllables = sum(syllables) / len(syllables)
        
        # Find common words
        all_words = ' '.join(lines).lower().split()
        word_counts = Counter(all_words)
        common_words = [word for word, count in word_counts.most_common(20) 
                       if len(word) > 3 and count > 1]
        
        return {
            "complexity": verse_score,
            "rhyme_scheme": rhyme_scheme,
            "avg_syllables_per_line": round(avg_syllables, 1),
            "syllable_range": (min(syllables), max(syllables)),
            "common_words": common_words,
            "line_count": len(lines)
        }
    
    def update_from_session(self, lines: List[str]):
        """
        Update style profile based on a writing session
        """
        analysis = self.analyze_lines(lines)
        
        if not analysis:
            return
        
        # Update statistics
        stats = self.style_data["statistics"]
        stats["total_lines_written"] = stats.get("total_lines_written", 0) + len(lines)
        stats["total_sessions"] = stats.get("total_sessions", 0) + 1
        
        # Running average for complexity
        old_avg = stats.get("avg_complexity_score", 0.0)
        old_count = stats.get("total_sessions", 1) - 1
        new_score = analysis["complexity"].get("overall", 0)
        stats["avg_complexity_score"] = round(
            (old_avg * old_count + new_score) / stats["total_sessions"], 2
        )
        
        # Update learned patterns
        patterns = self.style_data["learned_patterns"]
        
        # Update average syllables
        old_syllables = patterns.get("avg_syllables_per_line", 0)
        patterns["avg_syllables_per_line"] = round(
            (old_syllables * old_count + analysis["avg_syllables_per_line"]) / stats["total_sessions"], 1
        )
        
        # Track rhyme scheme preference
        rhyme_schemes = patterns.get("preferred_rhyme_schemes", [])
        rhyme_schemes.append(analysis["rhyme_scheme"])
        # Keep last 20 schemes
        patterns["preferred_rhyme_schemes"] = rhyme_schemes[-20:]
        
        # Update vocabulary
        vocab = self.style_data["vocabulary"]
        favorite_words = set(vocab.get("favorite_words", []))
        favorite_words.update(analysis["common_words"][:10])
        vocab["favorite_words"] = list(favorite_words)[:50]  # Cap at 50
        
        self.save_style()
    
    def get_style_summary(self) -> Dict:
        """
        Get a summary of the user's style for AI context
        """
        style = self.style_data
        defaults = self._get_default_style()
        
        # Safely access nested keys with defaults
        preferences = style.get("preferences", defaults["preferences"])
        vocabulary = style.get("vocabulary", defaults["vocabulary"])
        themes = style.get("themes", defaults["themes"])
        learned_patterns = style.get("learned_patterns", defaults["learned_patterns"])
        statistics = style.get("statistics", defaults["statistics"])
        
        return {
            "rhyme_style": preferences.get("rhyme_style", "mixed"),
            "complexity_level": preferences.get("complexity_level", "medium"),
            "favorite_words": vocabulary.get("favorite_words", [])[:10],
            "favorite_slangs": vocabulary.get("favorite_slangs", [])[:5],
            "avoided_words": vocabulary.get("avoided_words", []),
            "preferred_themes": themes.get("preferred", [])[:5],
            "avg_syllables": learned_patterns.get("avg_syllables_per_line", 12),
            "common_rhyme_schemes": self._get_common_schemes(),
            "complexity_score": statistics.get("avg_complexity_score", 0.5)
        }
    
    def _get_common_schemes(self) -> List[str]:
        """Get most common rhyme schemes used"""
        schemes = self.style_data["learned_patterns"].get("preferred_rhyme_schemes", [])
        if not schemes:
            return ["AABB", "ABAB"]  # Defaults
        
        scheme_counts = Counter(schemes)
        return [scheme for scheme, _ in scheme_counts.most_common(3)]
    
    def update_preference(self, key: str, value: Any):
        """Update a specific preference"""
        if key in self.style_data["preferences"]:
            self.style_data["preferences"][key] = value
            self.save_style()
    
    def add_favorite_word(self, word: str):
        """Add a word to favorites"""
        favorites = self.style_data["vocabulary"]["favorite_words"]
        if word.lower() not in favorites:
            favorites.append(word.lower())
            self.save_style()
    
    def add_avoided_word(self, word: str):
        """Add a word to avoided list"""
        avoided = self.style_data["vocabulary"]["avoided_words"]
        if word.lower() not in avoided:
            avoided.append(word.lower())
            self.save_style()
    
    def add_preferred_theme(self, theme: str):
        """Add a preferred theme"""
        themes = self.style_data["themes"]["preferred"]
        if theme.lower() not in themes:
            themes.append(theme.lower())
            self.save_style()
