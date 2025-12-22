"""
Perplexity AI Provider
Uses Perplexity AI API for lyric generation
"""
import os
import requests
from .base_provider import BaseAIProvider
from .prompts import LyricPrompts
from .context_builder import ContextBuilder


class PerplexityProvider(BaseAIProvider):
    """Perplexity AI implementation - Best with Premium Plus subscription"""
    
    def __init__(self):
        self.api_key = os.getenv("PERPLEXITY_API_KEY")
        self.base_url = "https://api.perplexity.ai"
        # Use the latest and most capable model for Premium Plus users
        self.model = "llama-3.1-sonar-huge-128k-online"  # Most powerful, requires Pro/Premium
        self.prompts = LyricPrompts()
        self.context_builder = ContextBuilder()
    
    def _make_request(self, messages: list, max_tokens: int = 500) -> str:
        """Make a request to Perplexity API"""
        if not self.api_key:
            raise ValueError("PERPLEXITY_API_KEY not set in environment")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.8
        }
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code != 200:
            raise Exception(f"Perplexity API error: {response.text}")
        
        result = response.json()
        return result["choices"][0]["message"]["content"]
    
    def suggest_next_line(self, previous_lines: list, bpm: int = 140, 
                         style_context: dict = None) -> dict:
        """Suggest the next lyric line"""
        context = self.context_builder.build_suggestion_context(
            previous_lines, bpm, style_context
        )
        
        messages = [
            {"role": "system", "content": self.prompts.get_system_prompt()},
            {"role": "user", "content": self.prompts.get_suggestion_prompt(context)}
        ]
        
        response = self._make_request(messages)
        return self._parse_suggestion_response(response)
    
    def improve_line(self, line: str, improvement_type: str = "rhyme",
                    bpm: int = 140, style_context: dict = None) -> dict:
        """Improve an existing line"""
        context = self.context_builder.build_improvement_context(
            line, improvement_type, bpm, style_context
        )
        
        messages = [
            {"role": "system", "content": self.prompts.get_system_prompt()},
            {"role": "user", "content": self.prompts.get_improvement_prompt(context)}
        ]
        
        response = self._make_request(messages)
        return self._parse_improvement_response(response)
    
    def answer_user_question(self, question: str, session_context: dict = None) -> str:
        """Answer a user question about lyrics/writing"""
        messages = [
            {"role": "system", "content": self.prompts.get_system_prompt()},
            {"role": "user", "content": f"Question about hip-hop lyric writing: {question}"}
        ]
        
        return self._make_request(messages, max_tokens=800)
    
    def _parse_suggestion_response(self, response: str) -> dict:
        """Parse the AI response into structured suggestion data"""
        lines = response.strip().split('\n')
        suggestion = lines[0] if lines else ""
        alternatives = [l.strip('- ') for l in lines[1:4] if l.strip()]
        
        return {
            "suggestion": suggestion,
            "alternatives": alternatives,
            "rhyme_info": None,
            "question": None
        }
    
    def _parse_improvement_response(self, response: str) -> dict:
        """Parse improvement response"""
        lines = response.strip().split('\n')
        improved = lines[0] if lines else ""
        alternatives = [l.strip('- ') for l in lines[1:4] if l.strip()]
        
        return {
            "improved": improved,
            "alternatives": alternatives,
            "explanation": None
        }
