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

from ..database import get_db
from ..models import LyricSession, LyricLine
from ..schemas import SessionCreate, SessionUpdate, SessionResponse, SuccessResponse
from ..services.rhyme_detector import RhymeDetector

router = APIRouter()


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
    
    # Add highlighting
    rhyme_detector = RhymeDetector()
    text_lines = [l.final_version or l.user_input for l in lines]
    
    if text_lines:
        highlighted = rhyme_detector.highlight_lyrics(text_lines)
        heatmap = rhyme_detector.get_density_heatmap(text_lines)
        
        for line, html, hm in zip(lines, highlighted, heatmap):
            line.highlighted_html = html
            line.heatmap_class = f"heatmap-{hm['color']}"
    
    return {
        "success": True,
        "session": session.to_dict(),
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


@router.post("/sessions/{session_id}/upload-audio", response_model=dict)
async def upload_audio(
    session_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """Upload audio file for beat player"""
    result = await db.execute(
        select(LyricSession).where(LyricSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Save file
    upload_dir = "uploads/audio"
    os.makedirs(upload_dir, exist_ok=True)
    
    filename = f"session_{session_id}_{file.filename}"
    filepath = os.path.join(upload_dir, filename)
    
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    session.audio_path = f"/uploads/audio/{filename}"
    
    return {
        "success": True,
        "audio_path": session.audio_path,
        "message": "Audio uploaded successfully"
    }
