"""
Sessions Router
CRUD operations for lyric sessions
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List
import os
import shutil
import re

from ..database import get_db
from ..models import LyricSession, LyricLine
from ..schemas import SessionCreate, SessionUpdate, SessionResponse, SuccessResponse
from ..services.rhyme_detector import RhymeDetector

router = APIRouter()

# ── Singleton ───────────────────────────────────────────────────────
_rhyme_detector = RhymeDetector()

# ── Upload constraints ──────────────────────────────────────────────
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50 MB
ALLOWED_AUDIO_TYPES = {
    "audio/mpeg", "audio/mp3", "audio/wav", "audio/x-wav",
    "audio/ogg", "audio/flac", "audio/aac", "audio/mp4",
    "audio/webm",
}
SAFE_FILENAME_RE = re.compile(r'[^a-zA-Z0-9_\-.]')


@router.get("/sessions", response_model=dict)
async def list_sessions(db: AsyncSession = Depends(get_db)):
    """Get all sessions"""
    result = await db.execute(
        select(LyricSession)
        .options(selectinload(LyricSession.lines))
        .order_by(LyricSession.updated_at.desc())
    )
    sessions = result.scalars().all()

    return {
        "success": True,
        "sessions": [s.to_dict() for s in sessions]
    }


@router.post("/sessions", response_model=dict)
async def create_session(data: SessionCreate, db: AsyncSession = Depends(get_db)):
    """Create a new session"""
    session = LyricSession(
        title=data.title,
        bpm=data.bpm,
        mood=data.mood,
        theme=data.theme
    )
    db.add(session)
    await db.flush()
    await db.refresh(session)

    return {
        "success": True,
        "session": session.to_dict()
    }


@router.get("/sessions/{session_id}", response_model=dict)
async def get_session(session_id: int, db: AsyncSession = Depends(get_db)):
    """Get a session with all its lines"""
    result = await db.execute(
        select(LyricSession).where(LyricSession.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get lines
    lines_result = await db.execute(
        select(LyricLine)
        .where(LyricLine.session_id == session_id)
        .order_by(LyricLine.line_number)
    )
    lines = lines_result.scalars().all()

    # Backfill has_internal_rhyme for lines that were created before v2.4.0
    for line in lines:
        text = line.final_version or line.user_input
        if text and not line.has_internal_rhyme:
            detected = _rhyme_detector.detect_internal_rhymes(text)
            if detected:
                line.has_internal_rhyme = True

    # Add highlighting
    text_lines = [l.final_version or l.user_input for l in lines]

    session_data = session.to_dict()

    if text_lines:
        highlighted = _rhyme_detector.highlight_lyrics(text_lines)
        heatmap = _rhyme_detector.get_density_heatmap(text_lines)
        rhyme_scheme = _rhyme_detector.get_rhyme_scheme_string(text_lines)

        # Add rhyme scheme to session response
        session_data["rhyme_scheme"] = rhyme_scheme

        for line, html, hm in zip(lines, highlighted, heatmap):
            line.highlighted_html = html
            line.heatmap_class = f"heatmap-{hm['color']}"

    return {
        "success": True,
        "session": session_data,
        "lines": [l.to_dict(include_highlights=True) for l in lines]
    }


@router.put("/sessions/{session_id}", response_model=dict)
async def update_session(
    session_id: int,
    data: SessionUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update session metadata"""
    result = await db.execute(
        select(LyricSession).where(LyricSession.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if data.title is not None:
        session.title = data.title
    if data.bpm is not None:
        session.bpm = data.bpm
    if data.mood is not None:
        session.mood = data.mood
    if data.theme is not None:
        session.theme = data.theme

    return {"success": True}


@router.delete("/sessions/{session_id}", response_model=dict)
async def delete_session(session_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a session"""
    result = await db.execute(
        select(LyricSession).where(LyricSession.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    await db.delete(session)

    return {"success": True}


@router.post("/sessions/{session_id}/heartbeat", response_model=dict)
async def session_heartbeat(session_id: int, db: AsyncSession = Depends(get_db)):
    """Record a writing heartbeat — client pings every 30s to track writing time."""
    from datetime import timezone as tz
    result = await db.execute(
        select(LyricSession).where(LyricSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    now = datetime.now(tz.utc)
    # If last heartbeat was within 60 seconds, count the interval as writing time
    if session.last_active_at:
        delta = (now - session.last_active_at).total_seconds()
        if delta < 60:
            session.total_writing_seconds += int(delta)

    session.last_active_at = now
    return {
        "success": True,
        "total_writing_seconds": session.total_writing_seconds
    }


@router.post("/sessions/{session_id}/upload-audio", response_model=dict)
async def upload_audio(
    session_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """Upload audio file for beat player (max 50 MB, audio types only)"""
    result = await db.execute(
        select(LyricSession).where(LyricSession.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Validate file type
    if file.content_type and file.content_type not in ALLOWED_AUDIO_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Allowed: mp3, wav, ogg, flac, aac, mp4, webm"
        )

    # Validate file size (read in chunks)
    upload_dir = "uploads/audio"
    os.makedirs(upload_dir, exist_ok=True)

    # Sanitize filename to prevent path traversal
    safe_name = SAFE_FILENAME_RE.sub('_', file.filename or "audio.mp3")
    filename = f"session_{session_id}_{safe_name}"
    filepath = os.path.join(upload_dir, filename)

    total_size = 0
    with open(filepath, "wb") as buffer:
        while True:
            chunk = await file.read(1024 * 1024)  # 1 MB chunks
            if not chunk:
                break
            total_size += len(chunk)
            if total_size > MAX_UPLOAD_SIZE:
                # Clean up partial file
                buffer.close()
                os.remove(filepath)
                raise HTTPException(
                    status_code=413,
                    detail=f"File too large. Maximum size is {MAX_UPLOAD_SIZE // (1024*1024)} MB"
                )
            buffer.write(chunk)

    session.audio_path = f"/uploads/audio/{filename}"

    return {
        "success": True,
        "audio_path": session.audio_path,
        "message": "Audio uploaded successfully"
    }
