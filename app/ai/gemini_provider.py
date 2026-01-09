"""
Google Gemini Provider Implementation
Uses Gemini Pro for lyric generation and analysis
"""
import json
from typing import Optional, Dict, List, Any
import google.generativeai as genai
from app.config import Config
from .base_provider import BaseAIProvider
from .prompts import LyricPrompts


class GeminiProvider(BaseAIProvider):
    """Google Gemini implementation for lyric operations with model rotation"""
    
    # Model rotation hierarchy (lowest tier to highest tier)
    # When quota is exceeded, we try the next model in the list
    MODEL_HIERARCHY = [
        'gemma-3n-e4b-it',       # Lowest tier - Gemma (always available)
        'gemini-2.0-flash-lite',  # Gemini 2.0 Flash Lite
        'gemini-2.0-flash',       # Gemini 2.0 Flash
        'gemini-2.5-flash',       # Gemini 2.5 Flash (highest/preferred)
    ]
    
    def __init__(self):
        genai.configure(api_key=Config.GEMINI_API_KEY)
        # Start with highest-tier model
        self.current_model_index = len(self.MODEL_HIERARCHY) - 1
        self._init_model()
    
    def _init_model(self):
        """Initialize the generative model with current model selection"""
        model_name = self.MODEL_HIERARCHY[self.current_model_index]
        self.model = genai.GenerativeModel(model_name)
        self.current_model_name = model_name
    
    def _rotate_to_next_model(self) -> bool:
        """Rotate to the next available model in the fallback hierarchy.
        Returns True if a model is available, False if all exhausted."""
        if self.current_model_index > 0:
            self.current_model_index -= 1
            self._init_model()
            print(f"[AI] Rotating to fallback model: {self.current_model_name}")
            return True
        return False
    
    def get_current_model_info(self) -> dict:
        """Get information about the current model being used"""
        return {
            'model_name': self.current_model_name,
            'tier': self.current_model_index + 1,
            'total_tiers': len(self.MODEL_HIERARCHY),
            'is_fallback': self.current_model_index < len(self.MODEL_HIERARCHY) - 1
        }
    
    def reset_to_best_model(self):
        """Reset to the highest-tier model (useful when quota resets)"""
        self.current_model_index = len(self.MODEL_HIERARCHY) - 1
        self._init_model()
        print(f"[AI] Reset to best model: {self.current_model_name}")
        
    def _call_api(self, user_prompt: str, temperature: float = 0.8) -> str:
        """Make API call to Gemini with automatic model rotation on quota errors"""
        max_retries = len(self.MODEL_HIERARCHY)
        last_error = None
        
        for attempt in range(max_retries):
            try:
                # Combine system prompt with user prompt
                full_prompt = f"{LyricPrompts.SYSTEM_PROMPT}\n\n---\n\n{user_prompt}"
                
                generation_config = genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=1000
                )
                
                response = self.model.generate_content(
                    full_prompt,
                    generation_config=generation_config
                )
                
                return response.text
            except Exception as e:
                error_str = str(e).lower()
                # Check for quota/rate limit errors
                if 'quota' in error_str or 'rate' in error_str or 'exhausted' in error_str or 'resource' in error_str or '429' in error_str:
                    last_error = e
                    print(f"[AI] Quota exceeded for {self.current_model_name}: {str(e)[:100]}")
                    if not self._rotate_to_next_model():
                        raise Exception(f"All Gemini models exhausted. Last error: {str(e)}")
                    continue
                else:
                    # Non-quota error, raise immediately
                    raise Exception(f"Gemini API error ({self.current_model_name}): {str(e)}")
        
        raise Exception(f"Failed after {max_retries} model rotation attempts. Last error: {str(last_error)}")
    
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
        
        response = self._call_api(prompt, temperature=0.3)
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
        
        scheme = []
        rhyme_groups = {}
        current_letter = ord('A')
        
        for line in lines[-4:]:
            words = line.strip().split()
            if not words:
                scheme.append('X')
                continue
            
            last_word = words[-1].lower().strip('.,!?')
            
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
        """Simple check if two words might rhyme"""
        if len(word1) < 2 or len(word2) < 2:
            return False
        return word1[-2:] == word2[-2:]
