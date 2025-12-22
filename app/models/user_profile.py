"""
User Profile Model
Stores user preferences and settings for AI personalization
"""
from .database import db, TimestampMixin


class UserProfile(db.Model, TimestampMixin):
    """User profile storing preferences and learned style patterns"""
    __tablename__ = 'user_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), default="default")
    
    # AI Preferences
    preferred_provider = db.Column(db.String(20), default="openai")  # openai or gemini
    default_bpm = db.Column(db.Integer, default=140)
    
    # Style Preferences (stored as JSON strings)
    favorite_themes = db.Column(db.Text, default="[]")  # JSON array
    complexity_level = db.Column(db.String(20), default="medium")  # low, medium, high
    rhyme_style = db.Column(db.String(20), default="mixed")  # internal, end, mixed, complex
    
    # Stats
    total_sessions = db.Column(db.Integer, default=0)
    total_lines_written = db.Column(db.Integer, default=0)
    total_corrections = db.Column(db.Integer, default=0)

    # Gamification Stats
    current_streak = db.Column(db.Integer, default=0)
    longest_streak = db.Column(db.Integer, default=0)
    last_active_date = db.Column(db.Date, nullable=True)
    words_written_today = db.Column(db.Integer, default=0)
    
    def update_streak(self):
        """Update streak logic based on activity today"""
        from datetime import date
        today = date.today()
        
        if self.last_active_date == today:
            return  # Already active today
            
        if self.last_active_date:
            delta = (today - self.last_active_date).days
            if delta == 1:
                self.current_streak += 1
            else:
                self.current_streak = 1
        else:
            self.current_streak = 1
            
        if self.current_streak > self.longest_streak:
            self.longest_streak = self.current_streak
            
        self.last_active_date = today
        # Reset daily counter if it's a new day (handled by logic consuming this)

    
    def __repr__(self):
        return f"<UserProfile {self.name}>"
    
    @classmethod
    def get_or_create_default(cls):
        """Get the default profile or create one if it doesn't exist"""
        profile = cls.query.filter_by(name="default").first()
        if not profile:
            profile = cls(name="default")
            db.session.add(profile)
            db.session.commit()
        return profile
