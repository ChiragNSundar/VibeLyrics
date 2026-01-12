"""
Stats Router
Writing statistics and achievements
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from collections import Counter

from ..database import get_db
from ..models import LyricSession, LyricLine

router = APIRouter()


@router.get("/", response_model=dict)
async def get_overview(db: AsyncSession = Depends(get_db)):
    """Get stats overview"""
    # Total counts
    sessions_result = await db.execute(select(func.count(LyricSession.id)))
    total_sessions = sessions_result.scalar() or 0
    
    lines_result = await db.execute(select(func.count(LyricLine.id)))
    total_lines = lines_result.scalar() or 0
    
    # Get all lines for word count
    all_lines_result = await db.execute(
        select(LyricLine.final_version, LyricLine.user_input)
    )
    all_lines = all_lines_result.all()
    
    total_words = sum(
        len((line[0] or line[1] or "").split())
        for line in all_lines
    )
    
    # Unique vocabulary
    all_text = " ".join(
        (line[0] or line[1] or "").lower()
        for line in all_lines
    )
    words = [w.strip('.,!?;:\'"()-[]') for w in all_text.split() if len(w) > 2]
    unique_words = len(set(words))
    
    # Average BPM
    bpm_result = await db.execute(select(func.avg(LyricSession.bpm)))
    avg_bpm = bpm_result.scalar() or 140
    
    # Sessions this week
    week_ago = datetime.utcnow() - timedelta(days=7)
    week_result = await db.execute(
        select(func.count(LyricSession.id)).where(LyricSession.created_at >= week_ago)
    )
    sessions_this_week = week_result.scalar() or 0
    
    # Lines today
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_result = await db.execute(
        select(func.count(LyricLine.id)).where(LyricLine.created_at >= today_start)
    )
    lines_today = today_result.scalar() or 0
    
    return {
        "success": True,
        "stats": {
            "total_sessions": total_sessions,
            "total_lines": total_lines,
            "total_words": total_words,
            "unique_vocabulary": unique_words,
            "avg_bpm": round(avg_bpm),
            "sessions_this_week": sessions_this_week,
            "lines_today": lines_today
        }
    }


@router.get("/history", response_model=dict)
async def get_history(db: AsyncSession = Depends(get_db)):
    """Get time-series data for charts"""
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    result = await db.execute(
        select(LyricLine.created_at).where(LyricLine.created_at >= thirty_days_ago)
    )
    lines = result.scalars().all()
    
    lines_by_day = Counter()
    for created_at in lines:
        if created_at:
            date_str = created_at.strftime('%Y-%m-%d')
            lines_by_day[date_str] += 1
    
    daily_data = []
    for i in range(30):
        date = (datetime.utcnow() - timedelta(days=29-i)).strftime('%Y-%m-%d')
        daily_data.append({
            "date": date,
            "lines": lines_by_day.get(date, 0)
        })
    
    return {
        "success": True,
        "daily_lines": daily_data
    }


@router.get("/achievements", response_model=dict)
async def get_achievements(db: AsyncSession = Depends(get_db)):
    """Get user achievements"""
    lines_result = await db.execute(select(func.count(LyricLine.id)))
    total_lines = lines_result.scalar() or 0
    
    sessions_result = await db.execute(select(func.count(LyricSession.id)))
    total_sessions = sessions_result.scalar() or 0
    
    achievements = []
    
    if total_lines >= 10:
        achievements.append({"name": "First Steps", "icon": "🌱", "desc": "Write 10 lines"})
    if total_lines >= 50:
        achievements.append({"name": "Getting Warmed Up", "icon": "🔥", "desc": "Write 50 lines"})
    if total_lines >= 100:
        achievements.append({"name": "Century", "icon": "💯", "desc": "Write 100 lines"})
    if total_lines >= 500:
        achievements.append({"name": "Prolific", "icon": "📚", "desc": "Write 500 lines"})
    if total_lines >= 1000:
        achievements.append({"name": "Legendary", "icon": "👑", "desc": "Write 1000 lines"})
    
    if total_sessions >= 5:
        achievements.append({"name": "Session Master", "icon": "🎯", "desc": "Complete 5 sessions"})
    if total_sessions >= 20:
        achievements.append({"name": "Album Ready", "icon": "💿", "desc": "Complete 20 sessions"})
    
    return {
        "success": True,
        "achievements": achievements,
        "total_lines": total_lines,
        "total_sessions": total_sessions
    }
