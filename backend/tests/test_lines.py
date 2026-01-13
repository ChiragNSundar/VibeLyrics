"""
Line Router Tests
"""
import pytest
from httpx import AsyncClient


class TestLines:
    """Test line CRUD operations"""
    
    @pytest.fixture
    async def session_with_id(self, client: AsyncClient, sample_session_data):
        """Create a session and return its ID"""
        response = await client.post("/api/sessions", json=sample_session_data)
        return response.json()["session"]["id"]
    
    @pytest.mark.asyncio
    async def test_add_line(self, client: AsyncClient, session_with_id):
        """Test adding a line to a session"""
        response = await client.post("/api/lines", json={
            "session_id": session_with_id,
            "content": "I'm on top of the world tonight",
            "section": "Verse"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["line"]["user_input"] == "I'm on top of the world tonight"
        assert data["line"]["line_number"] == 1
        assert data["line"]["syllable_count"] > 0
    
    @pytest.mark.asyncio
    async def test_add_multiple_lines(self, client: AsyncClient, session_with_id):
        """Test adding multiple lines increments line_number"""
        lines = [
            "First line of the verse",
            "Second line follows",
            "Third line ends it"
        ]
        
        for i, content in enumerate(lines):
            response = await client.post("/api/lines", json={
                "session_id": session_with_id,
                "content": content,
                "section": "Verse"
            })
            data = response.json()
            assert data["line"]["line_number"] == i + 1
    
    @pytest.mark.asyncio
    async def test_add_line_invalid_session(self, client: AsyncClient):
        """Test adding line to non-existent session"""
        response = await client.post("/api/lines", json={
            "session_id": 99999,
            "content": "Test line",
            "section": "Verse"
        })
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_update_line(self, client: AsyncClient, session_with_id):
        """Test updating a line"""
        # Create line
        create_response = await client.post("/api/lines", json={
            "session_id": session_with_id,
            "content": "Original content",
            "section": "Verse"
        })
        line_id = create_response.json()["line"]["id"]
        
        # Update line
        response = await client.put(f"/api/lines/{line_id}", json={
            "content": "Updated content with more words"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["line"]["user_input"] == "Updated content with more words"
    
    @pytest.mark.asyncio
    async def test_delete_line(self, client: AsyncClient, session_with_id):
        """Test deleting a line"""
        # Create line
        create_response = await client.post("/api/lines", json={
            "session_id": session_with_id,
            "content": "Line to delete",
            "section": "Verse"
        })
        line_id = create_response.json()["line"]["id"]
        
        # Delete line
        response = await client.delete(f"/api/lines/{line_id}")
        assert response.status_code == 200
        assert response.json()["success"] is True
    
    @pytest.mark.asyncio
    async def test_delete_line_not_found(self, client: AsyncClient):
        """Test deleting non-existent line"""
        response = await client.delete("/api/lines/99999")
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_lines_appear_in_session(self, client: AsyncClient, session_with_id):
        """Test that lines appear when fetching session"""
        # Add lines
        await client.post("/api/lines", json={
            "session_id": session_with_id,
            "content": "Line one",
            "section": "Verse"
        })
        await client.post("/api/lines", json={
            "session_id": session_with_id,
            "content": "Line two",
            "section": "Chorus"
        })
        
        # Get session
        response = await client.get(f"/api/sessions/{session_with_id}")
        data = response.json()
        assert len(data["lines"]) == 2
        assert data["lines"][0]["user_input"] == "Line one"
        assert data["lines"][1]["user_input"] == "Line two"
