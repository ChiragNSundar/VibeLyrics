"""
BPM Calculator
Calculates optimal bar lengths and syllable targets based on BPM
"""
from typing import Dict, Tuple, List
from .syllable_counter import SyllableCounter


class BPMCalculator:
    """Handles BPM-based calculations for lyric timing"""
    
    # Common BPM ranges for hip-hop subgenres
    GENRE_BPM = {
        "boom_bap": (85, 100),
        "trap": (130, 170),
        "melodic_rap": (120, 150),
        "drill": (140, 150),
        "old_school": (90, 100),
        "west_coast": (90, 105),
        "southern": (70, 85),
        "double_time": (70, 90),  # BPM but rapped double
    }
    
    # Syllables per bar recommendations
    SYLLABLE_RANGES = {
        (60, 80): {"min": 6, "max": 10, "optimal": 8},
        (80, 100): {"min": 8, "max": 14, "optimal": 11},
        (100, 120): {"min": 10, "max": 16, "optimal": 13},
        (120, 140): {"min": 12, "max": 18, "optimal": 15},
        (140, 160): {"min": 14, "max": 22, "optimal": 17},
        (160, 200): {"min": 16, "max": 26, "optimal": 20},
    }
    
    def __init__(self):
        self.syllable_counter = SyllableCounter()
    
    def get_bar_duration(self, bpm: int) -> float:
        """Get duration of one bar (4 beats) in seconds"""
        beat_duration = 60 / bpm
        return beat_duration * 4
    
    def get_beat_duration(self, bpm: int) -> float:
        """Get duration of one beat in seconds"""
        return 60 / bpm
    
    def get_syllable_target(self, bpm: int) -> Dict[str, int]:
        """Get recommended syllable counts for given BPM"""
        for (min_bpm, max_bpm), targets in self.SYLLABLE_RANGES.items():
            if min_bpm <= bpm < max_bpm:
                return targets
        
        # Default for out-of-range BPMs
        return {"min": 10, "max": 16, "optimal": 13}
    
    def analyze_bar_timing(self, line: str, bpm: int) -> Dict:
        """
        Analyze how well a line fits the beat
        """
        syllables = self.syllable_counter.count_line_syllables(line)
        targets = self.get_syllable_target(bpm)
        bar_duration = self.get_bar_duration(bpm)
        
        # Calculate timing
        syllables_per_second = syllables / bar_duration
        
        result = {
            "line": line,
            "bpm": bpm,
            "syllables": syllables,
            "bar_duration_seconds": round(bar_duration, 2),
            "syllables_per_second": round(syllables_per_second, 2),
            "target": targets,
            "fits_beat": targets["min"] <= syllables <= targets["max"],
        }
        
        # Provide feedback
        if syllables < targets["min"]:
            result["feedback"] = "Line is short - consider adding words or stretching syllables"
            result["adjustment_needed"] = targets["optimal"] - syllables
        elif syllables > targets["max"]:
            result["feedback"] = "Line is dense - consider cutting words or using shorter words"
            result["adjustment_needed"] = syllables - targets["optimal"]
        else:
            if abs(syllables - targets["optimal"]) <= 2:
                result["feedback"] = "Perfect fit for the beat!"
            else:
                result["feedback"] = "Good fit, room for minor adjustment"
            result["adjustment_needed"] = 0
        
        return result
    
    def suggest_flow_style(self, bpm: int) -> Dict:
        """
        Suggest flow styles that work well for given BPM
        """
        suggestions = []
        
        if bpm < 90:
            suggestions.append({
                "style": "laid_back",
                "description": "Relaxed, stretched syllables with emphasis on groove",
                "example_artists": ["Snoop Dogg", "Nipsey Hussle"]
            })
            suggestions.append({
                "style": "double_time",
                "description": "Rapid-fire delivery over slow beat",
                "example_artists": ["Eminem", "Tech N9ne"]
            })
        
        if 90 <= bpm <= 110:
            suggestions.append({
                "style": "boom_bap",
                "description": "Classic rhythmic patterns, punchy delivery",
                "example_artists": ["Nas", "J. Cole"]
            })
            suggestions.append({
                "style": "storytelling",
                "description": "Clear enunciation, narrative focus",
                "example_artists": ["Kendrick Lamar", "2Pac"]
            })
        
        if 120 <= bpm <= 150:
            suggestions.append({
                "style": "melodic",
                "description": "Sung-rap hybrid, auto-tune friendly",
                "example_artists": ["Travis Scott", "Future"]
            })
            suggestions.append({
                "style": "triplet",
                "description": "Three syllables per beat, bouncy flow",
                "example_artists": ["Migos", "Lil Baby"]
            })
        
        if bpm >= 140:
            suggestions.append({
                "style": "trap",
                "description": "Hi-hat driven, ad-lib heavy, punchy",
                "example_artists": ["21 Savage", "Playboi Carti"]
            })
            suggestions.append({
                "style": "drill",
                "description": "Dark, aggressive, sliding flow",
                "example_artists": ["Pop Smoke", "Chief Keef"]
            })
        
        return {
            "bpm": bpm,
            "bar_duration": self.get_bar_duration(bpm),
            "recommended_styles": suggestions
        }
    
    def calculate_verse_structure(self, bpm: int, target_seconds: int = 45) -> Dict:
        """
        Calculate how many bars/lines fit in a target duration
        """
        bar_duration = self.get_bar_duration(bpm)
        total_bars = int(target_seconds / bar_duration)
        
        # Standard structures
        structures = {
            "8_bar": min(8, total_bars),
            "12_bar": min(12, total_bars),
            "16_bar": min(16, total_bars),
            "full_verse": total_bars
        }
        
        return {
            "bpm": bpm,
            "target_duration_seconds": target_seconds,
            "bar_duration_seconds": round(bar_duration, 2),
            "total_bars_available": total_bars,
            "recommended_structures": structures,
            "syllable_target_per_bar": self.get_syllable_target(bpm)
        }
    
    def get_genre_for_bpm(self, bpm: int) -> List[str]:
        """Suggest genres that typically use this BPM range"""
        genres = []
        for genre, (min_bpm, max_bpm) in self.GENRE_BPM.items():
            if min_bpm <= bpm <= max_bpm:
                genres.append(genre.replace("_", " ").title())
        return genres if genres else ["Custom/Experimental"]
