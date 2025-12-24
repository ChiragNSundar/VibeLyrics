"""
Self Enhancer
Background learning module that improves the AI's knowledge even when user is not active.
This module:
1. Periodically expands the knowledge base with new techniques
2. Auto-indexes reference lyrics for learning
3. Consolidates patterns from user history
"""
import threading
import time
from typing import Dict, List
from datetime import datetime
import json


class SelfEnhancer:
    """
    Background self-improvement engine.
    Runs periodic tasks to enhance the app's knowledge.
    """
    
    def __init__(self):
        self.running = False
        self.thread = None
        self.enhancement_log = []
        self.last_run = None
        
        # Knowledge expansion data
        self.technique_expansions = [
            {
                "name": "Compound Rhymes",
                "description": "Two or more words that rhyme together",
                "instruction": "Use compound multi-word rhymes like 'city lights' / 'gritty fights'",
                "example": "I shine bright like city lights / Every night I win these gritty fights"
            },
            {
                "name": "Consonance",
                "description": "Repetition of consonant sounds in close words",
                "instruction": "Repeat hard consonants (k, t, p) for aggressive delivery, soft (l, m, n) for smooth",
                "example": "Kick it quick, stick and pick my battles THICK"
            },
            {
                "name": "Wordplay Stacking",
                "description": "Multiple meanings layered in one bar",
                "instruction": "Pack 2-3 double meanings into a single line",
                "example": "I'm raising stakes like vampires at a BBQ (stakes/steaks, raising stakes/raising vampires)"
            },
            {
                "name": "Callback Hooks",
                "description": "Reference earlier lines for cohesion",
                "instruction": "Echo a word or phrase from verse 1 in verse 2",
                "example": "Verse 1: 'Started from the bottom' ... Verse 3: 'Now they see me at the top, remember when I was at the bottom?'"
            },
            {
                "name": "Flow Switches",
                "description": "Changing rhythm mid-verse for impact",
                "instruction": "Break from steady 4/4 flow to triplets or double-time for emphasis",
                "example": "Steady... steady... then-I-hit-em-with-the-RAPID-fire-flow"
            },
        ]
        
        # Rhyme families to expand
        self.rhyme_family_expansions = [
            ["motion", "ocean", "potion", "devotion", "promotion", "emotion", "commotion"],
            ["grind", "mind", "find", "blind", "kind", "behind", "remind", "defined"],
            ["chase", "race", "place", "face", "grace", "embrace", "erase", "disgrace"],
            ["pain", "rain", "chain", "train", "brain", "maintain", "contain", "disdain"],
            ["crown", "town", "down", "ground", "sound", "around", "profound", "renowned"],
        ]
    
    def start_background_enhancement(self, interval_minutes: int = 30):
        """
        Start the background enhancement thread.
        """
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._enhancement_loop, args=(interval_minutes,), daemon=True)
        self.thread.start()
        self.log("Background enhancement started")
    
    def stop(self):
        """Stop the background enhancement."""
        self.running = False
        self.log("Background enhancement stopped")
    
    def _enhancement_loop(self, interval_minutes: int):
        """Main enhancement loop."""
        while self.running:
            try:
                self.run_enhancement_cycle()
            except Exception as e:
                self.log(f"Enhancement error: {e}")
            
            # Sleep for interval
            time.sleep(interval_minutes * 60)
    
    def run_enhancement_cycle(self):
        """
        Run one cycle of self-enhancement.
        This can be called manually or automatically.
        """
        self.log("Starting enhancement cycle")
        
        # 1. Expand elite knowledge with new techniques
        self._expand_technique_library()
        
        # 2. Auto-index any unindexed reference files
        self._auto_index_references()
        
        # 3. Consolidate learned patterns
        self._consolidate_patterns()
        
        self.last_run = datetime.now().isoformat()
        self.log("Enhancement cycle complete")
    
    def _expand_technique_library(self):
        """Add new techniques to the elite knowledge base dynamically."""
        try:
            from app.ai.elite_knowledge import TECHNIQUES
            
            # Add new techniques that don't exist
            added = 0
            for tech in self.technique_expansions:
                key = tech["name"].lower().replace(" ", "_")
                if key not in TECHNIQUES:
                    TECHNIQUES[key] = tech
                    added += 1
            
            if added > 0:
                self.log(f"Added {added} new techniques to knowledge base")
        except Exception as e:
            self.log(f"Technique expansion failed: {e}")
    
    def _auto_index_references(self):
        """Index any reference lyrics files for RAG."""
        try:
            from app.learning import get_vector_store
            from app.config import Config
            from pathlib import Path
            
            ref_dir = Path(Config.REFERENCES_DIR)
            if not ref_dir.exists():
                return
            
            vector_store = get_vector_store()
            indexed = 0
            
            for file in ref_dir.glob("*.txt"):
                try:
                    content = file.read_text(encoding='utf-8', errors='ignore')
                    lines = [l.strip() for l in content.split('\n') if l.strip() and not l.startswith('[')]
                    
                    for line in lines[:50]:  # Index up to 50 lines per file
                        vector_store.index_line(
                            text=line,
                            session_id=0,  # Special ID for references
                            session_title=f"REF:{file.stem}"
                        )
                        indexed += 1
                except Exception:
                    continue
            
            if indexed > 0:
                self.log(f"Auto-indexed {indexed} reference lines")
        except Exception as e:
            self.log(f"Reference indexing failed: {e}")
    
    def _consolidate_patterns(self):
        """Analyze user history and strengthen learned patterns."""
        try:
            from app.models import UserProfile
            from app.learning import get_correction_analyzer
            
            profile = UserProfile.get_or_create_default()
            style_data = profile.style_profile_data or {}
            
            corrections = style_data.get("correction_history", [])
            if len(corrections) < 5:
                return  # Not enough data
            
            analyzer = get_correction_analyzer()
            aggregated = analyzer.aggregate_learnings(corrections)
            
            # Store consolidated insights
            style_data["consolidated_insights"] = {
                "last_updated": datetime.now().isoformat(),
                "preferences": aggregated.get("preferences", []),
                "avoided_words": aggregated.get("avoided_words", []),
                "preferred_words": aggregated.get("preferred_words", []),
                "length_preference": aggregated.get("avg_length_preference", "neutral")
            }
            
            profile.style_profile_data = style_data
            
            # Note: We don't commit here as this runs in a background thread
            # The insights will be saved on the next user action that commits
            
            self.log("Consolidated learned patterns")
        except Exception as e:
            self.log(f"Pattern consolidation failed: {e}")
    
    def log(self, message: str):
        """Log enhancement activity."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "message": message
        }
        self.enhancement_log.append(entry)
        # Keep last 100 entries
        self.enhancement_log = self.enhancement_log[-100:]
        print(f"[SelfEnhancer] {message}")
    
    def get_status(self) -> Dict:
        """Get current enhancement status."""
        return {
            "running": self.running,
            "last_run": self.last_run,
            "techniques_available": len(self.technique_expansions),
            "recent_log": self.enhancement_log[-10:]
        }


# Module-level instance
_enhancer = None

def get_self_enhancer() -> SelfEnhancer:
    global _enhancer
    if _enhancer is None:
        _enhancer = SelfEnhancer()
    return _enhancer


def start_self_enhancement():
    """Convenience function to start background enhancement."""
    enhancer = get_self_enhancer()
    enhancer.start_background_enhancement(interval_minutes=30)
    return enhancer
