"""
Pydantic Schemas for request/response validation
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ============ Session Schemas ============

class SessionCreate(BaseModel):
    title: str = Field(default="Untitled", max_length=200)
    bpm: int = Field(default=140, ge=60, le=200)
    mood: Optional[str] = None
    theme: Optional[str] = None


class SessionUpdate(BaseModel):
    title: Optional[str] = None
    bpm: Optional[int] = None
    mood: Optional[str] = None
    theme: Optional[str] = None


class SessionResponse(BaseModel):
    id: int
    title: str
    bpm: int
    mood: Optional[str]
    theme: Optional[str]
    audio_path: Optional[str]
    line_count: int = 0
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ============ Line Schemas ============

class LineCreate(BaseModel):
    session_id: int
    content: str = Field(..., min_length=1)
    section: str = Field(default="Verse")


class LineUpdate(BaseModel):
    content: str = Field(..., min_length=1)


class LineResponse(BaseModel):
    id: int
    session_id: int
    line_number: int
    user_input: str
    ai_suggestion: Optional[str]
    final_version: Optional[str]
    section: str
    syllable_count: int
    stress_pattern: Optional[str]
    rhyme_end: Optional[str]
    has_internal_rhyme: bool
    complexity_score: Optional[float]
    highlighted_html: Optional[str] = None
    heatmap_class: Optional[str] = None
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


# ============ AI Schemas ============

class SuggestRequest(BaseModel):
    session_id: int
    partial_text: str = ""
    action: str = Field(default="continue")  # continue, improve, rhyme


class ImproveRequest(BaseModel):
    line_id: int
    improvement_type: str = Field(default="rhyme")  # rhyme, flow, wordplay, depth


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1)
    session_id: Optional[int] = None


class ProviderSwitch(BaseModel):
    provider: str = Field(..., pattern="^(gemini|openai|lmstudio)$")


# ============ Rhyme Schemas ============

class RhymeLookup(BaseModel):
    word: str = Field(..., min_length=1)
    max_results: int = Field(default=20, ge=1, le=100)


class ThesaurusLookup(BaseModel):
    word: str = Field(..., min_length=1)
    include_rhymes: bool = True
    include_synonyms: bool = True


# ============ Journal Schemas ============

class JournalCreate(BaseModel):
    content: str = Field(..., min_length=1)
    mood: Optional[str] = None
    tags: List[str] = []


class JournalResponse(BaseModel):
    id: int
    content: str
    mood: Optional[str]
    tags: List[str] = []
    themes: List[str] = []
    keywords: List[str] = []
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


# ============ Settings Schemas ============

class SettingsUpdate(BaseModel):
    preferred_provider: Optional[str] = None
    default_bpm: Optional[int] = None
    complexity_level: Optional[str] = None
    rhyme_style: Optional[str] = None


class VocabularyAdd(BaseModel):
    word: str = Field(..., min_length=1)
    list_type: str = Field(default="favorite")  # favorite, slang, avoided


# ============ Stats Schemas ============

class StatsResponse(BaseModel):
    total_sessions: int
    total_lines: int
    total_words: int
    unique_vocabulary: int
    avg_bpm: int
    sessions_this_week: int
    lines_today: int


class AchievementResponse(BaseModel):
    name: str
    icon: str
    desc: str


# ============ Generic Responses ============

class SuccessResponse(BaseModel):
    success: bool = True
    message: Optional[str] = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
