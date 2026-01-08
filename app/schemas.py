"""
Pydantic Schemas for API Request Validation
Uses Pydantic v2 for strict typing and automatic validation
"""
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator


# =============================================================================
# LINE MANAGEMENT SCHEMAS
# =============================================================================

class AddLineRequest(BaseModel):
    """Request schema for adding a new line to a session"""
    session_id: int
    line: str = Field(..., min_length=1, description="The lyric line text")
    section: str = Field(default="Verse", description="Section type (Verse, Chorus, etc.)")
    
    @field_validator('line')
    @classmethod
    def strip_and_validate(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError('Line cannot be empty or whitespace only')
        return stripped


class UpdateLineRequest(BaseModel):
    """Request schema for updating an existing line"""
    line_id: int
    text: str = Field(..., min_length=1, description="New text for the line")
    
    @field_validator('text')
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        return v.strip()


class DeleteLineRequest(BaseModel):
    """Request schema for deleting a line"""
    line_id: int


# =============================================================================
# AI PROVIDER SCHEMAS
# =============================================================================

class SwitchProviderRequest(BaseModel):
    """Request schema for switching AI provider"""
    provider: Literal["openai", "gemini", "perplexity"]


# =============================================================================
# SUGGESTION SCHEMAS
# =============================================================================

class SuggestLineRequest(BaseModel):
    """Request schema for AI line suggestions"""
    session_id: int
    action: Literal["next", "improve"] = Field(default="next")
    current_line: Optional[str] = Field(default="")
    improvement_type: Literal["rhyme", "flow", "wordplay", "depth"] = Field(default="rhyme")


class AcceptSuggestionRequest(BaseModel):
    """Request schema for accepting an AI suggestion"""
    session_id: int
    suggestion: str
    original_input: Optional[str] = Field(default=None)
    was_modified: bool = Field(default=False)
    section: str = Field(default="Verse")


# =============================================================================
# LOOKUP SCHEMAS
# =============================================================================

class RhymeLookupRequest(BaseModel):
    """Request schema for rhyme lookup"""
    word: str = Field(..., min_length=1)
    
    @field_validator('word')
    @classmethod
    def strip_and_validate(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError('Word cannot be empty')
        return stripped


class AskQuestionRequest(BaseModel):
    """Request schema for asking AI a question"""
    session_id: int
    question: str = Field(..., min_length=1)
