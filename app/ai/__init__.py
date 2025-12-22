"""
AI package initialization
"""
from .base_provider import BaseAIProvider
from .openai_provider import OpenAIProvider
from .gemini_provider import GeminiProvider
from .perplexity_provider import PerplexityProvider
from .prompts import LyricPrompts
from .context_builder import ContextBuilder

__all__ = [
    'BaseAIProvider',
    'OpenAIProvider', 
    'GeminiProvider',
    'PerplexityProvider',
    'LyricPrompts',
    'ContextBuilder',
    'get_provider',
    'get_provider_with_fallback'
]


def get_provider(provider_name: str = None):
    """Factory function to get the appropriate AI provider"""
    from app.config import Config
    import os
    
    provider_name = provider_name or Config.DEFAULT_AI_PROVIDER
    
    if provider_name == "openai":
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY not set")
        return OpenAIProvider()
    elif provider_name == "gemini":
        if not os.getenv("GEMINI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
            raise ValueError("GEMINI_API_KEY not set")
        return GeminiProvider()
    elif provider_name == "perplexity":
        if not os.getenv("PERPLEXITY_API_KEY"):
            raise ValueError("PERPLEXITY_API_KEY not set")
        return PerplexityProvider()
    else:
        raise ValueError(f"Unknown provider: {provider_name}")


def get_provider_with_fallback(preferred: str = None):
    """Get AI provider with automatic fallback if preferred is unavailable"""
    import os
    from app.config import Config
    
    # Order of preference for fallback
    providers = ['gemini', 'openai', 'perplexity']
    
    # Try preferred first
    if preferred:
        providers.remove(preferred) if preferred in providers else None
        providers.insert(0, preferred)
    
    for provider_name in providers:
        try:
            return get_provider(provider_name)
        except ValueError:
            continue
    
    raise ValueError("No AI provider available. Please configure at least one API key in .env")

