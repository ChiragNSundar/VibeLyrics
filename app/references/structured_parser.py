"""
Structured Parser
Parses lyrics files with YAML frontmatter metadata
"""
import re
from typing import Dict, List, Optional
from datetime import datetime

from .txt_parser import TxtParser


class StructuredParser:
    """
    Parses structured lyrics files with YAML frontmatter
    
    Expected format:
    ---
    artist: Kendrick Lamar
    song: DNA
    album: DAMN.
    year: 2017
    genre: hip-hop
    bpm: 140
    ---
    
    [Verse 1]
    Lyrics here...
    """
    
    def __init__(self):
        self.txt_parser = TxtParser()
        self.frontmatter_pattern = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)
    
    def parse(self, content: str) -> Dict:
        """
        Parse structured lyrics file
        """
        result = {
            "metadata": {},
            "lyrics": {},
            "raw_content": content
        }
        
        # Extract frontmatter if present
        frontmatter_match = self.frontmatter_pattern.match(content)
        
        if frontmatter_match:
            frontmatter = frontmatter_match.group(1)
            result["metadata"] = self._parse_frontmatter(frontmatter)
            
            # Get lyrics content after frontmatter
            lyrics_content = content[frontmatter_match.end():]
        else:
            lyrics_content = content
        
        # Parse the lyrics content
        result["lyrics"] = self.txt_parser.parse(lyrics_content)
        
        # Merge metadata
        if result["metadata"].get("artist"):
            result["lyrics"]["artist"] = result["metadata"]["artist"]
        if result["metadata"].get("song"):
            result["lyrics"]["song"] = result["metadata"]["song"]
        
        return result
    
    def _parse_frontmatter(self, frontmatter: str) -> Dict:
        """Parse YAML-like frontmatter"""
        metadata = {}
        
        for line in frontmatter.split('\n'):
            line = line.strip()
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()
                
                # Convert known numeric fields
                if key in ['year', 'bpm']:
                    try:
                        value = int(value)
                    except ValueError:
                        pass
                
                # Handle lists (comma-separated)
                if key in ['tags', 'themes', 'features']:
                    value = [v.strip() for v in value.split(',')]
                
                metadata[key] = value
        
        return metadata
    
    def create_structured_content(
        self,
        lyrics: str,
        artist: str,
        song: str,
        album: Optional[str] = None,
        year: Optional[int] = None,
        genre: Optional[str] = None,
        bpm: Optional[int] = None,
        tags: Optional[List[str]] = None
    ) -> str:
        """
        Create a structured lyrics file content
        """
        frontmatter_lines = [
            "---",
            f"artist: {artist}",
            f"song: {song}",
        ]
        
        if album:
            frontmatter_lines.append(f"album: {album}")
        if year:
            frontmatter_lines.append(f"year: {year}")
        if genre:
            frontmatter_lines.append(f"genre: {genre}")
        if bpm:
            frontmatter_lines.append(f"bpm: {bpm}")
        if tags:
            frontmatter_lines.append(f"tags: {', '.join(tags)}")
        
        frontmatter_lines.append(f"added: {datetime.now().strftime('%Y-%m-%d')}")
        frontmatter_lines.append("---")
        frontmatter_lines.append("")
        
        return '\n'.join(frontmatter_lines) + lyrics
    
    def extract_style_notes(self, parsed: Dict) -> Dict:
        """
        Extract style notes from parsed lyrics for AI context
        """
        metadata = parsed.get("metadata", {})
        lyrics = parsed.get("lyrics", {})
        
        style_notes = {
            "artist": metadata.get("artist") or lyrics.get("artist"),
            "song": metadata.get("song") or lyrics.get("song"),
            "genre": metadata.get("genre", "hip-hop"),
            "bpm": metadata.get("bpm"),
            "themes": metadata.get("themes", []),
            "line_count": len(lyrics.get("all_lines", [])),
            "sections": [s["name"] for s in lyrics.get("sections", [])],
        }
        
        # Analyze some actual content
        all_lines = lyrics.get("all_lines", [])
        if all_lines:
            # Get average line length
            avg_words = sum(len(line.split()) for line in all_lines) / len(all_lines)
            style_notes["avg_words_per_line"] = round(avg_words, 1)
            
            # Sample lines for reference
            style_notes["sample_lines"] = all_lines[:4]
        
        return style_notes
    
    def is_structured(self, content: str) -> bool:
        """Check if content has structured frontmatter"""
        return bool(self.frontmatter_pattern.match(content))
    
    def get_metadata_only(self, content: str) -> Dict:
        """Get just the metadata without parsing full lyrics"""
        frontmatter_match = self.frontmatter_pattern.match(content)
        
        if frontmatter_match:
            return self._parse_frontmatter(frontmatter_match.group(1))
        
        return {}


# Template for adding new reference lyrics
STRUCTURED_TEMPLATE = """---
artist: 
song: 
album: 
year: 
genre: hip-hop
bpm: 
tags: 
notes: 
---

[Verse 1]


[Chorus]


[Verse 2]

"""
