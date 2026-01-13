"""
Lyrics Scraper Service
Scrapes lyrics from web sources (AZLyrics, etc.) without API keys.
Uses DuckDuckGo for search to find the correct URL.
"""
import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS
from typing import Optional, Dict
import re
import random
import time

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def clean_lyrics(text: str) -> str:
    """Clean up scraped lyrics text."""
    # Remove container text like "Submit Corrections"
    text = re.sub(r'Submit Corrections', '', text)
    text = re.sub(r'Writer\(s\):.*', '', text)
    return text.strip()

class LyricsScraper:
    def __init__(self):
        self.ddgs = DDGS()

    def search_and_scrape(self, artist: str, title: str) -> Optional[Dict[str, str]]:
        """
        Search for song lyrics and scrape them.
        Returns dict with title, artist, lyrics, and source URL.
        """
        query = f"{artist} {title} lyrics site:azlyrics.com"
        
        try:
            # Search using DuckDuckGo
            results = list(self.ddgs.text(query, max_results=3))
            
            if not results:
                print("No search results found.")
                return None
                
            # Try to scrape the first valid AZLyrics result
            for result in results:
                url = result.get('href')
                if 'azlyrics.com/lyrics' in url:
                    print(f"Scraping {url}...")
                    lyrics = self._scrape_azlyrics(url)
                    if lyrics:
                        return {
                            "title": title,
                            "artist": artist,
                            "lyrics": lyrics,
                            "source": url
                        }
                    
                    # Random delay to be polite
                    time.sleep(random.uniform(1, 3))
            
            return None

        except Exception as e:
            print(f"Scraping error: {e}")
            return None

    def _scrape_azlyrics(self, url: str) -> Optional[str]:
        """Scrape lyrics specifically from AZLyrics HTML structure."""
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # AZLyrics structure is tricky, lyrics are in a div with no class
            # but usually between usage comments
            # Usage: <!-- Usage of azlyrics.com content by any third-party... -->
            
            # Find the main container
            main_div = soup.find('div', class_='col-xs-12 col-lg-8 text-center')
            if not main_div:
                return None
                
            # Iterate divs to find the one with lyrics (no class, not div.div-share)
            for div in main_div.find_all('div', recursive=False):
                if not div.attrs and not div.get('class'):
                    text = div.get_text(strip=True, separator='\n')
                    return clean_lyrics(text)
                    
            return None

        except Exception as e:
            print(f"AZLyrics parse error: {e}")
            return None
