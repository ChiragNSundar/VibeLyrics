"""
Tests for Lyrics Scraper
"""
import pytest
from unittest.mock import MagicMock, patch
from backend.services.scraper import LyricsScraper

@pytest.fixture
def scraper():
    return LyricsScraper()

def test_clean_lyrics():
    from backend.services.scraper import clean_lyrics
    raw = "Hello world\nSubmit Corrections"
    cleaned = clean_lyrics(raw)
    assert "Submit Corrections" not in cleaned
    assert cleaned == "Hello world"

@patch('backend.services.scraper.DDGS')
def test_search_and_scrape_no_results(mock_ddgs, scraper):
    # Mock search returning empty
    mock_ddgs.return_value.text.return_value = []
    
    result = scraper.search_and_scrape("Artist", "Song")
    assert result is None

@patch('backend.services.scraper.DDGS')
@patch('backend.services.scraper.requests.get')
def test_search_and_scrape_success(mock_get, mock_ddgs, scraper):
    # Mock search results
    mock_ddgs.return_value.text.return_value = [
        {"href": "https://www.azlyrics.com/lyrics/artist/song.html"}
    ]
    
    # Mock HTML response
    mock_response = MagicMock()
    mock_response.text = """
    <div class="col-xs-12 col-lg-8 text-center">
        <div>
            <!-- Usage of azlyrics.com content by any third-party... -->
            La la la
            Lyrics here
        </div>
    </div>
    """
    mock_get.return_value = mock_response
    
    result = scraper.search_and_scrape("Artist", "Song")
    if result:
        assert result['lyrics'] == "La la la\n            Lyrics here"
        assert result['source'] == "https://www.azlyrics.com/lyrics/artist/song.html"
