"""
Tests for Rhyme Sandbox API Endpoints
"""
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_extract_phonetics_english(client: AsyncClient):
    """Test extracting English phonetics via API"""
    response = await client.post("/api/rhymes/extract", json={"word": "rapper", "language": "en"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["word"] == "rapper"
    assert "vowel_sequence" in data
    assert "exact_key" in data
    assert data["syllable_count"] == 2

@pytest.mark.asyncio
async def test_extract_phonetics_hindi(client: AsyncClient):
    """Test extracting Hindi phonetics via API"""
    response = await client.post("/api/rhymes/extract", json={"word": "अपना", "language": "hi"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["word"] == "अपना"
    assert data["vowel_sequence"] == "a-aa"
    assert data["syllable_count"] == 2

@pytest.mark.asyncio
async def test_extract_phonetics_kannada(client: AsyncClient):
    """Test extracting Kannada phonetics via API"""
    response = await client.post("/api/rhymes/extract", json={"word": "ಬಂಗಾರ", "language": "kn"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["word"] == "ಬಂಗಾರ"
    assert data["vowel_sequence"] == "a-aa-a"
    assert data["syllable_count"] == 3

@pytest.mark.asyncio
async def test_register_phonetics(client: AsyncClient):
    """Test registering phonetic overrides via API"""
    register_payload = {
        "word": "customword",
        "language": "en",
        "vowel_sequence": "AH-OW",
        "exact_key": "OW",
        "syllable_count": 2,
        "is_slang": True
    }
    response = await client.post("/api/rhymes/register", json=register_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "registered" in data["message"]
    
    # Verify updating the registered word
    register_payload["vowel_sequence"] = "AH-OW-OW"
    register_payload["syllable_count"] = 3
    response_update = await client.post("/api/rhymes/register", json=register_payload)
    assert response_update.status_code == 200
    data_update = response_update.json()
    assert data_update["success"] is True
