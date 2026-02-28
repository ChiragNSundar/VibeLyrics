"""
AI Router
AI suggestions, improvements, and Q&A
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from ..database import get_db
from ..models import LyricSession, LyricLine, UserProfile, JournalEntry
from ..schemas import SuggestRequest, ImproveRequest, AskRequest, ProviderSwitch, RhymeCompleteRequest
from ..services.ai_provider import get_ai_provider, set_provider
from ..services.learning import StyleExtractor, CorrectionTracker, VocabularyManager

router = APIRouter()

# Singletons for learning services
_style_extractor = StyleExtractor()
_correction_tracker = CorrectionTracker()
_vocab_manager = VocabularyManager()


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
    line_texts = [l.final_version or l.user_input for l in lines]

    # Learn from current session lines (updates style model)
    if line_texts:
        _style_extractor.learn_from_session(line_texts)

    # Fetch recent journal entries for inspiration
    journal_result = await db.execute(
        select(JournalEntry).order_by(desc(JournalEntry.created_at)).limit(5)
    )
    journal_entries = journal_result.scalars().all()
    journal_dicts = [e.to_dict() for e in journal_entries]

    # Learn from journal thoughts continuously
    if journal_dicts:
        _style_extractor.learn_from_journal(journal_dicts)

    # Fetch User Preferences
    profile_result = await db.execute(select(UserProfile).limit(1))
    profile = profile_result.scalar_one_or_none()

    # Track vocabulary usage from session lines
    if line_texts:
        all_words = []
        for lt in line_texts:
            all_words.extend(lt.lower().split())
        _vocab_manager.track_usage(all_words)

    # Extract rhyme target (last word of last line)
    rhyme_target = ""
    if line_texts:
        last_words = line_texts[-1].split()
        if last_words:
            rhyme_target = last_words[-1].strip(".,!?;:'\"")

    # Build context with journal + learning + vocabulary data
    context = {
        "session": session.to_dict(),
        "lines": line_texts,
        "partial": data.partial_text,
        "action": data.action,
        "journal_entries": journal_dicts,
        "preferences": profile.to_dict() if profile else {},
        "style_summary": _style_extractor.get_style_summary(),
        "correction_insights": _correction_tracker.get_correction_insights(),
        "vocabulary": _vocab_manager.get_vocabulary_context(),
        "rhyme_target": rhyme_target,
    }

    # Fetch user's best lines across all sessions (dynamic few-shot)
    try:
        best_result = await db.execute(
            select(LyricLine)
            .where(LyricLine.complexity_score >= 40)
            .order_by(LyricLine.complexity_score.desc())
            .limit(6)
        )
        best_lines_objs = best_result.scalars().all()
        context["best_lines"] = [
            l.final_version or l.user_input for l in best_lines_objs
            if (l.final_version or l.user_input) and l.session_id != data.session_id
        ][:4]
    except Exception:
        context["best_lines"] = []

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

    original_text = line.final_version or line.user_input

    provider = get_ai_provider()
    print(f"[improve] Using provider: {provider.name}, line: '{original_text}', type: {data.improvement_type}")
    improved = await provider.improve_line(original_text, data.improvement_type)
    print(f"[improve] Result: '{improved}'")

    if not improved:
        return {
            "success": False,
            "error": f"AI provider '{provider.name}' could not improve this line. Check that LM Studio is running and the model is loaded."
        }

    # Track the correction so the AI learns the user's editing tendencies
    if improved != original_text:
        _correction_tracker.track_correction(original_text, improved)

    return {
        "success": True,
        "original": original_text,
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


@router.get("/ai/test-connection", response_model=dict)
async def test_ai_connection():
    """Detailed connectivity test for the current provider"""
    provider = get_ai_provider()
    if hasattr(provider, "test_connectivity"):
        results = await provider.test_connectivity()
        return {
            "success": results.get("response_generated", False),
            "results": results
        }
    
    return {
        "success": provider.is_available(),
        "provider": provider.name,
        "message": "Basic availability check performed (detailed test not implemented for this provider)"
    }


@router.post("/ai/improve-session", response_model=dict)
async def improve_session(data: dict, db: AsyncSession = Depends(get_db)):
    """Improve all lyrics in a session at once"""
    session_id = data.get("session_id")
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")

    # Get existing lines
    lines_result = await db.execute(
        select(LyricLine)
        .where(LyricLine.session_id == session_id)
        .order_by(LyricLine.line_number)
    )
    lines = lines_result.scalars().all()
    if not lines:
        return {"success": False, "error": "No lyrics to improve"}

    full_text = "\n".join([l.final_version or l.user_input for l in lines])

    provider = get_ai_provider()
    improved_lyrics = await provider.improve_lyrics_bulk(full_text)

    return {
        "success": True,
        "original": full_text,
        "improved": improved_lyrics
    }


@router.post("/ai/apply-polish", response_model=dict)
async def apply_polished_lyrics(data: dict, db: AsyncSession = Depends(get_db)):
    """Apply the polished block of text back to the session lines"""
    session_id = data.get("session_id")
    polished_text = data.get("polished_text")
    
    if not session_id or not polished_text:
        raise HTTPException(status_code=400, detail="session_id and polished_text are required")

    # 1. Clear existing lines
    await db.execute(
        LyricLine.__table__.delete().where(LyricLine.session_id == session_id)
    )

    # 2. Parse text into lines
    raw_lines = polished_text.split("\n")
    current_section = "Verse"
    lines_to_add = []
    
    line_num = 1
    for raw in raw_lines:
        clean = raw.strip()
        if not clean:
            continue
            
        # Check for section markers
        if any(marker in clean.lower() for marker in ["verse", "chorus", "hook", "bridge", "outro"]):
            current_section = clean.strip("[](): ").title()
            continue
            
        new_line = LyricLine(
            session_id=session_id,
            line_number=line_num,
            user_input=clean,
            final_version=clean,
            section=current_section
        )
        lines_to_add.append(new_line)
        line_num += 1

    if lines_to_add:
        db.add_all(lines_to_add)
        await db.commit()
    
    # 3. Fetch all lines back
    result = await db.execute(
        select(LyricLine)
        .where(LyricLine.session_id == session_id)
        .order_by(LyricLine.line_number)
    )
    final_lines = result.scalars().all()

    return {
        "success": True,
        "lines": [l.to_dict() for l in final_lines]
    }


@router.post("/ai/complete-rhyme", response_model=dict)
async def complete_rhyme(data: RhymeCompleteRequest, db: AsyncSession = Depends(get_db)):
    """
    Generate rhyming line completions for the partial input.
    Returns 3 different options that rhyme with the input.
    """
    # Get session context for style matching
    result = await db.execute(
        select(LyricSession).where(LyricSession.id == data.session_id)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get existing lines for context
    lines_result = await db.execute(
        select(LyricLine)
        .where(LyricLine.session_id == data.session_id)
        .order_by(LyricLine.line_number.desc())
        .limit(5)
    )
    recent_lines = lines_result.scalars().all()
    
    # Build prompt for rhyme completion
    context = {
        "session": session.to_dict(),
        "recent_lines": [l.final_version or l.user_input for l in recent_lines],
        "partial_line": data.partial_line,
        "count": data.count
    }
    
    provider = get_ai_provider()
    
    # Generate completions using AI
    prompt = f"""Complete this line with {data.count} different rhyming options.
    
Current line: "{data.partial_line}"
Recent context: {', '.join(context['recent_lines'][:3]) if context['recent_lines'] else 'None'}
Session mood: {session.mood or 'not set'}
Session theme: {session.theme or 'not set'}

Return ONLY {data.count} complete lines (not just endings), one per line, no numbering or bullets.
Each should rhyme with the last word of the input and fit the flow."""
    
    try:
        response = await provider.answer_question(prompt, context)
        # Parse response into list
        completions = [line.strip() for line in response.strip().split('\n') if line.strip()][:data.count]
        
        return {
            "success": True,
            "completions": completions,
            "partial": data.partial_line
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "completions": []
        }


# ── Phase 5: AI Generators ─────────────────────────────────────────

class AdlibRequest(BaseModel):
    lines: list[str]
    mood: str = "energetic"

class HookRequest(BaseModel):
    theme: str
    mood: str = "confident"
    verse_lines: list[str] = []

class StructureRequest(BaseModel):
    theme: str
    mood: str = "confident"
    bpm: int = 140


@router.post("/ai/adlibs")
async def generate_adlibs(data: AdlibRequest):
    """Generate context-aware adlibs based on the energy of recent bars."""
    from ..services.advanced_analysis import PunchlineEngine
    engine = PunchlineEngine()

    # Score the energy of the lines
    scores = [engine.score_punchline(line)["score"] for line in data.lines if line.strip()]
    avg_score = sum(scores) / max(1, len(scores))

    # Energy-based adlib selection
    if avg_score > 50:
        pool = ["SHEESH!", "No cap! 🧢", "Let's go!", "Talk to 'em!", "Period! 💅",
                "Say less!", "On God!", "Facts!", "Ayo!", "Gang gang!"]
    elif avg_score > 25:
        pool = ["Yeah yeah", "Uh huh", "You know it", "Real talk", "Word",
                "That's right", "Okay okay", "For sure", "Hmm", "Feel me?"]
    else:
        pool = ["Yeah...", "Mmm", "For real", "Damn...", "Woah",
                "Slowly now...", "Listen...", "True", "Sigh...", "Nah fr"]

    import random
    selected = random.sample(pool, min(5, len(pool)))

    return {
        "success": True,
        "adlibs": selected,
        "energy_score": round(avg_score),
        "energy_level": "high" if avg_score > 50 else "medium" if avg_score > 25 else "low"
    }


@router.post("/ai/hook")
async def generate_hook(data: HookRequest):
    """Generate catchy hook/chorus options using AI."""
    provider = get_ai_provider()

    verse_context = "\n".join(data.verse_lines) if data.verse_lines else "No verse provided"

    prompt = f"""Generate exactly 3 different catchy 2-line hooks/choruses for a song.

Theme: {data.theme}
Mood: {data.mood}
Verse context:
{verse_context}

Rules:
- Each hook should be exactly 2 lines
- Make them catchy and memorable — suitable for a chorus
- They should match the theme and mood
- Use repetition, rhythm, and rhyme for catchiness

Return ONLY the 3 hooks, separated by blank lines. No numbering, no labels."""

    try:
        result = await provider.generate(prompt)
        hooks = [h.strip() for h in result.split("\n\n") if h.strip()][:3]
        return {"success": True, "hooks": hooks}
    except Exception as e:
        return {"success": False, "error": str(e), "hooks": []}


@router.post("/ai/structure")
async def generate_structure(data: StructureRequest):
    """Generate a song structure blueprint using AI."""
    provider = get_ai_provider()

    prompt = f"""Create a song structure blueprint for a hip-hop/rap song.

Theme: {data.theme}
Mood: {data.mood}
BPM: {data.bpm}

Return a JSON array of sections. Each section should have:
- "section": the section name (Intro, Verse 1, Hook, Verse 2, Bridge, Hook, Outro etc.)
- "bars": number of bars (4, 8, 12, or 16)
- "description": a 1-sentence description of what this section should convey
- "energy": "low", "medium", or "high"

Return ONLY valid JSON array, no other text."""

    try:
        result = await provider.generate(prompt)
        import json as json_mod
        # Try to parse JSON from the response
        clean = result.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[1].rsplit("```", 1)[0]
        sections = json_mod.loads(clean)
        return {"success": True, "sections": sections}
    except Exception as e:
        # Fallback structure
        fallback = [
            {"section": "Intro", "bars": 4, "description": f"Set the tone for {data.theme}", "energy": "low"},
            {"section": "Verse 1", "bars": 16, "description": "Introduce the story and set the scene", "energy": "medium"},
            {"section": "Hook", "bars": 8, "description": f"Catchy chorus about {data.theme}", "energy": "high"},
            {"section": "Verse 2", "bars": 16, "description": "Deepen the narrative with more detail", "energy": "medium"},
            {"section": "Hook", "bars": 8, "description": f"Repeat the hook for memorability", "energy": "high"},
            {"section": "Bridge", "bars": 8, "description": "Shift perspective or add a twist", "energy": "low"},
            {"section": "Hook", "bars": 8, "description": "Final chorus — go hard", "energy": "high"},
            {"section": "Outro", "bars": 4, "description": "Wind down and close out", "energy": "low"},
        ]
        return {"success": True, "sections": fallback, "fallback": True}
