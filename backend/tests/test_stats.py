"""
Stats Router Tests
"""
import pytest
from httpx import AsyncClient


class TestStats:
    """Test stats endpoints"""
    
    @pytest.mark.asyncio
    async def test_get_overview_empty(self, client: AsyncClient):
        """Test getting stats when empty"""
        response = await client.get("/api/stats/")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["stats"]["total_sessions"] == 0
        assert data["stats"]["total_lines"] == 0
    
    @pytest.mark.asyncio
    async def test_get_overview_with_data(self, client: AsyncClient, sample_session_data):
        """Test stats after adding data"""
        # Create session
        await client.post("/api/sessions", json=sample_session_data)
        
        response = await client.get("/api/stats/")
        data = response.json()
        assert data["stats"]["total_sessions"] == 1
    
    @pytest.mark.asyncio
    async def test_get_history(self, client: AsyncClient):
        """Test getting history data"""
        response = await client.get("/api/stats/history")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "daily_lines" in data
        assert len(data["daily_lines"]) == 30
    
    @pytest.mark.asyncio
    async def test_get_achievements_empty(self, client: AsyncClient):
        """Test achievements when no progress"""
        response = await client.get("/api/stats/achievements")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["achievements"] == []
        assert data["total_lines"] == 0
