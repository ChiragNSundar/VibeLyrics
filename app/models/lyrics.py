"""
Lyrics Models
Stores lyric writing sessions and individual lines
"""
from .database import db, TimestampMixin


class LyricSession(db.Model, TimestampMixin):
    """A lyric writing session (one song/verse)"""
    __tablename__ = 'lyric_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), default="Untitled")
    bpm = db.Column(db.Integer, default=140)
    mood = db.Column(db.String(50), nullable=True)  # introspective, hype, emotional, etc.
    theme = db.Column(db.String(100), nullable=True)  # love, struggle, success, etc.
    
    # Status
    status = db.Column(db.String(20), default="in_progress")  # in_progress, completed, archived
    
    # Relationships
    lines = db.relationship('LyricLine', backref='session', lazy='dynamic', 
                           order_by='LyricLine.line_number',
                           cascade='all, delete-orphan')
    
    # Context from journal entries used (stored as JSON of entry IDs)
    journal_context_ids = db.Column(db.Text, default="[]")
    
    def __repr__(self):
        return f"<LyricSession '{self.title}' @ {self.bpm}bpm>"
    
    @property
    def line_count(self):
        return self.lines.count()
    
    def get_full_lyrics(self):
        """Get all lines as a single string"""
        return "\n".join([line.final_version or line.user_input for line in self.lines.all()])


class LyricLine(db.Model, TimestampMixin):
    """A single line/bar in a lyric session"""
    __tablename__ = 'lyric_lines'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('lyric_sessions.id'), nullable=False)
    line_number = db.Column(db.Integer, nullable=False)
    
    # Content versions
    user_input = db.Column(db.Text, nullable=False)  # What user originally wrote
    ai_suggestion = db.Column(db.Text, nullable=True)  # AI's suggested improvement
    final_version = db.Column(db.Text, nullable=True)  # What user accepted/modified
    
    # Analysis data
    syllable_count = db.Column(db.Integer, nullable=True)
    rhyme_scheme = db.Column(db.String(10), nullable=True)  # A, B, C, etc.
    has_internal_rhyme = db.Column(db.Boolean, default=False)
    complexity_score = db.Column(db.Float, nullable=True)  # 0.0 to 1.0
    
    # AI interaction
    ai_question = db.Column(db.Text, nullable=True)  # Question AI asked about this line
    user_response = db.Column(db.Text, nullable=True)  # User's response to AI question
    
    # Status
    was_corrected = db.Column(db.Boolean, default=False)  # User modified AI suggestion
    
    def __repr__(self):
        preview = (self.final_version or self.user_input)[:30]
        return f"<LyricLine {self.line_number}: '{preview}...'>"
