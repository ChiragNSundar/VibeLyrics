"""
Genius Scraper
Fetches lyrics from Genius API
"""
import re
from typing import Optional, List, Dict
import requests
from bs4 import BeautifulSoup

from app.config import Config
from .folder_manager import FolderManager
from .structured_parser import StructuredParser


class GeniusScraper:
    """Scrapes lyrics from Genius using their API"""
    
    BASE_URL = "https://api.genius.com"
    
    def __init__(self):
        self.access_token = Config.GENIUS_ACCESS_TOKEN
        self.folder_manager = FolderManager()
        self.structured_parser = StructuredParser()
        
        self.headers = {
            "Authorization": f"Bearer {self.access_token}"
        } if self.access_token else {}
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make authenticated request to Genius API"""
        if not self.access_token:
            raise ValueError("Genius API access token not configured")
        
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Genius API error: {e}")
            return None
    
    def search(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search for songs on Genius
        """
        data = self._make_request("/search", params={"q": query})
        
        if not data:
            return []
        
        results = []
        hits = data.get("response", {}).get("hits", [])[:limit]
        
        for hit in hits:
            song = hit.get("result", {})
            results.append({
                "id": song.get("id"),
                "title": song.get("title"),
                "artist": song.get("primary_artist", {}).get("name"),
                "url": song.get("url"),
                "thumbnail": song.get("song_art_image_thumbnail_url"),
                "full_title": song.get("full_title")
            })
        
        return results
    
    def get_song(self, song_id: int) -> Optional[Dict]:
        """
        Get song details by ID
        """
        data = self._make_request(f"/songs/{song_id}")
        
        if not data:
            return None
        
        song = data.get("response", {}).get("song", {})
        
        return {
            "id": song.get("id"),
            "title": song.get("title"),
            "artist": song.get("primary_artist", {}).get("name"),
            "album": song.get("album", {}).get("name") if song.get("album") else None,
            "release_date": song.get("release_date"),
            "url": song.get("url"),
            "description": song.get("description", {}).get("plain") if song.get("description") else None,
        }
    
    def get_lyrics(self, song_url: str) -> Optional[str]:
        """
        Scrape lyrics from a Genius song page
        Note: Genius API doesn't provide lyrics directly, so we scrape the page
        """
        try:
            response = requests.get(song_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Genius uses data-lyrics-container for lyrics
            lyrics_containers = soup.find_all('div', {'data-lyrics-container': 'true'})
            
            if not lyrics_containers:
                # Fallback to old selector
                lyrics_div = soup.find('div', class_='lyrics')
                if lyrics_div:
                    return lyrics_div.get_text(separator='\n').strip()
                return None
            
            lyrics_parts = []
            for container in lyrics_containers:
                # Extract text while preserving line breaks
                for br in container.find_all('br'):
                    br.replace_with('\n')
                
                text = container.get_text(separator='')
                lyrics_parts.append(text)
            
            lyrics = '\n'.join(lyrics_parts)
            
            # Clean up the lyrics
            lyrics = self._clean_lyrics(lyrics)
            
            return lyrics
            
        except requests.RequestException as e:
            print(f"Error fetching lyrics: {e}")
            return None
    
    def _clean_lyrics(self, lyrics: str) -> str:
        """Clean up scraped lyrics"""
        # Remove annotations in brackets that aren't section headers
        lyrics = re.sub(r'\[[^\]]*Verse\s*\d*[^\]]*\]', r'\n[Verse]\n', lyrics, flags=re.IGNORECASE)
        lyrics = re.sub(r'\[[^\]]*Chorus[^\]]*\]', r'\n[Chorus]\n', lyrics, flags=re.IGNORECASE)
        lyrics = re.sub(r'\[[^\]]*Hook[^\]]*\]', r'\n[Hook]\n', lyrics, flags=re.IGNORECASE)
        lyrics = re.sub(r'\[[^\]]*Bridge[^\]]*\]', r'\n[Bridge]\n', lyrics, flags=re.IGNORECASE)
        lyrics = re.sub(r'\[[^\]]*Outro[^\]]*\]', r'\n[Outro]\n', lyrics, flags=re.IGNORECASE)
        lyrics = re.sub(r'\[[^\]]*Intro[^\]]*\]', r'\n[Intro]\n', lyrics, flags=re.IGNORECASE)
        
        # Remove contributor annotations
        lyrics = re.sub(r'\d+\s*Contributors?.*?Lyrics', '', lyrics, flags=re.IGNORECASE)
        lyrics = re.sub(r'Embed$', '', lyrics)
        lyrics = re.sub(r'You might also like', '', lyrics)
        
        # Clean up multiple newlines
        lyrics = re.sub(r'\n{3,}', '\n\n', lyrics)
        
        return lyrics.strip()
    
    def search_and_save(
        self,
        query: str,
        save_first: bool = True
    ) -> Optional[Dict]:
        """
        Search for a song and optionally save the first result
        """
        results = self.search(query, limit=1 if save_first else 5)
        
        if not results:
            return None
        
        song = results[0]
        
        if save_first and song.get("url"):
            lyrics = self.get_lyrics(song["url"])
            
            if lyrics:
                # Create structured content
                content = self.structured_parser.create_structured_content(
                    lyrics=lyrics,
                    artist=song["artist"],
                    song=song["title"],
                    tags=["genius", "reference"]
                )
                
                # Save to folder
                filepath = self.folder_manager.add_lyrics_file(
                    content=lyrics,
                    artist=song["artist"],
                    song_title=song["title"],
                    structured=True
                )
                
                song["saved_path"] = filepath
                song["lyrics"] = lyrics
        
        return song
    
    def get_artist_songs(self, artist_name: str, limit: int = 10) -> List[Dict]:
        """
        Get top songs by an artist
        """
        # Search for artist first
        data = self._make_request("/search", params={"q": artist_name})
        
        if not data:
            return []
        
        hits = data.get("response", {}).get("hits", [])
        
        # Filter to get songs by the specific artist
        songs = []
        for hit in hits:
            song = hit.get("result", {})
            artist = song.get("primary_artist", {}).get("name", "")
            
            if artist_name.lower() in artist.lower():
                songs.append({
                    "id": song.get("id"),
                    "title": song.get("title"),
                    "artist": artist,
                    "url": song.get("url")
                })
            
            if len(songs) >= limit:
                break
        
        return songs
    
    def is_configured(self) -> bool:
        """Check if Genius API is configured"""
        return bool(self.access_token)
