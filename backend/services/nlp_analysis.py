"""
NLP Analysis Services
- Contextual Wordplay Engine (AI-powered)
- Rhyme Complexity Scoring (phoneme-based)
- Semantic Drift Detection (keyword overlap)
- Theme Clustering for 3D Neural Network
"""
import re
import math
import random
from typing import List, Dict, Optional, Tuple
from collections import Counter, defaultdict

try:
    import pronouncing
except ImportError:
    pronouncing = None


# ── Wordplay Engine ─────────────────────────────────────────────────

class WordplayEngine:
    """
    Generate contextual wordplay suggestions (double-entendres, puns,
    metaphorical twists) using the AI provider, with a static fallback.
    """

    WORDPLAY_FRAMES = {
        "money": ["bread", "dough", "cake", "paper", "bands", "racks", "stacks", "cheese", "guap", "moolah"],
        "success": ["crown", "throne", "peak", "summit", "W", "trophy", "gold", "diamond", "ring"],
        "struggle": ["trenches", "mud", "quicksand", "uphill", "storm", "drought", "desert", "grind"],
        "love": ["fire", "flame", "spark", "magnet", "gravity", "orbit", "drug", "addiction", "ocean"],
        "power": ["lion", "king", "chess", "checkmate", "tower", "fortress", "hammer", "thunder"],
        "speed": ["bullet", "rocket", "lightning", "flash", "blur", "comet", "jet", "whip"],
        "betrayal": ["snake", "knife", "mask", "shadow", "wolf", "venom", "poison", "two-faced"],
        "time": ["clock", "sand", "hourglass", "season", "chapter", "page", "rewind", "fast-forward"],
        "city": ["concrete", "asphalt", "blocks", "corners", "sirens", "neon", "skyline", "pavement"],
    }

    DOUBLE_ENTENDRE_TEMPLATES = [
        "I keep it {word1} — they don't know which way I {word2}",
        "Call me {word1}, 'cause I always {word2}",
        "They say I'm {word1} but I'm really {word2}",
        "{word1} on the surface, {word2} underneath",
        "I {word1} so hard they think I {word2}",
    ]

    async def generate_wordplay(
        self,
        theme: str,
        recent_lines: List[str] = None,
        mood: str = None,
        count: int = 5,
    ) -> Dict:
        """Generate contextual wordplay suggestions using AI with static fallback."""
        try:
            from ..services.ai_provider import get_ai_provider
            provider = get_ai_provider()

            lines_context = ""
            if recent_lines:
                lines_context = "\n".join(f"  {l}" for l in recent_lines[-6:])

            prompt = f"""You are a hip-hop wordplay expert. Generate {count} clever wordplay suggestions.

Theme/Topic: {theme}
{"Mood: " + mood if mood else ""}
{"Recent lyrics:" + chr(10) + lines_context if lines_context else ""}

Generate {count} wordplay suggestions. Each should be ONE of these types:
- DOUBLE ENTENDRE: A phrase with two meanings (literal + figurative)
- PUN: A play on words using similar-sounding words
- METAPHORICAL TWIST: An unexpected metaphor connection

Format each suggestion as:
[TYPE] suggestion text | brief explanation

Return ONLY the suggestions, one per line."""

            response = await provider.answer_question(prompt, None)
            suggestions = []
            for line in response.strip().split("\n"):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                # Parse [TYPE] suggestion | explanation
                wp_type = "wordplay"
                explanation = ""
                if line.startswith("["):
                    bracket_end = line.find("]")
                    if bracket_end > 0:
                        wp_type = line[1:bracket_end].strip().lower()
                        line = line[bracket_end + 1:].strip()
                if "|" in line:
                    parts = line.split("|", 1)
                    line = parts[0].strip()
                    explanation = parts[1].strip()
                line = line.strip("- ").strip()
                if line:
                    suggestions.append({
                        "text": line,
                        "type": wp_type,
                        "explanation": explanation,
                    })

            if suggestions:
                return {"suggestions": suggestions[:count], "source": "ai", "theme": theme}
        except Exception:
            pass

        # Static fallback
        return self._static_fallback(theme, count)

    def _static_fallback(self, theme: str, count: int = 5) -> Dict:
        """Generate wordplay using static templates."""
        theme_lower = theme.lower()
        words = []
        for key, frame_words in self.WORDPLAY_FRAMES.items():
            if key in theme_lower or theme_lower in key:
                words = frame_words
                break
        if not words:
            # Just pick a random frame
            words = random.choice(list(self.WORDPLAY_FRAMES.values()))

        suggestions = []
        used = set()
        for template in self.DOUBLE_ENTENDRE_TEMPLATES:
            if len(suggestions) >= count:
                break
            w1, w2 = random.sample(words, min(2, len(words)))
            if (w1, w2) in used:
                continue
            used.add((w1, w2))
            text = template.format(word1=w1, word2=w2)
            suggestions.append({
                "text": text,
                "type": "double entendre",
                "explanation": f"Playing on '{w1}' and '{w2}' — {theme} theme",
            })

        return {"suggestions": suggestions[:count], "source": "static", "theme": theme}


# ── Rhyme Complexity Scorer ─────────────────────────────────────────

class RhymeComplexityScorer:
    """
    Score lyric complexity on a 0–100 scale based on:
    - Internal rhyme density
    - Multi-syllabic rhyme frequency
    - Assonance density
    - Consonance density
    - Vocabulary richness
    """

    VOWEL_PHONEMES = {
        "AA", "AE", "AH", "AO", "AW", "AY", "EH", "ER", "EY",
        "IH", "IY", "OW", "OY", "UH", "UW",
    }

    CONSONANT_PHONEMES = {
        "B", "CH", "D", "DH", "F", "G", "HH", "JH", "K", "L", "M",
        "N", "NG", "P", "R", "S", "SH", "T", "TH", "V", "W", "Y", "Z", "ZH",
    }

    def score(self, lines: List[str]) -> Dict:
        """
        Return a 0–100 complexity score with dimensional breakdown.
        """
        if not lines or not any(l.strip() for l in lines):
            return {
                "score": 0,
                "grade": "N/A",
                "dimensions": {
                    "internal_rhyme": 0,
                    "multisyllabic": 0,
                    "assonance": 0,
                    "consonance": 0,
                    "vocabulary": 0,
                },
                "details": "No lines to analyze.",
            }

        internal_score = self._internal_rhyme_density(lines)
        multi_score = self._multisyllabic_score(lines)
        asson_score = self._assonance_density(lines)
        conson_score = self._consonance_density(lines)
        vocab_score = self._vocabulary_richness(lines)

        # Weighted combination
        overall = (
            internal_score * 0.30
            + multi_score * 0.25
            + asson_score * 0.15
            + conson_score * 0.10
            + vocab_score * 0.20
        )
        overall = min(100, max(0, round(overall)))

        grade = self._grade(overall)

        return {
            "score": overall,
            "grade": grade,
            "dimensions": {
                "internal_rhyme": round(internal_score),
                "multisyllabic": round(multi_score),
                "assonance": round(asson_score),
                "consonance": round(conson_score),
                "vocabulary": round(vocab_score),
            },
            "details": self._details_text(overall, grade),
        }

    # ── dimension helpers ───

    def _internal_rhyme_density(self, lines: List[str]) -> float:
        """How many internal rhyme pairs per line on average (0–100)."""
        if not pronouncing:
            return 0
        total_pairs = 0
        valid_lines = 0
        for line in lines:
            words = re.findall(r"[a-zA-Z']+", line)
            if len(words) < 3:
                continue
            valid_lines += 1
            endings = []
            for w in words:
                phones_list = pronouncing.phones_for_word(w.lower())
                if phones_list:
                    rp = pronouncing.rhyming_part(phones_list[0])
                    endings.append(rp)
            # Count unique rhyme-pair matches
            seen = set()
            pairs = 0
            for i in range(len(endings)):
                for j in range(i + 1, len(endings)):
                    if endings[i] and endings[j] and endings[i] == endings[j]:
                        key = tuple(sorted([i, j]))
                        if key not in seen:
                            seen.add(key)
                            pairs += 1
            total_pairs += pairs

        if valid_lines == 0:
            return 0
        avg_pairs = total_pairs / valid_lines
        # Scale: 0 pairs → 0, 3+ pairs → 100
        return min(100, (avg_pairs / 3.0) * 100)

    def _multisyllabic_score(self, lines: List[str]) -> float:
        """Percentage of words with 3+ syllables (0–100)."""
        all_words = []
        for line in lines:
            all_words.extend(re.findall(r"[a-zA-Z']+", line))
        if not all_words:
            return 0
        multi = sum(1 for w in all_words if self._count_syllables(w) >= 3)
        pct = multi / len(all_words)
        # Scale: 0% → 0, 30%+ → 100
        return min(100, (pct / 0.30) * 100)

    def _assonance_density(self, lines: List[str]) -> float:
        """Repeated vowel sounds within lines (0–100)."""
        if not pronouncing:
            return 0
        total_score = 0
        count = 0
        for line in lines:
            words = re.findall(r"[a-zA-Z']+", line)
            if len(words) < 2:
                continue
            count += 1
            vowels = []
            for w in words:
                phones_list = pronouncing.phones_for_word(w.lower())
                if phones_list:
                    for p in phones_list[0].split():
                        stripped = re.sub(r"\d", "", p)
                        if stripped in self.VOWEL_PHONEMES:
                            vowels.append(stripped)
            if vowels:
                counter = Counter(vowels)
                repeats = sum(v - 1 for v in counter.values() if v > 1)
                total_score += min(1.0, repeats / 4.0)

        if count == 0:
            return 0
        return (total_score / count) * 100

    def _consonance_density(self, lines: List[str]) -> float:
        """Repeated consonant clusters within lines (0–100)."""
        if not pronouncing:
            return 0
        total_score = 0
        count = 0
        for line in lines:
            words = re.findall(r"[a-zA-Z']+", line)
            if len(words) < 2:
                continue
            count += 1
            consonants = []
            for w in words:
                phones_list = pronouncing.phones_for_word(w.lower())
                if phones_list:
                    for p in phones_list[0].split():
                        stripped = re.sub(r"\d", "", p)
                        if stripped in self.CONSONANT_PHONEMES:
                            consonants.append(stripped)
            if consonants:
                counter = Counter(consonants)
                repeats = sum(v - 1 for v in counter.values() if v > 1)
                total_score += min(1.0, repeats / 5.0)

        if count == 0:
            return 0
        return (total_score / count) * 100

    def _vocabulary_richness(self, lines: List[str]) -> float:
        """Type-token ratio scaled to 0–100."""
        all_words = []
        for line in lines:
            all_words.extend(w.lower() for w in re.findall(r"[a-zA-Z']+", line))
        if len(all_words) < 2:
            return 0
        ttr = len(set(all_words)) / len(all_words)
        # Scale: 0.3 → 0, 0.8+ → 100
        return min(100, max(0, ((ttr - 0.3) / 0.5) * 100))

    # ── utilities ───

    def _count_syllables(self, word: str) -> int:
        """Estimate syllable count."""
        word = word.lower().strip("'")
        if pronouncing:
            phones_list = pronouncing.phones_for_word(word)
            if phones_list:
                return pronouncing.syllable_count(phones_list[0])
        # Fallback heuristic
        vowels = "aeiouy"
        count = 0
        prev_vowel = False
        for ch in word:
            is_vowel = ch in vowels
            if is_vowel and not prev_vowel:
                count += 1
            prev_vowel = is_vowel
        if word.endswith("e") and count > 1:
            count -= 1
        return max(1, count)

    def _grade(self, score: int) -> str:
        if score >= 85:
            return "S-Tier"
        elif score >= 70:
            return "A-Tier"
        elif score >= 55:
            return "B-Tier"
        elif score >= 40:
            return "C-Tier"
        elif score >= 20:
            return "D-Tier"
        return "Beginner"

    def _details_text(self, score: int, grade: str) -> str:
        if score >= 85:
            return f"{grade} — Elite internal rhyme density and vocabulary. Eminem-level complexity."
        elif score >= 70:
            return f"{grade} — Strong multisyllabic and assonance patterns. Professional quality."
        elif score >= 55:
            return f"{grade} — Solid rhyme craft. Try adding more internal rhymes and varied vocabulary."
        elif score >= 40:
            return f"{grade} — Average complexity. Focus on multisyllabic words and assonance."
        elif score >= 20:
            return f"{grade} — Basic rhyme patterns. Experiment with internal rhymes within lines."
        return f"{grade} — Just getting started. Focus on end-rhymes first, then build complexity."


# ── Semantic Drift Detector ─────────────────────────────────────────

class SemanticDriftDetector:
    """
    Detect when lyrics drift away from their established theme.
    Uses keyword-overlap + phoneme similarity heuristic.
    """

    STOP_WORDS = {
        "i", "me", "my", "you", "your", "we", "us", "the", "a", "an",
        "is", "am", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would",
        "could", "should", "can", "may", "might", "shall",
        "in", "on", "at", "to", "for", "of", "with", "by", "from",
        "up", "out", "if", "or", "and", "but", "not", "no", "so",
        "too", "very", "just", "don't", "don", "didn", "didn't",
        "it", "its", "it's", "that", "this", "those", "these",
        "what", "when", "where", "who", "how", "all", "each",
        "every", "both", "few", "more", "most", "other", "some",
        "such", "than", "then", "only", "own", "same",
        "like", "got", "get", "go", "going", "gonna", "ain't",
        "yeah", "uh", "oh", "ay", "hey", "yo",
    }

    def detect(self, lines: List[str], session_theme: str = "") -> Dict:
        """
        Analyze drift between early lines (anchor) and recent lines.
        Returns drift score 0.0–1.0 and a warning message.
        """
        clean_lines = [l.strip() for l in lines if l.strip()]

        if len(clean_lines) < 6:
            return {
                "drift_score": 0.0,
                "status": "stable",
                "warning": "",
                "anchor_keywords": [],
                "recent_keywords": [],
            }

        # Anchor: first 4 lines + session theme
        anchor_text = " ".join(clean_lines[:4])
        if session_theme:
            anchor_text += " " + session_theme

        # Recent: last 4 lines
        recent_text = " ".join(clean_lines[-4:])

        anchor_kw = self._extract_keywords(anchor_text)
        recent_kw = self._extract_keywords(recent_text)

        if not anchor_kw or not recent_kw:
            return {
                "drift_score": 0.0,
                "status": "stable",
                "warning": "",
                "anchor_keywords": list(anchor_kw),
                "recent_keywords": list(recent_kw),
            }

        # Jaccard similarity
        intersection = anchor_kw & recent_kw
        union = anchor_kw | recent_kw
        similarity = len(intersection) / len(union) if union else 1.0

        # Drift = 1 - similarity
        drift = round(1.0 - similarity, 3)

        # Determine status
        if drift < 0.4:
            status = "stable"
            warning = ""
        elif drift < 0.65:
            status = "drifting"
            warning = f"Your recent bars are starting to wander from the original theme. Anchor keywords: {', '.join(sorted(anchor_kw)[:5])}"
        else:
            status = "off-topic"
            warning = f"Heavy drift detected! Your recent bars share almost no thematic overlap with your opening. Consider circling back to: {', '.join(sorted(anchor_kw)[:5])}"

        return {
            "drift_score": drift,
            "status": status,
            "warning": warning,
            "anchor_keywords": sorted(anchor_kw)[:10],
            "recent_keywords": sorted(recent_kw)[:10],
        }

    def _extract_keywords(self, text: str) -> set:
        """Extract meaningful keywords from text."""
        words = re.findall(r"[a-zA-Z']+", text.lower())
        return {w for w in words if w not in self.STOP_WORDS and len(w) > 2}


# ── Theme Clusterer (for 3D Neural Network) ────────────────────────

class ThemeClusterer:
    """
    Analyze all sessions to extract recurring themes and build a
    3D-renderable graph of theme relationships.
    """

    THEME_CATEGORIES = {
        "ambition": ["grind", "hustle", "goal", "dream", "vision", "chase", "mission", "focus", "driven", "rise"],
        "wealth": ["money", "cash", "bread", "dough", "bands", "racks", "rich", "million", "billion", "diamond", "gold", "chain"],
        "struggle": ["pain", "struggle", "fight", "battle", "survive", "bleed", "scar", "wound", "tough", "hard"],
        "love": ["love", "heart", "soul", "kiss", "touch", "hold", "feel", "miss", "baby", "forever"],
        "loyalty": ["trust", "real", "solid", "loyal", "ride", "day-one", "brother", "family", "bond"],
        "betrayal": ["snake", "fake", "betray", "lie", "stab", "mask", "enemy", "snitch", "backstab"],
        "street": ["block", "corner", "trap", "hood", "street", "concrete", "city", "ghetto", "project"],
        "flex": ["ice", "drip", "fly", "fresh", "swag", "sauce", "clean", "foreign", "whip", "rock"],
        "introspection": ["think", "reflect", "remember", "wonder", "question", "soul", "mirror", "truth", "mind"],
        "celebration": ["party", "celebrate", "toast", "vibe", "lit", "turnt", "wave", "celebrate", "enjoy"],
        "nature": ["sky", "sun", "moon", "star", "rain", "ocean", "mountain", "fire", "wind", "earth"],
        "legacy": ["legacy", "history", "legend", "forever", "immortal", "statue", "monument", "name", "story"],
    }

    def cluster(self, sessions_data: List[Dict]) -> Dict:
        """
        Build a theme graph from session data.

        sessions_data: List of {"id": int, "title": str, "lines": List[str]}

        Returns: {"nodes": [...], "links": [...]}
        """
        # Count theme occurrences per session
        theme_sessions = defaultdict(set)  # theme → set of session_ids
        theme_freq = Counter()  # theme → total word hits

        for session in sessions_data:
            session_id = session.get("id", 0)
            all_text = " ".join(session.get("lines", [])).lower()
            words = set(re.findall(r"[a-zA-Z']+", all_text))

            for theme, keywords in self.THEME_CATEGORIES.items():
                hits = words & set(keywords)
                if hits:
                    theme_sessions[theme].add(session_id)
                    theme_freq[theme] += len(hits)

        if not theme_freq:
            return {"nodes": [], "links": []}

        # Build nodes
        nodes = []
        theme_list = sorted(theme_freq.keys(), key=lambda t: -theme_freq[t])

        # Assign 3D positions (spherical distribution)
        for i, theme in enumerate(theme_list):
            freq = theme_freq[theme]
            phi = (i / max(1, len(theme_list) - 1)) * math.pi * 2
            theta = (i % 5) / 5 * math.pi
            radius = 100 + (i % 3) * 30

            x = radius * math.sin(theta) * math.cos(phi)
            y = radius * math.sin(theta) * math.sin(phi)
            z = radius * math.cos(theta)

            # Cluster color assignment
            cluster_id = i % 6
            colors = ["#60a5fa", "#34d399", "#f59e0b", "#f87171", "#a78bfa", "#ec4899"]

            nodes.append({
                "id": theme,
                "label": theme.title(),
                "frequency": freq,
                "sessions_count": len(theme_sessions[theme]),
                "size": min(20, 5 + freq * 0.5),
                "x": round(x, 2),
                "y": round(y, 2),
                "z": round(z, 2),
                "color": colors[cluster_id],
                "cluster": cluster_id,
            })

        # Build links (themes that co-occur in the same session)
        links = []
        theme_keys = list(theme_sessions.keys())
        for i in range(len(theme_keys)):
            for j in range(i + 1, len(theme_keys)):
                t1, t2 = theme_keys[i], theme_keys[j]
                shared = theme_sessions[t1] & theme_sessions[t2]
                if shared:
                    strength = len(shared)
                    links.append({
                        "source": t1,
                        "target": t2,
                        "value": strength,
                        "shared_sessions": len(shared),
                    })

        return {"nodes": nodes, "links": links}
