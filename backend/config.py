"""
Configuration settings using Pydantic
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    """Application settings loaded from environment"""
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./vibelyrics.db"
    
    # AI Providers
    gemini_api_key: str = ""
    openai_api_key: str = ""
    genius_access_token: str = ""
    
    # App settings
    debug: bool = False
    default_provider: str = "gemini"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()
