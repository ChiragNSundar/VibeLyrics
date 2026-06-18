"""
WebSocket Router for Real-time Streaming AI Suggestions and Lyrics Analysis
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import re
from sqlalchemy import select

from ..database import async_session
from ..models import LyricSession, LyricLine
from ..services.rhyme_detector import RhymeDetector, SyllableCounter
from ..services.ai_provider import get_ai_provider

router = APIRouter()
_syllable_counter = SyllableCounter()
_rhyme_detector = RhymeDetector()

def compute_complexity(content: str) -> float:
    """Compute a 0-100 complexity score for a single line."""
    words = content.lower().split()
    if not words:
        return 0.0

    # Handle basic character ranges for both English and Indian scripts
    clean_words = []
    for w in words:
        is_indian = any(0x0900 <= ord(c) <= 0x097F or 0x0C80 <= ord(c) <= 0x0CFF for c in w)
        if is_indian:
            clean = re.sub(r'[^\u0900-\u097f\u0c80-\u0cff]', '', w)
        else:
            clean = re.sub(r'[^a-z]', '', w)
        if clean:
            clean_words.append(clean)

    if not clean_words:
        return 0.0

    unique = set(clean_words)
    vocab_diversity = len(unique) / len(clean_words)

    # Count multi-syllable words (3+ syllables)
    multi_count = sum(1 for w in clean_words if _syllable_counter.count(w) >= 3)
    multi_ratio = multi_count / len(clean_words)

    # Average word length bonus
    avg_len = sum(len(w) for w in clean_words) / len(clean_words)
    length_score = min(1.0, avg_len / 8.0)

    score = (vocab_diversity * 40) + (multi_ratio * 35) + (length_score * 25)
    return round(min(100.0, score), 1)

@router.websocket("/ws/suggest")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time suggestions and analysis"""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON payload"})
                continue

            msg_type = payload.get("type")

            if msg_type == "suggest":
                session_id = payload.get("session_id")
                partial = payload.get("partial", "")

                if not session_id:
                    await websocket.send_json({"type": "error", "message": "session_id is required"})
                    continue

                async with async_session() as db:
                    # Load session configuration
                    session_result = await db.execute(
                        select(LyricSession).where(LyricSession.id == session_id)
                    )
                    session = session_result.scalar_one_or_none()

                    # Get recent lines for context
                    lines_result = await db.execute(
                        select(LyricLine)
                        .where(LyricLine.session_id == session_id)
                        .order_by(LyricLine.line_number.desc())
                        .limit(8)
                    )
                    recent_lines = list(reversed(lines_result.scalars().all()))
                    line_texts = [l.final_version or l.user_input for l in recent_lines]

                # Get last word for rhyme target
                rhyme_target = ""
                if line_texts:
                    last_words = line_texts[-1].split()
                    if last_words:
                        rhyme_target = last_words[-1].strip(".,!?;:'\"")

                # Build prompt context
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

                try:
                    provider = get_ai_provider()
                    async for chunk in provider.stream_suggestion_with_context(
                        session_id, partial, context_str
                    ):
                        await websocket.send_json({"type": "suggest_chunk", "chunk": chunk})
                    await websocket.send_json({"type": "suggest_done"})
                except Exception as e:
                    await websocket.send_json({"type": "error", "message": f"AI streaming failed: {str(e)}"})

            elif msg_type == "analyze":
                content = payload.get("content", "")
                syllable_count = _syllable_counter.count(content)
                stress_pattern = _syllable_counter.get_stress_pattern(content)
                has_internal = _rhyme_detector.detect_internal_rhymes(content)
                complexity = compute_complexity(content)

                await websocket.send_json({
                    "type": "analysis_result",
                    "syllables": syllable_count,
                    "stress": stress_pattern,
                    "has_internal": has_internal,
                    "complexity": complexity
                })

            else:
                await websocket.send_json({"type": "error", "message": f"Unknown payload type: {msg_type}"})

    except WebSocketDisconnect:
        # Client disconnected
        pass
