from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any

from ..services.scraper import LyricsScraper
from ..services.learning import StyleExtractor, VocabularyManager

router = APIRouter()
_scraper = LyricsScraper()
_style_extractor = StyleExtractor()
_vocab_manager = VocabularyManager()

class ScrapeRequest(BaseModel):
    artist: str
    max_songs: int = 3

@router.get("/learning/status")
async def get_learning_status() -> Dict[str, Any]:
    """Get the current learning dashboard metrics."""
    vocab_context = _vocab_manager.get_vocabulary_context()
    style_summary = _style_extractor.get_style_summary()
    
    return {
        "success": True,
        "vocabulary": {
            "favorites": vocab_context.get("favorites", []),
            "slangs": vocab_context.get("slangs", []),
            "most_used": vocab_context.get("most_used", [])[:15],
            "avoided": vocab_context.get("avoided", [])
        },
        "style": {
            "themes": style_summary.get("preferred_themes", []),
            "rhyme_preference": style_summary.get("rhyme_preference", "Not enough data"),
            "avg_line_length": style_summary.get("avg_line_length", 0)
        }
    }


def _process_learning_data(artist: str, max_songs: int):
    """Background task to fetch and learn."""
    try:
        results = _scraper.scrape_artist_songs(artist, max_songs=max_songs)
        
        all_lines = []
        all_words = []
        
        for song in results:
            text = song.get("lyrics", "")
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            all_lines.extend(lines)
            
            for line in lines:
                all_words.extend(line.lower().split())
                
        if all_lines:
            _style_extractor.learn_from_session(all_lines)
        if all_words:
            _vocab_manager.track_usage(all_words)
            
        print(f"[Learning System] Successfully learned from {len(results)} {artist} songs.")
        
    except Exception as e:
        print(f"[Learning System] Error scraping {artist}: {e}")

@router.post("/learning/scrape")
async def start_learning_scrape(data: ScrapeRequest, background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """Start scraping lyrics to feed into the learning model."""
    if not data.artist:
        raise HTTPException(status_code=400, detail="Artist name is required")
        
    background_tasks.add_task(_process_learning_data, data.artist, data.max_songs)
    
    return {
        "success": True,
        "message": f"Started background learning from {data.artist} ({data.max_songs} songs)."
    }
