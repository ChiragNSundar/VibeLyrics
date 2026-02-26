"""
User Settings Router
User preferences and configuration
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json

from ..database import get_db
from ..models import UserProfile
from ..schemas import SettingsUpdate, VocabularyAdd
from ..services.ai_provider import GeminiProvider, LMStudioProvider

router = APIRouter()

# Check provider availability once at import
_gemini = GeminiProvider()
_lmstudio = LMStudioProvider()


async def get_or_create_profile(db: AsyncSession) -> UserProfile:
    """Get or create user profile"""
    result = await db.execute(select(UserProfile).limit(1))
    profile = result.scalar_one_or_none()

    if not profile:
        profile = UserProfile()
        db.add(profile)
        await db.flush()
        await db.refresh(profile)

    return profile


@router.get("/", response_model=dict)
async def get_settings(db: AsyncSession = Depends(get_db)):
    """Get all settings"""
    profile = await get_or_create_profile(db)

    return {
        "success": True,
        "profile": profile.to_dict(),
        "providers": {
            "gemini": _gemini.is_available(),
            "openai": bool(__import__('os').getenv("OPENAI_API_KEY")),
            "lmstudio": _lmstudio.is_available()
        }
    }


@router.put("/", response_model=dict)
async def update_settings(data: SettingsUpdate, db: AsyncSession = Depends(get_db)):
    """Update user settings"""
    profile = await get_or_create_profile(db)

    if data.preferred_provider is not None:
        profile.preferred_provider = data.preferred_provider
    if data.default_bpm is not None:
        profile.default_bpm = data.default_bpm
    if data.complexity_level is not None:
        profile.complexity_level = data.complexity_level
    if data.rhyme_style is not None:
        profile.rhyme_style = data.rhyme_style

    return {"success": True}


@router.post("/vocabulary", response_model=dict)
async def add_vocabulary(data: VocabularyAdd, db: AsyncSession = Depends(get_db)):
    """Add word to vocabulary list (favorite_words, banned_words, or slang_preferences)"""
    profile = await get_or_create_profile(db)

    word = data.word.lower().strip()
    if not word:
        return {"success": False, "error": "Word cannot be empty"}

    # Determine which list to update
    list_map = {
        "favorite": "favorite_words",
        "banned": "banned_words",
        "slang": "slang_preferences",
    }
    field_name = list_map.get(data.list_type, "favorite_words")

    # Load current list, add word, save back
    current_value = getattr(profile, field_name) or "[]"
    word_list = json.loads(current_value)

    if word not in word_list:
        word_list.append(word)
        setattr(profile, field_name, json.dumps(word_list))

    return {
        "success": True,
        "word": word,
        "list_type": data.list_type,
        "total": len(word_list)
    }


@router.delete("/vocabulary/{word}", response_model=dict)
async def remove_vocabulary(word: str, list_type: str = "favorite", db: AsyncSession = Depends(get_db)):
    """Remove word from vocabulary"""
    profile = await get_or_create_profile(db)

    word = word.lower().strip()
    list_map = {
        "favorite": "favorite_words",
        "banned": "banned_words",
        "slang": "slang_preferences",
    }
    field_name = list_map.get(list_type, "favorite_words")

    current_value = getattr(profile, field_name) or "[]"
    word_list = json.loads(current_value)

    if word in word_list:
        word_list.remove(word)
        setattr(profile, field_name, json.dumps(word_list))

    return {"success": True, "word": word, "removed": True}


@router.post("/reset", response_model=dict)
async def reset_learning(db: AsyncSession = Depends(get_db)):
    """Reset all learning data"""
    profile = await get_or_create_profile(db)
    profile.favorite_words = "[]"
    profile.banned_words = "[]"
    profile.slang_preferences = "[]"
    profile.total_sessions = 0
    profile.total_lines_written = 0
    profile.total_corrections = 0

    return {
        "success": True,
        "message": "Learning data reset"
    }
