"""
Tests for API routes
"""
import json


class TestLineAPI:
    """Tests for line-related API endpoints"""
    
    def test_add_line(self, client, sample_session):
        """Test adding a line to a session"""
        response = client.post('/api/line/add',
            data=json.dumps({
                'session_id': sample_session,
                'line': 'New bar for the test'
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'line_id' in data
        assert 'syllable_count' in data
    
    def test_add_empty_line(self, client, sample_session):
        """Test adding an empty line returns error"""
        response = client.post('/api/line/add',
            data=json.dumps({
                'session_id': sample_session,
                'line': ''
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_update_line(self, client, app, sample_session):
        """Test updating an existing line"""
        # First add a line
        with app.app_context():
            from app.models import LyricLine
            line = LyricLine.query.filter_by(session_id=sample_session).first()
            line_id = line.id
        
        response = client.post('/api/line/update',
            data=json.dumps({
                'line_id': line_id,
                'text': 'Updated bar text'
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
    
    def test_delete_line(self, client, app, sample_session):
        """Test deleting a line"""
        with app.app_context():
            from app.models import LyricLine
            line = LyricLine.query.filter_by(session_id=sample_session).first()
            line_id = line.id
        
        response = client.post('/api/line/delete',
            data=json.dumps({'line_id': line_id}),
            content_type='application/json'
        )
        
        assert response.status_code == 200


class TestSessionAPI:
    """Tests for session-related API endpoints"""
    
    def test_analyze_session(self, client, sample_session):
        """Test session analysis endpoint"""
        response = client.get(f'/api/session/{sample_session}/analyze')
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'line_count' in data
        assert 'rhyme_scheme' in data
        assert 'complexity' in data
    
    def test_analyze_empty_session(self, client, app):
        """Test analyzing session with no lines"""
        with app.app_context():
            from app.models import LyricSession, db
            session = LyricSession(title="Empty", bpm=120)
            db.session.add(session)
            db.session.commit()
            session_id = session.id
        
        response = client.get(f'/api/session/{session_id}/analyze')
        assert response.status_code == 400


class TestProviderAPI:
    """Tests for AI provider switching"""
    
    def test_switch_to_gemini(self, client):
        """Test switching to Gemini provider"""
        response = client.post('/api/provider/switch',
            data=json.dumps({'provider': 'gemini'}),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['provider'] == 'gemini'
    
    def test_switch_invalid_provider(self, client):
        """Test switching to invalid provider returns error"""
        response = client.post('/api/provider/switch',
            data=json.dumps({'provider': 'invalid'}),
            content_type='application/json'
        )
        
        assert response.status_code == 400


class TestRhymeAPI:
    """Tests for rhyme dictionary API endpoints"""
    
    def test_rhyme_lookup(self, client):
        """Test looking up rhymes for a word"""
        response = client.post('/api/rhyme/lookup',
            data=json.dumps({'word': 'cat'}),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'rhymes' in data
        assert len(data['rhymes']) > 0
    
    def test_rhyme_lookup_empty(self, client):
        """Test empty word returns error"""
        response = client.post('/api/rhyme/lookup',
            data=json.dumps({'word': ''}),
            content_type='application/json'
        )
        
        assert response.status_code == 400
    
    def test_slang_categories(self, client):
        """Test getting slang categories"""
        response = client.get('/api/rhyme/categories')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'categories' in data
        assert 'money' in data['categories']
    
    def test_slang_lookup(self, client):
        """Test getting slang for a category"""
        response = client.get('/api/rhyme/slang/money')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'synonyms' in data
        assert len(data['synonyms']) > 0

