"""
Stats & Analytics Router
- Writing streaks
- Vocabulary growth over time
- Rhyme scheme calendar
- Flow template listings
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Dict, Any
from datetime import datetime, timezone, timedelta
from collections import Counter
import json
import os

from ..database import get_db
from ..models import LyricSession, LyricLine
from ..services.flow_templates import list_flow_templates
from ..services.rhyme_detector import RhymeDetector

router = APIRouter()
_rhyme_detector = RhymeDetector()

STREAK_FILE = "data/streaks.json"


def _load_streaks() -> dict:
    if os.path.exists(STREAK_FILE):
        try:
            with open(STREAK_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {"current_streak": 0, "longest_streak": 0, "last_write_date": None, "history": []}


def _save_streaks(data: dict):
    os.makedirs(os.path.dirname(STREAK_FILE), exist_ok=True)
    with open(STREAK_FILE, 'w') as f:
        json.dump(data, f)


@router.get("/stats/streak")
async def get_streak():
    """Get the current writing streak data."""
    data = _load_streaks()
    return {"success": True, **data}


@router.post("/stats/streak/check-in")
async def streak_check_in():
    """Record a writing check-in for today."""
    data = _load_streaks()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    if data["last_write_date"] == today:
        return {"success": True, "message": "Already checked in today", **data}

    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")

    if data["last_write_date"] == yesterday:
        data["current_streak"] += 1
    else:
        data["current_streak"] = 1

    data["longest_streak"] = max(data["longest_streak"], data["current_streak"])
    data["last_write_date"] = today

    if today not in data["history"]:
        data["history"].append(today)
    # Keep last 365 days
    data["history"] = data["history"][-365:]

    _save_streaks(data)
    return {"success": True, **data}


@router.get("/stats/vocabulary-growth")
async def get_vocabulary_growth(db: AsyncSession = Depends(get_db)):
    """Get cumulative unique word count growth over time."""
    result = await db.execute(
        select(LyricLine.created_at, LyricLine.user_input)
        .order_by(LyricLine.created_at)
    )
    rows = result.all()

    all_words = set()
    growth = []
    current_date = None

    for created_at, text in rows:
        if not text:
            continue
        day = created_at.strftime("%Y-%m-%d") if created_at else "unknown"
        words = set(text.lower().split())
        all_words.update(words)

        if day != current_date:
            current_date = day
            growth.append({"date": day, "unique_words": len(all_words)})
        else:
            # Update the last entry
            growth[-1]["unique_words"] = len(all_words)

    return {"success": True, "growth": growth}


@router.get("/stats/rhyme-calendar")
async def get_rhyme_calendar(db: AsyncSession = Depends(get_db)):
    """Get rhyme scheme usage per day for a calendar heatmap."""
    result = await db.execute(
        select(LyricSession)
        .order_by(LyricSession.created_at)
    )
    sessions = result.scalars().all()

    calendar = []
    for session in sessions:
        day = session.created_at.strftime("%Y-%m-%d") if session.created_at else "unknown"

        # Get lines for this session
        lines_result = await db.execute(
            select(LyricLine)
            .where(LyricLine.session_id == session.id)
            .order_by(LyricLine.line_number)
        )
        lines = lines_result.scalars().all()
        text_lines = [l.final_version or l.user_input for l in lines if l.user_input]

        if text_lines:
            scheme = _rhyme_detector.get_rhyme_scheme_string(text_lines)
        else:
            scheme = "None"

        calendar.append({
            "date": day,
            "scheme": scheme,
            "session_id": session.id,
            "session_title": session.title,
        })

    return {"success": True, "calendar": calendar}


@router.get("/flow-templates")
async def get_flow_templates():
    """Get all available flow pattern templates."""
    return {"success": True, "templates": list_flow_templates()}
