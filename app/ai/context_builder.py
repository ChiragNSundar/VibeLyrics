"""
Context Builder
Builds rich context from journal entries, reference lyrics, and session data
"""
import json
from typing import Optional, List, Dict, Any
from app.models import JournalEntry, LyricSession


class ContextBuilder:
    """Builds context for AI prompts from various sources"""
    
    def __init__(self, ai_provider=None):
        self.ai_provider = ai_provider
    
    def build_session_context(
        self,
        session: LyricSession,
        include_journal: bool = True,
        include_references: bool = True,
        max_journal_entries: int = 3
    ) -> Dict[str, Any]:
        """
        Build a comprehensive context dictionary for a writing session
        """
        context = {
            "title": session.title,
            "bpm": session.bpm,
            "mood": session.mood,
            "theme": session.theme,
            "line_count": session.line_count,
            "previous_lines": [
                line.final_version or line.user_input 
                for line in session.lines.all()
            ]
        }
        
        if include_journal and session.journal_context_ids:
            try:
                journal_ids = json.loads(session.journal_context_ids)
                journal_entries = JournalEntry.query.filter(
                    JournalEntry.id.in_(journal_ids)
                ).limit(max_journal_entries).all()
                
                context["journal_context"] = [
                    {
                        "content": entry.content,
                        "mood": entry.mood,
                        "themes": json.loads(entry.extracted_themes) if entry.extracted_themes else []
                    }
                    for entry in journal_entries
                ]
            except (json.JSONDecodeError, Exception):
                context["journal_context"] = []
        
        return context
    
    def build_style_context(self, user_style: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build style context from user preferences
        """
        return {
            "rhyme_style": user_style.get("preferences", {}).get("rhyme_style", "mixed"),
            "complexity_level": user_style.get("preferences", {}).get("complexity_level", "medium"),
            "favorite_words": user_style.get("vocabulary", {}).get("favorite_words", []),
            "favorite_slangs": user_style.get("vocabulary", {}).get("favorite_slangs", []),
            "avoided_words": user_style.get("vocabulary", {}).get("avoided_words", []),
            "preferred_themes": user_style.get("themes", {}).get("preferred", []),
            "learned_patterns": user_style.get("learned_patterns", {})
        }
    
    def get_relevant_journal_entries(
        self,
        mood: Optional[str] = None,
        theme: Optional[str] = None,
        limit: int = 5
    ) -> List[JournalEntry]:
        """
        Get journal entries relevant to the current session
        """
        query = JournalEntry.query
        
        if mood:
            query = query.filter(JournalEntry.mood == mood)
        
        if theme:
            # Search in extracted_themes JSON
            query = query.filter(JournalEntry.extracted_themes.contains(theme))
        
        # Order by most recently used and limit
        return query.order_by(JournalEntry.created_at.desc()).limit(limit).all()
    
    def format_journal_for_context(self, entries: List[JournalEntry]) -> str:
        """
        Format journal entries into a context string for prompts
        """
        if not entries:
            return ""
        
        formatted = ["Relevant journal thoughts:"]
        for entry in entries:
            mood_tag = f"[{entry.mood}]" if entry.mood else ""
            formatted.append(f"- {mood_tag} {entry.content[:200]}...")
        
        return "\n".join(formatted)
    
    def format_reference_context(self, reference_notes: List[Dict]) -> str:
        """
        Format reference lyrics notes for context
        """
        if not reference_notes:
            return ""
        
        formatted = ["Reference style notes:"]
        for note in reference_notes:
            formatted.append(f"- {note.get('artist', 'Unknown')}: {note.get('style_note', '')}")
        
        return "\n".join(formatted)
