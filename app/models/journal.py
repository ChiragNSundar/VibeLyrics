"""
Journal Model
Stores random thoughts and scribbles that become lyric context
"""
from .database import db, TimestampMixin


class JournalEntry(db.Model, TimestampMixin):
    """A journal entry for capturing random thoughts"""
    __tablename__ = 'journal_entries'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    
    # Metadata for context building
    mood = db.Column(db.String(50), nullable=True)
    tags = db.Column(db.Text, default="[]")  # JSON array of tags
    
    # Tracking usage
    times_used = db.Column(db.Integer, default=0)  # How often used as context
    last_used_at = db.Column(db.DateTime, nullable=True)
    
    # Extracted themes/keywords (populated by AI analysis)
    extracted_themes = db.Column(db.Text, default="[]")  # JSON array
    extracted_keywords = db.Column(db.Text, default="[]")  # JSON array
    
    def __repr__(self):
        preview = self.content[:40] if self.content else ""
        return f"<JournalEntry '{preview}...'>"
    
    def mark_used(self):
        """Mark this entry as used for context"""
        from datetime import datetime
        self.times_used += 1
        self.last_used_at = datetime.utcnow()
        db.session.commit()
