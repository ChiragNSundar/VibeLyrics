"""
AI Router
AI suggestions, improvements, and Q&A
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from ..database import get_db
from ..models import LyricSession, LyricLine, UserProfile, JournalEntry
from ..schemas import SuggestRequest, ImproveRequest, AskRequest, ProviderSwitch
from ..services.ai_provider import get_ai_provider, set_provider

router = APIRouter()


@router.post("/ai/suggest", response_model=dict)
async def suggest_line(data: SuggestRequest, db: AsyncSession = Depends(get_db)):
    """Get AI suggestion for next line or improvement"""
    # Get session context
    result = await db.execute(
        select(LyricSession).where(LyricSession.id == data.session_id)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get existing lines
    lines_result = await db.execute(
        select(LyricLine)
        .where(LyricLine.session_id == data.session_id)
        .order_by(LyricLine.line_number)
    )
    lines = lines_result.scalars().all()
    
    # Fetch recent journal entries for inspiration
    journal_result = await db.execute(
        select(JournalEntry).order_by(desc(JournalEntry.created_at)).limit(5)
    )
    journal_entries = journal_result.scalars().all()

    # Fetch User Preferences
    profile_result = await db.execute(select(UserProfile).limit(1))
    profile = profile_result.scalar_one_or_none()
    
    # Build context
    context = {
        "session": session.to_dict(),
        "lines": [l.final_version or l.user_input for l in lines],
        "partial": data.partial_text,
        "action": data.action,
        "journal_entries": [e.to_dict() for e in journal_entries],
        "preferences": profile.to_dict() if profile else {}
    }
    
    # Get suggestion
    provider = get_ai_provider()
    suggestion = await provider.get_suggestion(context)
    
    return {
        "success": True,
        "suggestion": suggestion
    }


@router.post("/ai/improve", response_model=dict)
async def improve_line(data: ImproveRequest, db: AsyncSession = Depends(get_db)):
    """Improve an existing line"""
    result = await db.execute(
        select(LyricLine).where(LyricLine.id == data.line_id)
    )
    line = result.scalar_one_or_none()
    
    if not line:
        raise HTTPException(status_code=404, detail="Line not found")
    
    provider = get_ai_provider()
    improved = await provider.improve_line(
        line.final_version or line.user_input,
        data.improvement_type
    )
    
    return {
        "success": True,
        "original": line.final_version or line.user_input,
        "improved": improved
    }


@router.post("/ai/ask", response_model=dict)
async def ask_question(data: AskRequest, db: AsyncSession = Depends(get_db)):
    """Ask AI a question about lyrics/writing"""
    context = None
    
    if data.session_id:
        result = await db.execute(
            select(LyricSession).where(LyricSession.id == data.session_id)
        )
        session = result.scalar_one_or_none()
        if session:
            lines_result = await db.execute(
                select(LyricLine)
                .where(LyricLine.session_id == data.session_id)
                .order_by(LyricLine.line_number)
            )
            lines = lines_result.scalars().all()
            context = {
                "session": session.to_dict(),
                "lines": [l.final_version or l.user_input for l in lines]
            }
    
    provider = get_ai_provider()
    answer = await provider.answer_question(data.question, context)
    
    return {
        "success": True,
        "answer": answer
    }


@router.post("/ai/switch-provider", response_model=dict)
async def switch_provider(data: ProviderSwitch, db: AsyncSession = Depends(get_db)):
    """Switch AI provider"""
    set_provider(data.provider)
    
    # Update user profile
    result = await db.execute(select(UserProfile).limit(1))
    profile = result.scalar_one_or_none()
    
    if profile:
        profile.preferred_provider = data.provider
    else:
        profile = UserProfile(preferred_provider=data.provider)
        db.add(profile)
    
    return {
        "success": True,
        "provider": data.provider
    }


@router.get("/ai/provider", response_model=dict)
async def get_current_provider():
    """Get current AI provider"""
    provider = get_ai_provider()
    return {
        "success": True,
        "provider": provider.name,
        "available": provider.is_available()
    }
