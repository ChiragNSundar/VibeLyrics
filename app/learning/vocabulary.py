"""
Vocabulary Manager
Tracks and manages user's vocabulary preferences
"""
import json
from typing import List, Dict, Set
from collections import Counter
from pathlib import Path

from app.config import Config


class VocabularyManager:
    """Manages vocabulary tracking and preferences"""
    
    def __init__(self):
        self.style_path = Config.USER_STYLE_PATH
        self._load_vocabulary()
    
    def _load_vocabulary(self):
        """Load vocabulary from style file"""
        try:
            with open(self.style_path, 'r') as f:
                data = json.load(f)
                vocab = data.get("vocabulary", {})
                self.favorite_words = set(vocab.get("favorite_words", []))
                self.favorite_slangs = set(vocab.get("favorite_slangs", []))
                self.avoided_words = set(vocab.get("avoided_words", []))
                self.word_frequency = Counter(vocab.get("word_frequency", {}))
        except (FileNotFoundError, json.JSONDecodeError):
            self.favorite_words = set()
            self.favorite_slangs = set()
            self.avoided_words = set()
            self.word_frequency = Counter()
    
    def _save_vocabulary(self):
        """Save vocabulary to style file"""
        try:
            with open(self.style_path, 'r') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {}
        
        data["vocabulary"] = {
            "favorite_words": list(self.favorite_words),
            "favorite_slangs": list(self.favorite_slangs),
            "avoided_words": list(self.avoided_words),
            "word_frequency": dict(self.word_frequency.most_common(100))
        }
        
        with open(self.style_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def track_words(self, text: str):
        """Track word usage from a piece of text"""
        words = text.lower().split()
        # Filter out very short and very common words
        meaningful_words = [w.strip('.,!?;:"\'') for w in words 
                          if len(w) > 3 and w.isalpha()]
        self.word_frequency.update(meaningful_words)
        self._save_vocabulary()
    
    def add_favorite(self, word: str, is_slang: bool = False):
        """Add a word to favorites"""
        word = word.lower().strip()
        if is_slang:
            self.favorite_slangs.add(word)
        else:
            self.favorite_words.add(word)
        
        # Remove from avoided if present
        self.avoided_words.discard(word)
        self._save_vocabulary()
    
    def add_avoided(self, word: str):
        """Add a word to avoided list"""
        word = word.lower().strip()
        self.avoided_words.add(word)
        
        # Remove from favorites if present
        self.favorite_words.discard(word)
        self.favorite_slangs.discard(word)
        self._save_vocabulary()
    
    def remove_favorite(self, word: str):
        """Remove a word from favorites"""
        word = word.lower().strip()
        self.favorite_words.discard(word)
        self.favorite_slangs.discard(word)
        self._save_vocabulary()
    
    def remove_avoided(self, word: str):
        """Remove a word from avoided list"""
        word = word.lower().strip()
        self.avoided_words.discard(word)
        self._save_vocabulary()
    
    def get_vocabulary_context(self) -> Dict:
        """Get vocabulary context for AI prompts"""
        return {
            "favorite_words": list(self.favorite_words)[:15],
            "favorite_slangs": list(self.favorite_slangs)[:10],
            "avoided_words": list(self.avoided_words),
            "most_used_words": [word for word, _ in self.word_frequency.most_common(20)]
        }
    
    def is_avoided(self, word: str) -> bool:
        """Check if a word should be avoided"""
        return word.lower().strip() in self.avoided_words
    
    def is_favorite(self, word: str) -> bool:
        """Check if a word is a favorite"""
        word = word.lower().strip()
        return word in self.favorite_words or word in self.favorite_slangs
    
    def get_word_suggestions(self, count: int = 10) -> List[str]:
        """Get suggested words based on usage patterns"""
        # Return most frequently used words that aren't avoided
        suggestions = []
        for word, _ in self.word_frequency.most_common(count * 2):
            if word not in self.avoided_words:
                suggestions.append(word)
                if len(suggestions) >= count:
                    break
        return suggestions
    
    def analyze_text_vocabulary(self, text: str) -> Dict:
        """Analyze vocabulary in a piece of text"""
        words = text.lower().split()
        words = [w.strip('.,!?;:"\'') for w in words if w.strip('.,!?;:"\'')]
        
        unique_words = set(words)
        
        return {
            "total_words": len(words),
            "unique_words": len(unique_words),
            "vocabulary_richness": round(len(unique_words) / len(words), 2) if words else 0,
            "favorites_used": [w for w in unique_words if w in self.favorite_words],
            "slangs_used": [w for w in unique_words if w in self.favorite_slangs],
            "avoided_used": [w for w in unique_words if w in self.avoided_words]
        }


# Common hip-hop slang dictionary for reference
COMMON_SLANG = {
    "cap": "lie/lying",
    "no cap": "for real/truth",
    "bussin": "really good",
    "drip": "style/fashion",
    "fire": "excellent",
    "lit": "exciting/drunk",
    "flex": "show off",
    "slay": "do exceptionally well",
    "vibe": "mood/feeling",
    "lowkey": "somewhat/secretly",
    "highkey": "very much/openly",
    "finna": "going to",
    "tryna": "trying to",
    "deadass": "seriously",
    "bet": "okay/agreement",
    "salty": "upset/bitter",
    "savage": "ruthless/cool",
    "squad": "friend group",
    "goat": "greatest of all time",
    "banger": "great song",
    "bars": "lyrics/rhymes",
    "heat": "something impressive",
    "ice": "diamonds/jewelry",
    "whip": "car",
    "stack": "money",
    "rack": "thousand dollars",
    "bag": "money/success",
    "plug": "connection/source",
    "glow up": "transformation/improvement"
}
