"""
Vector Search Service for Journal Semantic Search
Uses sentence-transformers for embedding, JSON file for storage.
Gracefully falls back to keyword search if sentence-transformers not installed.
"""
import os
import json
from typing import List, Dict, Optional


class JournalVectorStore:
    """Semantic search for journal entries using sentence embeddings"""
    
    def __init__(self, storage_path: str = "data/journal_vectors.json"):
        self.storage_path = storage_path
        self._model = None
        self._embeddings: Dict[str, List[float]] = {}
        self._entries: Dict[str, str] = {}  # id -> content
        self._available = None
        self._load()
    
    @property
    def is_available(self) -> bool:
        """Check if sentence-transformers is installed"""
        if self._available is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._available = True
            except ImportError:
                self._available = False
                print("[Vector Search] sentence-transformers not installed — falling back to keyword search")
        return self._available
    
    def _get_model(self):
        """Lazy-load the sentence transformer model"""
        if self._model is None and self.is_available:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer('all-MiniLM-L6-v2')
        return self._model
    
    def _load(self):
        """Load stored embeddings from disk"""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                self._embeddings = data.get("embeddings", {})
                self._entries = data.get("entries", {})
            except Exception as e:
                print(f"[Vector Search] Failed to load vectors: {e}")
                self._embeddings = {}
                self._entries = {}
    
    def _save(self):
        """Persist embeddings to disk"""
        os.makedirs(os.path.dirname(self.storage_path) or '.', exist_ok=True)
        try:
            with open(self.storage_path, 'w') as f:
                json.dump({
                    "embeddings": self._embeddings,
                    "entries": self._entries
                }, f)
        except Exception as e:
            print(f"[Vector Search] Failed to save vectors: {e}")
    
    def encode(self, text: str) -> List[float]:
        """Encode text to embedding vector"""
        model = self._get_model()
        if model is None:
            return []
        embedding = model.encode(text)
        return embedding.tolist()
    
    def add_entry(self, entry_id: int, content: str):
        """Add or update a journal entry in the vector store"""
        str_id = str(entry_id)
        self._entries[str_id] = content
        
        if self.is_available:
            embedding = self.encode(content)
            if embedding:
                self._embeddings[str_id] = embedding
        
        self._save()
    
    def remove_entry(self, entry_id: int):
        """Remove a journal entry from the vector store"""
        str_id = str(entry_id)
        self._embeddings.pop(str_id, None)
        self._entries.pop(str_id, None)
        self._save()
    
    def search(self, query: str, top_k: int = 5, mode: str = "auto") -> List[Dict]:
        """
        Search journal entries.
        mode: 'semantic' (vector), 'keyword' (text), 'auto' (semantic if available)
        """
        if mode == "auto":
            mode = "semantic" if self.is_available else "keyword"
        
        if mode == "semantic" and self.is_available:
            return self._semantic_search(query, top_k)
        else:
            return self._keyword_search(query, top_k)
    
    def _semantic_search(self, query: str, top_k: int) -> List[Dict]:
        """Search using cosine similarity on embeddings"""
        query_embedding = self.encode(query)
        if not query_embedding or not self._embeddings:
            return self._keyword_search(query, top_k)
        
        try:
            from sklearn.metrics.pairwise import cosine_similarity
            import numpy as np
            
            query_vec = np.array([query_embedding])
            
            results = []
            for entry_id, embedding in self._embeddings.items():
                entry_vec = np.array([embedding])
                similarity = float(cosine_similarity(query_vec, entry_vec)[0][0])
                results.append({
                    "entry_id": int(entry_id),
                    "content": self._entries.get(entry_id, ""),
                    "similarity": round(similarity, 4),
                    "match_type": "semantic"
                })
            
            # Sort by similarity descending
            results.sort(key=lambda x: x["similarity"], reverse=True)
            return results[:top_k]
            
        except ImportError:
            return self._keyword_search(query, top_k)
    
    def _keyword_search(self, query: str, top_k: int) -> List[Dict]:
        """Fallback: simple keyword search with word overlap scoring"""
        query_words = set(query.lower().split())
        results = []
        
        for entry_id, content in self._entries.items():
            content_words = set(content.lower().split())
            overlap = query_words & content_words
            
            if overlap:
                score = len(overlap) / max(len(query_words), 1)
                results.append({
                    "entry_id": int(entry_id),
                    "content": content,
                    "similarity": round(score, 4),
                    "match_type": "keyword",
                    "matched_words": list(overlap)
                })
        
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]
    
    def reindex_all(self, entries: List[Dict]):
        """Reindex all journal entries (for initialization or repair)"""
        self._embeddings = {}
        self._entries = {}
        
        for entry in entries:
            entry_id = str(entry["id"])
            content = entry["content"]
            self._entries[entry_id] = content
            
            if self.is_available:
                embedding = self.encode(content)
                if embedding:
                    self._embeddings[entry_id] = embedding
        
        self._save()
        return len(self._entries)


# Singleton instance
_vector_store: Optional[JournalVectorStore] = None


def get_vector_store() -> JournalVectorStore:
    """Get or create the singleton vector store"""
    global _vector_store
    if _vector_store is None:
        _vector_store = JournalVectorStore()
    return _vector_store
