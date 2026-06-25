"""
Lyrics Scraper Service
Scrapes lyrics from web sources (AZLyrics, etc.) without API keys.
Uses DuckDuckGo for search to find the correct URL.
"""
import requests
from bs4 import BeautifulSoup
try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS
from typing import Optional, Dict
import re
import random
import time
import os
import json

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SCRAPED_TRACKS_FILE = os.path.join(ROOT_DIR, "data", "scraped_songs.json")

def get_scraped_urls() -> set:
    if os.path.exists(SCRAPED_TRACKS_FILE):
        try:
            with open(SCRAPED_TRACKS_FILE, 'r') as f:
                urls = json.load(f)
                if isinstance(urls, list):
                    return set(urls)
        except Exception:
            pass
    return set()

def save_scraped_url(url: str):
    urls = list(get_scraped_urls())
    if url not in urls:
        urls.append(url)
        os.makedirs(os.path.dirname(SCRAPED_TRACKS_FILE), exist_ok=True)
        try:
            with open(SCRAPED_TRACKS_FILE, 'w') as f:
                json.dump(urls, f, indent=2)
        except Exception:
            pass

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
        # Search generally to find azlyrics or lyricsmania links
        query = f"{artist} {title} lyrics"
        
        try:
            # Search using DuckDuckGo
            results = list(self.ddgs.text(query, max_results=5))
            
            if not results:
                print("No search results found.")
                return None
                
            scraped_urls = get_scraped_urls()
            # Try to scrape the first valid result
            for result in results:
                url = result.get('link') or result.get('href', '')
                if url in scraped_urls:
                    print(f"Skipping already scraped song: {url}")
                    continue
                
                if 'lyricsmania.com/' in url:
                    print(f"Scraping from LyricsMania: {url}")
                    lyrics = self._scrape_lyricsmania(url)
                    if lyrics:
                        save_scraped_url(url)
                        return {
                            "title": title,
                            "artist": artist,
                            "lyrics": lyrics,
                            "source": url
                        }
                elif 'azlyrics.com/lyrics' in url:
                    print(f"Scraping from AZLyrics: {url}")
                    lyrics = self._scrape_azlyrics(url)
                    if lyrics:
                        save_scraped_url(url)
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

    async def scrape_artist_songs_stream(self, artist: str, max_songs: int = 3, era: Optional[str] = None):
        """
        Search and scrape multiple songs for a specific artist, optionally filtered by era.
        Yields progress messages and final results for Server-Sent Events (SSE).
        """
        era_term = f" {era}" if era else ""
        
        # Primary search on LyricsMania (since it doesn't block)
        query = f"\"{artist}\"{era_term} lyrics site:lyricsmania.com"
        yield {"type": "progress", "msg": f"Searching DuckDuckGo for: {query}"}
        
        try:
            # Search using DuckDuckGo
            results = list(self.ddgs.text(query, max_results=max_songs + 15))
            
            # Fallback to AZLyrics if no LyricsMania results
            if not results:
                query = f"\"{artist}\"{era_term} lyrics site:azlyrics.com"
                yield {"type": "progress", "msg": f"No LyricsMania results. Falling back to: {query}"}
                results = list(self.ddgs.text(query, max_results=max_songs + 15))
                
            if not results:
                yield {"type": "error", "msg": "No search results found."}
                return
                
            yield {"type": "progress", "msg": f"Found potential matches. Beginning extraction..."}
            
            seen_urls = set()
            scraped_urls = get_scraped_urls()
            results_out = []
            
            # Generate slugs for matching
            slug_underscore = artist.lower().replace(' ', '_')
            slug_plain = artist.lower().replace(' ', '')
            
            for result in results:
                if len(results_out) >= max_songs:
                    break
                    
                url = result.get('link') or result.get('href', '')
                if url in seen_urls:
                    continue
                    
                is_valid = False
                is_lyricsmania = 'lyricsmania.com/' in url
                is_azlyrics = 'azlyrics.com/lyrics' in url
                
                if is_lyricsmania:
                    if slug_underscore in url.lower() or slug_plain in url.lower():
                        is_valid = True
                elif is_azlyrics:
                    if f'/lyrics/{slug_plain}/' in url.lower():
                        is_valid = True
                        
                if is_valid:
                    if url in scraped_urls:
                        yield {"type": "progress", "msg": f"Skipping already scraped track: {url}"}
                        continue
                    seen_urls.add(url)
                    
                    # Extract title from URL
                    import re
                    title_match = re.search(r'/([^/_]+)_lyrics', url) # LyricsMania format
                    if not title_match:
                        title_match = re.search(r'/([^/]+)\.html$', url) # AZLyrics or general format
                    title = title_match.group(1).replace('-', ' ').replace('_', ' ').title() if title_match else "Unknown Track"
                    
                    yield {"type": "progress", "msg": f"Scraping lyrics for: {title}..."}
                    
                    lyrics = self._scrape_lyricsmania(url) if is_lyricsmania else self._scrape_azlyrics(url)
                    if lyrics:
                        save_scraped_url(url)
                        results_out.append({
                            "title": title,
                            "artist": artist,
                            "lyrics": lyrics,
                            "source": url
                        })
                        yield {"type": "success", "msg": f"Successfully extracted: {title}"}
                    else:
                        yield {"type": "warning", "msg": f"Failed to extract lyrics from {url}"}
                        
                    time.sleep(random.uniform(1.5, 3.0))
            
            yield {"type": "done", "results": results_out}
            
        except Exception as e:
            yield {"type": "error", "msg": f"Artist scraping error: {str(e)}"}

    def _scrape_azlyrics(self, url: str) -> Optional[str]:
        """Scrape lyrics specifically from AZLyrics HTML structure."""
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check for bot detection page block
            if soup.title and "request for access" in soup.title.string.lower():
                print(f"[Scraper] AZLyrics blocked access (CAPTCHA) for: {url}")
                return None
            
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

    def _scrape_lyricsmania(self, url: str) -> Optional[str]:
        """Scrape lyrics from LyricsMania HTML structure."""
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the lyrics-body container
            lyrics_div = soup.find('div', class_='lyrics-body')
            if lyrics_div:
                text = lyrics_div.get_text(strip=True, separator='\n')
                # Clean up footers
                text = re.sub(r'Lyrics licensed by.*', '', text, flags=re.IGNORECASE)
                return text.strip()
                
            return None
        except Exception as e:
            print(f"LyricsMania parse error: {e}")
            return None
