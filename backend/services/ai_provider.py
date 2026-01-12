"""
AI Provider Service
Handles Gemini, OpenAI, and local LM Studio
"""
import os
from typing import Optional, Dict, AsyncGenerator
from abc import ABC, abstractmethod

# Current provider instance
_current_provider = None
_provider_name = "gemini"


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


class GeminiProvider(AIProvider):
    """Google Gemini AI provider"""
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self._model = None
    
    @property
    def name(self) -> str:
        return "gemini"
    
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    def _get_model(self):
        if self._model is None and self.api_key:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self._model = genai.GenerativeModel("gemini-2.0-flash")
        return self._model
    
    async def get_suggestion(self, context: Dict) -> str:
        model = self._get_model()
        if not model:
            return ""
        
        prompt = self._build_prompt(context)
        
        try:
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Gemini error: {e}")
            return ""
    
    async def improve_line(self, line: str, improvement_type: str) -> str:
        model = self._get_model()
        if not model:
            return line
        
        prompts = {
            "rhyme": f"Improve this lyric line to have better rhyme scheme, keep similar meaning:\n{line}",
            "flow": f"Improve the flow and rhythm of this lyric line:\n{line}",
            "wordplay": f"Add clever wordplay to this lyric line:\n{line}",
            "depth": f"Add more emotional depth to this lyric line:\n{line}"
        }
        
        prompt = prompts.get(improvement_type, prompts["rhyme"])
        
        try:
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Gemini error: {e}")
            return line
    
    async def answer_question(self, question: str, context: Optional[Dict]) -> str:
        model = self._get_model()
        if not model:
            return "AI not available"
        
        prompt = f"You are a lyric writing expert. Answer this question:\n{question}"
        
        if context:
            lines = context.get("lines", [])
            if lines:
                prompt += f"\n\nContext (current lyrics):\n" + "\n".join(lines)
        
        try:
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Gemini error: {e}")
            return "Error getting response"
    
    async def stream_suggestion(self, session_id: int, partial: str) -> AsyncGenerator[str, None]:
        model = self._get_model()
        if not model:
            yield ""
            return
        
        prompt = f"""Complete this lyric line with creative, rhyming content:
"{partial}"

Only output the completion, not the original text. Keep it concise (one line)."""
        
        try:
            response = model.generate_content(prompt, stream=True)
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            yield f"[ERROR] {e}"
    
    def _build_prompt(self, context: Dict) -> str:
        session = context.get("session", {})
        lines = context.get("lines", [])
        partial = context.get("partial", "")
        action = context.get("action", "continue")
        
        prompt = f"""ROLE:
You are the world's greatest ghostwriter, a musical genius who understands the soul of the artist. You are NOT an AI assistant; you are a collaborative partner. Your name is Vibe.
You possess deep knowledge of all genres (Hip-Hop, R&B, Pop, Rock, Poetry) and literary devices (internal rhyme, multi-syllabic rhyme, assonance, consonance, metonymy, synecdoche).

OBJECTIVE:
Help the user write their masterpiece. Your goal is to elevate their writing while preserving their unique voice.

STYLE ADAPTATION INSTRUCTIONS:
1. **Analyze the Context**: Look at the "Current Lyrics" below. Identify the user's:
   - **Vocabulary Density**: Simple/Raw vs. Complex/Lyrical.
   - **Slang Usage**: Current street slang vs. Formal/Poetic.
   - **Flow Pattern**: Short, punchy lines vs. Long, storytelling bars.
   - **Emotional Tone**: Aggressive, Melancholic, Hype, Introspective.
2. **Mimic the Style**: Your output MUST match the identified style. Do not sound like a robot. Use imperfections, contractions, and raw emotion.
3. **Be "Human"**: It's okay to break grammar rules for effect. It's okay to be gritty.

SESSION CONTEXT:
- **Title**: {session.get('title', 'Untitled')}
- **BPM**: {session.get('bpm', 140)} (Adjust flow to match this tempo)
- **Mood**: {session.get('mood', 'Passionate')}
- **Theme**: {session.get('theme', 'Life')}

CURRENT LYRICS (Study this style):
{chr(10).join(lines[-16:]) if lines else '(This is the start of the song. Set the tone.)'}

==================================================
YOUR TASK:
"""
        
        if action == "continue":
            prompt += f"""Task: Write the next line.
Requirements:
- Must rhyme strictly with the previous line if applicable (AABB/ABAB).
- Use slant rhymes or multi-syllable rhymes if perfect rhymes aren't available.
- Maintain the flow and syllable count.
- Feel free to use slang if it fits the mood.
- Partial input to complete: "{partial}"
"""
        elif action == "improve":
            prompt += f"Task: Rewrite this line to be more impactful, have better flow, or a stronger rhyme: '{partial}'"
        elif action == "rhyme":
            prompt += f"Task: Write a killer line that rhymes with: '{partial}'"
        
        prompt += "\nOutput ONLY the lyric line. No explanations, no quotes."
        
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
                messages=[{"role": "user", "content": self._build_prompt(context)}],
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
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": f"Improve this lyric for {improvement_type}: {line}"}],
                max_tokens=100
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return line
    
    async def answer_question(self, question: str, context: Optional[Dict]) -> str:
        client = self._get_client()
        if not client:
            return "AI not available"
        
        try:
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": f"Lyric writing question: {question}"}],
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
    
    def _build_prompt(self, context: Dict) -> str:
        return f"Write a lyric line: {context.get('partial', '')}"


def get_ai_provider() -> AIProvider:
    """Get the current AI provider"""
    global _current_provider, _provider_name
    
    if _current_provider is None:
        if _provider_name == "openai":
            _current_provider = OpenAIProvider()
        else:
            _current_provider = GeminiProvider()
    
    return _current_provider


def set_provider(name: str):
    """Set the AI provider"""
    global _current_provider, _provider_name
    
    _provider_name = name
    _current_provider = None  # Reset to create new instance
