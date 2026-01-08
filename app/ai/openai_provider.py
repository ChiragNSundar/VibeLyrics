"""
OpenAI Provider Implementation
Uses GPT-4 for lyric generation and analysis
"""
import json
from typing import Optional, Dict, List, Any
from openai import OpenAI
from app.config import Config
from .base_provider import BaseAIProvider
from .prompts import LyricPrompts


class OpenAIProvider(BaseAIProvider):
    """OpenAI GPT-4 implementation for lyric operations"""
    
    def __init__(self):
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.model = "gpt-4o"  # Best for creative writing
        
    def _call_api(self, user_prompt: str, temperature: float = 0.8) -> str:
        """Make API call to OpenAI"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": LyricPrompts.SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    def _parse_json_response(self, response: str) -> Dict:
        """Parse JSON from response, handling markdown code blocks"""
        # Remove markdown code blocks if present
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            response = response.split("```")[1].split("```")[0]
        
        try:
            return json.loads(response.strip())
        except json.JSONDecodeError:
            # If JSON parsing fails, return a structured default
            return {"error": "Failed to parse response", "raw": response}
    
    def _call_api_stream(self, user_prompt: str, temperature: float = 0.8):
        """Streaming API call yielding chunks"""
        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": LyricPrompts.SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=200, # Shorter for streaming suggestions
                stream=True
            )
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            yield f"[ERROR: {str(e)}]"

    def suggest_next_line_stream(
        self,
        previous_lines: List[str],
        bpm: int,
        style_context: Dict[str, Any]
    ):
        """Stream suggestion for next line"""
        syllable_range = Config.get_syllable_target(bpm)
        rhyme_scheme = self._analyze_rhyme_scheme(previous_lines) if previous_lines else "Starting fresh"
        prev_lines_text = "\n".join([f"{i+1}. {line}" for i, line in enumerate(previous_lines)]) if previous_lines else "No previous lines"
        
        prompt = LyricPrompts.SUGGEST_NEXT_LINE.format(
            previous_lines=prev_lines_text,
            bpm=bpm,
            syllable_range=f"{syllable_range[0]}-{syllable_range[1]} syllables",
            style_context=json.dumps(style_context),
            journal_context="",
            reference_context="",
            rhyme_scheme=rhyme_scheme
        )
        
        # Append instruction to return ONLY the raw line text for streaming, no JSON
        prompt += "\n\nCRITICAL: Return ONLY the suggested lyric text. Do not wrap in JSON. Do not include quotes."
        
        return self._call_api_stream(prompt, temperature=0.9)

    def suggest_next_line(
        self,
        previous_lines: List[str],
        bpm: int,
        style_context: Dict[str, Any],
        journal_context: Optional[str] = None,
        reference_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Suggest the next line based on context"""
        syllable_range = Config.get_syllable_target(bpm)
        
        # Build rhyme scheme from previous lines
        rhyme_scheme = self._analyze_rhyme_scheme(previous_lines) if previous_lines else "Starting fresh"
        
        # Format previous lines
        prev_lines_text = "\n".join([f"{i+1}. {line}" for i, line in enumerate(previous_lines)]) if previous_lines else "No previous lines yet - this is the first line"
        
        # Format optional contexts
        journal_text = f"\nJournal context to draw from:\n{journal_context}" if journal_context else ""
        reference_text = f"\nReference style notes:\n{reference_context}" if reference_context else ""
        
        prompt = LyricPrompts.SUGGEST_NEXT_LINE.format(
            previous_lines=prev_lines_text,
            bpm=bpm,
            syllable_range=f"{syllable_range[0]}-{syllable_range[1]} syllables",
            style_context=json.dumps(style_context),
            journal_context=journal_text,
            reference_context=reference_text,
            rhyme_scheme=rhyme_scheme
        )
        
        response = self._call_api(prompt)
        return self._parse_json_response(response)
    
    def improve_line(
        self,
        line: str,
        improvement_type: str,
        bpm: int,
        style_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Suggest improvements for an existing line"""
        syllable_range = Config.get_syllable_target(bpm)
        
        prompt = LyricPrompts.IMPROVE_LINE.format(
            line=line,
            improvement_type=improvement_type,
            bpm=bpm,
            syllable_range=f"{syllable_range[0]}-{syllable_range[1]} syllables",
            style_context=json.dumps(style_context)
        )
        
        response = self._call_api(prompt)
        return self._parse_json_response(response)
    
    def analyze_bars(
        self,
        lines: List[str],
        bpm: int
    ) -> Dict[str, Any]:
        """Analyze a set of bars for rhyme scheme, flow, complexity"""
        lines_text = "\n".join([f"{i+1}. {line}" for i, line in enumerate(lines)])
        
        prompt = LyricPrompts.ANALYZE_BARS.format(
            lines=lines_text,
            bpm=bpm
        )
        
        response = self._call_api(prompt, temperature=0.3)  # Lower temp for analysis
        return self._parse_json_response(response)
    
    def ask_clarifying_question(
        self,
        current_line: str,
        context: Dict[str, Any]
    ) -> Optional[str]:
        """Determine if a clarifying question should be asked"""
        prompt = LyricPrompts.CLARIFYING_QUESTION.format(
            current_line=current_line,
            context=json.dumps(context)
        )
        
        response = self._call_api(prompt, temperature=0.5)
        
        # Check if response indicates no question needed
        if "null" in response.lower() or "no question" in response.lower():
            return None
        
        return response.strip().strip('"')
    
    def answer_user_question(
        self,
        question: str,
        session_context: Dict[str, Any]
    ) -> str:
        """Answer a question the user has about lyrics/writing"""
        prompt = f"""The artist asks: "{question}"

Session context: {json.dumps(session_context)}

Answer helpfully and specifically for their hip-hop writing session. 
Be concise but thorough. If they're asking about technique, give examples."""
        
        response = self._call_api(prompt, temperature=0.7)
        return response
    
    def extract_themes_from_journal(
        self,
        journal_entry: str
    ) -> Dict[str, Any]:
        """Extract themes and keywords from a journal entry"""
        prompt = LyricPrompts.JOURNAL_EXTRACTION.format(
            journal_entry=journal_entry
        )
        
        response = self._call_api(prompt, temperature=0.6)
        return self._parse_json_response(response)
    
    def _analyze_rhyme_scheme(self, lines: List[str]) -> str:
        """Quick rhyme scheme analysis for context"""
        if not lines:
            return "N/A"
        
        # Simple placeholder - will be enhanced by analysis module
        scheme = []
        rhyme_groups = {}
        current_letter = ord('A')
        
        for line in lines[-4:]:  # Only look at last 4 lines for scheme
            # Get last word
            words = line.strip().split()
            if not words:
                scheme.append('X')
                continue
            
            last_word = words[-1].lower().strip('.,!?')
            
            # Check if rhymes with existing
            found = False
            for word, letter in rhyme_groups.items():
                if self._simple_rhyme_check(last_word, word):
                    scheme.append(letter)
                    found = True
                    break
            
            if not found:
                letter = chr(current_letter)
                rhyme_groups[last_word] = letter
                scheme.append(letter)
                current_letter += 1
        
        return ''.join(scheme)
    
    def _simple_rhyme_check(self, word1: str, word2: str) -> bool:
        """Simple check if two words might rhyme (based on ending)"""
        if len(word1) < 2 or len(word2) < 2:
            return False
        return word1[-2:] == word2[-2:]
