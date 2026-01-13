"""
Session Router Tests
"""
import pytest
from httpx import AsyncClient


class TestSessions:
    """Test session CRUD operations"""
    
    @pytest.mark.asyncio
    async def test_list_sessions_empty(self, client: AsyncClient):
        """Test listing sessions when empty"""
        response = await client.get("/api/sessions")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["sessions"] == []
    
    @pytest.mark.asyncio
    async def test_create_session(self, client: AsyncClient, sample_session_data):
        """Test creating a new session"""
        response = await client.post("/api/sessions", json=sample_session_data)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["session"]["title"] == "Test Session"
        assert data["session"]["bpm"] == 120
        assert data["session"]["mood"] == "confident"
    
    @pytest.mark.asyncio
    async def test_create_session_defaults(self, client: AsyncClient):
        """Test creating session with defaults"""
        response = await client.post("/api/sessions", json={})
        assert response.status_code == 200
        data = response.json()
        assert data["session"]["title"] == "Untitled"
        assert data["session"]["bpm"] == 140
    
    @pytest.mark.asyncio
    async def test_get_session(self, client: AsyncClient, sample_session_data):
        """Test getting a session by ID"""
        # Create session
        create_response = await client.post("/api/sessions", json=sample_session_data)
        session_id = create_response.json()["session"]["id"]
        
        # Get session
        response = await client.get(f"/api/sessions/{session_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["session"]["id"] == session_id
        assert data["lines"] == []
    
    @pytest.mark.asyncio
    async def test_get_session_not_found(self, client: AsyncClient):
        """Test getting non-existent session"""
        response = await client.get("/api/sessions/99999")
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_update_session(self, client: AsyncClient, sample_session_data):
        """Test updating a session"""
        # Create session
        create_response = await client.post("/api/sessions", json=sample_session_data)
        session_id = create_response.json()["session"]["id"]
        
        # Update session
        response = await client.put(
            f"/api/sessions/{session_id}",
            json={"title": "Updated Title", "bpm": 150}
        )
        assert response.status_code == 200
        assert response.json()["success"] is True
        
        # Verify update
        get_response = await client.get(f"/api/sessions/{session_id}")
        data = get_response.json()
        assert data["session"]["title"] == "Updated Title"
        assert data["session"]["bpm"] == 150
    
    @pytest.mark.asyncio
    async def test_delete_session(self, client: AsyncClient, sample_session_data):
        """Test deleting a session"""
        # Create session
        create_response = await client.post("/api/sessions", json=sample_session_data)
        session_id = create_response.json()["session"]["id"]
        
        # Delete session
        response = await client.delete(f"/api/sessions/{session_id}")
        assert response.status_code == 200
        assert response.json()["success"] is True
        
        # Verify deletion
        get_response = await client.get(f"/api/sessions/{session_id}")
        assert get_response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_list_sessions(self, client: AsyncClient):
        """Test listing multiple sessions"""
        # Create multiple sessions
        for i in range(3):
            await client.post("/api/sessions", json={"title": f"Session {i}"})
        
        response = await client.get("/api/sessions")
        assert response.status_code == 200
        data = response.json()
        assert len(data["sessions"]) == 3
