"""
AI Router
AI suggestions, improvements, and Q&A
"""
from fastapi import APIRouter, Depends, HTTPException
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
    improved = await provider.improve_line(original_text, data.improvement_type)

    # Track the correction so the AI learns the user's editing tendencies
    if improved and improved != original_text:
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

