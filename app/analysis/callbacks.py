"""
Callback Detector
Detects when new lyrics reference or are similar to user's past work
"""
from typing import List, Dict, Optional
from app.learning import get_vector_store


class CallbackDetector:
    """
    Detects callbacks - references to previous lyrics.
    Uses the VectorStore for similarity matching.
    """
    
    def __init__(self):
        self.vector_store = get_vector_store()
        self.min_similarity = 0.25  # Threshold for callback detection
        self.phrase_min_words = 3   # Minimum words for phrase matching
    
    def detect_callbacks(self, line: str, current_session_id: int = None) -> List[Dict]:
        """
        Detect if a line is similar to or references past lyrics.
        
        Args:
            line: The new lyric line to check
            current_session_id: ID of current session to exclude
            
        Returns:
            List of callback matches with source info
        """
        if not line or len(line.strip()) < 10:
            return []
        
        callbacks = []
        
        # 1. Full line similarity check
        similar = self.vector_store.search_similar(
            query=line,
            top_k=5,
            exclude_session_id=current_session_id
        )
        
        for match in similar:
            if match.get('similarity', 0) >= self.min_similarity:
                callbacks.append({
                    'type': 'similar_line',
                    'original': match.get('text', ''),
                    'source_session': match.get('session_title', 'Unknown'),
                    'similarity': match.get('similarity', 0),
                    'description': f"Similar to: \"{match.get('text', '')[:50]}...\""
                })
        
        # 2. Phrase matching (3+ consecutive words)
        phrase_matches = self._find_phrase_matches(line, current_session_id)
        callbacks.extend(phrase_matches)
        
        # Remove duplicates and sort by similarity
        seen = set()
        unique_callbacks = []
        for cb in callbacks:
            key = cb.get('original', '')[:30]
            if key not in seen:
                seen.add(key)
                unique_callbacks.append(cb)
        
        unique_callbacks.sort(key=lambda x: x.get('similarity', 0), reverse=True)
        
        return unique_callbacks[:5]  # Top 5 callbacks
    
    def _find_phrase_matches(self, line: str, exclude_session_id: int = None) -> List[Dict]:
        """Find matching phrases (3+ word sequences) in past lyrics"""
        words = line.lower().split()
        matches = []
        
        if len(words) < self.phrase_min_words:
            return []
        
        # Generate n-grams (3 to 5 words)
        for n in range(self.phrase_min_words, min(6, len(words) + 1)):
            for i in range(len(words) - n + 1):
                phrase = ' '.join(words[i:i+n])
                
                # Search for this phrase
                similar = self.vector_store.search_similar(
                    query=phrase,
                    top_k=3,
                    exclude_session_id=exclude_session_id
                )
                
                for match in similar:
                    if match.get('similarity', 0) >= 0.5:  # Higher threshold for phrases
                        original_text = match.get('text', '').lower()
                        # Check if phrase actually appears in original
                        if phrase in original_text:
                            matches.append({
                                'type': 'phrase_match',
                                'phrase': phrase,
                                'original': match.get('text', ''),
                                'source_session': match.get('session_title', 'Unknown'),
                                'similarity': match.get('similarity', 0),
                                'description': f"Phrase \"{phrase}\" appears in \"{match.get('text', '')[:40]}...\""
                            })
        
        return matches
    
    def get_callback_summary(self, session_id: int) -> Dict:
        """Get summary of callbacks for an entire session"""
        from app.models import LyricSession
        
        session = LyricSession.query.get(session_id)
        if not session:
            return {"error": "Session not found"}
        
        all_callbacks = []
        lines = session.lines.all()
        
        for line in lines:
            text = line.final_version or line.user_input
            callbacks = self.detect_callbacks(text, session_id)
            if callbacks:
                all_callbacks.append({
                    'line_number': line.line_number,
                    'line_text': text,
                    'callbacks': callbacks
                })
        
        return {
            'session_title': session.title,
            'total_lines': len(lines),
            'lines_with_callbacks': len(all_callbacks),
            'callbacks': all_callbacks
        }


# Singleton instance
_callback_detector = None

def get_callback_detector() -> CallbackDetector:
    """Get singleton callback detector instance"""
    global _callback_detector
    if _callback_detector is None:
        _callback_detector = CallbackDetector()
    return _callback_detector
