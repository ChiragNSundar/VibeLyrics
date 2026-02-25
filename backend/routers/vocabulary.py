"""
Vocabulary Router
- Vocabulary Age / Reading Level analysis
- Per-session vocabulary metrics
- Vocabulary evolution tracking
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..models import LyricSession, LyricLine
from ..services.vocabulary_analyzer import VocabularyAnalyzer

router = APIRouter()
vocab_analyzer = VocabularyAnalyzer()


@router.get("/age", response_model=dict)
async def get_vocabulary_age(db: AsyncSession = Depends(get_db)):
    """
    Get vocabulary evolution timeline across all sessions.
    Returns time-series data for charting Flesch-Kincaid grade evolution.
    """
    # Get all sessions with their lines
    sessions_result = await db.execute(
        select(LyricSession).order_by(LyricSession.created_at)
    )
    sessions = sessions_result.scalars().all()
    
    if not sessions:
        return {
            "success": True,
            "evolution": [],
            "summary": vocab_analyzer.get_summary([])
        }
    
    sessions_data = []
    for session in sessions:
        lines_result = await db.execute(
            select(LyricLine)
            .where(LyricLine.session_id == session.id)
            .order_by(LyricLine.line_number)
        )
        lines = lines_result.scalars().all()
        text_lines = [l.final_version or l.user_input for l in lines]
        
        if text_lines:
            sessions_data.append({
                "session_id": session.id,
                "lines": text_lines,
                "created_at": session.created_at.isoformat() if session.created_at else ""
            })
    
    evolution = vocab_analyzer.get_vocabulary_evolution(sessions_data)
    summary = vocab_analyzer.get_summary(evolution)
    
    return {
        "success": True,
        "evolution": evolution,
        "summary": summary
    }


@router.get("/session/{session_id}", response_model=dict)
async def get_session_vocabulary(session_id: int, db: AsyncSession = Depends(get_db)):
    """Get detailed vocabulary metrics for a single session"""
    # Get session
    session_result = await db.execute(
        select(LyricSession).where(LyricSession.id == session_id)
    )
    session = session_result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get lines
    lines_result = await db.execute(
        select(LyricLine)
        .where(LyricLine.session_id == session_id)
        .order_by(LyricLine.line_number)
    )
    lines = lines_result.scalars().all()
    text_lines = [l.final_version or l.user_input for l in lines]
    
    if not text_lines:
        raise HTTPException(status_code=404, detail="Session has no lines")
    
    created_at = session.created_at.isoformat() if session.created_at else None
    metrics = vocab_analyzer.analyze_session(text_lines, created_at)
    
    return {
        "success": True,
        "session_id": session_id,
        "session_title": session.title,
        **metrics
    }
