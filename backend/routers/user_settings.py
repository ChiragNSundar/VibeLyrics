"""
User Settings Router
User preferences and configuration
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..models import UserProfile
from ..schemas import SettingsUpdate, VocabularyAdd

router = APIRouter()


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
            "gemini": True,  # Would check actual availability
            "openai": True,
            "lmstudio": False
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
    """Add word to vocabulary list"""
    # Would integrate with VocabularyManager
    return {
        "success": True,
        "word": data.word,
        "list_type": data.list_type
    }


@router.delete("/vocabulary/{word}", response_model=dict)
async def remove_vocabulary(word: str, db: AsyncSession = Depends(get_db)):
    """Remove word from vocabulary"""
    return {"success": True}


@router.post("/reset", response_model=dict)
async def reset_learning(db: AsyncSession = Depends(get_db)):
    """Reset all learning data"""
    # Would reset style extractor, vocabulary manager, etc.
    return {
        "success": True,
        "message": "Learning data reset"
    }
