"""
Vector Store for RAG (Retrieval Augmented Generation)
Simple TF-IDF based similarity search for user lyrics memory
"""
import json
import math
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from collections import Counter
from datetime import datetime

from app.config import Config


class VectorStore:
    """
    Simple TF-IDF based vector store for lyric memory.
    No external dependencies - uses pure Python.
    """
    
    def __init__(self):
        self.store_path = Path(Config.DATA_DIR) / "lyric_memory.json"
        self._documents = None
        self._idf_cache = None
    
    @property
    def documents(self) -> List[Dict]:
        """Lazy load documents"""
        if self._documents is None:
            self._documents = self._load_store()
        return self._documents
    
    def _load_store(self) -> List[Dict]:
        """Load vector store from JSON file"""
        if self.store_path.exists():
            try:
                with open(self.store_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return []
    
    def _save_store(self):
        """Save vector store to JSON file"""
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.store_path, 'w', encoding='utf-8') as f:
            json.dump(self.documents, f, indent=2)
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization for lyrics"""
        # Lowercase and split, remove punctuation
        words = text.lower().split()
        return [w.strip('.,!?;:"\'-()[]') for w in words if len(w) > 2]
    
    def _compute_tf(self, tokens: List[str]) -> Dict[str, float]:
        """Compute term frequency"""
        counts = Counter(tokens)
        total = len(tokens)
        if total == 0:
            return {}
        return {word: count / total for word, count in counts.items()}
    
    def _compute_idf(self) -> Dict[str, float]:
        """Compute inverse document frequency across all documents"""
        if self._idf_cache is not None:
            return self._idf_cache
        
        doc_count = len(self.documents)
        if doc_count == 0:
            return {}
        
        # Count documents containing each term
        term_doc_counts = Counter()
        for doc in self.documents:
            tokens = set(self._tokenize(doc.get("text", "")))
            for token in tokens:
                term_doc_counts[token] += 1
        
        # Compute IDF with smoothing
        idf = {}
        for term, doc_freq in term_doc_counts.items():
            idf[term] = math.log((doc_count + 1) / (doc_freq + 1)) + 1
        
        self._idf_cache = idf
        return idf
    
    def _compute_tfidf(self, text: str) -> Dict[str, float]:
        """Compute TF-IDF vector for text"""
        tokens = self._tokenize(text)
        tf = self._compute_tf(tokens)
        idf = self._compute_idf()
        
        return {word: tf_val * idf.get(word, 1.0) for word, tf_val in tf.items()}
    
    def _cosine_similarity(self, vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
        """Compute cosine similarity between two TF-IDF vectors"""
        # Get common terms
        common_terms = set(vec1.keys()) & set(vec2.keys())
        
        if not common_terms:
            return 0.0
        
        # Dot product
        dot_product = sum(vec1[term] * vec2[term] for term in common_terms)
        
        # Magnitudes
        mag1 = math.sqrt(sum(v ** 2 for v in vec1.values()))
        mag2 = math.sqrt(sum(v ** 2 for v in vec2.values()))
        
        if mag1 == 0 or mag2 == 0:
            return 0.0
        
        return dot_product / (mag1 * mag2)
    
    def index_line(self, text: str, session_id: int = None, session_title: str = None, 
                   metadata: Dict = None) -> bool:
        """
        Add a lyric line to the vector store.
        
        Args:
            text: The lyric line text
            session_id: Optional session ID
            session_title: Optional session title
            metadata: Optional additional metadata
            
        Returns:
            True if indexed successfully
        """
        if not text or len(text.strip()) < 5:
            return False
        
        # Check for duplicates (exact match)
        for doc in self.documents:
            if doc.get("text", "").lower().strip() == text.lower().strip():
                return False
        
        doc = {
            "text": text.strip(),
            "session_id": session_id,
            "session_title": session_title or "",
            "indexed_at": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        self.documents.append(doc)
        self._idf_cache = None  # Invalidate cache
        self._save_store()
        
        return True
    
    def search_similar(self, query: str, top_k: int = 5, 
                       exclude_session_id: int = None) -> List[Dict]:
        """
        Search for similar lyrics using TF-IDF similarity.
        
        Args:
            query: The query text
            top_k: Number of results to return
            exclude_session_id: Optional session to exclude (current session)
            
        Returns:
            List of similar documents with similarity scores
        """
        if not self.documents or not query:
            return []
        
        query_vec = self._compute_tfidf(query)
        
        results = []
        for doc in self.documents:
            # Exclude current session if specified
            if exclude_session_id and doc.get("session_id") == exclude_session_id:
                continue
            
            doc_vec = self._compute_tfidf(doc.get("text", ""))
            similarity = self._cosine_similarity(query_vec, doc_vec)
            
            if similarity > 0.1:  # Threshold to filter noise
                results.append({
                    "text": doc["text"],
                    "session_title": doc.get("session_title", ""),
                    "similarity": round(similarity, 3),
                    "indexed_at": doc.get("indexed_at", "")
                })
        
        # Sort by similarity descending
        results.sort(key=lambda x: x["similarity"], reverse=True)
        
        return results[:top_k]
    
    def get_stats(self) -> Dict:
        """Get memory statistics"""
        return {
            "total_lines": len(self.documents),
            "unique_sessions": len(set(d.get("session_id") for d in self.documents if d.get("session_id")))
        }
    
    def format_for_prompt(self, similar_lines: List[Dict]) -> str:
        """Format similar lines for AI prompt context"""
        if not similar_lines:
            return ""
        
        formatted = ["Your past lyrics that might be relevant:"]
        for item in similar_lines[:3]:
            title = item.get("session_title", "")
            title_str = f' (from "{title}")' if title else ""
            formatted.append(f'- "{item["text"]}"{title_str}')
        
        return "\n".join(formatted)


# Singleton instance
_vector_store = None

def get_vector_store() -> VectorStore:
    """Get singleton vector store instance"""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
