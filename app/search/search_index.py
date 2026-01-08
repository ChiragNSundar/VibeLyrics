"""
Full-Text Search Index using Whoosh
Provides advanced search with fuzzy matching and phonetic rhyme discovery
"""
import os
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

try:
    from whoosh import index
    from whoosh.fields import Schema, TEXT, ID, NUMERIC, DATETIME, KEYWORD
    from whoosh.analysis import StemmingAnalyzer, RegexTokenizer, LowercaseFilter
    from whoosh.qparser import QueryParser, MultifieldParser, FuzzyTermPlugin
    from whoosh.query import FuzzyTerm, Or
    from whoosh.writing import AsyncWriter
    WHOOSH_AVAILABLE = True
except ImportError:
    WHOOSH_AVAILABLE = False

from app.config import Config


class LyricSearchIndex:
    """
    Full-text search index for lyrics using Whoosh.
    Features:
    - Fuzzy search with typo tolerance
    - Phonetic matching for rhymes
    - Real-time index updates
    """
    
    def __init__(self):
        self.index_dir = Path(Config.DATA_DIR) / "search_index"
        self._index = None
        self._schema = None
        
        if not WHOOSH_AVAILABLE:
            print("[Search] Whoosh not installed. Run: pip install whoosh")
            return
        
        self._setup_schema()
        self._ensure_index()
    
    def _setup_schema(self):
        """Define the search schema for lyrics"""
        # Custom analyzer for lyrics - handles slang, abbreviations
        lyric_analyzer = StemmingAnalyzer() | LowercaseFilter()
        
        self._schema = Schema(
            id=ID(stored=True, unique=True),
            session_id=NUMERIC(stored=True),
            session_title=TEXT(stored=True),
            section=KEYWORD(stored=True),
            line_number=NUMERIC(stored=True),
            text=TEXT(analyzer=lyric_analyzer, stored=True),
            # Store ending sounds for rhyme matching
            ending_sound=KEYWORD(stored=True),
            created_at=DATETIME(stored=True)
        )
    
    def _ensure_index(self):
        """Create or open the search index"""
        if not WHOOSH_AVAILABLE:
            return
        
        self.index_dir.mkdir(parents=True, exist_ok=True)
        
        if index.exists_in(str(self.index_dir)):
            self._index = index.open_dir(str(self.index_dir))
        else:
            self._index = index.create_in(str(self.index_dir), self._schema)
    
    def _get_ending_sound(self, text: str) -> str:
        """Extract phonetic ending for rhyme matching"""
        words = text.strip().split()
        if not words:
            return ""
        
        last_word = words[-1].lower().strip('.,!?;:\'"()-[]')
        
        # Simple phonetic ending extraction (last 2-3 characters)
        # For better accuracy, could use phonetics library
        if len(last_word) >= 3:
            return last_word[-3:]
        elif len(last_word) >= 2:
            return last_word[-2:]
        return last_word
    
    def index_line(self, line_id: int, session_id: int, session_title: str,
                   section: str, line_number: int, text: str) -> bool:
        """
        Add or update a lyric line in the search index.
        
        Args:
            line_id: Unique line ID
            session_id: Session this line belongs to
            session_title: Title of the session
            section: Verse, Chorus, etc.
            line_number: Position in session
            text: The lyric text
            
        Returns:
            True if indexed successfully
        """
        if not WHOOSH_AVAILABLE or not self._index:
            return False
        
        if not text or len(text.strip()) < 3:
            return False
        
        try:
            writer = AsyncWriter(self._index)
            writer.update_document(
                id=str(line_id),
                session_id=session_id,
                session_title=session_title or "",
                section=section or "Verse",
                line_number=line_number,
                text=text.strip(),
                ending_sound=self._get_ending_sound(text),
                created_at=datetime.now()
            )
            writer.commit()
            return True
        except Exception as e:
            print(f"[Search] Index error: {e}")
            return False
    
    def delete_line(self, line_id: int) -> bool:
        """Remove a line from the index"""
        if not WHOOSH_AVAILABLE or not self._index:
            return False
        
        try:
            writer = self._index.writer()
            writer.delete_by_term('id', str(line_id))
            writer.commit()
            return True
        except Exception as e:
            print(f"[Search] Delete error: {e}")
            return False
    
    def search(self, query: str, limit: int = 20, 
               session_id: int = None, fuzzy: bool = True) -> List[Dict]:
        """
        Search lyrics with optional fuzzy matching.
        
        Args:
            query: Search query
            limit: Maximum results
            session_id: Optional session filter
            fuzzy: Enable fuzzy matching for typos
            
        Returns:
            List of matching documents
        """
        if not WHOOSH_AVAILABLE or not self._index:
            return []
        
        if not query or len(query.strip()) < 2:
            return []
        
        try:
            with self._index.searcher() as searcher:
                # Use multifield parser for text and session_title
                parser = MultifieldParser(
                    ["text", "session_title"], 
                    schema=self._schema
                )
                
                if fuzzy:
                    parser.add_plugin(FuzzyTermPlugin())
                    # Add fuzzy suffix for typo tolerance
                    query = f"{query}~2"
                
                parsed_query = parser.parse(query)
                
                results = searcher.search(parsed_query, limit=limit)
                
                output = []
                for hit in results:
                    # Filter by session if specified
                    if session_id and hit['session_id'] != session_id:
                        continue
                    
                    output.append({
                        'id': int(hit['id']),
                        'session_id': hit['session_id'],
                        'session_title': hit['session_title'],
                        'section': hit['section'],
                        'line_number': hit['line_number'],
                        'text': hit['text'],
                        'score': hit.score
                    })
                
                return output
        except Exception as e:
            print(f"[Search] Search error: {e}")
            return []
    
    def search_rhymes(self, word: str, limit: int = 30) -> List[Dict]:
        """
        Find lines that rhyme with the given word.
        Uses phonetic ending matching.
        
        Args:
            word: Word to find rhymes for
            limit: Maximum results
            
        Returns:
            List of rhyming lines
        """
        if not WHOOSH_AVAILABLE or not self._index:
            return []
        
        ending = self._get_ending_sound(word)
        if not ending:
            return []
        
        try:
            with self._index.searcher() as searcher:
                # Search by ending sound
                parser = QueryParser("ending_sound", schema=self._schema)
                parsed_query = parser.parse(ending)
                
                results = searcher.search(parsed_query, limit=limit)
                
                output = []
                seen_endings = set()
                
                for hit in results:
                    # Get the last word of each result
                    text = hit['text']
                    words = text.strip().split()
                    if words:
                        last_word = words[-1].lower().strip('.,!?;:\'"()-[]')
                        
                        # Avoid duplicate rhyme words
                        if last_word not in seen_endings and last_word != word.lower():
                            seen_endings.add(last_word)
                            output.append({
                                'id': int(hit['id']),
                                'text': hit['text'],
                                'session_title': hit['session_title'],
                                'rhyme_word': last_word,
                                'score': hit.score
                            })
                
                return output
        except Exception as e:
            print(f"[Search] Rhyme search error: {e}")
            return []
    
    def reindex_all(self) -> Dict:
        """
        Rebuild the entire search index from database.
        
        Returns:
            Statistics about reindexing
        """
        if not WHOOSH_AVAILABLE:
            return {"error": "Whoosh not installed"}
        
        from app.models import LyricSession, LyricLine
        
        # Clear and recreate index
        if self._index:
            self._index.close()
        
        import shutil
        if self.index_dir.exists():
            shutil.rmtree(self.index_dir)
        
        self._ensure_index()
        
        # Index all lines
        indexed = 0
        errors = 0
        
        sessions = LyricSession.query.all()
        
        for session in sessions:
            for line in session.lines.all():
                text = line.final_version or line.user_input
                success = self.index_line(
                    line_id=line.id,
                    session_id=session.id,
                    session_title=session.title,
                    section=line.section,
                    line_number=line.line_number,
                    text=text
                )
                if success:
                    indexed += 1
                else:
                    errors += 1
        
        return {
            "indexed": indexed,
            "errors": errors,
            "sessions": len(sessions)
        }
    
    def get_stats(self) -> Dict:
        """Get index statistics"""
        if not WHOOSH_AVAILABLE or not self._index:
            return {"available": False}
        
        return {
            "available": True,
            "doc_count": self._index.doc_count(),
            "index_path": str(self.index_dir)
        }


# Singleton instance
_search_index = None

def get_search_index() -> LyricSearchIndex:
    """Get singleton search index instance"""
    global _search_index
    if _search_index is None:
        _search_index = LyricSearchIndex()
    return _search_index
