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
import re

from ..database import get_db
from ..models import LyricSession, LyricLine
from ..schemas import LineCreate, LineUpdate
from ..services.rhyme_detector import RhymeDetector, SyllableCounter
from ..services.ai_provider import get_ai_provider

router = APIRouter()

# ── Singletons (avoid re-instantiation per request) ────────────────
_syllable_counter = SyllableCounter()
_rhyme_detector = RhymeDetector()


def _compute_complexity(content: str) -> float:
    """
    Compute a 0-100 complexity score for a single line.
    Factors: vocabulary diversity, multi-syllable words, word length.
    """
    words = content.lower().split()
    if not words:
        return 0.0

    clean_words = [re.sub(r'[^a-z]', '', w) for w in words]
    clean_words = [w for w in clean_words if w]

    if not clean_words:
        return 0.0

    unique = set(clean_words)
    vocab_diversity = len(unique) / len(clean_words)

    # Count multi-syllable words (3+ syllables)
    multi_count = sum(1 for w in clean_words if _syllable_counter.count(w) >= 3)
    multi_ratio = multi_count / len(clean_words)

    # Average word length bonus
    avg_len = sum(len(w) for w in clean_words) / len(clean_words)
    length_score = min(1.0, avg_len / 8.0)  # normalize: 8+ chars = max

    score = (vocab_diversity * 40) + (multi_ratio * 35) + (length_score * 25)
    return round(min(100.0, score), 1)


@router.post("/lines", response_model=dict)
async def add_line(data: LineCreate, db: AsyncSession = Depends(get_db)):
    """Add a new line to a session"""
    # Input validation
    content = data.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="Line content cannot be empty")

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

    # Create line with all analysis
    line = LyricLine(
        session_id=data.session_id,
        line_number=line_count + 1,
        user_input=content,
        final_version=content,
        section=data.section,
        syllable_count=_syllable_counter.count(content),
        stress_pattern=_syllable_counter.get_stress_pattern(content),
        has_internal_rhyme=_rhyme_detector.detect_internal_rhymes(content),
        complexity_score=_compute_complexity(content),
    )

    # End-rhyme analysis
    words = content.split()
    if words:
        line.rhyme_end = _rhyme_detector.get_rhyme_ending(words[-1])

    db.add(line)
    await db.flush()
    await db.refresh(line)

    # Highlight with context of ALL session lines for proper cross-line detection
    all_lines_result = await db.execute(
        select(LyricLine)
        .where(LyricLine.session_id == data.session_id)
        .order_by(LyricLine.line_number)
    )
    all_lines = all_lines_result.scalars().all()
    text_lines = [l.final_version or l.user_input for l in all_lines]

    highlighted = _rhyme_detector.highlight_lyrics(text_lines)

    # Return the full set of highlighted lines so the frontend can update all of them
    for db_line, html in zip(all_lines, highlighted):
        db_line.highlighted_html = html

    return {
        "success": True,
        "line": line.to_dict(include_highlights=True),
        "all_lines": [l.to_dict(include_highlights=True) for l in all_lines]
    }


@router.put("/lines/{line_id}", response_model=dict)
async def update_line(line_id: int, data: LineUpdate, db: AsyncSession = Depends(get_db)):
    """Update an existing line"""
    content = data.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="Line content cannot be empty")

    result = await db.execute(
        select(LyricLine).where(LyricLine.id == line_id)
    )
    line = result.scalar_one_or_none()

    if not line:
        raise HTTPException(status_code=404, detail="Line not found")

    line.user_input = content
    line.final_version = content
    line.syllable_count = _syllable_counter.count(content)
    line.stress_pattern = _syllable_counter.get_stress_pattern(content)
    line.has_internal_rhyme = _rhyme_detector.detect_internal_rhymes(content)
    line.complexity_score = _compute_complexity(content)

    words = content.split()
    if words:
        line.rhyme_end = _rhyme_detector.get_rhyme_ending(words[-1])

    # Re-highlight all lines in the session for cross-line context
    all_lines_result = await db.execute(
        select(LyricLine)
        .where(LyricLine.session_id == line.session_id)
        .order_by(LyricLine.line_number)
    )
    all_lines = all_lines_result.scalars().all()
    text_lines = [l.final_version or l.user_input for l in all_lines]
    highlighted = _rhyme_detector.highlight_lyrics(text_lines)

    for db_line, html in zip(all_lines, highlighted):
        db_line.highlighted_html = html

    return {
        "success": True,
        "line": line.to_dict(include_highlights=True),
        "all_lines": [l.to_dict(include_highlights=True) for l in all_lines]
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


@router.post("/lines/reorder", response_model=dict)
async def reorder_lines(data: dict, db: AsyncSession = Depends(get_db)):
    """
    Reorder lines within a session.
    Expects: { "session_id": int, "order": [{ "id": int, "line_number": int }, ...] }
    """
    session_id = data.get("session_id")
    order = data.get("order", [])

    if not session_id or not order:
        raise HTTPException(status_code=400, detail="session_id and order are required")

    # Verify session exists
    session_result = await db.execute(
        select(LyricSession).where(LyricSession.id == session_id)
    )
    if not session_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Session not found")

    # Update line numbers
    for item in order:
        line_result = await db.execute(
            select(LyricLine).where(
                LyricLine.id == item["id"],
                LyricLine.session_id == session_id
            )
        )
        line = line_result.scalar_one_or_none()
        if line:
            line.line_number = item["line_number"]

    # Re-highlight after reorder
    all_lines_result = await db.execute(
        select(LyricLine)
        .where(LyricLine.session_id == session_id)
        .order_by(LyricLine.line_number)
    )
    all_lines = all_lines_result.scalars().all()
    text_lines = [l.final_version or l.user_input for l in all_lines]
    highlighted = _rhyme_detector.highlight_lyrics(text_lines)

    for db_line, html in zip(all_lines, highlighted):
        db_line.highlighted_html = html

    return {
        "success": True,
        "all_lines": [l.to_dict(include_highlights=True) for l in all_lines]
    }


@router.get("/lines/stream")
async def stream_suggestion(
    session_id: int,
    partial: str = "",
    request: Request = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Stream AI suggestions using Server-Sent Events (SSE)
    Now loads full session context for better suggestions.
    """
    # ── Load context for the AI ──
    session_result = await db.execute(
        select(LyricSession).where(LyricSession.id == session_id)
    )
    session = session_result.scalar_one_or_none()

    # Get recent lines for context + rhyme target
    lines_result = await db.execute(
        select(LyricLine)
        .where(LyricLine.session_id == session_id)
        .order_by(LyricLine.line_number.desc())
        .limit(8)
    )
    recent_lines = list(reversed(lines_result.scalars().all()))
    line_texts = [l.final_version or l.user_input for l in recent_lines]

    # Get last word for rhyme targeting
    rhyme_target = ""
    if line_texts:
        last_words = line_texts[-1].split()
        if last_words:
            rhyme_target = last_words[-1].strip(".,!?;:'\"")

    async def generate():
        try:
            provider = get_ai_provider()

            # Build a context-aware prompt instead of the bare one
            context_parts = []
            if session:
                context_parts.append(
                    f"Session: {session.title or 'Untitled'} | "
                    f"BPM: {session.bpm or 140} | "
                    f"Mood: {session.mood or 'Passionate'} | "
                    f"Theme: {session.theme or 'Life'}"
                )
            if line_texts:
                context_parts.append("Recent lyrics:\n" + "\n".join(line_texts[-6:]))
            if rhyme_target:
                context_parts.append(f"Rhyme target (last word of prev line): \"{rhyme_target}\"")

            context_str = "\n".join(context_parts)

            async for chunk in provider.stream_suggestion_with_context(
                session_id, partial, context_str
            ):
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
