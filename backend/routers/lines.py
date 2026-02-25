"""
Lines Router
Line CRUD and SSE streaming suggestions
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import asyncio
import json

from ..database import get_db
from ..models import LyricSession, LyricLine
from ..schemas import LineCreate, LineUpdate
from ..services.rhyme_detector import RhymeDetector, SyllableCounter
from ..services.ai_provider import get_ai_provider

router = APIRouter()
syllable_counter = SyllableCounter()


@router.post("/lines", response_model=dict)
async def add_line(data: LineCreate, db: AsyncSession = Depends(get_db)):
    """Add a new line to a session"""
    # Get session
    result = await db.execute(
        select(LyricSession).where(LyricSession.id == data.session_id)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get next line number
    count_result = await db.execute(
        select(func.count(LyricLine.id)).where(LyricLine.session_id == data.session_id)
    )
    line_count = count_result.scalar() or 0
    
    # Create line
    line = LyricLine(
        session_id=data.session_id,
        line_number=line_count + 1,
        user_input=data.content,
        final_version=data.content,
        section=data.section,
        syllable_count=syllable_counter.count(data.content),
        stress_pattern=syllable_counter.get_stress_pattern(data.content)
    )
    
    # Analyze rhyme
    rhyme_detector = RhymeDetector()
    words = data.content.split()
    if words:
        line.rhyme_end = rhyme_detector.get_rhyme_ending(words[-1])
    
    # Detect internal rhymes
    line.has_internal_rhyme = rhyme_detector.detect_internal_rhymes(data.content)
    
    db.add(line)
    await db.flush()
    await db.refresh(line)

    # Add highlighting for response
    # We need the context of other lines to do proper highlighting (e.g. alliteration/rhyme finding)
    # But for a single line response, we can at least return the self-contained properties 
    # OR we really should re-fetch the whole session context to be perfect, but that's expensive.
    # For now, let's at least populate the HTML property so frontend doesn't crash or show raw text.
    # Actually, the RhymeDetector needs the list of lines to find matches.
    # A simple localized highlight (e.g. just internal rhymes) is better than nothing, 
    # but to get 'rhyme-word' relative to OTHERS, we need others.
    # Let's do a quick fetch of recent lines? No, let's just use the `highlight_lyrics` on this single line
    # knowing it won't find inter-line rhymes yet, but will format it correctly.
    # Wait, the frontend might rely on this HTML.
    
    # Better approach: The frontend triggers a re-fetch of the session or the line update should include context.
    # Given the user wants "interactivity", let's try to do it right.
    
    highlighted = rhyme_detector.highlight_lyrics([line.final_version or line.user_input])
    # Note: this won't show rhymes with *other* lines, but ensures the field exists.
    line.highlighted_html = highlighted[0] if highlighted else line.user_input
    
    return {
        "success": True,
        "line": line.to_dict(include_highlights=True)
    }


@router.put("/lines/{line_id}", response_model=dict)
async def update_line(line_id: int, data: LineUpdate, db: AsyncSession = Depends(get_db)):
    """Update an existing line"""
    result = await db.execute(
        select(LyricLine).where(LyricLine.id == line_id)
    )
    line = result.scalar_one_or_none()
    
    if not line:
        raise HTTPException(status_code=404, detail="Line not found")
    
    line.user_input = data.content
    line.final_version = data.content
    line.syllable_count = syllable_counter.count(data.content)
    line.stress_pattern = syllable_counter.get_stress_pattern(data.content)
    
    # Update rhyme
    rhyme_detector = RhymeDetector()
    words = data.content.split()
    if words:
        line.rhyme_end = rhyme_detector.get_rhyme_ending(words[-1])
    
    # Detect internal rhymes
    line.has_internal_rhyme = rhyme_detector.detect_internal_rhymes(data.content)
        
    highlighted = rhyme_detector.highlight_lyrics([line.final_version or line.user_input])
    line.highlighted_html = highlighted[0] if highlighted else line.user_input
    
    return {
        "success": True,
        "line": line.to_dict(include_highlights=True)
    }


@router.delete("/lines/{line_id}", response_model=dict)
async def delete_line(line_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a line"""
    result = await db.execute(
        select(LyricLine).where(LyricLine.id == line_id)
    )
    line = result.scalar_one_or_none()
    
    if not line:
        raise HTTPException(status_code=404, detail="Line not found")
    
    await db.delete(line)
    
    return {"success": True}


@router.get("/lines/stream")
async def stream_suggestion(
    session_id: int,
    partial: str = "",
    request: Request = None
):
    """
    Stream AI suggestions using Server-Sent Events (SSE)
    FastAPI native streaming support
    """
    async def generate():
        try:
            provider = get_ai_provider()
            
            async for chunk in provider.stream_suggestion(session_id, partial):
                if await request.is_disconnected():
                    break
                yield f"data: {chunk}\n\n"
            
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            yield f"data: [ERROR] {str(e)}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
