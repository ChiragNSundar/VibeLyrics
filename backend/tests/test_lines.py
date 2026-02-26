"""
Line Router Tests — updated for v2.4.x response format
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
        """Test adding a line returns enriched data with all_lines"""
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
        # v2.4.x: complexity_score should be computed
        assert "complexity_score" in data["line"]
        assert data["line"]["complexity_score"] >= 0
        # v2.4.x: all_lines returned for cross-line highlighting
        assert "all_lines" in data
        assert len(data["all_lines"]) == 1

    @pytest.mark.asyncio
    async def test_add_empty_line_rejected(self, client: AsyncClient, session_with_id):
        """Test that empty/whitespace-only content is rejected"""
        response = await client.post("/api/lines", json={
            "session_id": session_with_id,
            "content": "   ",
            "section": "Verse"
        })
        assert response.status_code == 400

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
            # all_lines should grow each time
            assert len(data["all_lines"]) == i + 1

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
        """Test updating a line returns refreshed highlights"""
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
        # v2.4.x: all_lines returned on update too
        assert "all_lines" in data

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
        """Test that lines appear when fetching session with has_internal_rhyme backfill"""
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
        # v2.4.x: has_internal_rhyme should be backfilled
        assert "has_internal_rhyme" in data["lines"][0]

    @pytest.mark.asyncio
    async def test_rhyme_highlighting_across_lines(self, client: AsyncClient, session_with_id):
        """Test that rhyming lines get highlighted HTML"""
        await client.post("/api/lines", json={
            "session_id": session_with_id,
            "content": "I see the light",
            "section": "Verse"
        })
        response = await client.post("/api/lines", json={
            "session_id": session_with_id,
            "content": "Everything is right",
            "section": "Verse"
        })
        data = response.json()
        # Both lines should have highlighted_html after cross-line analysis
        for line in data["all_lines"]:
            assert "highlighted_html" in line
