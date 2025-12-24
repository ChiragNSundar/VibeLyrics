"""
Context Builder
Builds rich context from journal entries, reference lyrics, session data,
learned corrections, and elite ghostwriting knowledge.
"""
import json
from typing import Optional, List, Dict, Any
from app.models import JournalEntry, LyricSession


class ContextBuilder:
    """Builds context for AI prompts from various sources"""
    
    def __init__(self, ai_provider=None):
        self.ai_provider = ai_provider
        self._correction_prefs = None
    
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
        Build style context from user preferences and learned patterns
        """
        learned_patterns = user_style.get("learned_patterns", {})
        vocabulary = user_style.get("vocabulary", {})
        
        # Build personalized hints for AI
        hints = []
        
        # Syllable preference
        avg_syl = learned_patterns.get("avg_syllables_per_line", 0)
        if avg_syl > 0:
            hints.append(f"User typically writes {avg_syl:.0f} syllables per line")
        
        # Rhyme scheme preference
        schemes = learned_patterns.get("preferred_rhyme_schemes", [])
        if schemes:
            from collections import Counter
            common = Counter(schemes).most_common(1)
            if common:
                hints.append(f"User prefers {common[0][0]} rhyme schemes")
        
        # Words to prioritize/avoid
        favorites = vocabulary.get("favorite_words", [])[:10]
        avoided = vocabulary.get("avoided_words", [])
        
        if favorites:
            hints.append(f"Favorite vocabulary: {', '.join(favorites[:5])}")
        if avoided:
            hints.append(f"Avoid these words: {', '.join(avoided[:5])}")
        
        return {
            "rhyme_style": user_style.get("preferences", {}).get("rhyme_style", "mixed"),
            "complexity_level": user_style.get("preferences", {}).get("complexity_level", "medium"),
            "favorite_words": favorites,
            "favorite_slangs": vocabulary.get("favorite_slangs", []),
            "avoided_words": avoided,
            "preferred_themes": user_style.get("themes", {}).get("preferred", []),
            "learned_patterns": learned_patterns,
            "personalized_hints": hints,
            "avg_syllables": avg_syl if avg_syl > 0 else 12
        }
    
    def build_elite_prompt(
        self,
        session: LyricSession,
        user_profile = None,
        include_few_shot: bool = True
    ) -> str:
        """
        Build an elite-quality prompt with all learnings and techniques.
        This is the main method for generating top-notch suggestions.
        """
        from app.ai.elite_knowledge import get_elite_prompt_additions, ELITE_SYSTEM_PROMPT
        
        parts = [ELITE_SYSTEM_PROMPT]
        
        # Add few-shot examples based on mood
        mood = session.mood or "confident"
        if include_few_shot:
            parts.append(get_elite_prompt_additions(mood=mood))
        
        # Add correction-based preferences
        if user_profile:
            correction_hints = self._get_correction_hints(user_profile)
            if correction_hints:
                parts.append("\n## LEARNED FROM USER CORRECTIONS:")
                parts.append(correction_hints)
        
        # Add session context
        parts.append(f"\n## CURRENT SONG:")
        parts.append(f"Title: {session.title}")
        parts.append(f"BPM: {session.bpm} (target ~{self._syllables_for_bpm(session.bpm)} syllables/line)")
        if session.mood:
            parts.append(f"Mood: {session.mood}")
        if session.theme:
            parts.append(f"Theme: {session.theme}")
        
        # Add previous lines for context
        prev_lines = [l.final_version or l.user_input for l in session.lines.all()][-8:]
        if prev_lines:
            parts.append("\n## PREVIOUS LINES (maintain flow):")
            for i, line in enumerate(prev_lines, 1):
                parts.append(f"  {i}. {line}")
        
        return "\n".join(parts)
    
    def _get_correction_hints(self, user_profile) -> str:
        """
        Get hints learned from user's corrections to AI suggestions.
        """
        try:
            from app.learning.correction_analyzer import get_correction_analyzer
            
            # Get stored corrections from profile
            style_data = user_profile.style_profile_data or {}
            corrections_raw = style_data.get("correction_history", [])
            
            if not corrections_raw:
                return ""
            
            analyzer = get_correction_analyzer()
            aggregated = analyzer.aggregate_learnings(corrections_raw)
            
            hints = []
            for pref in aggregated.get("preferences", []):
                hints.append(f"- {pref}")
            
            avoided = aggregated.get("avoided_words", [])
            if avoided:
                hints.append(f"- AVOID these words (user replaced them): {', '.join(avoided[:5])}")
            
            preferred = aggregated.get("preferred_words", [])
            if preferred:
                hints.append(f"- PREFER these words (user chose them): {', '.join(preferred[:5])}")
            
            return "\n".join(hints)
        except Exception:
            return ""
    
    def _syllables_for_bpm(self, bpm: int) -> int:
        """Calculate target syllables per line based on BPM"""
        if bpm < 80:
            return 8
        elif bpm < 100:
            return 10
        elif bpm < 140:
            return 12
        else:
            return 14
    
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

