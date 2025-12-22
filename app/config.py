"""
VibeLyrics Configuration Module
Manages all configuration settings and environment variables
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set GOOGLE_API_KEY for Gemini SDK if GEMINI_API_KEY is set
if os.getenv("GEMINI_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY")

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
REFERENCES_DIR = DATA_DIR / "references"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
REFERENCES_DIR.mkdir(exist_ok=True)


class Config:
    """Application configuration"""
    
    # Flask
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-change-in-production")
    DEBUG = os.getenv("FLASK_DEBUG", "true").lower() == "true"
    
    # Database
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DATA_DIR / 'vibelyrics.db'}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # AI Providers
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    DEFAULT_AI_PROVIDER = os.getenv("DEFAULT_AI_PROVIDER", "openai")
    
    # Genius API
    GENIUS_ACCESS_TOKEN = os.getenv("GENIUS_ACCESS_TOKEN")
    
    # Paths
    USER_STYLE_PATH = DATA_DIR / "user_style.json"
    REFERENCES_PATH = REFERENCES_DIR
    
    # BPM Defaults
    DEFAULT_BPM = 140
    MIN_BPM = 60
    MAX_BPM = 200
    
    # Syllable targets per bar at different BPMs
    # Format: (min_bpm, max_bpm): (min_syllables, max_syllables)
    SYLLABLE_TARGETS = {
        (60, 80): (6, 10),    # Slow tempo
        (80, 100): (8, 12),   # Mid tempo
        (100, 130): (10, 14), # Fast tempo
        (130, 160): (12, 18), # Trap tempo
        (160, 200): (14, 22), # Double time
    }
    
    @classmethod
    def get_syllable_target(cls, bpm: int) -> tuple:
        """Get recommended syllable count range for given BPM"""
        for (min_bpm, max_bpm), syllables in cls.SYLLABLE_TARGETS.items():
            if min_bpm <= bpm < max_bpm:
                return syllables
        return (10, 14)  # Default fallback
