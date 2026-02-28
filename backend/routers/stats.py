"""
Stats Router
Writing statistics and achievements
"""
import json
import os
from pathlib import Path
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from collections import Counter

from ..database import get_db
from ..models import LyricSession, LyricLine

router = APIRouter()

STREAKS_FILE = Path("data/streaks.json")

def load_streaks():
    if not STREAKS_FILE.exists():
        return {"current_streak": 0, "longest_streak": 0, "last_write_date": None, "history": []}
    try:
        with open(STREAKS_FILE, "r") as f:
            return json.load(f)
    except:
        return {"current_streak": 0, "longest_streak": 0, "last_write_date": None, "history": []}

def save_streaks(data):
    STREAKS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STREAKS_FILE, "w") as f:
        json.dump(data, f)


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


@router.get("/vocabulary-growth", response_model=dict)
async def get_vocabulary_growth(db: AsyncSession = Depends(get_db)):
    """Get unique vocabulary growth over time"""
    # Fetch all lines ordered by creation date
    result = await db.execute(
        select(LyricLine.created_at, LyricLine.final_version, LyricLine.user_input)
        .order_by(LyricLine.created_at)
    )
    lines = result.all()
    
    daily_vocab = {} # date -> set of unique words up to that date
    cumulative_words = set()
    
    for created_at, final_ver, user_input in lines:
        if not created_at:
            continue
            
        date_str = created_at.strftime('%Y-%m-%d')
        text = (final_ver or user_input or "").lower()
        words = [w.strip('.,!?;:\'"()-[]') for w in text.split() if len(w) > 2]
        
        cumulative_words.update(words)
        daily_vocab[date_str] = len(cumulative_words)
        
    # Format for chart: sort by date
    growth_data = [{"date": d, "unique_words": count} for d, count in sorted(daily_vocab.items())]
    
    return {
        "success": True,
        "growth": growth_data
    }


@router.get("/rhyme-calendar", response_model=dict)
async def get_rhyme_calendar(db: AsyncSession = Depends(get_db)):
    """Get dominant rhyme scheme per day for the heatmap"""
    result = await db.execute(
        select(LyricSession.created_at, LyricSession.rhyme_scheme, LyricSession.id, LyricSession.title)
        .where(LyricSession.rhyme_scheme.is_not(None))
        .order_by(LyricSession.created_at)
    )
    sessions = result.all()
    
    daily_schemes = {}
    for created_at, scheme, s_id, title in sessions:
        if not created_at or not scheme:
            continue
            
        date_str = created_at.strftime('%Y-%m-%d')
        # If multiple sessions in one day, just keep the latest (simplest approach)
        daily_schemes[date_str] = {
            "date": date_str,
            "scheme": scheme,
            "session_id": s_id,
            "session_title": title
        }
        
    calendar_data = list(daily_schemes.values())
    
    return {
        "success": True,
        "calendar": calendar_data
    }


@router.get("/streak", response_model=dict)
async def get_streak():
    """Get current writing streak"""
    data = load_streaks()
    
    # Check if streak was broken (last write was before yesterday)
    today = datetime.utcnow().strftime('%Y-%m-%d')
    yesterday_date = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    last_write = data.get("last_write_date")
    if last_write and last_write != today and last_write != yesterday_date:
        data["current_streak"] = 0
        save_streaks(data)
        
    return {
        "success": True,
        "current_streak": data.get("current_streak", 0),
        "longest_streak": data.get("longest_streak", 0),
        "last_write_date": data.get("last_write_date"),
        "history": data.get("history", [])
    }


@router.post("/streak/check-in", response_model=dict)
async def process_streak_check_in():
    """Register a writing check-in to increment streak if applicable"""
    data = load_streaks()
    today = datetime.utcnow().strftime('%Y-%m-%d')
    
    # Already checked in today?
    if data.get("last_write_date") == today:
        return {
            "success": True,
            "current_streak": data.get("current_streak", 0),
            "longest_streak": data.get("longest_streak", 0),
            "last_write_date": data.get("last_write_date"),
            "history": data.get("history", [])
        }
        
    # Was last check-in exactly yesterday?
    yesterday_date = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d')
    if data.get("last_write_date") == yesterday_date:
        data["current_streak"] = data.get("current_streak", 0) + 1
    else:
        data["current_streak"] = 1 # Start fresh
        
    if data["current_streak"] > data.get("longest_streak", 0):
        data["longest_streak"] = data["current_streak"]
        
    data["last_write_date"] = today
    if "history" not in data:
        data["history"] = []
    
    if today not in data["history"]:
        data["history"].append(today)
        
    save_streaks(data)
    
    return {
        "success": True,
        "current_streak": data["current_streak"],
        "longest_streak": data["longest_streak"],
        "last_write_date": data["last_write_date"],
        "history": data["history"]
    }

@router.get("/style", response_model=dict)
async def get_style_analysis(db: AsyncSession = Depends(get_db)):
    """
    Get comprehensive style analysis for the StyleDashboard.
    Returns vocabulary density, rhyme metrics, complexity scores, and artist comparisons.
    """
    # Get all lines for analysis
    lines_result = await db.execute(
        select(LyricLine.user_input, LyricLine.final_version, LyricLine.syllable_count,
               LyricLine.has_internal_rhyme, LyricLine.complexity_score, LyricLine.stress_pattern)
    )
    lines = lines_result.all()
    
    if not lines:
        return {
            "success": True,
            "style": {
                "dimensions": {"vocabulary": 0, "rhyme_density": 0, "flow": 0, "complexity": 0, "wordplay": 0},
                "benchmarks": [],
                "progress": []
            }
        }
    
    # Calculate metrics
    all_text = " ".join((l[1] or l[0] or "").lower() for l in lines)
    words = [w.strip('.,!?;:\'"()-[]') for w in all_text.split() if len(w) > 2]
    total_words = len(words)
    unique_words = len(set(words))
    
    # Vocabulary density (unique/total ratio)
    vocabulary_density = (unique_words / max(total_words, 1)) * 100
    
    # Rhyme density (% of lines with internal rhyme)
    lines_with_rhyme = sum(1 for l in lines if l[3])  # has_internal_rhyme
    rhyme_density = (lines_with_rhyme / max(len(lines), 1)) * 100
    
    # Average complexity
    complexities = [l[4] for l in lines if l[4] is not None]
    avg_complexity = sum(complexities) / max(len(complexities), 1)
    
    # Flow score (syllable consistency)
    syllables = [l[2] for l in lines if l[2] is not None]
    if syllables:
        avg_syllables = sum(syllables) / len(syllables)
        syllable_variance = sum((s - avg_syllables) ** 2 for s in syllables) / len(syllables)
        flow_score = max(0, 100 - syllable_variance * 2)  # Lower variance = higher flow
    else:
        flow_score = 50
    
    # Wordplay estimate (words with 3+ syllables)
    complex_words = sum(1 for w in words if sum(1 for c in w if c in 'aeiou') >= 3)
    wordplay_score = (complex_words / max(total_words, 1)) * 100 * 2  # Scale up
    
    # Normalize to 0-100 scale
    dimensions = {
        "vocabulary": min(100, vocabulary_density * 2),
        "rhyme_density": min(100, rhyme_density),
        "flow": min(100, flow_score),
        "complexity": min(100, avg_complexity * 10),
        "wordplay": min(100, wordplay_score)
    }
    
    # Artist benchmarks for comparison (simulated based on known styles)
    benchmarks = [
        {"name": "Eminem", "vocabulary": 85, "rhyme_density": 95, "flow": 80, "complexity": 90, "wordplay": 95},
        {"name": "Kendrick", "vocabulary": 90, "rhyme_density": 75, "flow": 85, "complexity": 95, "wordplay": 80},
        {"name": "Drake", "vocabulary": 60, "rhyme_density": 70, "flow": 90, "complexity": 50, "wordplay": 40},
        {"name": "J. Cole", "vocabulary": 80, "rhyme_density": 65, "flow": 85, "complexity": 85, "wordplay": 70},
        {"name": "You", "vocabulary": dimensions["vocabulary"], "rhyme_density": dimensions["rhyme_density"],
         "flow": dimensions["flow"], "complexity": dimensions["complexity"], "wordplay": dimensions["wordplay"]}
    ]
    
    return {
        "success": True,
        "style": {
            "dimensions": dimensions,
            "benchmarks": benchmarks,
            "total_lines": len(lines),
            "total_words": total_words,
            "unique_words": unique_words
        }
    }

