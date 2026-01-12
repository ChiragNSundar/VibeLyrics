"""
Reference Lyrics Management
- Folder management
- File parsing
- Search
"""
import os
import re
from typing import List, Dict, Optional
from pathlib import Path


class FolderManager:
    """Manage reference lyrics folder"""
    
    BASE_DIR = "data/references"
    
    def __init__(self):
        os.makedirs(self.BASE_DIR, exist_ok=True)
    
    def list_all_files(self) -> List[Dict]:
        """List all reference files"""
        files = []
        
        for root, dirs, filenames in os.walk(self.BASE_DIR):
            for filename in filenames:
                if filename.endswith(('.txt', '.md', '.lyrics')):
                    path = os.path.join(root, filename)
                    rel_path = os.path.relpath(path, self.BASE_DIR)
                    
                    files.append({
                        "filename": filename,
                        "path": rel_path,
                        "size": os.path.getsize(path),
                        "artist": self._extract_artist(filename),
                        "title": self._extract_title(filename)
                    })
        
        return files
    
    def _extract_artist(self, filename: str) -> str:
        """Extract artist from filename"""
        base = filename.rsplit('.', 1)[0]
        if ' - ' in base:
            return base.split(' - ')[0]
        return "Unknown"
    
    def _extract_title(self, filename: str) -> str:
        """Extract title from filename"""
        base = filename.rsplit('.', 1)[0]
        if ' - ' in base:
            return base.split(' - ', 1)[1]
        return base
    
    def get_file_content(self, filename: str) -> Optional[str]:
        """Get file content"""
        path = os.path.join(self.BASE_DIR, filename)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        return None
    
    def add_lyrics_file(
        self, 
        content: str, 
        artist: str, 
        song_title: str,
        structured: bool = False
    ) -> str:
        """Add a new lyrics file"""
        filename = f"{artist} - {song_title}.txt"
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)  # Sanitize
        
        path = os.path.join(self.BASE_DIR, filename)
        
        with open(path, 'w', encoding='utf-8') as f:
            if structured:
                f.write(f"# {song_title}\n")
                f.write(f"## Artist: {artist}\n\n")
            f.write(content)
        
        return filename
    
    def delete_file(self, filename: str) -> bool:
        """Delete a file"""
        path = os.path.join(self.BASE_DIR, filename)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False
    
    def search_files(self, query: str) -> List[Dict]:
        """Search files by content or name"""
        query_lower = query.lower()
        results = []
        
        for file_info in self.list_all_files():
            # Search in filename
            if query_lower in file_info["filename"].lower():
                results.append(file_info)
                continue
            
            # Search in content
            content = self.get_file_content(file_info["path"])
            if content and query_lower in content.lower():
                results.append(file_info)
        
        return results
    
    def get_statistics(self) -> Dict:
        """Get folder statistics"""
        files = self.list_all_files()
        total_size = sum(f["size"] for f in files)
        artists = set(f["artist"] for f in files)
        
        return {
            "total_files": len(files),
            "total_size_kb": round(total_size / 1024, 1),
            "unique_artists": len(artists)
        }


class TxtParser:
    """Parse plain text lyrics"""
    
    def parse(self, content: str) -> Dict:
        """Parse lyrics content"""
        lines = [l.strip() for l in content.split('\n') if l.strip()]
        
        return {
            "all_lines": lines,
            "line_count": len(lines)
        }
    
    def analyze_structure(self, content: str) -> Dict:
        """Analyze lyrics structure"""
        lines = content.split('\n')
        
        sections = []
        current_section = None
        section_lines = []
        
        section_markers = ['[Verse', '[Chorus', '[Bridge', '[Hook', '[Outro', '[Intro']
        
        for line in lines:
            line = line.strip()
            
            # Check for section marker
            is_section = False
            for marker in section_markers:
                if line.lower().startswith(marker.lower()):
                    if current_section:
                        sections.append({
                            "name": current_section,
                            "line_count": len(section_lines)
                        })
                    current_section = line.strip('[]')
                    section_lines = []
                    is_section = True
                    break
            
            if not is_section and line:
                section_lines.append(line)
        
        if current_section:
            sections.append({
                "name": current_section,
                "line_count": len(section_lines)
            })
        
        return {
            "sections": sections,
            "section_count": len(sections)
        }


class StructuredParser:
    """Parse structured lyrics files (with metadata)"""
    
    def is_structured(self, content: str) -> bool:
        """Check if content is structured format"""
        return content.strip().startswith('#')
    
    def parse(self, content: str) -> Dict:
        """Parse structured content"""
        lines = content.split('\n')
        
        metadata = {}
        lyrics_lines = []
        sections = []
        current_section = {"name": "Intro", "lines": []}
        
        for line in lines:
            line = line.strip()
            
            # Metadata (## Key: Value)
            if line.startswith('## '):
                if ':' in line:
                    key, value = line[3:].split(':', 1)
                    metadata[key.strip().lower()] = value.strip()
                continue
            
            # Title (# Title)
            if line.startswith('# '):
                metadata['title'] = line[2:]
                continue
            
            # Section marker
            if line.startswith('[') and line.endswith(']'):
                if current_section["lines"]:
                    sections.append(current_section)
                current_section = {"name": line[1:-1], "lines": []}
                continue
            
            # Regular line
            if line:
                current_section["lines"].append(line)
                lyrics_lines.append(line)
        
        if current_section["lines"]:
            sections.append(current_section)
        
        return {
            "metadata": metadata,
            "lyrics": {
                "all_lines": lyrics_lines,
                "sections": sections
            }
        }
