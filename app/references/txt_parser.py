"""
TXT Parser
Parses plain text lyrics files
"""
import re
from typing import Dict, List, Optional


class TxtParser:
    """Parses plain .txt lyrics files"""
    
    # Common section headers in lyrics
    SECTION_PATTERNS = [
        r'\[([^\]]+)\]',           # [Verse 1], [Chorus], etc.
        r'\(([^\)]+)\)',           # (Verse 1), (Chorus), etc.
        r'^(Verse|Chorus|Hook|Bridge|Intro|Outro|Pre-Chorus|Post-Chorus)\s*\d*:?\s*$',
    ]
    
    def __init__(self):
        self.section_regex = re.compile('|'.join(self.SECTION_PATTERNS), re.IGNORECASE | re.MULTILINE)
    
    def parse(self, content: str) -> Dict:
        """
        Parse lyrics content into structured format
        """
        lines = content.strip().split('\n')
        
        result = {
            "artist": None,
            "song": None,
            "raw_content": content,
            "sections": [],
            "all_lines": []
        }
        
        # Try to extract artist/song from first lines
        if lines:
            first_line = lines[0].strip()
            # Common formats: "Artist - Song" or "Song by Artist"
            if ' - ' in first_line:
                parts = first_line.split(' - ', 1)
                result["artist"] = parts[0].strip()
                result["song"] = parts[1].strip() if len(parts) > 1 else None
            elif ' by ' in first_line.lower():
                parts = first_line.lower().split(' by ', 1)
                result["song"] = parts[0].strip().title()
                result["artist"] = parts[1].strip().title() if len(parts) > 1 else None
        
        # Parse sections
        current_section = {"name": "Intro", "lines": []}
        
        for line in lines:
            line = line.strip()
            
            if not line:
                continue
            
            # Check if this is a section header
            section_match = self.section_regex.match(line)
            if section_match or self._is_section_header(line):
                # Save previous section if it has content
                if current_section["lines"]:
                    result["sections"].append(current_section)
                
                # Extract section name
                section_name = section_match.group(1) if section_match else line.rstrip(':')
                current_section = {"name": section_name.strip(), "lines": []}
            else:
                # Regular lyric line
                if not self._is_metadata_line(line):
                    current_section["lines"].append(line)
                    result["all_lines"].append(line)
        
        # Don't forget the last section
        if current_section["lines"]:
            result["sections"].append(current_section)
        
        return result
    
    def _is_section_header(self, line: str) -> bool:
        """Check if a line is likely a section header"""
        line_lower = line.lower().strip()
        header_keywords = [
            'verse', 'chorus', 'hook', 'bridge', 'intro', 'outro',
            'pre-chorus', 'post-chorus', 'interlude', 'break'
        ]
        
        for keyword in header_keywords:
            if line_lower.startswith(keyword):
                # Check it's not a lyric that starts with these words
                if len(line_lower) < 20 or line_lower.endswith(':'):
                    return True
        
        return False
    
    def _is_metadata_line(self, line: str) -> bool:
        """Check if a line is metadata, not lyrics"""
        metadata_patterns = [
            r'^artist\s*:',
            r'^song\s*:',
            r'^album\s*:',
            r'^year\s*:',
            r'^written by',
            r'^produced by',
            r'^feat\.',
            r'^\[.*\]$',  # Just a section marker alone
        ]
        
        line_lower = line.lower()
        for pattern in metadata_patterns:
            if re.match(pattern, line_lower):
                return True
        
        return False
    
    def get_lines_only(self, content: str) -> List[str]:
        """Get just the lyric lines without metadata or section headers"""
        parsed = self.parse(content)
        return parsed["all_lines"]
    
    def extract_bars(self, content: str, bars_per_section: int = 4) -> List[List[str]]:
        """
        Extract lyrics as groups of bars
        Useful for analyzing rhyme patterns in 4-bar or 8-bar sections
        """
        lines = self.get_lines_only(content)
        bars = []
        
        for i in range(0, len(lines), bars_per_section):
            bar_group = lines[i:i + bars_per_section]
            if bar_group:
                bars.append(bar_group)
        
        return bars
    
    def analyze_structure(self, content: str) -> Dict:
        """
        Analyze the structure of a song
        """
        parsed = self.parse(content)
        
        section_counts = {}
        for section in parsed["sections"]:
            name = section["name"].lower()
            # Normalize section names (Verse 1, Verse 2 -> verse)
            base_name = re.sub(r'\s*\d+\s*$', '', name).strip()
            section_counts[base_name] = section_counts.get(base_name, 0) + 1
        
        return {
            "total_lines": len(parsed["all_lines"]),
            "total_sections": len(parsed["sections"]),
            "section_counts": section_counts,
            "sections": [s["name"] for s in parsed["sections"]],
            "avg_lines_per_section": (
                len(parsed["all_lines"]) / len(parsed["sections"])
                if parsed["sections"] else 0
            )
        }
