"""
Corrections Model
Tracks user corrections to learn from preferences
"""
from .database import db, TimestampMixin


class Correction(db.Model, TimestampMixin):
    """Tracks corrections user makes to AI suggestions for learning"""
    __tablename__ = 'corrections'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # The correction pair
    original_suggestion = db.Column(db.Text, nullable=False)
    user_correction = db.Column(db.Text, nullable=False)
    
    # Context
    line_id = db.Column(db.Integer, db.ForeignKey('lyric_lines.id'), nullable=True)
    session_id = db.Column(db.Integer, db.ForeignKey('lyric_sessions.id'), nullable=True)
    
    # Classification
    correction_type = db.Column(db.String(50), nullable=True)
    # Types: word_choice, rhyme, flow, slang, tone, meaning, simplify, complexify
    
    # Learning status
    learned = db.Column(db.Boolean, default=False)  # Has been incorporated into style
    confidence = db.Column(db.Float, default=1.0)  # How confident we are in this pattern
    
    # Pattern extraction
    pattern_extracted = db.Column(db.Text, nullable=True)  # JSON of extracted pattern
    
    def __repr__(self):
        return f"<Correction '{self.original_suggestion[:20]}...' -> '{self.user_correction[:20]}...'>"
    
    @classmethod
    def get_unlearned(cls):
        """Get corrections that haven't been incorporated yet"""
        return cls.query.filter_by(learned=False).all()
    
    @classmethod
    def get_by_type(cls, correction_type):
        """Get all corrections of a specific type"""
        return cls.query.filter_by(correction_type=correction_type).all()
