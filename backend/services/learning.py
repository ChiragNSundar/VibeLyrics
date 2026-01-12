"""
Learning System Services
- Style extraction
- Vocabulary management
- User preference learning
"""
import json
import os
from typing import Dict, List, Set, Optional
from collections import Counter
from pathlib import Path


class StyleExtractor:
    """Extract and learn user's writing style"""
    
    DATA_FILE = "data/user_style.json"
    
    def __init__(self):
        self.style_data = self._load_style()
    
    def _load_style(self) -> Dict:
        """Load style data from file"""
        if os.path.exists(self.DATA_FILE):
            try:
                with open(self.DATA_FILE, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return self._get_default_style()
    
    def _get_default_style(self) -> Dict:
        """Default style profile"""
        return {
            "vocabulary": {
                "favorite_words": [],
                "avoided_words": [],
                "slang_preference": "moderate"
            },
            "structure": {
                "avg_line_length": 8,
                "preferred_sections": ["Verse", "Chorus", "Bridge"]
            },
            "rhyme": {
                "scheme_preference": "AABB",
                "internal_rhyme_frequency": "moderate"
            },
            "themes": {
                "preferred": [],
                "explored": []
            }
        }
    
    def save_style(self):
        """Save style data"""
        os.makedirs(os.path.dirname(self.DATA_FILE), exist_ok=True)
        with open(self.DATA_FILE, 'w') as f:
            json.dump(self.style_data, f, indent=2)
    
    def analyze_lines(self, lines: List[str]) -> Dict:
        """Analyze lines to extract style patterns"""
        if not lines:
            return {}
        
        words = []
        for line in lines:
            words.extend(line.lower().split())
        
        # Word frequency
        word_freq = Counter(words)
        common_words = word_freq.most_common(10)
        
        # Average line length
        avg_length = sum(len(line.split()) for line in lines) / len(lines)
        
        return {
            "common_words": [w for w, c in common_words],
            "avg_line_length": round(avg_length, 1),
            "total_lines": len(lines),
            "unique_words": len(set(words))
        }
    
    def learn_from_session(self, lines: List[str]):
        """Update style from a writing session"""
        analysis = self.analyze_lines(lines)
        
        # Update average line length
        current_avg = self.style_data["structure"]["avg_line_length"]
        new_avg = analysis.get("avg_line_length", current_avg)
        self.style_data["structure"]["avg_line_length"] = round(
            (current_avg + new_avg) / 2, 1
        )
        
        self.save_style()
    
    def get_style_summary(self) -> Dict:
        """Get summary of learned style"""
        return {
            "vocabulary_size": len(self.style_data["vocabulary"]["favorite_words"]),
            "avg_line_length": self.style_data["structure"]["avg_line_length"],
            "preferred_themes": self.style_data["themes"]["preferred"][:5],
            "rhyme_preference": self.style_data["rhyme"]["scheme_preference"]
        }
    
    def update_preference(self, key: str, value):
        """Update a specific preference"""
        if key == "preferred_provider":
            pass  # Handled by settings
        elif key == "default_bpm":
            pass  # Handled by settings
        else:
            # Generic update
            pass
        self.save_style()
    
    def add_preferred_theme(self, theme: str):
        """Add a preferred theme"""
        themes = self.style_data["themes"]["preferred"]
        if theme not in themes:
            themes.append(theme)
            self.save_style()


class VocabularyManager:
    """Manage user's vocabulary preferences"""
    
    DATA_FILE = "data/vocabulary.json"
    
    def __init__(self):
        self.favorite_words: Set[str] = set()
        self.favorite_slangs: Set[str] = set()
        self.avoided_words: Set[str] = set()
        self.word_frequency: Counter = Counter()
        self._load_vocabulary()
    
    def _load_vocabulary(self):
        """Load vocabulary from file"""
        if os.path.exists(self.DATA_FILE):
            try:
                with open(self.DATA_FILE, 'r') as f:
                    data = json.load(f)
                    self.favorite_words = set(data.get("favorites", []))
                    self.favorite_slangs = set(data.get("slangs", []))
                    self.avoided_words = set(data.get("avoided", []))
                    self.word_frequency = Counter(data.get("frequency", {}))
            except Exception:
                pass
    
    def _save_vocabulary(self):
        """Save vocabulary to file"""
        os.makedirs(os.path.dirname(self.DATA_FILE), exist_ok=True)
        data = {
            "favorites": list(self.favorite_words),
            "slangs": list(self.favorite_slangs),
            "avoided": list(self.avoided_words),
            "frequency": dict(self.word_frequency.most_common(500))
        }
        with open(self.DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    
    def add_favorite(self, word: str, is_slang: bool = False):
        """Add a favorite word"""
        word = word.lower().strip()
        if is_slang:
            self.favorite_slangs.add(word)
        else:
            self.favorite_words.add(word)
        self._save_vocabulary()
    
    def add_avoided(self, word: str):
        """Add an avoided word"""
        self.avoided_words.add(word.lower().strip())
        self._save_vocabulary()
    
    def remove_favorite(self, word: str):
        """Remove from favorites"""
        word = word.lower().strip()
        self.favorite_words.discard(word)
        self.favorite_slangs.discard(word)
        self._save_vocabulary()
    
    def remove_avoided(self, word: str):
        """Remove from avoided"""
        self.avoided_words.discard(word.lower().strip())
        self._save_vocabulary()
    
    def track_usage(self, words: List[str]):
        """Track word usage"""
        for word in words:
            word = word.lower().strip()
            if len(word) > 2:
                self.word_frequency[word] += 1
        self._save_vocabulary()
    
    def get_vocabulary_context(self) -> Dict:
        """Get vocabulary context for AI prompts"""
        return {
            "favorites": list(self.favorite_words)[:20],
            "slangs": list(self.favorite_slangs)[:10],
            "avoided": list(self.avoided_words)[:10],
            "most_used": [w for w, c in self.word_frequency.most_common(20)]
        }


class CorrectionTracker:
    """Track user corrections to AI suggestions"""
    
    DATA_FILE = "data/corrections.json"
    
    def __init__(self):
        self.corrections: List[Dict] = []
        self._load_corrections()
    
    def _load_corrections(self):
        """Load corrections from file"""
        if os.path.exists(self.DATA_FILE):
            try:
                with open(self.DATA_FILE, 'r') as f:
                    self.corrections = json.load(f)
            except Exception:
                pass
    
    def _save_corrections(self):
        """Save corrections"""
        os.makedirs(os.path.dirname(self.DATA_FILE), exist_ok=True)
        with open(self.DATA_FILE, 'w') as f:
            json.dump(self.corrections[-100:], f, indent=2)  # Keep last 100
    
    def track_correction(self, original: str, corrected: str):
        """Track a correction"""
        self.corrections.append({
            "original": original,
            "corrected": corrected,
            "diff_length": len(corrected) - len(original)
        })
        self._save_corrections()
    
    def get_correction_insights(self) -> Dict:
        """Get insights from corrections"""
        if not self.corrections:
            return {"total": 0, "avg_change": 0}
        
        total = len(self.corrections)
        avg_change = sum(c["diff_length"] for c in self.corrections) / total
        
        return {
            "total": total,
            "avg_change": round(avg_change, 1),
            "tends_to": "lengthen" if avg_change > 0 else "shorten"
        }
