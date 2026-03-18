"""
Training Data Service — Advanced
- Score-gated dataset generation (quality filtering)
- DPO preference pairs (chosen/rejected training)
- Multi-LoRA profile management (mood/genre-specific training splits)
- RAG-augmented training (self-referential callback pairs)
- Granular micro-feedback tracking
- Import/export in Alpaca, JSONL, DPO, and plain-text formats
- LM Studio model discovery and training pipeline management
"""
import json
import os
import io
import zipfile
import time
import subprocess
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path


TRAINING_DIR = "data/training"
SUGGESTION_LOG = "data/suggestion_log.json"
DPO_LOG = "data/dpo_pairs.json"
FEEDBACK_LOG = "data/micro_feedback.json"
RLHF_LOG = "data/rlhf_log.json"
CONTINUAL_BUFFER = "data/continual_buffer.json"
CONTINUAL_CONFIG_FILE = "data/continual_config.json"
LORA_PROFILES_DIR = os.path.join(TRAINING_DIR, "profiles")


# ═══════════════════════════════════════════════════════════════════
#  1. SUGGESTION TRACKER — Enhanced with DPO + Micro-Feedback
# ═══════════════════════════════════════════════════════════════════

class SuggestionTracker:
    """Track AI suggestion acceptance/rejection + micro-feedback for DPO training."""

    DATA_FILE = SUGGESTION_LOG

    def __init__(self):
        self.suggestions: List[Dict] = []
        self._load()

    def _load(self):
        if os.path.exists(self.DATA_FILE):
            try:
                with open(self.DATA_FILE, "r") as f:
                    self.suggestions = json.load(f)
            except Exception:
                self.suggestions = []

    def _save(self):
        os.makedirs(os.path.dirname(self.DATA_FILE), exist_ok=True)
        with open(self.DATA_FILE, "w") as f:
            json.dump(self.suggestions[-500:], f, indent=2)

    def log_suggestion(
        self,
        session_id: int,
        prompt: str,
        suggestion: str,
        action: str = "continue",
    ) -> str:
        """Log an AI suggestion with pending status. Returns suggestion_id."""
        suggestion_id = f"sug_{int(time.time() * 1000)}"
        self.suggestions.append(
            {
                "id": suggestion_id,
                "session_id": session_id,
                "prompt": prompt,
                "suggestion": suggestion,
                "action": action,
                "status": "pending",
                "user_replacement": None,
                "feedback_type": None,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
        self._save()
        return suggestion_id

    def update_status(self, suggestion_id: str, status: str,
                      user_replacement: Optional[str] = None,
                      feedback_type: Optional[str] = None):
        """
        Mark a suggestion as accepted/rejected.
        For DPO: if rejected, user_replacement is what the user wrote instead.
        feedback_type: 'more_complex', 'change_rhyme', 'more_aggressive',
                       'fix_syllables', 'too_generic', 'off_topic'
        """
        for s in self.suggestions:
            if s["id"] == suggestion_id:
                s["status"] = status
                if user_replacement:
                    s["user_replacement"] = user_replacement
                if feedback_type:
                    s["feedback_type"] = feedback_type
                break
        self._save()

    def get_accepted(self) -> List[Dict]:
        return [s for s in self.suggestions if s.get("status") == "accepted"]

    def get_rejected(self) -> List[Dict]:
        return [s for s in self.suggestions if s.get("status") == "rejected"]

    def get_dpo_pairs(self) -> List[Dict]:
        """Get DPO-ready chosen/rejected pairs from rejected suggestions with replacements."""
        pairs = []
        for s in self.suggestions:
            if s.get("status") == "rejected" and s.get("user_replacement"):
                pairs.append({
                    "prompt": s.get("prompt", ""),
                    "chosen": s["user_replacement"],
                    "rejected": s["suggestion"],
                    "feedback_type": s.get("feedback_type", "general"),
                    "action": s.get("action", "continue"),
                })
        return pairs

    def get_all(self) -> List[Dict]:
        return self.suggestions

    def get_feedback_stats(self) -> Dict:
        """Get counts of each feedback type."""
        counts: Dict[str, int] = {}
        for s in self.suggestions:
            ft = s.get("feedback_type")
            if ft:
                counts[ft] = counts.get(ft, 0) + 1
        return counts

    def reset(self):
        self.suggestions = []
        if os.path.exists(self.DATA_FILE):
            os.remove(self.DATA_FILE)


class MicroFeedbackTracker:
    """Track granular micro-feedback for fine-grained training signals."""

    DATA_FILE = FEEDBACK_LOG

    def __init__(self):
        self.feedback: List[Dict] = []
        self._load()

    def _load(self):
        if os.path.exists(self.DATA_FILE):
            try:
                with open(self.DATA_FILE, "r") as f:
                    self.feedback = json.load(f)
            except Exception:
                self.feedback = []

    def _save(self):
        os.makedirs(os.path.dirname(self.DATA_FILE), exist_ok=True)
        with open(self.DATA_FILE, "w") as f:
            json.dump(self.feedback[-1000:], f, indent=2)

    def log_feedback(self, suggestion_id: str, feedback_type: str,
                     original_text: str, context: str = "") -> str:
        """
        Log micro-feedback on a suggestion.
        feedback_type: more_complex, change_rhyme, more_aggressive,
                       fix_syllables, too_generic, off_topic, better_wordplay
        """
        fb_id = f"fb_{int(time.time() * 1000)}"
        self.feedback.append({
            "id": fb_id,
            "suggestion_id": suggestion_id,
            "feedback_type": feedback_type,
            "original_text": original_text,
            "context": context,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        self._save()
        return fb_id

    def get_all(self) -> List[Dict]:
        return self.feedback

    def get_feedback_instructions(self) -> List[Dict]:
        """
        Convert micro-feedback into negative instruction training pairs.
        E.g., "too_generic" → instruction to be more specific.
        """
        FEEDBACK_MAP = {
            "more_complex": "Use more advanced wordplay, multi-syllabic rhymes, and complex metaphors.",
            "change_rhyme": "Change the rhyme scheme; use a different end rhyme or internal rhymes.",
            "more_aggressive": "Make the delivery harder, more confrontational and intense.",
            "fix_syllables": "Match the syllable count to fit the beat and flow pattern.",
            "too_generic": "Avoid clichés. Be more specific, personal, and original.",
            "off_topic": "Stay on-theme. The line should connect to what came before it.",
            "better_wordplay": "Add clever double entendres, metaphors, or punchlines.",
        }
        pairs = []
        for fb in self.feedback:
            instruction = FEEDBACK_MAP.get(fb["feedback_type"], "Improve this line.")
            if fb.get("original_text"):
                pairs.append({
                    "instruction": f"Rewrite this rap line. {instruction}",
                    "input": fb["original_text"],
                    "output": "",  # To be filled by user's actual replacement
                    "source": "micro_feedback",
                    "feedback_type": fb["feedback_type"],
                })
        return pairs


# ═══════════════════════════════════════════════════════════════════
#  2. MULTI-LORA PROFILE MANAGER
# ═══════════════════════════════════════════════════════════════════

class LoRAProfileManager:
    """
    Manage mood/genre-specific LoRA training profiles.
    Each profile produces a separate training dataset and LoRA adapter.
    """

    PROFILES_FILE = os.path.join(LORA_PROFILES_DIR, "profiles.json")

    DEFAULT_PROFILES = [
        {
            "id": "aggressive",
            "name": "Aggressive / Diss",
            "mood_tags": ["aggressive", "angry", "intense", "dark", "hard"],
            "bpm_range": [120, 180],
            "description": "Hard-hitting bars, confrontational delivery",
        },
        {
            "id": "melodic",
            "name": "Melodic / R&B",
            "mood_tags": ["melodic", "emotional", "sad", "romantic", "chill"],
            "bpm_range": [70, 110],
            "description": "Smooth, emotional, sing-rap flow",
        },
        {
            "id": "trap",
            "name": "Trap / Hype",
            "mood_tags": ["hype", "confident", "energetic", "trap", "turnt"],
            "bpm_range": [130, 160],
            "description": "High-energy trap cadence and ad-libs",
        },
        {
            "id": "conscious",
            "name": "Conscious / Lyrical",
            "mood_tags": ["conscious", "thoughtful", "lyrical", "deep", "storytelling"],
            "bpm_range": [80, 120],
            "description": "Intricate wordplay, deep themes, storytelling",
        },
    ]

    def __init__(self):
        self.profiles: List[Dict] = []
        self._load()

    def _load(self):
        if os.path.exists(self.PROFILES_FILE):
            try:
                with open(self.PROFILES_FILE, "r") as f:
                    self.profiles = json.load(f)
            except Exception:
                self.profiles = list(self.DEFAULT_PROFILES)
        else:
            self.profiles = list(self.DEFAULT_PROFILES)

    def _save(self):
        os.makedirs(LORA_PROFILES_DIR, exist_ok=True)
        with open(self.PROFILES_FILE, "w") as f:
            json.dump(self.profiles, f, indent=2)

    def get_profiles(self) -> List[Dict]:
        return self.profiles

    def get_profile(self, profile_id: str) -> Optional[Dict]:
        for p in self.profiles:
            if p["id"] == profile_id:
                return p
        return None

    def add_profile(self, profile: Dict) -> Dict:
        self.profiles.append(profile)
        self._save()
        return profile

    def match_session(self, mood: str, bpm: int) -> Optional[str]:
        """Determine which LoRA profile a session matches."""
        mood_lower = (mood or "").lower()
        for profile in self.profiles:
            # Check mood tags
            mood_match = any(tag in mood_lower for tag in profile.get("mood_tags", []))
            # Check BPM range
            bpm_range = profile.get("bpm_range", [0, 300])
            bpm_match = bpm_range[0] <= bpm <= bpm_range[1]
            if mood_match or (bpm_match and mood_lower):
                return profile["id"]
        return None

    def filter_dataset_for_profile(self, dataset: List[Dict],
                                   db_sessions: List[Dict],
                                   profile_id: str) -> List[Dict]:
        """Filter a training dataset to only include pairs matching a profile."""
        profile = self.get_profile(profile_id)
        if not profile:
            return dataset

        # Build set of session IDs matching this profile
        matching_sids = set()
        for s in db_sessions:
            mood = (s.get("mood") or "").lower()
            bpm = s.get("bpm", 140)
            mood_match = any(tag in mood for tag in profile.get("mood_tags", []))
            bpm_range = profile.get("bpm_range", [0, 300])
            bpm_match = bpm_range[0] <= bpm <= bpm_range[1]
            if mood_match or bpm_match:
                matching_sids.add(s["id"])

        # Filter: keep pairs from matching sessions + non-session pairs
        return [
            p for p in dataset
            if p.get("session_id") in matching_sids or "session_id" not in p
        ]



# ═══════════════════════════════════════════════════════════════════
#  2b. RLHF TRACKER (AI Arena)
# ═══════════════════════════════════════════════════════════════════

class RLHFTracker:
    """
    Track AI Arena votes for Reinforcement Learning from Human Feedback.
    Each arena round generates 1 chosen + 3 rejected DPO pairs.
    """

    DATA_FILE = RLHF_LOG

    def __init__(self):
        self.matches: List[Dict] = []
        self._load()

    def _load(self):
        if os.path.exists(self.DATA_FILE):
            try:
                with open(self.DATA_FILE, "r") as f:
                    self.matches = json.load(f)
            except Exception:
                self.matches = []

    def _save(self):
        os.makedirs(os.path.dirname(self.DATA_FILE) or ".", exist_ok=True)
        with open(self.DATA_FILE, "w") as f:
            json.dump(self.matches[-500:], f, indent=2)

    def log_vote(self, prompt: str, variants: List[str],
                 chosen_index: int, session_id: int = 0) -> str:
        """
        Log an arena vote.  variants = list of 4 AI-generated lines.
        chosen_index = index of the one the user picked.
        Returns a match_id.
        """
        match_id = f"arena_{int(time.time() * 1000)}"
        self.matches.append({
            "id": match_id,
            "prompt": prompt,
            "variants": variants,
            "chosen_index": chosen_index,
            "chosen": variants[chosen_index] if chosen_index < len(variants) else "",
            "rejected": [v for i, v in enumerate(variants) if i != chosen_index],
            "session_id": session_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        self._save()
        return match_id

    def get_dpo_pairs(self) -> List[Dict]:
        """Convert arena results into DPO-format chosen/rejected pairs."""
        pairs = []
        for m in self.matches:
            chosen = m.get("chosen", "")
            for rejected in m.get("rejected", []):
                if chosen and rejected:
                    pairs.append({
                        "prompt": m.get("prompt", ""),
                        "chosen": chosen,
                        "rejected": rejected,
                        "feedback_type": "arena_vote",
                    })
        return pairs

    def get_stats(self) -> Dict:
        total = len(self.matches)
        dpo_count = sum(len(m.get("rejected", [])) for m in self.matches)
        return {"total_matches": total, "dpo_pairs_generated": dpo_count}

    def get_all(self) -> List[Dict]:
        return self.matches


# ═══════════════════════════════════════════════════════════════════
#  2c. CONTINUAL LEARNING MANAGER
# ═══════════════════════════════════════════════════════════════════

class ContinualLearningManager:
    """
    Buffer high-complexity lines as they are written.
    When buffer reaches batch_size, trigger a background training run.
    """

    BUFFER_FILE = CONTINUAL_BUFFER
    CONFIG_FILE = CONTINUAL_CONFIG_FILE

    DEFAULT_CONFIG = {
        "enabled": False,
        "min_complexity": 55,
        "batch_size": 50,
        "auto_retrain": True,
    }

    def __init__(self):
        self.buffer: List[Dict] = []
        self.config: Dict = dict(self.DEFAULT_CONFIG)
        self._load()

    def _load(self):
        if os.path.exists(self.BUFFER_FILE):
            try:
                with open(self.BUFFER_FILE, "r") as f:
                    self.buffer = json.load(f)
            except Exception:
                self.buffer = []
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, "r") as f:
                    self.config = json.load(f)
            except Exception:
                self.config = dict(self.DEFAULT_CONFIG)

    def _save(self):
        os.makedirs(os.path.dirname(self.BUFFER_FILE) or ".", exist_ok=True)
        with open(self.BUFFER_FILE, "w") as f:
            json.dump(self.buffer, f, indent=2)
        with open(self.CONFIG_FILE, "w") as f:
            json.dump(self.config, f, indent=2)

    def get_config(self) -> Dict:
        return self.config

    def update_config(self, updates: Dict) -> Dict:
        self.config.update(updates)
        self._save()
        return self.config

    def push_line(self, text: str, complexity_score: float,
                  session_id: int = 0) -> Dict:
        """
        Push a line into the buffer if it meets the quality threshold.
        Returns status dict with buffer_size and whether training was triggered.
        """
        if not self.config.get("enabled", False):
            return {"buffered": False, "reason": "continual_learning_disabled"}

        min_comp = self.config.get("min_complexity", 55)
        if complexity_score < min_comp:
            return {"buffered": False, "reason": "below_threshold",
                    "score": complexity_score, "threshold": min_comp}

        self.buffer.append({
            "text": text,
            "complexity_score": complexity_score,
            "session_id": session_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        self._save()

        batch_size = self.config.get("batch_size", 50)
        triggered = False
        if len(self.buffer) >= batch_size and self.config.get("auto_retrain", True):
            triggered = True
            # Caller (lines router) will trigger the actual training

        return {
            "buffered": True,
            "buffer_size": len(self.buffer),
            "batch_size": batch_size,
            "training_triggered": triggered,
        }

    def flush_buffer(self) -> List[Dict]:
        """Return and clear the buffer (called when training starts)."""
        flushed = list(self.buffer)
        self.buffer = []
        self._save()
        return flushed

    def get_buffer_status(self) -> Dict:
        return {
            "enabled": self.config.get("enabled", False),
            "buffer_size": len(self.buffer),
            "batch_size": self.config.get("batch_size", 50),
            "min_complexity": self.config.get("min_complexity", 55),
            "progress_pct": round(
                len(self.buffer) / max(self.config.get("batch_size", 50), 1) * 100, 1
            ),
        }


# ═══════════════════════════════════════════════════════════════════
#  2d. CONCEPT ERASER (Anti-Cliché)
# ═══════════════════════════════════════════════════════════════════

class ConceptEraser:
    """
    Surgically removes cliché words/phrases from model output by generating
    synthetic negative DPO pairs. If a user bans 'fire', we take a good line
    ending in 'wire', create a rejected version ending in 'fire', and pair
    them as (chosen='wire' original, rejected='fire' synthetic).
    """

    def generate_erasure_pairs(self, banned_words: List[str],
                               high_quality_lines: List[Dict]) -> List[Dict]:
        """
        Generate synthetic DPO pairs to erase banned concepts.

        Args:
            banned_words: Words the user wants the model to never use.
            high_quality_lines: List of dicts with 'text' key.

        Returns:
            List of DPO-format dicts {prompt, chosen, rejected, feedback_type}.
        """
        if not banned_words:
            return []

        pairs = []
        banned_set = set(w.lower().strip() for w in banned_words if w.strip())

        for line_dict in high_quality_lines:
            text = line_dict.get("text", "").strip()
            if not text or len(text) < 5:
                continue

            words = text.lower().split()
            last_word = words[-1].strip(".,!?;:'\"") if words else ""

            for banned in banned_set:
                # Strategy 1: If the line does NOT contain the banned word,
                # create a synthetic rejected version that does
                if banned not in text.lower():
                    # Replace the last word with the banned word
                    if last_word and last_word != banned:
                        original_words = text.split()
                        rejected_words = original_words[:-1] + [banned]
                        rejected_line = " ".join(rejected_words)
                        pairs.append({
                            "prompt": f"Continue this verse. Output only the next lyric line.",
                            "chosen": text,
                            "rejected": rejected_line,
                            "feedback_type": "concept_erasure",
                            "erased_word": banned,
                        })

                # Strategy 2: If the line DOES contain the banned word,
                # it IS the rejected example; need a 'chosen' replacement
                elif banned in text.lower():
                    # Create chosen version by replacing banned word with [REDACTED]
                    import re as re_mod
                    clean = re_mod.sub(
                        r'\b' + re_mod.escape(banned) + r'\b',
                        "___",
                        text,
                        flags=re_mod.IGNORECASE,
                    )
                    if clean != text:
                        pairs.append({
                            "prompt": f"Continue this verse. Avoid the word '{banned}'. "
                                      f"Output only the next lyric line.",
                            "chosen": clean,
                            "rejected": text,
                            "feedback_type": "concept_erasure",
                            "erased_word": banned,
                        })

            if len(pairs) >= 100:  # Cap erasure pairs
                break

        return pairs

    def get_erasure_stats(self, banned_words: List[str],
                          high_quality_lines: List[Dict]) -> Dict:
        """Preview how many erasure pairs would be generated."""
        pairs = self.generate_erasure_pairs(banned_words, high_quality_lines)
        words_targeted = set(p.get("erased_word", "") for p in pairs)
        return {
            "total_pairs": len(pairs),
            "words_targeted": list(words_targeted),
            "banned_words_count": len(banned_words),
        }


# ═══════════════════════════════════════════════════════════════════
#  3. TRAINING DATA GENERATOR — Advanced
# ═══════════════════════════════════════════════════════════════════

class TrainingDataGenerator:
    """
    Generate fine-tuning datasets with advanced quality controls.

    Sources:
    1. Session lines       — consecutive line pairs (score-gated)
    2. Line versions       — rewrite pairs
    3. Corrections         — improve pairs
    4. Accepted suggestions — positive examples
    5. DPO pairs           — chosen/rejected preference pairs
    6. RAG callbacks       — self-referential lyric pairs
    7. Micro-feedback      — negative instruction pairs
    8. Imported datasets   — user-supplied
    """

    DATASET_FILE = os.path.join(TRAINING_DIR, "dataset.json")
    METADATA_FILE = os.path.join(TRAINING_DIR, "metadata.json")
    IMPORTED_FILE = os.path.join(TRAINING_DIR, "imported.json")
    DPO_FILE = os.path.join(TRAINING_DIR, "dpo_dataset.json")

    def __init__(self):
        self._dataset: List[Dict] = []
        self._dpo_dataset: List[Dict] = []
        self._metadata: Dict = {}
        self._load()

    # ── persistence ────────────────────────────────────────────────

    def _load(self):
        if os.path.exists(self.DATASET_FILE):
            try:
                with open(self.DATASET_FILE, "r") as f:
                    self._dataset = json.load(f)
            except Exception:
                self._dataset = []
        if os.path.exists(self.METADATA_FILE):
            try:
                with open(self.METADATA_FILE, "r") as f:
                    self._metadata = json.load(f)
            except Exception:
                self._metadata = {}
        if os.path.exists(self.DPO_FILE):
            try:
                with open(self.DPO_FILE, "r") as f:
                    self._dpo_dataset = json.load(f)
            except Exception:
                self._dpo_dataset = []

    def _save(self):
        os.makedirs(TRAINING_DIR, exist_ok=True)
        with open(self.DATASET_FILE, "w") as f:
            json.dump(self._dataset, f, indent=2)
        with open(self.METADATA_FILE, "w") as f:
            json.dump(self._metadata, f, indent=2)
        with open(self.DPO_FILE, "w") as f:
            json.dump(self._dpo_dataset, f, indent=2)

    # ── dataset generation ─────────────────────────────────────────

    def generate(self, db_sessions: List[Dict], db_lines: List[Dict],
                 db_versions: List[Dict],
                 quality_threshold: float = 0.0,
                 enable_rag: bool = True,
                 **kwargs) -> Dict:
        """
        Rebuild the entire training dataset from current DB + JSON data.

        Parameters:
            db_sessions       - list of session dicts from SQLite
            db_lines          - list of line dicts from SQLite
            db_versions       - list of version dicts from SQLite
            quality_threshold - min complexity_score to include (0 = no filter)
            enable_rag        - generate RAG callback pairs
        """
        pairs: List[Dict] = []
        quality_stats = {"total_lines": 0, "quality_passed": 0, "quality_filtered": 0}

        # ── 1. Consecutive session lines (SCORE-GATED) ──
        sessions_map: Dict[int, List[Dict]] = {}
        for line in db_lines:
            sid = line.get("session_id")
            text = line.get("final_version") or line.get("user_input", "")
            score = line.get("complexity_score") or 0
            syllables = line.get("syllable_count") or 0
            stress = line.get("stress_pattern") or ""
            rhyme_end = line.get("rhyme_end") or ""
            has_internal = line.get("has_internal_rhyme", False)

            if sid and text.strip():
                quality_stats["total_lines"] += 1
                if quality_threshold > 0 and score < quality_threshold:
                    quality_stats["quality_filtered"] += 1
                    continue
                quality_stats["quality_passed"] += 1
                sessions_map.setdefault(sid, []).append({
                    "text": text.strip(),
                    "score": score,
                    "syllables": syllables,
                    "stress": stress,
                    "rhyme_end": rhyme_end,
                    "has_internal": has_internal,
                })

        session_meta: Dict[int, Dict] = {}
        for s in db_sessions:
            session_meta[s["id"]] = s

        for sid, line_dicts in sessions_map.items():
            meta = session_meta.get(sid, {})
            mood = meta.get("mood", "")
            theme = meta.get("theme", "")
            bpm = meta.get("bpm", 140)

            # Build rich context with metre info
            context_parts = []
            if theme:
                context_parts.append(f"theme: {theme}")
            if mood:
                context_parts.append(f"mood: {mood}")
            if bpm:
                context_parts.append(f"BPM: {bpm}")
            context = ", ".join(context_parts) if context_parts else "freestyle"

            for i in range(len(line_dicts) - 1):
                curr = line_dicts[i]
                nxt = line_dicts[i + 1]

                # Build syllable/metre-tagged instruction
                metre_hint = ""
                if nxt["syllables"] > 0:
                    metre_hint = f" Target: ~{nxt['syllables']} syllables."
                if nxt["rhyme_end"]:
                    metre_hint += f" Rhyme with '{nxt['rhyme_end']}'."

                quality_tag = ""
                if curr["score"] >= 60:
                    quality_tag = " [HIGH QUALITY]"
                elif curr["score"] >= 30:
                    quality_tag = " [GOOD]"

                pairs.append({
                    "instruction": f"Continue this rap verse ({context}).{metre_hint}"
                                   f" Output only the next lyric line.{quality_tag}",
                    "input": curr["text"],
                    "output": nxt["text"],
                    "source": "session_lines",
                    "session_id": sid,
                    "quality_score": (curr["score"] + nxt["score"]) / 2,
                })

        # ── 2. Line versions (rewrite pairs) ──
        version_map: Dict[int, List[Dict]] = {}
        for v in db_versions:
            lid = v.get("line_id")
            if lid:
                version_map.setdefault(lid, []).append(v)

        for lid, versions in version_map.items():
            sorted_v = sorted(versions, key=lambda x: x.get("version_number", 0))
            for i in range(len(sorted_v) - 1):
                old_text = sorted_v[i].get("content", "").strip()
                new_text = sorted_v[i + 1].get("content", "").strip()
                if old_text and new_text and old_text != new_text:
                    pairs.append({
                        "instruction": "Rewrite this lyric line to improve it. "
                                       "Output only the improved line.",
                        "input": old_text,
                        "output": new_text,
                        "source": "line_versions",
                    })

        # ── 3. Corrections (from CorrectionTracker) ──
        corrections_file = "data/corrections.json"
        if os.path.exists(corrections_file):
            try:
                with open(corrections_file, "r") as f:
                    corrections = json.load(f)
                for c in corrections:
                    orig = c.get("original", "").strip()
                    corrected = c.get("corrected", "").strip()
                    if orig and corrected and orig != corrected:
                        pairs.append({
                            "instruction": "Improve this lyric line. "
                                           "Output only the improved version.",
                            "input": orig,
                            "output": corrected,
                            "source": "corrections",
                        })
            except Exception:
                pass

        # ── 4. Accepted AI suggestions ──
        if os.path.exists(SUGGESTION_LOG):
            try:
                with open(SUGGESTION_LOG, "r") as f:
                    suggestions = json.load(f)
                for s in suggestions:
                    if s.get("status") == "accepted":
                        prompt = s.get("prompt", "").strip()
                        suggestion = s.get("suggestion", "").strip()
                        action = s.get("action", "continue")
                        if prompt and suggestion:
                            pairs.append({
                                "instruction": f"As a ghostwriter, {action} this lyric. "
                                               "Output only the lyric line.",
                                "input": prompt,
                                "output": suggestion,
                                "source": "accepted_suggestions",
                            })
            except Exception:
                pass

        # ── 5. DPO preference pairs ──
        dpo_pairs: List[Dict] = []
        suggestion_tracker = SuggestionTracker()
        raw_dpo = suggestion_tracker.get_dpo_pairs()
        for dp in raw_dpo:
            if dp["chosen"] and dp["rejected"]:
                dpo_pairs.append({
                    "prompt": dp["prompt"],
                    "chosen": dp["chosen"],
                    "rejected": dp["rejected"],
                    "feedback_type": dp.get("feedback_type", "general"),
                })

        # ── 5b. RLHF Arena DPO pairs ──
        rlhf_tracker = RLHFTracker()
        for dp in rlhf_tracker.get_dpo_pairs():
            if dp["chosen"] and dp["rejected"]:
                dpo_pairs.append(dp)

        # ── 5c. Concept Erasure synthetic DPO pairs ──
        eraser = ConceptEraser()
        # Gather banned words from user profile (passed via generate call or loaded)
        banned_words = kwargs.get("banned_words", [])
        if banned_words:
            high_q = [{"text": ld["text"]} for ld in sessions_map.get(list(sessions_map.keys())[0], []) if ld.get("score", 0) >= 30] if sessions_map else []
            # Flatten all high-quality lines across all sessions
            high_q = []
            for sid_lines in sessions_map.values():
                for ld in sid_lines:
                    if ld.get("score", 0) >= 30:
                        high_q.append({"text": ld["text"]})
            erasure_pairs = eraser.generate_erasure_pairs(banned_words, high_q)
            dpo_pairs.extend(erasure_pairs)

        # ── 6. RAG-augmented callback pairs ──
        if enable_rag:
            rag_pairs = self._generate_rag_pairs(line_dicts_all=db_lines, sessions=db_sessions)
            pairs.extend(rag_pairs)

        # ── 7. Micro-feedback instruction pairs ──
        feedback_tracker = MicroFeedbackTracker()
        feedback_pairs = feedback_tracker.get_feedback_instructions()
        for fp in feedback_pairs:
            if fp.get("input"):
                pairs.append(fp)

        # ── 8. Imported datasets ──
        if os.path.exists(self.IMPORTED_FILE):
            try:
                with open(self.IMPORTED_FILE, "r") as f:
                    imported = json.load(f)
                for entry in imported:
                    entry["source"] = "imported"
                    pairs.append(entry)
            except Exception:
                pass

        self._dataset = pairs
        self._dpo_dataset = dpo_pairs
        self._metadata = {
            "total_pairs": len(pairs),
            "dpo_pairs": len(dpo_pairs),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "sources": self._count_sources(pairs),
            "quality_stats": quality_stats,
            "quality_threshold": quality_threshold,
            "feedback_stats": suggestion_tracker.get_feedback_stats(),
            "rlhf_stats": rlhf_tracker.get_stats(),
            "erasure_pairs": len(erasure_pairs) if banned_words else 0,
        }
        self._save()
        return self._metadata

    def _generate_rag_pairs(self, line_dicts_all: List[Dict],
                            sessions: List[Dict]) -> List[Dict]:
        """
        Generate RAG-augmented self-referential training pairs.
        Find similar past lyrics and create 'callback' instruction pairs.
        """
        pairs = []
        # Collect all finalized lines with their text
        all_lines = []
        for line in line_dicts_all:
            text = (line.get("final_version") or line.get("user_input", "")).strip()
            if text and len(text) > 10:
                all_lines.append({
                    "text": text,
                    "session_id": line.get("session_id"),
                    "score": line.get("complexity_score") or 0,
                })

        if len(all_lines) < 10:
            return pairs  # Not enough data for meaningful RAG

        # Simple word-overlap similarity for RAG (no heavy deps needed)
        # Find pairs of lines from different sessions with shared themes
        for i, line_a in enumerate(all_lines[:50]):  # Cap to avoid O(n²) explosion
            words_a = set(line_a["text"].lower().split())
            # Skip very short word sets
            if len(words_a) < 3:
                continue
            for j, line_b in enumerate(all_lines):
                if i == j or line_a["session_id"] == line_b["session_id"]:
                    continue
                words_b = set(line_b["text"].lower().split())
                if len(words_b) < 3:
                    continue
                overlap = words_a & words_b - {"the", "a", "i", "to", "and", "in", "it", "my", "is", "of", "you", "that", "on", "for", "with"}
                similarity = len(overlap) / max(len(words_a | words_b), 1)

                if similarity > 0.15 and len(overlap) >= 2:
                    pairs.append({
                        "instruction": f"Write a callback line that references this past lyric. "
                                       f"Shared themes: {', '.join(list(overlap)[:4])}. "
                                       "Output only the new callback line.",
                        "input": line_a["text"],
                        "output": line_b["text"],
                        "source": "rag_callbacks",
                    })

                if len(pairs) >= 50:  # Cap RAG pairs
                    return pairs

        return pairs

    def _count_sources(self, pairs: List[Dict]) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for p in pairs:
            src = p.get("source", "unknown")
            counts[src] = counts.get(src, 0) + 1
        return counts

    # ── export formats ─────────────────────────────────────────────

    def get_alpaca_json(self) -> List[Dict]:
        """Return dataset in Alpaca instruction-tuning format."""
        return [
            {
                "instruction": p["instruction"],
                "input": p.get("input", ""),
                "output": p["output"],
            }
            for p in self._dataset
        ]

    def get_jsonl_conversations(self) -> List[Dict]:
        """Return dataset as ChatML / conversational JSONL entries."""
        style_context = self._load_style_context()
        system_msg = (
            "You are VibeLyrics, an elite rap ghostwriter AI. "
            "You have been trained on the user's personal writing style. "
            f"{style_context}"
            "Respond with only the lyric line — no explanations or labels."
        )

        entries = []
        for p in self._dataset:
            messages = [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": f"{p['instruction']}\n\n{p.get('input', '')}".strip()},
                {"role": "assistant", "content": p["output"]},
            ]
            entries.append({"messages": messages})
        return entries

    def get_dpo_json(self) -> List[Dict]:
        """Return DPO preference dataset for RLHF/DPO training."""
        return self._dpo_dataset

    def get_text_corpus(self) -> str:
        """Return all lyrics as a plain-text corpus for continued pretraining."""
        lines = []
        seen = set()
        for p in self._dataset:
            for text in [p.get("input", ""), p.get("output", "")]:
                text = text.strip()
                if text and text not in seen:
                    seen.add(text)
                    lines.append(text)
        return "\n".join(lines)

    def _load_style_context(self) -> str:
        style_file = "data/user_style.json"
        if not os.path.exists(style_file):
            return ""
        try:
            with open(style_file, "r") as f:
                style = json.load(f)
            themes = style.get("themes", {}).get("preferred_themes", [])
            flow = style.get("learned_patterns", {}).get("flow_patterns", [])
            parts = []
            if themes:
                parts.append(f"Preferred themes: {', '.join(themes[:5])}.")
            if flow:
                parts.append(f"Flow styles: {', '.join(flow[:3])}.")
            return " ".join(parts) + " " if parts else ""
        except Exception:
            return ""

    # ── export ZIP ─────────────────────────────────────────────────

    def export_zip(self) -> bytes:
        """Create an in-memory ZIP file with all export formats + metadata."""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            # Alpaca JSON
            alpaca = self.get_alpaca_json()
            zf.writestr("alpaca.json", json.dumps(alpaca, indent=2))

            # JSONL
            jsonl_entries = self.get_jsonl_conversations()
            jsonl_text = "\n".join(json.dumps(e) for e in jsonl_entries)
            zf.writestr("conversations.jsonl", jsonl_text)

            # DPO pairs
            dpo = self.get_dpo_json()
            if dpo:
                zf.writestr("dpo_pairs.json", json.dumps(dpo, indent=2))

            # Text corpus
            corpus = self.get_text_corpus()
            zf.writestr("corpus.txt", corpus)

            # Metadata
            zf.writestr("metadata.json", json.dumps(self._metadata, indent=2))

        return buf.getvalue()

    # ── import ─────────────────────────────────────────────────────

    def import_dataset(self, data: List[Dict]) -> Dict:
        """Import an external dataset (Alpaca format). Merges with imported.json."""
        os.makedirs(TRAINING_DIR, exist_ok=True)

        existing: List[Dict] = []
        if os.path.exists(self.IMPORTED_FILE):
            try:
                with open(self.IMPORTED_FILE, "r") as f:
                    existing = json.load(f)
            except Exception:
                existing = []

        added = 0
        for entry in data:
            if "instruction" in entry and "output" in entry:
                existing.append({
                    "instruction": entry["instruction"],
                    "input": entry.get("input", ""),
                    "output": entry["output"],
                    "source": "imported",
                })
                added += 1

        with open(self.IMPORTED_FILE, "w") as f:
            json.dump(existing, f, indent=2)

        return {"imported": added, "total_imported": len(existing)}

    # ── query & preview ────────────────────────────────────────────

    def get_stats(self) -> Dict:
        if not self._metadata:
            return {
                "total_pairs": 0,
                "dpo_pairs": 0,
                "generated_at": None,
                "sources": {},
                "quality_stats": {},
                "quality_threshold": 0,
                "feedback_stats": {},
            }
        return self._metadata

    def preview(self, n: int = 10) -> List[Dict]:
        return self._dataset[:n]

    def preview_dpo(self, n: int = 10) -> List[Dict]:
        return self._dpo_dataset[:n]

    def get_available_formats(self) -> List[Dict]:
        return [
            {
                "id": "alpaca",
                "name": "Alpaca JSON",
                "description": "Instruction-tuning format (instruction/input/output). "
                               "Compatible with Unsloth, axolotl, LLaMA-Factory.",
                "extension": ".json",
            },
            {
                "id": "jsonl",
                "name": "ChatML JSONL",
                "description": "Conversational format with system/user/assistant messages. "
                               "Compatible with OpenAI fine-tuning, Unsloth chat.",
                "extension": ".jsonl",
            },
            {
                "id": "dpo",
                "name": "DPO Preference Pairs",
                "description": "Chosen/rejected pairs for DPO training. "
                               "Teaches the model what NOT to write.",
                "extension": ".json",
            },
            {
                "id": "text",
                "name": "Plain Text Corpus",
                "description": "Raw lyrics text for continued pretraining or "
                               "domain adaptation. One line per lyric.",
                "extension": ".txt",
            },
            {
                "id": "zip",
                "name": "Complete ZIP Bundle",
                "description": "All formats (SFT + DPO + corpus) bundled with metadata.",
                "extension": ".zip",
            },
        ]


# ═══════════════════════════════════════════════════════════════════
#  4. LM STUDIO TRAINING MANAGER — Multi-LoRA + Automated Pipeline
# ═══════════════════════════════════════════════════════════════════

class LMStudioTrainingManager:
    """
    Manage LM Studio model discovery, multi-LoRA training,
    and automated fine-tuning pipeline.
    """

    CONFIG_FILE = os.path.join(TRAINING_DIR, "training_config.json")
    STATUS_FILE = os.path.join(TRAINING_DIR, "training_status.json")

    def __init__(self):
        self.config = self._load_config()
        self.status = self._load_status()
        self._process = None  # Subprocess handle for auto-train

    def _load_config(self) -> Dict:
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return self._default_config()

    def _default_config(self) -> Dict:
        return {
            "base_model": "unsloth/Mistral-7B-Instruct-v0.3-bnb-4bit",
            "output_dir": "data/training/output",
            "lora_rank": 16,
            "lora_alpha": 16,
            "epochs": 3,
            "learning_rate": 2e-4,
            "batch_size": 4,
            "max_seq_length": 512,
            "warmup_steps": 10,
            "weight_decay": 0.01,
            "gradient_accumulation_steps": 4,
            "quantization": "4bit",
            "dataset_format": "alpaca",
            "active_profile": None,       # Multi-LoRA: active profile ID
            "enable_dpo": False,           # Enable DPO training phase
            "dpo_beta": 0.1,              # DPO beta parameter
            "quality_threshold": 0.0,     # Score gate threshold
            "enable_rag": True,           # Enable RAG callback pairs
        }

    def _load_status(self) -> Dict:
        if os.path.exists(self.STATUS_FILE):
            try:
                with open(self.STATUS_FILE, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "state": "idle",
            "progress": 0,
            "message": "",
            "started_at": None,
            "log_lines": [],
        }

    def save_config(self, config: Dict):
        os.makedirs(TRAINING_DIR, exist_ok=True)
        self.config = {**self._default_config(), **config}
        with open(self.CONFIG_FILE, "w") as f:
            json.dump(self.config, f, indent=2)

    def _save_status(self):
        os.makedirs(TRAINING_DIR, exist_ok=True)
        with open(self.STATUS_FILE, "w") as f:
            json.dump(self.status, f, indent=2)

    def get_config(self) -> Dict:
        return self.config

    def get_status(self) -> Dict:
        # If there's a running subprocess, check on it
        if self._process and self._process.poll() is not None:
            exit_code = self._process.poll()
            self.status["state"] = "completed" if exit_code == 0 else "failed"
            self.status["progress"] = 100 if exit_code == 0 else self.status["progress"]
            self.status["message"] = (
                "Training complete! Model ready for GGUF conversion."
                if exit_code == 0 else
                f"Training failed with exit code {exit_code}."
            )
            self._process = None
            self._save_status()
        return self.status

    def discover_lmstudio_models(self) -> List[Dict]:
        """Query LM Studio's local API for loaded models."""
        lm_url = os.getenv("LM_STUDIO_BASE_URL", "http://127.0.0.1:1234")
        if not lm_url.endswith("/v1"):
            lm_url = f"{lm_url.rstrip('/')}/v1"

        try:
            import httpx
            check_url = lm_url.rstrip("/").replace("/v1", "")
            r = httpx.get(f"{check_url}/v1/models", timeout=3)
            if r.status_code == 200:
                models = r.json().get("data", [])
                return [
                    {
                        "id": m.get("id", "unknown"),
                        "object": m.get("object", "model"),
                        "owned_by": m.get("owned_by", "local"),
                    }
                    for m in models
                ]
        except Exception:
            pass
        return []

    def start_training(self, dataset_path: str,
                       auto_run: bool = False) -> Dict:
        """
        Generate training script and optionally auto-run it.
        Supports SFT + DPO phases and multi-LoRA profiles.
        """
        profile_name = self.config.get("active_profile") or "default"
        script_path = os.path.join(TRAINING_DIR, f"train_{profile_name}.py")

        self.status = {
            "state": "preparing",
            "progress": 5,
            "message": f"Generating training script for profile '{profile_name}'...",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "dataset_path": dataset_path,
            "profile": profile_name,
            "log_lines": [],
        }
        self._save_status()

        self._generate_training_script(script_path, dataset_path)

        if auto_run:
            self.status["state"] = "training"
            self.status["progress"] = 15
            self.status["message"] = "Training started in background..."
            self._save_status()
            try:
                self._process = subprocess.Popen(
                    ["python", script_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    cwd=os.getcwd(),
                )
                self.status["pid"] = self._process.pid
                self._save_status()
            except Exception as e:
                self.status["state"] = "failed"
                self.status["message"] = f"Failed to start: {str(e)}"
                self._save_status()
        else:
            self.status["state"] = "ready"
            self.status["progress"] = 10
            self.status["message"] = (
                f"Training script generated at {script_path}. "
                "Run manually or click 'Auto-Train' to execute. "
                "See docs/TRAINING_SETUP.md for instructions."
            )
            self.status["script_path"] = script_path

        self._save_status()
        return self.status

    def _generate_training_script(self, script_path: str, dataset_path: str):
        """Generate a Python training script with SFT + optional DPO."""
        os.makedirs(os.path.dirname(script_path), exist_ok=True)
        config = self.config
        profile = config.get("active_profile") or "default"
        enable_dpo = config.get("enable_dpo", False)
        dpo_beta = config.get("dpo_beta", 0.1)
        dpo_path = os.path.abspath(os.path.join(TRAINING_DIR, "dpo_dataset.json"))

        script = f'''#!/usr/bin/env python3
"""
VibeLyrics Fine-Tuning Script — Profile: {profile}
Auto-generated by VibeLyrics Training Hub
Supports SFT{" + DPO" if enable_dpo else ""} training with Unsloth.
"""
import json, os, sys

# ── Configuration ──
BASE_MODEL     = "{config['base_model']}"
DATASET_PATH   = r"{os.path.abspath(dataset_path)}"
OUTPUT_DIR     = r"{os.path.abspath(config['output_dir'])}"
PROFILE        = "{profile}"
LORA_RANK      = {config['lora_rank']}
LORA_ALPHA     = {config['lora_alpha']}
EPOCHS         = {config['epochs']}
LEARNING_RATE  = {config['learning_rate']}
BATCH_SIZE     = {config['batch_size']}
MAX_SEQ_LEN    = {config['max_seq_length']}
WARMUP_STEPS   = {config['warmup_steps']}
WEIGHT_DECAY   = {config['weight_decay']}
GRAD_ACCUM     = {config['gradient_accumulation_steps']}
ENABLE_DPO     = {enable_dpo}
DPO_BETA       = {dpo_beta}
DPO_PATH       = r"{dpo_path}"

def main():
    print("=" * 60)
    print(f"VibeLyrics Fine-Tuning — Profile: {{PROFILE}}")
    print("=" * 60)

    # Step 1: Load model
    print("\\n[1/6] Loading base model with Unsloth 4-bit quantization...")
    from unsloth import FastLanguageModel

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=BASE_MODEL,
        max_seq_length=MAX_SEQ_LEN,
        dtype=None,
        load_in_4bit=True,
    )

    # Step 2: Add LoRA adapters
    print("[2/6] Attaching LoRA adapters...")
    model = FastLanguageModel.get_peft_model(
        model,
        r=LORA_RANK,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                         "gate_proj", "up_proj", "down_proj"],
        lora_alpha=LORA_ALPHA,
        lora_dropout=0,
        bias="none",
        use_gradient_checkpointing="unsloth",
    )

    # Step 3: Load SFT dataset
    print("[3/6] Loading VibeLyrics training dataset...")
    from datasets import Dataset

    with open(DATASET_PATH, "r") as f:
        raw_data = json.load(f)

    TEMPLATE = """Below is an instruction that describes a task, paired with an input. Write a response.

### Instruction:
{{{{instruction}}}}

### Input:
{{{{input}}}}

### Response:
{{{{output}}}}"""

    def format_sample(sample):
        text = TEMPLATE.replace("{{{{instruction}}}}", sample["instruction"])
        text = text.replace("{{{{input}}}}", sample.get("input", ""))
        text = text.replace("{{{{output}}}}", sample["output"])
        return {{"text": text + tokenizer.eos_token}}

    dataset = Dataset.from_list(raw_data).map(format_sample)
    print(f"    Loaded {{len(dataset)}} SFT training samples")

    # Step 4: SFT Training
    print("[4/6] Starting SFT fine-tuning...")
    from trl import SFTTrainer
    from transformers import TrainingArguments

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        dataset_text_field="text",
        max_seq_length=MAX_SEQ_LEN,
        dataset_num_proc=2,
        packing=False,
        args=TrainingArguments(
            per_device_train_batch_size=BATCH_SIZE,
            gradient_accumulation_steps=GRAD_ACCUM,
            warmup_steps=WARMUP_STEPS,
            num_train_epochs=EPOCHS,
            learning_rate=LEARNING_RATE,
            fp16=True,
            logging_steps=5,
            optim="adamw_8bit",
            weight_decay=WEIGHT_DECAY,
            lr_scheduler_type="linear",
            output_dir=OUTPUT_DIR,
            save_strategy="epoch",
        ),
    )

    trainer.train()
    print("    SFT Training complete!")

    # Step 5: DPO Phase (optional)
    if ENABLE_DPO and os.path.exists(DPO_PATH):
        print("[5/6] Starting DPO preference training...")
        try:
            with open(DPO_PATH, "r") as f:
                dpo_data = json.load(f)
            if dpo_data:
                from trl import DPOTrainer, DPOConfig

                def format_dpo(sample):
                    return {{
                        "prompt": sample["prompt"],
                        "chosen": sample["chosen"],
                        "rejected": sample["rejected"],
                    }}

                dpo_dataset = Dataset.from_list(dpo_data).map(format_dpo)
                print(f"    Loaded {{len(dpo_dataset)}} DPO preference pairs")

                dpo_trainer = DPOTrainer(
                    model=model,
                    ref_model=None,
                    train_dataset=dpo_dataset,
                    tokenizer=tokenizer,
                    args=DPOConfig(
                        per_device_train_batch_size=2,
                        num_train_epochs=1,
                        learning_rate=5e-6,
                        beta=DPO_BETA,
                        output_dir=os.path.join(OUTPUT_DIR, "dpo"),
                        logging_steps=5,
                    ),
                )
                dpo_trainer.train()
                print("    DPO Training complete!")
            else:
                print("    No DPO pairs found, skipping...")
        except Exception as e:
            print(f"    DPO training skipped: {{e}}")
    else:
        print("[5/6] DPO skipped (not enabled or no data)")

    # Step 6: Save and convert
    print("[6/6] Saving model...")
    lora_dir = os.path.join(OUTPUT_DIR, f"lora_{{PROFILE}}")
    model.save_pretrained(lora_dir)
    tokenizer.save_pretrained(lora_dir)
    print(f"    LoRA adapter saved to: {{lora_dir}}")

    merged_dir = os.path.join(OUTPUT_DIR, f"merged_{{PROFILE}}")
    model.save_pretrained_merged(merged_dir, tokenizer, save_method="merged_16bit")
    print(f"    Merged model saved to: {{merged_dir}}")

    gguf_name = f"vibelyrics-{{PROFILE}}"
    print(f"    Converting to GGUF (Q4_K_M)...")
    model.save_pretrained_gguf(
        os.path.join(OUTPUT_DIR, gguf_name),
        tokenizer,
        quantization_method="q4_k_m",
    )
    print(f"    GGUF saved to: {{os.path.join(OUTPUT_DIR, gguf_name + '.gguf')}}")

    print()
    print("=" * 60)
    print("DONE! Next steps:")
    print(f"  1. Copy the GGUF to your LM Studio models folder")
    print(f"  2. Load it in LM Studio")
    print(f"  3. Set VibeLyrics provider to 'lmstudio'")
    if PROFILE != "default":
        print(f"  4. This is the '{{PROFILE}}' LoRA — best for matching moods/genres")
    print("=" * 60)

if __name__ == "__main__":
    main()
'''
        with open(script_path, "w") as f:
            f.write(script)
