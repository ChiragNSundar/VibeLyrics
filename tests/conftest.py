"""
Test fixtures and configuration for VibeLyrics tests
"""
import pytest
import os
import tempfile

# Set test environment before importing app
os.environ['FLASK_DEBUG'] = 'false'

from app import create_app
from app.models import db, LyricSession, LyricLine, JournalEntry, UserProfile


@pytest.fixture
def app():
    """Create test application"""
    # Create temp dir for lyrics
    lyrics_dir = tempfile.mkdtemp()
    
    test_config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-secret-key',
        'LYRICS_FOLDER': lyrics_dir
    }
    
    app = create_app(test_config)
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()


@pytest.fixture
def client(app):
    """Test client for making requests"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """CLI runner for testing commands"""
    return app.test_cli_runner()


@pytest.fixture
def sample_session(app):
    """Create a sample lyric session"""
    with app.app_context():
        session = LyricSession(
            title="Test Session",
            bpm=140,
            mood="confident",
            theme="hustle"
        )
        db.session.add(session)
        db.session.commit()
        
        # Add some lines
        lines = [
            "I'm on the grind every single day",
            "Making moves, there's no other way",
            "Stack my bread, keep the haters at bay"
        ]
        
        for i, text in enumerate(lines, 1):
            line = LyricLine(
                session_id=session.id,
                line_number=i,
                user_input=text,
                final_version=text,
                syllable_count=8
            )
            db.session.add(line)
        
        db.session.commit()
        return session.id


@pytest.fixture
def sample_journal_entry(app):
    """Create a sample journal entry"""
    with app.app_context():
        entry = JournalEntry(
            content="Feeling motivated today, ready to create something fire",
            mood="motivated"
        )
        db.session.add(entry)
        db.session.commit()
        return entry.id
