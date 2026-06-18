import pytest
from fastapi.testclient import TestClient
from backend.main import app

def test_websocket_invalid_json():
    client = TestClient(app)
    with client.websocket_connect("/api/ws/suggest") as websocket:
        websocket.send_text("invalid json")
        data = websocket.receive_json()
        assert data["type"] == "error"
        assert "Invalid JSON payload" in data["message"]

def test_websocket_analyze():
    client = TestClient(app)
    with client.websocket_connect("/api/ws/suggest") as websocket:
        websocket.send_json({
            "type": "analyze",
            "content": "Double up the check and get the money"
        })
        data = websocket.receive_json()
        assert data["type"] == "analysis_result"
        assert "syllables" in data
        assert "stress" in data
        assert "has_internal" in data
        assert "complexity" in data
        assert data["syllables"] > 0
