"""
Vocabulary Analyzer Service
- Flesch-Kincaid grade level calculation
- Per-session vocabulary metrics
- Vocabulary evolution over time (Vocabulary Age)
"""
import re
from typing import List, Dict
from datetime import datetime


class VocabularyAnalyzer:
    """Analyze vocabulary complexity and track growth over time"""
    
    # Reading level labels for Flesch-Kincaid grade
    LEVEL_LABELS = [
        (5, "Elementary"),
        (8, "Middle School"),
        (12, "High School"),
        (16, "College"),
        (float('inf'), "Graduate+"),
    ]
    
    def analyze_session(self, lines: List[str], session_created_at: str = None) -> Dict:
        """
        Analyze vocabulary metrics for a single session's lines.
        Returns complexity metrics including Flesch-Kincaid grade level.
        """
        if not lines:
            return self._empty_metrics(session_created_at)
        
        all_text = " ".join(lines)
        words = self._extract_words(all_text)
        sentences = self._count_sentences(all_text)
        
        total_words = len(words)
        if total_words == 0:
            return self._empty_metrics(session_created_at)
        
        unique_words = set(words)
        total_syllables = sum(self._count_syllables(w) for w in words)
        multisyllabic = [w for w in words if self._count_syllables(w) >= 3]
        
        # Flesch-Kincaid Grade Level
        # FK = 0.39 * (words/sentences) + 11.8 * (syllables/words) - 15.59
        words_per_sentence = total_words / max(1, sentences)
        syllables_per_word = total_syllables / max(1, total_words)
        fk_grade = 0.39 * words_per_sentence + 11.8 * syllables_per_word - 15.59
        fk_grade = max(1.0, round(fk_grade, 1))
        
        # Average word length
        avg_word_length = sum(len(w) for w in words) / total_words
        
        return {
            "total_words": total_words,
            "unique_words": len(unique_words),
            "vocabulary_density": round(len(unique_words) / total_words, 3),
            "avg_word_length": round(avg_word_length, 2),
            "avg_syllables_per_word": round(syllables_per_word, 2),
            "multisyllabic_count": len(multisyllabic),
            "multisyllabic_pct": round(len(multisyllabic) / total_words * 100, 1),
            "flesch_kincaid_grade": fk_grade,
            "reading_level": self.get_reading_level_label(fk_grade),
            "sentences": sentences,
            "date": session_created_at
        }
    
    def get_vocabulary_evolution(self, sessions_data: List[Dict]) -> List[Dict]:
        """
        Track vocabulary growth across multiple sessions.
        
        sessions_data: List of {"session_id": int, "lines": [str], "created_at": str}
        Returns time-series data for charting.
        """
        evolution = []
        cumulative_words = set()
        
        # Sort by creation date
        sorted_sessions = sorted(
            sessions_data,
            key=lambda s: s.get("created_at", "")
        )
        
        for session in sorted_sessions:
            lines = session.get("lines", [])
            session_id = session.get("session_id", 0)
            created_at = session.get("created_at", "")
            
            # Analyze this session
            metrics = self.analyze_session(lines, created_at)
            
            # Track cumulative unique words
            all_text = " ".join(lines)
            session_words = set(self._extract_words(all_text))
            new_words = session_words - cumulative_words
            cumulative_words.update(session_words)
            
            evolution.append({
                "session_id": session_id,
                "date": created_at,
                "grade_level": metrics["flesch_kincaid_grade"],
                "reading_level": metrics["reading_level"],
                "unique_words": metrics["unique_words"],
                "multisyllabic_pct": metrics["multisyllabic_pct"],
                "vocabulary_density": metrics["vocabulary_density"],
                "cumulative_unique_words": len(cumulative_words),
                "new_words_introduced": len(new_words),
                "avg_syllables_per_word": metrics["avg_syllables_per_word"],
            })
        
        return evolution
    
    def get_reading_level_label(self, grade: float) -> str:
        """Map Flesch-Kincaid grade to a human-readable label"""
        for threshold, label in self.LEVEL_LABELS:
            if grade <= threshold:
                return label
        return "Graduate+"
    
    def get_summary(self, evolution: List[Dict]) -> Dict:
        """Generate a summary of vocabulary growth"""
        if not evolution:
            return {
                "current_grade": 0,
                "current_level": "No data",
                "grade_trend": "flat",
                "total_unique_words": 0,
                "sessions_analyzed": 0
            }
        
        current = evolution[-1]
        first = evolution[0]
        
        # Determine trend
        grade_diff = current["grade_level"] - first["grade_level"]
        if grade_diff > 1:
            trend = "improving"
        elif grade_diff < -1:
            trend = "declining"
        else:
            trend = "stable"
        
        # Average grade across last 5 sessions
        recent = evolution[-5:]
        avg_grade = sum(e["grade_level"] for e in recent) / len(recent)
        
        return {
            "current_grade": current["grade_level"],
            "current_level": current["reading_level"],
            "average_grade": round(avg_grade, 1),
            "grade_trend": trend,
            "grade_change": round(grade_diff, 1),
            "total_unique_words": current["cumulative_unique_words"],
            "sessions_analyzed": len(evolution)
        }
    
    def _extract_words(self, text: str) -> List[str]:
        """Extract clean words from text"""
        words = re.findall(r"[a-z']+", text.lower())
        return [w for w in words if len(w) > 1]
    
    def _count_syllables(self, word: str) -> int:
        """Count syllables in a word"""
        word = word.lower().strip()
        if not word:
            return 1
        
        vowels = 'aeiouy'
        count = 0
        prev_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_vowel:
                count += 1
            prev_vowel = is_vowel
        
        # Adjust for silent 'e'
        if word.endswith('e') and count > 1:
            count -= 1
        
        return max(1, count)
    
    def _count_sentences(self, text: str) -> int:
        """Count sentences (or lines) in lyrics — each line is treated as a sentence"""
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        if not lines:
            # Fall back to punctuation-based counting
            sentences = re.split(r'[.!?]+', text)
            return max(1, len([s for s in sentences if s.strip()]))
        return max(1, len(lines))
    
    def _empty_metrics(self, date: str = None) -> Dict:
        """Return empty metrics structure"""
        return {
            "total_words": 0,
            "unique_words": 0,
            "vocabulary_density": 0,
            "avg_word_length": 0,
            "avg_syllables_per_word": 0,
            "multisyllabic_count": 0,
            "multisyllabic_pct": 0,
            "flesch_kincaid_grade": 0,
            "reading_level": "No data",
            "sentences": 0,
            "date": date
        }
