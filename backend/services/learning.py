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

    def reset(self):
        """Wipe all learned style data and reset to default."""
        self.style_data = self._get_default_style()
        self.save_style()
    
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

        # Track common words as potential favorites
        common = analysis.get("common_words", [])
        stop_words = {"i", "the", "a", "an", "is", "was", "are", "in", "on", "to", "and", "of", "my", "me", "it", "you", "your", "we", "they", "that", "this"}
        for word in common:
            if word not in stop_words and len(word) > 3:
                fav = self.style_data["vocabulary"]["favorite_words"]
                if word not in fav:
                    fav.append(word)
                    self.style_data["vocabulary"]["favorite_words"] = fav[-50:]
        
        self.save_style()

    def learn_from_journal(self, journal_entries: List[Dict]):
        """
        Continuously learn from journal entries.
        Extracts mood patterns and recurring keywords to inform AI suggestions.
        """
        if not journal_entries:
            return

        moods = []
        keywords = []
        for entry in journal_entries:
            content = entry.get("content", "") if isinstance(entry, dict) else str(entry)
            mood = entry.get("mood", "") if isinstance(entry, dict) else ""
            if mood:
                moods.append(mood.lower())
            # Extract meaningful keywords
            words = content.lower().split()
            stop_words = {"i", "the", "a", "an", "is", "was", "are", "in", "on", "to",
                         "and", "of", "my", "me", "it", "you", "your", "we", "they",
                         "that", "this", "but", "for", "with", "have", "had", "been",
                         "just", "about", "like", "not", "so", "at", "from", "do"}
            meaningful = [w.strip(".,!?;:'\"") for w in words
                         if w.strip(".,!?;:'\"") not in stop_words and len(w) > 3]
            keywords.extend(meaningful)

        # Store mood tendency
        if moods:
            mood_freq = Counter(moods)
            dominant_mood = mood_freq.most_common(1)[0][0]
            self.style_data.setdefault("journal", {})
            self.style_data["journal"]["dominant_mood"] = dominant_mood
            self.style_data["journal"]["mood_history"] = moods[:20]

        # Store recurring keywords
        if keywords:
            keyword_freq = Counter(keywords)
            top_keywords = [w for w, _ in keyword_freq.most_common(15)]
            self.style_data.setdefault("journal", {})
            self.style_data["journal"]["recurring_keywords"] = top_keywords

        self.save_style()
    
    def get_style_summary(self) -> Dict:
        """Get summary of learned style including journal insights"""
        summary = {
            "vocabulary_size": len(self.style_data["vocabulary"]["favorite_words"]),
            "avg_line_length": self.style_data["structure"]["avg_line_length"],
            "preferred_themes": self.style_data["themes"]["preferred"][:5],
            "rhyme_preference": self.style_data["rhyme"]["scheme_preference"],
        }
        journal = self.style_data.get("journal", {})
        if journal.get("dominant_mood"):
            summary["mood_tendency"] = journal["dominant_mood"]
        if journal.get("recurring_keywords"):
            summary["journal_keywords"] = journal["recurring_keywords"][:10]
        return summary
    
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

    def track_co_occurrences(self, lines: List[str]):
        """Track which words appear together in the same line for the brain map."""
        co_file = "data/co_occurrences.json"
        # Load existing
        co_data: Dict[str, Dict[str, int]] = {}
        if os.path.exists(co_file):
            try:
                with open(co_file, 'r') as f:
                    co_data = json.load(f)
            except Exception:
                pass

        stopwords = {"the", "a", "an", "is", "are", "was", "were", "in", "on", "at", "to",
                      "for", "of", "and", "or", "but", "not", "it", "its", "my", "your",
                      "i", "me", "you", "he", "she", "we", "they", "this", "that", "with"}

        for line in lines:
            words = [w.lower().strip() for w in line.split() if len(w.strip()) > 2]
            words = [w for w in words if w not in stopwords and w.isalpha()]
            # Only care about unique words per line
            unique = list(set(words))
            for i in range(len(unique)):
                for j in range(i + 1, len(unique)):
                    w1, w2 = sorted([unique[i], unique[j]])
                    if w1 not in co_data:
                        co_data[w1] = {}
                    co_data[w1][w2] = co_data[w1].get(w2, 0) + 1

        os.makedirs(os.path.dirname(co_file), exist_ok=True)
        with open(co_file, 'w') as f:
            json.dump(co_data, f)

    def get_brain_map_data(self) -> Dict:
        """Generate nodes and links for the interactive brain map force graph."""
        nodes = []
        links = []
        node_ids = set()

        # Build nodes from top vocabulary
        top_words = self.word_frequency.most_common(60)
        for word, freq in top_words:
            category = "signature"
            if word in self.favorite_slangs:
                category = "slang"
            elif word in self.avoided_words:
                category = "avoided"
            elif word in self.favorite_words:
                category = "favorite"

            nodes.append({
                "id": word,
                "val": max(2, min(20, freq // 2)),
                "category": category,
                "frequency": freq
            })
            node_ids.add(word)

        # Build links from co-occurrences
        co_file = "data/co_occurrences.json"
        if os.path.exists(co_file):
            try:
                with open(co_file, 'r') as f:
                    co_data = json.load(f)
                for w1, connections in co_data.items():
                    if w1 in node_ids:
                        for w2, strength in connections.items():
                            if w2 in node_ids and strength >= 2:
                                links.append({
                                    "source": w1,
                                    "target": w2,
                                    "value": min(5, strength)
                                })
            except Exception:
                pass

        return {"nodes": nodes, "links": links}
    
    def get_vocabulary_context(self) -> Dict:
        """Get vocabulary context for AI prompts"""
        return {
            "favorites": list(self.favorite_words)[:20],
            "slangs": list(self.favorite_slangs)[:10],
            "avoided": list(self.avoided_words)[:10],
            "most_used": [w for w, c in self.word_frequency.most_common(20)]
        }

    def reset(self):
        """Wipe all tracked vocabulary completely."""
        self.favorite_words.clear()
        self.favorite_slangs.clear()
        self.avoided_words.clear()
        self.word_frequency.clear()
        if os.path.exists(self.DATA_FILE):
            os.remove(self.DATA_FILE)
        self._save_vocabulary()


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
