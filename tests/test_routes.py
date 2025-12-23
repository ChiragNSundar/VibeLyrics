"""
Tests for journal functionality
"""
import json


class TestJournal:
    """Tests for journal routes"""
    
    def test_journal_index(self, client):
        """Test journal page loads"""
        response = client.get('/journal/')
        assert response.status_code == 200
    
    def test_quick_add_thought(self, client):
        """Test quick adding a thought"""
        response = client.post('/journal/quick-add',
            data=json.dumps({
                'content': 'Random thought for lyrics',
                'mood': 'inspired'
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'entry' in data
        assert data['entry']['content'] == 'Random thought for lyrics'
    
    def test_quick_add_empty(self, client):
        """Test adding empty thought fails"""
        response = client.post('/journal/quick-add',
            data=json.dumps({
                'content': '',
                'mood': ''
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 400
    
    def test_delete_entry(self, client, sample_journal_entry):
        """Test deleting a journal entry"""
        response = client.post(f'/journal/delete/{sample_journal_entry}',
            content_type='application/json'
        )
        
        assert response.status_code == 200
    
    def test_search(self, client, sample_journal_entry):
        """Test searching journal"""
        response = client.get('/journal/search?q=motivated')
        assert response.status_code == 200


class TestWorkspace:
    """Tests for workspace routes"""
    
    def test_workspace_index(self, client):
        """Test workspace page loads"""
        response = client.get('/')
        assert response.status_code == 200


class TestSettings:
    """Tests for settings routes"""
    
    def test_settings_page(self, client):
        """Test settings page loads"""
        response = client.get('/settings/')
        assert response.status_code == 200


class TestReferences:
    """Tests for reference library routes"""
    
    def test_library_index(self, client):
        """Test references library page loads"""
        response = client.get('/references/')
        assert response.status_code == 200
    
    def test_add_manual_lyrics(self, client):
        """Test manually adding lyrics"""
        response = client.post('/references/add-manual',
            data={
                'artist': 'Test Artist',
                'song': 'Test Song',
                'lyrics': "Line 1\nLine 2\nLine 3"
            }
        )
        
        # It redirects on success
        assert response.status_code == 302
        
    def test_view_file(self, client):
        """Test viewing a lyrics file"""
        # First add a file via API to ensure it exists
        client.post('/references/add-manual',
            data={
                'artist': 'ViewTest',
                'song': 'ViewSong',
                'lyrics': "Verse 1\nChecking the view\nMaking sure it works"
            }
        )
        
        # Filename is usually Artist - Song.txt
        filename = "ViewTest - ViewSong.txt"
        
        response = client.get(f'/references/view/{filename}')
        assert response.status_code == 200
        # Check if lyrics are present
        assert b"Checking the" in response.data  # Note: 'view' is wrapped in rhyme-highlight span
        # Check if analysis metrics are present (proving template works)
        assert b"Complexity Score" in response.data
