"""
Base AI Provider Abstract Class
Defines the interface all AI providers must implement
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Any


class BaseAIProvider(ABC):
    """Abstract base class for AI providers"""
    
    @abstractmethod
    def suggest_next_line(
        self,
        previous_lines: List[str],
        bpm: int,
        style_context: Dict[str, Any],
        journal_context: Optional[str] = None,
        reference_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Suggest the next line based on context
        
        Returns:
            {
                "suggestion": str,
                "alternatives": List[str],
                "rhyme_info": str,
                "syllable_count": int,
                "question": Optional[str]  # Clarifying question if needed
            }
        """
        pass

    def suggest_next_line_stream(
        self,
        previous_lines: List[str],
        bpm: int,
        style_context: Dict[str, Any]
    ):
        """
        Stream suggestion for next line (Generator)
        Yields chunks of text.
        """
        yield "Streaming not supported by this provider"
    
    @abstractmethod
    def improve_line(
        self,
        line: str,
        improvement_type: str,  # rhyme, flow, wordplay, depth, simplify
        bpm: int,
        style_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Suggest improvements for an existing line
        
        Returns:
            {
                "improved": str,
                "explanation": str,
                "changes_made": List[str]
            }
        """
        pass
    
    @abstractmethod
    def analyze_bars(
        self,
        lines: List[str],
        bpm: int
    ) -> Dict[str, Any]:
        """
        Analyze a set of bars for rhyme scheme, flow, complexity
        
        Returns:
            {
                "rhyme_scheme": str,
                "internal_rhymes": List[Dict],
                "complexity_score": float,
                "flow_rating": str,
                "suggestions": List[str]
            }
        """
        pass
    
    @abstractmethod
    def ask_clarifying_question(
        self,
        current_line: str,
        context: Dict[str, Any]
    ) -> Optional[str]:
        """
        Determine if a clarifying question should be asked
        
        Returns: Question string or None if no question needed
        """
        pass
    
    @abstractmethod
    def answer_user_question(
        self,
        question: str,
        session_context: Dict[str, Any]
    ) -> str:
        """
        Answer a question the user has about lyrics/writing
        """
        pass
    
    @abstractmethod
    def extract_themes_from_journal(
        self,
        journal_entry: str
    ) -> Dict[str, Any]:
        """
        Extract themes and keywords from a journal entry
        
        Returns:
            {
                "themes": List[str],
                "keywords": List[str],
                "mood": str,
                "potential_lines": List[str]
            }
        """
        pass
