"""
LM Studio Provider Implementation
Uses local LM Studio instance via OpenAI-compatible API
"""
from openai import OpenAI
from .openai_provider import OpenAIProvider

class LMStudioProvider(OpenAIProvider):
    """LM Studio implementation interacting via OpenAI-compatible API"""
    
    def __init__(self):
        # API Key is not required for local LM Studio, but SDK requires a non-empty string
        # Base URL defaults to localhost:1234 which is standard for LM Studio
        self.client = OpenAI(
            base_url="http://localhost:1234/v1",
            api_key="lm-studio"
        )
        # LM Studio usually ignores the model name and uses whatever is currently loaded
        self.model = "local-model"

    def _call_api(self, user_prompt: str, temperature: float = 0.7) -> str:
        """Make API call to LM Studio - override to handle potential connection errors gracefully"""
        try:
            # Many local models/templates do not support the 'system' role.
            # We prepend the system instruction to the user prompt to ensure compatibility.
            system_instruction = "You are a helpful songwriting assistant."
            full_prompt = f"{system_instruction}\n\n{user_prompt}"

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": full_prompt}
                ],
                temperature=temperature,
                max_tokens=800
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"LM Studio API error: {str(e)}. Make sure LM Studio is running and the server is started on port 1234.")

    def _call_api_stream(self, user_prompt: str, temperature: float = 0.8):
        """Streaming API call yielding chunks - no system role for LM Studio"""
        try:
            # Prepend system instruction
            system_instruction = "You are a helpful songwriting assistant."
            full_prompt = f"{system_instruction}\n\n{user_prompt}"

            stream = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": full_prompt}
                ],
                temperature=temperature,
                max_tokens=200,
                stream=True
            )
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            yield f"[ERROR: {str(e)}]"
