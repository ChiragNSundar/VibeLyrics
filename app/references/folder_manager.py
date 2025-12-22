"""
Folder Manager
Manages the reference lyrics folder
"""
import os
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

from app.config import Config


class FolderManager:
    """Manages the reference lyrics folder"""
    
    def __init__(self):
        self.references_path = Config.REFERENCES_PATH
        self._ensure_folder_exists()
    
    def _ensure_folder_exists(self):
        """Ensure the references folder exists"""
        self.references_path.mkdir(parents=True, exist_ok=True)
    
    def list_all_files(self) -> List[Dict]:
        """List all lyrics files in the references folder"""
        files = []
        
        for file_path in self.references_path.rglob("*"):
            if file_path.is_file() and file_path.suffix in ['.txt', '.md', '.lyrics']:
                stat = file_path.stat()
                files.append({
                    "name": file_path.stem,
                    "path": str(file_path),
                    "relative_path": str(file_path.relative_to(self.references_path)),
                    "extension": file_path.suffix,
                    "size_bytes": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
        
        return sorted(files, key=lambda x: x["name"])
    
    def get_file_content(self, filename: str) -> Optional[str]:
        """Get content of a specific file"""
        # Try exact path first
        file_path = self.references_path / filename
        
        if not file_path.exists():
            # Search for file
            for path in self.references_path.rglob(f"*{filename}*"):
                if path.is_file():
                    file_path = path
                    break
        
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except UnicodeDecodeError:
                # Try with different encoding
                with open(file_path, 'r', encoding='latin-1') as f:
                    return f.read()
        
        return None
    
    def add_lyrics_file(
        self,
        content: str,
        artist: str,
        song_title: str,
        structured: bool = True
    ) -> str:
        """Add a new lyrics file to the folder"""
        # Create safe filename
        safe_artist = "".join(c for c in artist if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_title = "".join(c for c in song_title if c.isalnum() or c in (' ', '-', '_')).strip()
        
        filename = f"{safe_artist} - {safe_title}.txt"
        file_path = self.references_path / filename
        
        # Add structured header if requested
        if structured:
            header = f"""---
artist: {artist}
song: {song_title}
added: {datetime.now().isoformat()}
---

"""
            content = header + content
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return str(file_path)
    
    def delete_file(self, filename: str) -> bool:
        """Delete a lyrics file"""
        file_path = self.references_path / filename
        
        if file_path.exists():
            file_path.unlink()
            return True
        
        return False
    
    def search_files(self, query: str) -> List[Dict]:
        """Search for files by name or content"""
        query_lower = query.lower()
        results = []
        
        for file_info in self.list_all_files():
            # Search in filename
            if query_lower in file_info["name"].lower():
                file_info["match_type"] = "filename"
                results.append(file_info)
                continue
            
            # Search in content
            content = self.get_file_content(file_info["relative_path"])
            if content and query_lower in content.lower():
                file_info["match_type"] = "content"
                results.append(file_info)
        
        return results
    
    def create_artist_folder(self, artist: str) -> str:
        """Create a subfolder for an artist"""
        safe_artist = "".join(c for c in artist if c.isalnum() or c in (' ', '-', '_')).strip()
        artist_path = self.references_path / safe_artist
        artist_path.mkdir(exist_ok=True)
        return str(artist_path)
    
    def get_statistics(self) -> Dict:
        """Get statistics about the reference library"""
        files = self.list_all_files()
        
        total_size = sum(f["size_bytes"] for f in files)
        
        # Count by extension
        by_extension = {}
        for f in files:
            ext = f["extension"]
            by_extension[ext] = by_extension.get(ext, 0) + 1
        
        return {
            "total_files": len(files),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "by_extension": by_extension
        }
