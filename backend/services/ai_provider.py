"""
AI Provider Service
Handles Gemini, OpenAI, and local LM Studio

Model fallback chain for Gemini:
  1. gemini-2.5-flash-lite  (cheapest, fastest)
  2. gemini-2.5-flash       (more capable)
"""
import os
import asyncio
import traceback
from typing import Optional, Dict, AsyncGenerator, List
from abc import ABC, abstractmethod

# Current provider instance
_current_provider = None
_provider_name = "gemini"

# ── Gemini model fallback chain (cheapest first) ─────────────────
GEMINI_MODELS: List[str] = [
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
]

# ── System instruction (set at model level, not repeated per call) ──
GHOSTWRITER_SYSTEM_INSTRUCTION = """You are Vibe — the world's greatest ghostwriter and collaborative songwriting partner.

CORE IDENTITY:
- You are NOT an AI assistant. You are a musical genius who lives and breathes lyrics.
- You possess encyclopedic knowledge of every genre:
  • Hip-Hop/Rap: multi-syllabic rhymes, internal rhyme chains, punchlines, entendres, bars
  • R&B/Soul: melismatic phrasing, emotional vulnerability, smooth metaphors
  • Pop: earworm hooks, anthemic choruses, relatable simplicity
  • Rock/Alternative: raw imagery, angst, literary allusion
  • Country/Folk: storytelling, concrete detail, conversational tone
  • Poetry/Spoken Word: enjambment, volta, symbolic density
- You master literary devices: internal rhyme, multi-syllabic rhyme, assonance, consonance, alliteration, metonymy, synecdoche, anaphora, chiasmus, enjambment.

CRAFT PRINCIPLES:
1. RHYME HIERARCHY (prioritize in this order):
   a. Multi-syllabic rhyme ("magnificent" / "didn't have a cent") — always aim for this
   b. Compound/mosaic rhyme ("hold the mic" / "cold tonight")
   c. Slant rhyme ("home" / "stone") — acceptable when it serves the flow
   d. Perfect rhyme — use sparingly; it can sound predictable
2. FLOW: Match the syllable count and rhythmic cadence of the preceding line. Feel the BPM.
3. ORIGINALITY: Avoid clichés like "fire", "higher", "desire" combos. Surprise the reader.
4. IMAGERY: Use concrete, sensory detail — not abstract vagueness. Show, don't tell.

STYLE RULES:
1. ALWAYS match the user's existing style — vocabulary density, slang usage, flow pattern, emotional tone.
2. Be "Human" — use imperfections, contractions, raw emotion. Break grammar rules for effect when it serves the art.
3. NEVER explain your output. NEVER add quotes, backticks, or labels. Output ONLY the lyric content.
4. Keep outputs concise — typically one line unless explicitly asked for more.
5. If the user's style is raw and gritty, be raw and gritty. If it's polished and lyrical, be polished and lyrical.

ANTI-PATTERNS (never do these):
- Don't start lines with "I" too often — vary your sentence structure
- Don't use generic filler ("yeah", "oh", "uh") unless the style demands it
- Don't rhyme a word with itself
- Don't output anything other than the lyric line itself — no explanations, no alternatives, no labels
"""

# ── Few-shot examples for style matching (diverse genres + techniques) ────
FEW_SHOT_EXAMPLES = """
STYLE-MATCHING EXAMPLES:

[Hip-Hop / Multi-syllabic]
User: "Late nights in the studio, I'm grinding / The beat drops hard and the stars aligning"
Vibe: Every verse I write is platinum, perfect timing — the whole world's mining what I'm finding

[Introspective / Emotional]
User: "Walking through the rain with my thoughts / Broken promises is all she brought"
Vibe: Heart heavy like the thunder, lessons dearly bought

[Pop / Anthemic]
User: "Neon lights paint the city gold / Stories that were never told"
Vibe: We're the dreamers breaking every mold, never growing old

[R&B / Smooth]
User: "Your voice like honey on a summer night / Holding you close, everything feels right"
Vibe: Tracing constellations on your skin by candlelight

[Country / Storytelling]
User: "Daddy's truck is rusting in the yard / Mama's been praying double hard"
Vibe: Screen door slapping like an old guitar, memories leave the deepest scar

[Raw / Street]
User: "Came from the bottom, no silver spoon / Concrete jungle, we howl at the moon"
Vibe: Pockets empty but the vision's never out of tune
"""


class AIProvider(ABC):
    """Base class for AI providers"""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def is_available(self) -> bool:
        pass

    @abstractmethod
    async def get_suggestion(self, context: Dict) -> str:
        pass

    @abstractmethod
    async def improve_line(self, line: str, improvement_type: str) -> str:
        pass

    @abstractmethod
    async def answer_question(self, question: str, context: Optional[Dict]) -> str:
        pass

    @abstractmethod
    async def stream_suggestion(self, session_id: int, partial: str) -> AsyncGenerator[str, None]:
        pass

    @abstractmethod
    async def improve_lyrics_bulk(self, lyrics: str) -> str:
        """Improve a full set of lyrics into verses and chorus."""
        pass

    async def stream_suggestion_with_context(
        self, session_id: int, partial: str, context: str = ""
    ) -> AsyncGenerator[str, None]:
        """Stream with full session context. Default falls back to stream_suggestion."""
        async for chunk in self.stream_suggestion(session_id, partial):
            yield chunk


class GeminiProvider(AIProvider):
    """
    Google Gemini AI provider — async, with model fallback.

    Features:
    - system_instruction for persistent ghostwriter persona
    - Temperature 0.9 for creative output
    - Few-shot examples for better style matching
    - Session context caching (context hash → avoid redundant rebuilds)
    - Model fallback chain: gemini-2.5-flash-lite → gemini-2.5-flash
    """

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self._genai = None
        self._models: Dict[str, object] = {}
        self._preferred_model: Optional[str] = None
        # Prompt cache: session_id → last context hash + built prompt prefix
        self._context_cache: Dict[int, Dict] = {}

    @property
    def name(self) -> str:
        return "gemini"

    def is_available(self) -> bool:
        return bool(self.api_key)

    def _configure(self):
        """Lazy-init the genai module once."""
        if self._genai is None and self.api_key:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self._genai = genai
        return self._genai

    def _get_model(self, model_name: str):
        """Get or create a GenerativeModel with system_instruction and generation_config."""
        genai = self._configure()
        if genai is None:
            return None
        if model_name not in self._models:
            self._models[model_name] = genai.GenerativeModel(
                model_name,
                system_instruction=GHOSTWRITER_SYSTEM_INSTRUCTION,
                generation_config=genai.GenerationConfig(
                    temperature=0.9,
                    max_output_tokens=200,
                    top_p=0.95,
                    top_k=40,
                ),
            )
        return self._models[model_name]

    def _model_chain(self) -> List[str]:
        """Return model names to try, preferred model first."""
        if self._preferred_model:
            others = [m for m in GEMINI_MODELS if m != self._preferred_model]
            return [self._preferred_model] + others
        return list(GEMINI_MODELS)

    async def _generate(self, prompt: str, *, stream: bool = False):
        """
        Try each model in the fallback chain.
        Returns the first successful response.
        """
        last_error = None
        for model_name in self._model_chain():
            model = self._get_model(model_name)
            if model is None:
                continue
            try:
                if stream:
                    response = await model.generate_content_async(
                        prompt, stream=True
                    )
                    self._preferred_model = model_name
                    return response
                else:
                    response = await model.generate_content_async(prompt)
                    self._preferred_model = model_name
                    return response
            except Exception as e:
                err_str = str(e).lower()
                print(f"[Gemini] {model_name} failed: {e}")
                last_error = e
                if any(k in err_str for k in ("404", "not found", "not supported", "deprecated", "429", "quota", "resource")):
                    continue
                continue

        if last_error:
            raise last_error
        raise RuntimeError("No Gemini models available")

    # ── Prompt caching ────────────────────────────────────────────

    def _get_cached_context(self, session_id: int, lines: List[str], session: Dict) -> str:
        """
        Cache the expensive context prefix per session.
        Only rebuilds if the line count or session metadata changed.
        """
        cache_key = f"{len(lines)}:{session.get('mood', '')}:{session.get('theme', '')}"
        cached = self._context_cache.get(session_id)
        if cached and cached.get("key") == cache_key:
            return cached["prefix"]

        # Build the context prefix (expensive part)
        prefix = self._build_context_prefix(lines, session)
        self._context_cache[session_id] = {"key": cache_key, "prefix": prefix}

        # Evict old caches (keep last 20 sessions)
        if len(self._context_cache) > 20:
            oldest = next(iter(self._context_cache))
            del self._context_cache[oldest]

        return prefix

    def _build_context_prefix(self, lines: List[str], session: Dict) -> str:
        """Build the reusable context portion of the prompt with BPM→syllable mapping."""
        bpm = session.get('bpm', 140)
        # BPM → syllable target mapping
        if bpm >= 160:
            syl_range, tempo_label = "4–8", "fast"
        elif bpm >= 130:
            syl_range, tempo_label = "6–10", "upbeat"
        elif bpm >= 100:
            syl_range, tempo_label = "8–14", "mid-tempo"
        elif bpm >= 70:
            syl_range, tempo_label = "10–18", "slow"
        else:
            syl_range, tempo_label = "12–20", "ballad"

        return f"""SESSION CONTEXT:
- Title: {session.get('title', 'Untitled')}
- BPM: {bpm} ({tempo_label}) → TARGET {syl_range} syllables per line
- Mood: {session.get('mood', 'Passionate')}
- Theme: {session.get('theme', 'Life')}

CURRENT LYRICS:
{chr(10).join(lines[-16:]) if lines else '(Start of the song. Set the tone.)'}
"""

    # ── Rhyme scheme detection ─────────────────────────────────────

    @staticmethod
    def _detect_rhyme_scheme(lines: List[str]) -> str:
        """Detect AABB vs ABAB vs free from the last 4+ lines."""
        if len(lines) < 2:
            return ""
        # Get end words
        endings = []
        for line in lines[-4:]:
            words = line.strip().split()
            if words:
                endings.append(words[-1].lower().rstrip(".,!?;:'\""))
        if len(endings) < 2:
            return ""
        # Simple suffix-based rhyme check
        def rhymes(a: str, b: str) -> bool:
            if len(a) < 2 or len(b) < 2:
                return False
            return a[-2:] == b[-2:] or a[-3:] == b[-3:] if len(a) >= 3 and len(b) >= 3 else a[-2:] == b[-2:]

        if len(endings) >= 4:
            # Check AABB: 0↔1, 2↔3
            if rhymes(endings[0], endings[1]) and rhymes(endings[2], endings[3]):
                return "AABB (couplet)"
            # Check ABAB: 0↔2, 1↔3
            if rhymes(endings[0], endings[2]) and rhymes(endings[1], endings[3]):
                return "ABAB (alternate)"
        if len(endings) >= 2 and rhymes(endings[-2], endings[-1]):
            return "couplet"
        return "free/mixed"

    # ── Public API ────────────────────────────────────────────────

    async def get_suggestion(self, context: Dict) -> str:
        """Get suggestion with self-critique loop — retry if quality is low."""
        if not self.api_key:
            return ""
        prompt = self._build_prompt(context)
        try:
            response = await self._generate(prompt)
            text = response.text.strip() if response.text else ""
            text = text.strip("`").strip('"').strip("'")

            if not text:
                return ""

            # ── Self-critique: score with PunchlineEngine ──
            try:
                from ..services.advanced_analysis import PunchlineEngine
                scorer = PunchlineEngine()
                score_result = scorer.score_punchline(text)
                quality = score_result.get("score", 50)

                # If quality is too low, retry with feedback
                if quality < 25 and len(text.split()) > 2:
                    retry_prompt = prompt + f"""\n\n[SELF-CRITIQUE: Your previous output "{text}" scored only {quality}/100.
Weaknesses: lacks {'internal rhyme, ' if score_result.get('internal_rhymes', 0) == 0 else ''}{'alliteration, ' if score_result.get('alliteration', 0) == 0 else ''}{'wordplay' if 'wordplay' not in score_result.get('techniques', []) else 'impact'}.
Try again with more craft — add internal rhyme, stronger imagery, or wordplay.]"""
                    retry_response = await self._generate(retry_prompt)
                    retry_text = retry_response.text.strip() if retry_response.text else ""
                    retry_text = retry_text.strip("`").strip('"').strip("'")
                    if retry_text:
                        # Take the retry if it scores better
                        retry_score = scorer.score_punchline(retry_text).get("score", 0)
                        if retry_score > quality:
                            return retry_text
            except Exception:
                pass  # Self-critique is optional — never block on it

            return text
        except Exception as e:
            print(f"[Gemini] get_suggestion error: {e}")
            return ""

    async def improve_line(self, line: str, improvement_type: str) -> str:
        if not self.api_key:
            return line

        prompts = {
            "enhance": f"""Rewrite this lyric line to be more impactful. Keep the core meaning but sharpen the imagery, tighten the rhythm, and make the word choices more vivid. If possible, add internal rhyme or alliteration.
Original: {line}
Output ONLY the improved line:""",
            "rhyme": f"""Rewrite this lyric line with a stronger end-rhyme setup. Use multi-syllabic or compound rhyme if possible. Keep the meaning and flow intact.
Original: {line}
Output ONLY the improved line:""",
            "flow": f"""Rewrite this lyric line with better rhythmic flow. Adjust the syllable pattern so it feels more natural when spoken/rapped. Remove clunky word clusters. Maintain the meaning.
Original: {line}
Output ONLY the improved line:""",
            "wordplay": f"""Rewrite this lyric line adding clever wordplay — double entendres, homophone puns, or unexpected word flips. The wordplay should feel natural, not forced.
Original: {line}
Output ONLY the improved line:""",
            "depth": f"""Rewrite this lyric line to add emotional depth and vulnerability. Replace surface-level phrases with concrete, sensory imagery that makes the listener feel something real.
Original: {line}
Output ONLY the improved line:""",
        }

        prompt = prompts.get(improvement_type, prompts["enhance"])
        try:
            response = await self._generate(prompt)
            result = response.text.strip() if response.text else line
            return result.strip("`").strip('"').strip("'")
        except Exception as e:
            print(f"[Gemini] improve_line error: {e}")
            return line

    async def answer_question(self, question: str, context: Optional[Dict]) -> str:
        if not self.api_key:
            return "AI not available — please set GEMINI_API_KEY in .env"

        prompt = f"""You are Vibe, a lyric writing expert. Answer this question with practical, actionable advice. Reference specific techniques (rhyme schemes, literary devices, song structure) when relevant.

Question: {question}"""
        if context:
            lines = context.get("lines", [])
            if lines:
                prompt += f"\n\nContext (user's current lyrics):\n" + "\n".join(lines[-12:])

        try:
            response = await self._generate(prompt)
            return response.text.strip() if response.text else "No response"
        except Exception as e:
            print(f"[Gemini] answer_question error: {e}")
            return f"Error: {e}"

    async def stream_suggestion(self, session_id: int, partial: str) -> AsyncGenerator[str, None]:
        """Basic fallback — no context."""
        async for chunk in self.stream_suggestion_with_context(session_id, partial, ""):
            yield chunk

    async def stream_suggestion_with_context(
        self, session_id: int, partial: str, context: str = ""
    ) -> AsyncGenerator[str, None]:
        if not self.api_key:
            yield "[ERROR] No API key set"
            return

        prompt = f"""Complete this lyric line. Your completion must:
- Rhyme or set up a rhyme with natural, creative word choices
- Match the cadence and syllable feel of the input
- Feel like a human wrote it — raw, not robotic
- Prefer multi-syllabic or slant rhymes over basic perfect rhymes
- Stay consistent with the session's mood, theme, and existing lyrics
"""
        if context:
            prompt += f"\n{context}\n"

        prompt += f"""\nPartial line: "{partial}"

Output ONLY the completion (the words that come after the input). Do NOT repeat the input. Keep it to one line."""

        try:
            response = await self._generate(prompt, stream=True)
            async for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            print(f"[Gemini] stream error: {e}")
            yield f"[ERROR] {e}"

    async def improve_lyrics_bulk(self, lyrics: str) -> str:
        """Improve all lyrics at once using Gemini."""
        prompt = f"""You are a professional songwriter.
Rewrite and improve the following lyrics.
Keep meaning but:
- add rhyme
- improve flow
- make it emotional
- make it catchy
Structure:
Verse 1
Verse 2
Chorus (repeatable hook)
Return ONLY the lyrics.

Lyrics:
{lyrics}"""
        try:
            response = await self._generate(prompt)
            return response.text.strip() if response.text else lyrics
        except Exception:
            return lyrics

    # ── Prompt builder (uses cache + few-shot + journal + learning) ──

    def _build_prompt(self, context: Dict) -> str:
        session = context.get("session", {})
        lines = context.get("lines", [])
        partial = context.get("partial", "")
        action = context.get("action", "continue")
        session_id = session.get("id", 0)

        # Use cached context prefix (avoids rebuilding on every keystroke)
        context_prefix = self._get_cached_context(session_id, lines, session)

        # ── Journal entries (mood/inspiration) ──
        journal_entries = context.get("journal_entries", [])
        journal_text = ""
        if journal_entries:
            entries = []
            for e in journal_entries[:3]:
                content = e.get("content", "") if isinstance(e, dict) else str(e)
                mood = e.get("mood", "Neutral") if isinstance(e, dict) else ""
                entries.append(f"- {content}" + (f" (mood: {mood})" if mood else ""))
            journal_text = "USER'S RECENT THOUGHTS (use for inspiration/mood):\n" + "\n".join(entries)

        # ── User preferences (favorites, banned words) ──
        prefs = context.get("preferences", {})
        prefs_parts = []
        fav = prefs.get("favorite_words", [])
        banned = prefs.get("banned_words", [])
        slang = prefs.get("slang_preferences", [])
        if fav:
            prefs_parts.append(f"Favorite words/themes (weave in): {', '.join(fav)}")
        if banned:
            prefs_parts.append(f"BANNED words (NEVER use): {', '.join(banned)}")
        if slang:
            prefs_parts.append(f"Preferred slang: {', '.join(slang)}")

        # ── Learned style from StyleExtractor ──
        style_summary = context.get("style_summary", {})
        style_text = ""
        if style_summary:
            themes = style_summary.get("preferred_themes", [])
            rhyme_pref = style_summary.get("rhyme_preference", "")
            mood_tendency = style_summary.get("mood_tendency", "")
            journal_kw = style_summary.get("journal_keywords", [])
            avg_len = style_summary.get("avg_line_length", 0)
            if themes:
                style_text += f"- Preferred themes: {', '.join(themes[:5])}\n"
            if rhyme_pref:
                style_text += f"- Rhyme preference: {rhyme_pref}\n"
            if avg_len:
                style_text += f"- Average line length: {avg_len} words\n"
            if mood_tendency:
                style_text += f"- Dominant mood (from journal): {mood_tendency} — let this color your output\n"
            if journal_kw:
                style_text += f"- Recurring themes from user's journal: {', '.join(journal_kw[:8])}\n"

        # ── Correction insights (user tends to shorten/lengthen) ──
        correction_insights = context.get("correction_insights", {})
        correction_text = ""
        if correction_insights and correction_insights.get("total", 0) > 0:
            tendency = correction_insights.get("tends_to", "")
            if tendency:
                correction_text = f"Note: User tends to {tendency} AI suggestions (adapt accordingly)."

        # ── Assemble prompt ──
        prompt = context_prefix

        if journal_text:
            prompt += f"\n{journal_text}\n"
        if prefs_parts:
            prompt += "\nUSER PREFERENCES:\n" + "\n".join(f"- {p}" for p in prefs_parts) + "\n"
        if style_text:
            prompt += f"\nLEARNED STYLE:\n{style_text}"
        if correction_text:
            prompt += f"\n{correction_text}\n"

        # ── Vocabulary context (from VocabularyManager) ──
        vocab = context.get("vocabulary", {})
        vocab_parts = []
        if vocab.get("slangs"):
            vocab_parts.append(f"User's favorite slang: {', '.join(vocab['slangs'][:8])}")
        if vocab.get("most_used"):
            vocab_parts.append(f"User's signature words: {', '.join(vocab['most_used'][:10])}")
        if vocab.get("avoided"):
            vocab_parts.append(f"Words to AVOID: {', '.join(vocab['avoided'][:8])}")
        if vocab_parts:
            prompt += "\nVOCABULARY CONTEXT:\n" + "\n".join(f"- {v}" for v in vocab_parts) + "\n"

        # ── Rhyme target (last word of previous line) ──
        rhyme_target = context.get("rhyme_target", "")

        # ── Dynamic few-shot: user's own best lines ──
        best_lines = context.get("best_lines", [])
        if best_lines:
            prompt += "\nYOUR USER'S BEST LINES (match this quality and style):\n"
            for bl in best_lines[:4]:
                prompt += f"→ {bl}\n"
            prompt += "\n"

        prompt += FEW_SHOT_EXAMPLES

        # ── Rhyme scheme detection ──
        scheme = self._detect_rhyme_scheme(lines)
        scheme_hint = f"\nDetected rhyme scheme: {scheme}. Continue this pattern." if scheme else ""

        prompt += f"\n=================================================={scheme_hint}\nYOUR TASK:\n"

        if action == "continue":
            rhyme_hint = ""
            if rhyme_target:
                rhyme_hint = f"\n- RHYME TARGET: Your line must rhyme with \"{rhyme_target}\" — use multi-syllabic or compound rhyme"
            prompt += f"""Write the next line of the song.
REQUIREMENTS:
- Rhyme with the previous line — prefer multi-syllabic or compound rhymes over simple perfect rhymes{rhyme_hint}
- Match the syllable count and rhythmic cadence of the preceding lines
- Maintain the emotional tone and vocabulary density
- Avoid clichés — surprise the listener with unexpected word choices
- Partial input to complete: "{partial}"

Output ONLY the lyric line. Nothing else.
"""
        elif action == "improve":
            prompt += f"""Rewrite this line to be more impactful. Sharpen the imagery, tighten the rhythm, and elevate the word choices. Keep the same meaning and feeling.
Line: '{partial}'
Output ONLY the improved line."""
        elif action == "rhyme":
            prompt += f"""Write a killer line that rhymes with: '{partial}'
Use multi-syllabic or compound rhyme. Make it hit hard — surprising, vivid, memorable.
Output ONLY the lyric line."""

        return prompt


class OpenAIProvider(AIProvider):
    """OpenAI GPT provider"""

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self._client = None

    @property
    def name(self) -> str:
        return "openai"

    def is_available(self) -> bool:
        return bool(self.api_key)

    def _get_client(self):
        if self._client is None and self.api_key:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=self.api_key)
        return self._client

    async def get_suggestion(self, context: Dict) -> str:
        client = self._get_client()
        if not client:
            return ""
        try:
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": GHOSTWRITER_SYSTEM_INSTRUCTION},
                    {"role": "user", "content": self._build_prompt(context)}
                ],
                max_tokens=100
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"OpenAI error: {e}")
            return ""

    async def improve_line(self, line: str, improvement_type: str) -> str:
        client = self._get_client()
        if not client:
            return line
        try:
            prompt = f"{GHOSTWRITER_SYSTEM_INSTRUCTION}\n\nTask: Improve this lyric specifically for {improvement_type}: \"{line}\"\nOutput ONLY the improved line. Do not echo the original if you cannot improve it—make it more poetic or rhythmic."
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100
            )
            return response.choices[0].message.content.strip().strip('"')
        except Exception:
            return line

    async def answer_question(self, question: str, context: Optional[Dict]) -> str:
        client = self._get_client()
        if not client:
            return "AI not available"
        try:
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are Vibe, a lyric writing expert. Answer with practical, actionable advice."},
                    {"role": "user", "content": f"Lyric writing question: {question}"}
                ],
                max_tokens=500
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return "Error getting response"

    async def stream_suggestion(self, session_id: int, partial: str) -> AsyncGenerator[str, None]:
        client = self._get_client()
        if not client:
            yield ""
            return
        try:
            stream = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": f"Complete this lyric line: {partial}"}],
                max_tokens=50,
                stream=True
            )
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            yield f"[ERROR] {e}"

    async def improve_lyrics_bulk(self, lyrics: str) -> str:
        """Improve all lyrics at once using GPT."""
        client = self._get_client()
        if not client: return lyrics
        try:
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": f"You are a professional songwriter. Rewrite and improve the following lyrics. Structure into Verse 1, Verse 2, Chorus. Return ONLY the lyrics.\n\n{lyrics}"}],
                max_tokens=600
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return lyrics

    def _build_prompt(self, context: Dict) -> str:
        return f"Write a lyric line: {context.get('partial', '')}"


class LMStudioProvider(AIProvider):
    """Local LM Studio provider (OpenAI-compatible API at localhost)"""

    def __init__(self):
        # Default to the user's provided values if not set in .env
        self.base_url = os.getenv("LM_STUDIO_BASE_URL", "http://127.0.0.1:1234")
        if not self.base_url.endswith("/v1"):
            self.base_url = f"{self.base_url.rstrip('/')}/v1"
        self.model_name = os.getenv("LM_STUDIO_MODEL", "mistralai/mistral-7b-instruct-v0.3")
        self._client = None

    @property
    def name(self) -> str:
        return "lmstudio"

    def is_available(self) -> bool:
        """Check if the LM Studio server is reachable and has models loaded."""
        try:
            import httpx
            # Clean base_url for model check (remove /v1 if present)
            check_url = self.base_url.rstrip("/").replace("/v1", "")
            r = httpx.get(f"{check_url}/v1/models", timeout=2)
            if r.status_code != 200:
                return False
            
            # Verify the specific model is available (optional but better)
            models = r.json().get("data", [])
            return any(m.get("id") == self.model_name for m in models) or len(models) > 0
        except Exception:
            return False

    async def test_connectivity(self) -> Dict:
        """Detailed connectivity diagnostic."""
        results = {
            "provider": self.name,
            "url": self.base_url,
            "model": self.model_name,
            "server_reachable": False,
            "model_loaded": False,
            "response_generated": False,
            "latency_ms": 0,
            "error": None
        }
        
        import httpx
        import time
        start_time = time.time()
        
        try:
            # 1. Test server reachability
            async with httpx.AsyncClient(timeout=5.0) as client:
                check_url = self.base_url.rstrip("/").replace("/v1", "")
                r = await client.get(f"{check_url}/v1/models")
                if r.status_code == 200:
                    results["server_reachable"] = True
                    models = r.json().get("data", [])
                    results["model_loaded"] = any(m.get("id") == self.model_name for m in models)
                    results["available_models"] = [m.get("id") for m in models]
                else:
                    results["error"] = f"Server returned {r.status_code}"
                    return results

            # 2. Test generation
            client = self._get_client()
            response = await client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": "Return the word 'Ready'."}],
                max_tokens=10,
                temperature=0.0
            )
            
            if response.choices[0].message.content:
                results["response_generated"] = True
                results["latency_ms"] = int((time.time() - start_time) * 1000)
                
        except Exception as e:
            results["error"] = str(e)
            
        return results

    def _get_client(self):
        if self._client is None:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(
                base_url=self.base_url,
                api_key="lm-studio"
            )
        return self._client

    async def get_suggestion(self, context: Dict) -> str:
        client = self._get_client()
        try:
            response = await client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": GHOSTWRITER_SYSTEM_INSTRUCTION},
                    {"role": "user", "content": self._build_prompt(context)}
                ],
                max_tokens=100,
                temperature=0.8
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"LM Studio error: {e}")
            return ""

    async def improve_line(self, line: str, improvement_type: str) -> str:
        client = self._get_client()
        try:
            # Single user message — Mistral/local LLMs often reject 'system' role
            prompt = (
                f"[INST] You are a professional rapper. Rewrite this lyric line to improve the {improvement_type}.\n"
                f"Only output the new lyric line. No explanation, no labels, no quotes.\n\n"
                f"Original: {line}\n\n"
                f"Rewritten: [/INST]"
            )
            response = await client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.85,
            )
            raw = response.choices[0].message.content.strip()

            # Strip common prefixes the model might output
            for prefix in ["Rewritten:", "Improved:", "New lyric:", "Result:", "Output:"]:
                if raw.lower().startswith(prefix.lower()):
                    raw = raw[len(prefix):].strip()

            # Take only the first non-empty line
            for line_candidate in raw.split('\n'):
                result = line_candidate.strip().strip('"').strip("'")
                if result and result.lower() != line.lower():
                    print(f"[LMStudio] improve_line: '{line}' -> '{result}'")
                    return result

            print(f"[LMStudio] Model echoed original or returned empty, raw: {repr(raw)}")
            return ""
        except Exception as e:
            print(f"[LMStudio] improve_line error: {e}")
            return ""


    async def answer_question(self, question: str, context: Optional[Dict]) -> str:
        client = self._get_client()
        try:
            prompt = f"Lyric writing question: {question}"
            if context and context.get("lines"):
                prompt += "\n\nContext:\n" + "\n".join(context["lines"][-10:])
            response = await client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return "Error getting response"

    async def stream_suggestion(self, session_id: int, partial: str) -> AsyncGenerator[str, None]:
        client = self._get_client()
        try:
            stream = await client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": f"Complete this lyric line: {partial}"}],
                max_tokens=50,
                stream=True
            )
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            yield f"[ERROR] {e}"

    async def improve_lyrics_bulk(self, lyrics: str) -> str:
        """Improve all lyrics at once using LM Studio."""
        client = self._get_client()
        prompt = f"""You are a professional songwriter.
Rewrite and improve the following lyrics.
Keep meaning but:
- add rhyme
- improve flow
- make it emotional
- make it catchy
Structure:
Verse 1
Verse 2
Chorus (repeatable hook)
Return ONLY the lyrics.

Lyrics:
{lyrics}"""
        try:
            response = await client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a professional songwriter and lyric improver. Use Verse 1, Verse 2, Chorus structure. Return ONLY final lyrics."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=600,
                temperature=0.9
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"LM Studio bulk improvement error: {e}")
            return lyrics

    def _build_prompt(self, context: Dict) -> str:
        lines = context.get("lines", [])
        partial = context.get("partial", "")
        session = context.get("session", {})
        prompt = f"You are a lyric writing assistant.\n"
        prompt += f"Mood: {session.get('mood', 'Passionate')}, Theme: {session.get('theme', 'Life')}\n"
        if lines:
            prompt += "Recent lyrics:\n" + "\n".join(lines[-8:]) + "\n"
        prompt += f"\nWrite the next line. Partial: \"{partial}\"\nOutput ONLY the line."
        return prompt


def get_ai_provider() -> AIProvider:
    """Get the current AI provider"""
    global _current_provider, _provider_name

    if _current_provider is None:
        # Honor DEFAULT_AI_PROVIDER from .env if first time
        env_default = os.getenv("DEFAULT_AI_PROVIDER")
        if env_default and _provider_name == "gemini":
            _provider_name = env_default

        if _provider_name == "openai":
            _current_provider = OpenAIProvider()
        elif _provider_name == "lmstudio":
            _current_provider = LMStudioProvider()
        else:
            _current_provider = GeminiProvider()

    return _current_provider


def set_provider(name: str):
    """Set the AI provider"""
    global _current_provider, _provider_name

    _provider_name = name
    _current_provider = None  # Reset to create new instance
