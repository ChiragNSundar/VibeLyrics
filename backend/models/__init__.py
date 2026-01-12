"""
SQLAlchemy Models
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, Float, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class LyricSession(Base):
    """A writing session containing lyric lines"""
    __tablename__ = "lyric_sessions"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), default="Untitled")
    bpm: Mapped[int] = mapped_column(Integer, default=140)
    mood: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    theme: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    audio_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    lines: Mapped[List["LyricLine"]] = relationship(
        "LyricLine", 
        back_populates="session", 
        cascade="all, delete-orphan",
        order_by="LyricLine.line_number"
    )
    
    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "bpm": self.bpm,
            "mood": self.mood,
            "theme": self.theme,
            "audio_path": self.audio_path,
            "line_count": len(self.lines) if "lines" in self.__dict__ else 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class LyricLine(Base):
    """A single line of lyrics"""
    __tablename__ = "lyric_lines"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("lyric_sessions.id", ondelete="CASCADE"))
    line_number: Mapped[int] = mapped_column(Integer, default=1)
    user_input: Mapped[str] = mapped_column(Text, default="")
    ai_suggestion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    final_version: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    section: Mapped[str] = mapped_column(String(50), default="Verse")
    
    # Analysis data
    syllable_count: Mapped[int] = mapped_column(Integer, default=0)
    stress_pattern: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    rhyme_end: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    has_internal_rhyme: Mapped[bool] = mapped_column(Boolean, default=False)
    complexity_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session: Mapped["LyricSession"] = relationship("LyricSession", back_populates="lines")
    
    def to_dict(self, include_highlights=False):
        result = {
            "id": self.id,
            "session_id": self.session_id,
            "line_number": self.line_number,
            "user_input": self.user_input,
            "ai_suggestion": self.ai_suggestion,
            "final_version": self.final_version,
            "section": self.section,
            "syllable_count": self.syllable_count,
            "stress_pattern": self.stress_pattern,
            "rhyme_end": self.rhyme_end,
            "has_internal_rhyme": self.has_internal_rhyme,
            "complexity_score": self.complexity_score,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
        if include_highlights:
            result["highlighted_html"] = getattr(self, "highlighted_html", None)
            result["heatmap_class"] = getattr(self, "heatmap_class", None)
        return result


class JournalEntry(Base):
    """Journal entry for capturing thoughts"""
    __tablename__ = "journal_entries"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    content: Mapped[str] = mapped_column(Text, default="")
    mood: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    tags: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    extracted_themes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    extracted_keywords: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        import json
        return {
            "id": self.id,
            "content": self.content,
            "mood": self.mood,
            "tags": json.loads(self.tags) if self.tags else [],
            "themes": json.loads(self.extracted_themes) if self.extracted_themes else [],
            "keywords": json.loads(self.extracted_keywords) if self.extracted_keywords else [],
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class UserProfile(Base):
    """User preferences and learning data"""
    __tablename__ = "user_profiles"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    preferred_provider: Mapped[str] = mapped_column(String(50), default="gemini")
    default_bpm: Mapped[int] = mapped_column(Integer, default=140)
    complexity_level: Mapped[str] = mapped_column(String(50), default="medium")
    rhyme_style: Mapped[str] = mapped_column(String(50), default="mixed")
    
    # Vocabulary Preferences
    favorite_words: Mapped[Optional[str]] = mapped_column(Text, default="[]") # JSON list
    banned_words: Mapped[Optional[str]] = mapped_column(Text, default="[]") # JSON list
    slang_preferences: Mapped[Optional[str]] = mapped_column(Text, default="[]") # JSON list
    
    # Stats
    total_sessions: Mapped[int] = mapped_column(Integer, default=0)
    total_lines_written: Mapped[int] = mapped_column(Integer, default=0)
    total_corrections: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        import json
        return {
            "id": self.id,
            "preferred_provider": self.preferred_provider,
            "default_bpm": self.default_bpm,
            "complexity_level": self.complexity_level,
            "rhyme_style": self.rhyme_style,
            "favorite_words": json.loads(self.favorite_words) if self.favorite_words else [],
            "banned_words": json.loads(self.banned_words) if self.banned_words else [],
            "slang_preferences": json.loads(self.slang_preferences) if self.slang_preferences else [],
            "total_sessions": self.total_sessions,
            "total_lines_written": self.total_lines_written,
            "total_corrections": self.total_corrections
        }
