"""
Kannada-English Dictionary Search Service
Loads the structured dictionary index and provides exact lookups, semantic/keyword search,
and automatic context extraction for lyric lines.
"""
import os
import json
import re
from typing import List, Dict, Optional

INDEX_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "kannada_dictionary_index.json")

class DictionarySearchService:
    def __init__(self):
        self.dictionary: Dict[str, Dict] = {}
        self.loaded = False
        self._load_dictionary()

    def _load_dictionary(self):
        """Lazy load dictionary index from disk"""
        if not self.loaded and os.path.exists(INDEX_PATH):
            try:
                with open(INDEX_PATH, "r", encoding="utf-8") as f:
                    self.dictionary = json.load(f)
                self.loaded = True
                print(f"[Dictionary] Loaded {len(self.dictionary)} words from index.")
            except Exception as e:
                print(f"[Dictionary] Error loading dictionary index: {e}")

    def lookup_word(self, word: str) -> Optional[Dict]:
        """Look up a word exactly (case-insensitive)"""
        self._load_dictionary()
        word_clean = re.sub(r'[^a-zA-Zāīūśṣṭḍṅñṟēōṛḷ]', '', word).strip().lower()
        return self.dictionary.get(word_clean)

    def search(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search dictionary: matches either query word keys (prefix/exact)
        or matches terms inside the English definition.
        """
        self._load_dictionary()
        query_clean = query.strip().lower()
        if not query_clean:
            return []

        results = []
        seen = set()

        # 1. Exact Match first
        exact = self.lookup_word(query_clean)
        if exact:
            results.append(exact)
            seen.add(exact["word"])

        # 2. Key prefix / substring match
        for word, data in self.dictionary.items():
            if len(results) >= limit:
                break
            if word not in seen and (word.startswith(query_clean) or query_clean in word):
                results.append(data)
                seen.add(word)

        # 3. Content/Definition match (e.g. searching "dew" -> finds "ibbani")
        for word, data in self.dictionary.items():
            if len(results) >= limit:
                break
            if word not in seen:
                # Search across all definitions of the word
                for df in data["definitions"]:
                    if query_clean in df.lower():
                        results.append(data)
                        seen.add(word)
                        break

        return results[:limit]

    def extract_context_from_text(self, text: str, limit: int = 5) -> List[Dict]:
        """
        Scan text (lyrics, prompt context, theme) for Kannada words
        and return their dictionary entries for LLM context injection.
        """
        self._load_dictionary()
        # Extract clean alphanumeric strings from text
        words = re.findall(r"[a-zA-Zāīūśṣṭḍṅñṟēōṛḷ]+", text.lower())
        
        matches = []
        seen = set()
        
        for w in words:
            if len(w) < 2 or w in seen:
                continue
            entry = self.lookup_word(w)
            if entry:
                matches.append(entry)
                seen.add(w)
                if len(matches) >= limit:
                    break
                    
        return matches

# Singleton instance
_search_service = DictionarySearchService()

def get_dictionary_search() -> DictionarySearchService:
    """Get singleton instance of the dictionary search service"""
    return _search_service
