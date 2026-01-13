"""
Scraper Router
Endpoint for scraping lyrics
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_db
from ..services.scraper import LyricsScraper
from ..schemas.scraper import ScrapeRequest

router = APIRouter()
scraper = LyricsScraper()

@router.post("/scrape", response_model=dict)
async def scrape_lyrics(data: ScrapeRequest):
    """
    Search for and scrape lyrics for a given artist and song.
    """
    result = scraper.search_and_scrape(data.artist, data.title)
    
    if not result:
        return {
            "success": False,
            "error": "Lyrics not found"
        }
        
    return {
        "success": True,
        "data": result
    }
