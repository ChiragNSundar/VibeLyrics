"""
Advanced Features Router
- AI-powered punchline scoring & generation
- AI-powered metaphor/simile generation
- Complexity analysis
- Imagery analysis
- Contextual adlib generation
- Learning endpoints
- Reference management
- Audio: key detection, beat sections
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel, Field

from ..database import get_db
from ..models import LyricSession, LyricLine
from ..services.advanced_analysis import (
    PunchlineEngine, 
    MetaphorGenerator, 
    ComplexityScorer, 
    ImageryAnalyzer
)
from ..services.learning import StyleExtractor, VocabularyManager, CorrectionTracker
from ..services.references import FolderManager, TxtParser, StructuredParser
from ..services.audio import AudioAnalyzer, AdlibGenerator
from ..services.ai_provider import get_ai_provider

router = APIRouter()

# Initialize services
punchline_engine = PunchlineEngine()
metaphor_gen = MetaphorGenerator()
complexity_scorer = ComplexityScorer()
imagery_analyzer = ImageryAnalyzer()
style_extractor = StyleExtractor()
vocab_manager = VocabularyManager()
correction_tracker = CorrectionTracker()
folder_manager = FolderManager()
audio_analyzer = AudioAnalyzer()
adlib_gen = AdlibGenerator()


# ============ Punchline Endpoints ============

class PunchlineRequest(BaseModel):
    line: str = Field(..., min_length=1)


class ThemeRequest(BaseModel):
    theme: str = Field(..., min_length=1)


class AIPunchlineRequest(BaseModel):
    theme: str = Field(..., min_length=1)
    session_id: Optional[int] = None
    mood: Optional[str] = None
    count: int = Field(default=5, ge=1, le=10)


@router.post("/punchline/score", response_model=dict)
async def score_punchline(data: PunchlineRequest):
    """Score a line's punchline potential"""
    result = punchline_engine.score_punchline(data.line)
    return {"success": True, **result}


@router.post("/punchline/generate", response_model=dict)
async def generate_punchlines(data: ThemeRequest):
    """Generate punchline starters for a theme (rule-based fallback)"""
    starters = punchline_engine.generate_punchline_starters(data.theme)
    return {"success": True, "starters": starters}


@router.post("/punchline/ai-generate", response_model=dict)
async def ai_generate_punchlines(data: AIPunchlineRequest, db: AsyncSession = Depends(get_db)):
    """Generate punchlines using AI with full session context"""
    lines = []
    mood = data.mood
    
    if data.session_id:
        result = await db.execute(
            select(LyricLine)
            .where(LyricLine.session_id == data.session_id)
            .order_by(LyricLine.line_number)
        )
        db_lines = result.scalars().all()
        lines = [l.final_version or l.user_input for l in db_lines]
        
        if not mood:
            session_result = await db.execute(
                select(LyricSession).where(LyricSession.id == data.session_id)
            )
            session = session_result.scalar_one_or_none()
            if session:
                mood = session.mood
    
    result = await punchline_engine.generate_ai_punchlines(
        theme=data.theme, lines=lines, mood=mood, count=data.count
    )
    return {"success": True, **result}


@router.post("/punchline/analyze-verse", response_model=dict)
async def analyze_verse_punchlines(lines: List[str]):
    """Analyze entire verse for punchlines"""
    results = []
    for line in lines:
        score = punchline_engine.score_punchline(line)
        results.append({"line": line, **score})
    
    avg_score = sum(r["score"] for r in results) / max(1, len(results))
    
    return {
        "success": True,
        "lines": results,
        "avg_score": round(avg_score, 1)
    }


# ============ Metaphor Endpoints ============

class MetaphorRequest(BaseModel):
    concept: str = Field(..., min_length=1)
    count: int = Field(default=5, ge=1, le=20)
    session_id: Optional[int] = None


class SimileRequest(BaseModel):
    word: str = Field(..., min_length=1)
    count: int = Field(default=5, ge=1, le=20)
    session_id: Optional[int] = None


class SimileCompleteRequest(BaseModel):
    starter: str = Field(..., min_length=1)


@router.post("/metaphor/generate", response_model=dict)
async def generate_metaphors(data: MetaphorRequest, db: AsyncSession = Depends(get_db)):
    """Generate metaphors for a concept (AI-powered with rule-based fallback)"""
    context = []
    if data.session_id:
        result = await db.execute(
            select(LyricLine)
            .where(LyricLine.session_id == data.session_id)
            .order_by(LyricLine.line_number.desc())
            .limit(5)
        )
        context = [l.final_version or l.user_input for l in result.scalars().all()]
    
    result = await metaphor_gen.generate_ai_metaphors(data.concept, context, data.count)
    return {"success": True, **result}


@router.post("/simile/generate", response_model=dict)
async def generate_similes(data: SimileRequest, db: AsyncSession = Depends(get_db)):
    """Generate similes for a word (AI-powered with rule-based fallback)"""
    context = []
    if data.session_id:
        result = await db.execute(
            select(LyricLine)
            .where(LyricLine.session_id == data.session_id)
            .order_by(LyricLine.line_number.desc())
            .limit(5)
        )
        context = [l.final_version or l.user_input for l in result.scalars().all()]
    
    result = await metaphor_gen.generate_ai_similes(data.word, context, data.count)
    return {"success": True, **result}


@router.post("/simile/complete", response_model=dict)
async def complete_simile(data: SimileCompleteRequest):
    """Complete a simile starter"""
    completed = metaphor_gen.complete_simile(data.starter)
    return {"success": True, "completed": completed}


# ============ Brainstorm Endpoints ============

class BrainstormRequest(BaseModel):
    topic: str = Field(..., min_length=1)

@router.post("/brainstorm/themes", response_model=dict)
async def brainstorm_themes(data: BrainstormRequest):
    """Brainstorm related themes"""
    provider = get_ai_provider()
    prompt = f"List 5 creative song themes related to: {data.topic}. Return only the themes, one per line."
    response = await provider.answer_question(prompt, None)
    themes = [t.strip("- ") for t in response.split('\n') if t.strip()]
    return {"success": True, "themes": themes[:10]}

@router.post("/brainstorm/titles", response_model=dict)
async def brainstorm_titles(data: BrainstormRequest):
    """Brainstorm song titles"""
    provider = get_ai_provider()
    prompt = f"List 5 catchy song titles for a song about: {data.topic}. Return only titles, one per line."
    response = await provider.answer_question(prompt, None)
    titles = [t.strip("- ") for t in response.split('\n') if t.strip()]
    return {"success": True, "titles": titles[:10]}


# ============ Complexity Endpoints ============

@router.post("/complexity/score-verse", response_model=dict)
async def score_verse_complexity(lines: List[str]):
    """Score verse complexity"""
    result = complexity_scorer.score_verse(lines)
    return {"success": True, **result}


@router.get("/complexity/session/{session_id}", response_model=dict)
async def get_session_complexity(session_id: int, db: AsyncSession = Depends(get_db)):
    """Get complexity score for a session"""
    result = await db.execute(
        select(LyricLine)
        .where(LyricLine.session_id == session_id)
        .order_by(LyricLine.line_number)
    )
    lines = result.scalars().all()
    
    if not lines:
        raise HTTPException(status_code=404, detail="Session not found or empty")
    
    text_lines = [l.final_version or l.user_input for l in lines]
    score = complexity_scorer.score_verse(text_lines)
    
    return {"success": True, "session_id": session_id, **score}


# ============ Imagery Endpoints ============

@router.post("/imagery/analyze", response_model=dict)
async def analyze_imagery(lines: List[str]):
    """Analyze imagery density in lyrics"""
    result = imagery_analyzer.analyze_imagery(lines)
    return {"success": True, **result}


# ============ Learning Endpoints ============

class RateSuggestionRequest(BaseModel):
    suggestion: str
    rating: int = Field(..., ge=1, le=5)


class CorrectionRequest(BaseModel):
    original: str
    corrected: str


@router.post("/learning/rate-suggestion", response_model=dict)
async def rate_suggestion(data: RateSuggestionRequest):
    """Rate an AI suggestion"""
    return {"success": True, "message": "Rating recorded"}


@router.post("/learning/track-correction", response_model=dict)
async def track_correction(data: CorrectionRequest):
    """Track a user correction"""
    correction_tracker.track_correction(data.original, data.corrected)
    return {"success": True}


@router.get("/learning/status", response_model=dict)
async def get_learning_status():
    """Get current learning status"""
    return {
        "success": True,
        "style": style_extractor.get_style_summary(),
        "vocabulary": vocab_manager.get_vocabulary_context(),
        "corrections": correction_tracker.get_correction_insights()
    }


# ============ Reference Endpoints ============

@router.get("/references", response_model=dict)
async def list_references():
    """List all reference files"""
    files = folder_manager.list_all_files()
    stats = folder_manager.get_statistics()
    return {"success": True, "files": files, "stats": stats}


@router.get("/references/{filename:path}", response_model=dict)
async def get_reference(filename: str):
    """Get a reference file"""
    content = folder_manager.get_file_content(filename)
    if content is None:
        raise HTTPException(status_code=404, detail="File not found")
    
    structured = StructuredParser()
    txt = TxtParser()
    
    if structured.is_structured(content):
        parsed = structured.parse(content)
    else:
        parsed = {"lyrics": txt.parse(content), "metadata": {}}
    
    return {
        "success": True,
        "filename": filename,
        "content": content,
        "parsed": parsed
    }


class AddReferenceRequest(BaseModel):
    artist: str = Field(default="Unknown")
    title: str = Field(default="Untitled")
    lyrics: str = Field(..., min_length=1)


@router.post("/references", response_model=dict)
async def add_reference(data: AddReferenceRequest):
    """Add a new reference"""
    filepath = folder_manager.add_lyrics_file(
        content=data.lyrics,
        artist=data.artist,
        song_title=data.title,
        structured=True
    )
    return {"success": True, "path": filepath}


@router.delete("/references/{filename:path}", response_model=dict)
async def delete_reference(filename: str):
    """Delete a reference file"""
    success = folder_manager.delete_file(filename)
    if not success:
        raise HTTPException(status_code=404, detail="File not found")
    return {"success": True}


@router.get("/references/search", response_model=dict)
async def search_references(q: str):
    """Search reference files"""
    results = folder_manager.search_files(q)
    return {"success": True, "results": results}


# ============ DNA Analysis ============

@router.get("/dna/analyze/{session_id}", response_model=dict)
async def analyze_dna(session_id: int, db: AsyncSession = Depends(get_db)):
    """Analyze artist DNA for a session"""
    result = await db.execute(
        select(LyricLine)
        .where(LyricLine.session_id == session_id)
        .order_by(LyricLine.line_number)
    )
    lines = result.scalars().all()
    
    if not lines:
        raise HTTPException(status_code=404, detail="Session not found or empty")
    
    text_lines = [l.final_version or l.user_input for l in lines]
    
    complexity = complexity_scorer.score_verse(text_lines)
    imagery = imagery_analyzer.analyze_imagery(text_lines)
    
    dna = {
        "complexity": complexity["breakdown"]["vocabulary_diversity"] * 100,
        "imagery_density": imagery["density"] * 100,
        "word_count": complexity["breakdown"]["total_words"],
        "unique_vocab": complexity["breakdown"]["unique_words"]
    }
    
    return {"success": True, "dna": dna}


# ============ Audio Endpoints ============

@router.get("/audio/analyze/{filename:path}", response_model=dict)
async def analyze_audio(filename: str):
    """Analyze audio file — BPM, key, energy, waveform"""
    import os
    file_path = os.path.join("uploads/audio", filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    bpm = audio_analyzer.detect_bpm(file_path)
    key_info = audio_analyzer.detect_key(file_path)
    sections = audio_analyzer.get_energy_sections(file_path)
    waveform = audio_analyzer.get_waveform_data(file_path)
    
    return {
        "success": True,
        "bpm": bpm,
        "key": key_info,
        "sections": sections,
        "waveform": waveform
    }


@router.get("/audio/sections/{filename:path}", response_model=dict)
async def get_audio_sections(filename: str):
    """Detect beat structure sections (Intro, Verse, Chorus, Bridge, Outro)"""
    import os
    file_path = os.path.join("uploads/audio", filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    sections = audio_analyzer.detect_sections(file_path)
    bpm = audio_analyzer.detect_bpm(file_path)
    key_info = audio_analyzer.detect_key(file_path)
    
    return {
        "success": True,
        "bpm": bpm,
        "key": key_info,
        "sections": sections,
        "total_sections": len(sections)
    }


@router.get("/audio/section-waveform/{filename:path}", response_model=dict)
async def get_section_waveform(filename: str, start: float = 0, end: float = 0):
    """Get waveform data for a specific section (for looping)"""
    import os
    file_path = os.path.join("uploads/audio", filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    if end <= start:
        raise HTTPException(status_code=400, detail="end must be greater than start")
    
    waveform = audio_analyzer.get_section_waveform(file_path, start, end)
    
    return {
        "success": True,
        "start_sec": start,
        "end_sec": end,
        "waveform": waveform
    }


# ============ Adlib Endpoints ============

class AdlibRequest(BaseModel):
    line: str = Field(..., min_length=1)
    style: str = Field(default="mixed")


class ContextualAdlibRequest(BaseModel):
    line: str = Field(..., min_length=1)
    mood: Optional[str] = None
    artist_style: Optional[str] = None
    recent_lines: List[str] = []
    use_ai: bool = False


@router.post("/adlibs/generate", response_model=dict)
async def generate_adlibs(data: AdlibRequest):
    """Generate adlibs for a line (static)"""
    adlibs = adlib_gen.generate_adlibs(data.line, data.style)
    return {"success": True, "adlibs": adlibs}


@router.post("/adlibs/contextual", response_model=dict)
async def generate_contextual_adlibs(data: ContextualAdlibRequest):
    """Generate context-aware adlibs based on mood, artist style, and content"""
    if data.use_ai:
        result = await adlib_gen.generate_ai_adlibs(
            line=data.line,
            mood=data.mood,
            artist_style=data.artist_style,
            recent_lines=data.recent_lines
        )
    else:
        result = adlib_gen.generate_contextual_adlibs(
            line=data.line,
            mood=data.mood,
            artist_style=data.artist_style,
            recent_lines=data.recent_lines
        )
    return {"success": True, **result}


@router.post("/adlibs/placement", response_model=dict)
async def suggest_adlibs(data: AdlibRequest):
    """Suggest adlib placements"""
    suggestion = adlib_gen.suggest_placement(data.line)
    return {"success": True, **suggestion}


@router.get("/adlibs/categories", response_model=dict)
async def get_adlib_categories():
    """Get adlib categories"""
    categories = adlib_gen.get_categories()
    return {"success": True, "categories": categories}


@router.get("/adlibs/artist-styles", response_model=dict)
async def get_artist_styles():
    """Get available artist styles for adlibs"""
    styles = adlib_gen.get_artist_styles()
    return {"success": True, "styles": styles}
