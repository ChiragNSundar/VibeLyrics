"""
Correction Tracker
Learns from user corrections to AI suggestions
"""
import json
from typing import List, Dict, Optional, Tuple
from difflib import SequenceMatcher
from collections import Counter

from app.models import db, Correction
from app.config import Config


class CorrectionTracker:
    """Tracks and learns from user corrections"""
    
    # Correction types we categorize
    CORRECTION_TYPES = [
        "word_choice",    # Changed specific words
        "rhyme",          # Changed to improve rhyme
        "flow",           # Changed for better rhythm
        "slang",          # Preferred different slang
        "tone",           # Changed emotional tone
        "meaning",        # Changed meaning/message
        "simplify",       # Made simpler
        "complexify",     # Made more complex
        "length",         # Changed line length
    ]
    
    def __init__(self):
        self.style_path = Config.USER_STYLE_PATH
    
    def track_correction(
        self,
        original: str,
        corrected: str,
        line_id: Optional[int] = None,
        session_id: Optional[int] = None
    ) -> Correction:
        """
        Track a correction the user made to an AI suggestion
        """
        # Analyze the correction type
        correction_type = self._analyze_correction_type(original, corrected)
        
        # Extract the pattern
        pattern = self._extract_pattern(original, corrected)
        
        # Create correction record
        correction = Correction(
            original_suggestion=original,
            user_correction=corrected,
            line_id=line_id,
            session_id=session_id,
            correction_type=correction_type,
            pattern_extracted=json.dumps(pattern) if pattern else None
        )
        
        db.session.add(correction)
        db.session.commit()
        
        # Update style profile
        self._update_style_from_correction(correction)
        
        return correction
    
    def _analyze_correction_type(self, original: str, corrected: str) -> str:
        """Analyze what type of correction was made"""
        orig_words = original.lower().split()
        corr_words = corrected.lower().split()
        
        # Length change
        if len(corr_words) < len(orig_words) - 2:
            return "simplify"
        elif len(corr_words) > len(orig_words) + 2:
            return "complexify"
        
        # Check for word changes at the end (likely rhyme-related)
        if orig_words and corr_words:
            if orig_words[-1] != corr_words[-1]:
                return "rhyme"
        
        # Calculate overall similarity
        similarity = SequenceMatcher(None, original.lower(), corrected.lower()).ratio()
        
        if similarity > 0.9:
            return "word_choice"  # Minor tweak
        elif similarity > 0.7:
            return "flow"  # Moderate changes
        else:
            return "meaning"  # Significant rewrite
    
    def _extract_pattern(self, original: str, corrected: str) -> Optional[Dict]:
        """Extract the pattern from a correction for learning"""
        orig_words = original.lower().split()
        corr_words = corrected.lower().split()
        
        changes = []
        
        # Find word-level changes using SequenceMatcher
        matcher = SequenceMatcher(None, orig_words, corr_words)
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'replace':
                changes.append({
                    "type": "replace",
                    "original": orig_words[i1:i2],
                    "corrected": corr_words[j1:j2]
                })
            elif tag == 'delete':
                changes.append({
                    "type": "delete",
                    "original": orig_words[i1:i2]
                })
            elif tag == 'insert':
                changes.append({
                    "type": "insert",
                    "corrected": corr_words[j1:j2]
                })
        
        if not changes:
            return None
        
        return {
            "changes": changes,
            "similarity": SequenceMatcher(None, original.lower(), corrected.lower()).ratio()
        }
    
    def _update_style_from_correction(self, correction: Correction):
        """Update style profile based on correction patterns"""
        try:
            with open(self.style_path, 'r') as f:
                style = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return
        
        # Update correction count
        patterns = style.get("learned_patterns", {})
        patterns["corrections_applied"] = patterns.get("corrections_applied", 0) + 1
        
        # Track correction types
        type_counts = patterns.get("correction_type_counts", {})
        type_counts[correction.correction_type] = type_counts.get(correction.correction_type, 0) + 1
        patterns["correction_type_counts"] = type_counts
        
        # Extract words from corrections for vocabulary learning
        if correction.pattern_extracted:
            try:
                pattern = json.loads(correction.pattern_extracted)
                for change in pattern.get("changes", []):
                    if change["type"] == "replace":
                        # User preferred these words over AI's
                        corrected_words = change.get("corrected", [])
                        original_words = change.get("original", [])
                        
                        # Add corrected words to favorites
                        favorites = set(style.get("vocabulary", {}).get("favorite_words", []))
                        for word in corrected_words:
                            if len(word) > 3:
                                favorites.add(word)
                        style["vocabulary"]["favorite_words"] = list(favorites)[:50]
                        
                        # Track patterns of word changes
                        word_changes = patterns.get("word_preference_pairs", [])
                        if original_words and corrected_words:
                            word_changes.append({
                                "from": original_words,
                                "to": corrected_words
                            })
                        patterns["word_preference_pairs"] = word_changes[-50:]  # Keep last 50
            except json.JSONDecodeError:
                pass
        
        style["learned_patterns"] = patterns
        
        with open(self.style_path, 'w') as f:
            json.dump(style, f, indent=2)
    
    def get_correction_insights(self) -> Dict:
        """Get insights from collected corrections"""
        corrections = Correction.query.all()
        
        if not corrections:
            return {"total": 0, "insights": []}
        
        # Analyze patterns
        type_counts = Counter(c.correction_type for c in corrections)
        
        insights = []
        
        # Most common correction type
        if type_counts:
            most_common = type_counts.most_common(1)[0]
            insights.append(f"You most often correct for: {most_common[0]} ({most_common[1]} times)")
        
        # Similarity analysis
        similarities = []
        for c in corrections:
            if c.pattern_extracted:
                try:
                    pattern = json.loads(c.pattern_extracted)
                    similarities.append(pattern.get("similarity", 0))
                except json.JSONDecodeError:
                    pass
        
        if similarities:
            avg_similarity = sum(similarities) / len(similarities)
            if avg_similarity > 0.8:
                insights.append("Your corrections are usually minor tweaks - AI is getting close!")
            elif avg_similarity > 0.5:
                insights.append("Your corrections are moderate - AI is learning your style")
            else:
                insights.append("Your corrections are significant - keep teaching the AI")
        
        return {
            "total": len(corrections),
            "by_type": dict(type_counts),
            "insights": insights,
            "avg_similarity": round(sum(similarities) / len(similarities), 2) if similarities else 0
        }
    
    def get_learned_preferences(self) -> Dict:
        """Get preferences learned from corrections"""
        try:
            with open(self.style_path, 'r') as f:
                style = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
        
        patterns = style.get("learned_patterns", {})
        
        # Analyze word preference pairs
        word_pairs = patterns.get("word_preference_pairs", [])
        preferred_words = []
        avoided_words = []
        
        for pair in word_pairs:
            preferred_words.extend(pair.get("to", []))
            avoided_words.extend(pair.get("from", []))
        
        return {
            "correction_count": patterns.get("corrections_applied", 0),
            "type_distribution": patterns.get("correction_type_counts", {}),
            "preferred_words": list(set(preferred_words))[:20],
            "avoided_suggestions": list(set(avoided_words))[:20]
        }
    
    def apply_learned_preferences(self, suggestion: str) -> Tuple[str, List[str]]:
        """
        Apply learned preferences to a suggestion
        Returns modified suggestion and list of changes made
        """
        preferences = self.get_learned_preferences()
        changes = []
        modified = suggestion
        
        # Replace avoided words with preferred alternatives
        avoided = preferences.get("avoided_suggestions", [])
        preferred = preferences.get("preferred_words", [])
        
        # Simple replacement based on learned patterns (more sophisticated in practice)
        for word in avoided:
            if word in modified.lower() and preferred:
                # Find a phonetically similar preferred word would be ideal
                # For now, flag the word
                changes.append(f"Consider replacing '{word}'")
        
        return modified, changes
