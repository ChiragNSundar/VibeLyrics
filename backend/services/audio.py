"""
Audio Analysis Service
- BPM detection
- Waveform analysis
"""
import os
from typing import Dict, Optional, List


class AudioAnalyzer:
    """Analyze audio files for BPM and energy"""
    
    def detect_bpm(self, file_path: str) -> int:
        """Detect BPM from audio file"""
        try:
            import librosa
            y, sr = librosa.load(file_path)
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            return int(tempo)
        except ImportError:
            # Librosa not installed, return default
            return 0
        except Exception as e:
            print(f"BPM detection error: {e}")
            return 0
    
    def get_energy_sections(self, file_path: str) -> List[Dict]:
        """Get energy levels throughout the track"""
        try:
            import librosa
            import numpy as np
            
            y, sr = librosa.load(file_path)
            
            # Get RMS energy
            hop_length = 512
            rms = librosa.feature.rms(y=y, hop_length=hop_length)[0]
            
            # Divide into sections
            section_count = 8
            section_length = len(rms) // section_count
            
            sections = []
            for i in range(section_count):
                start = i * section_length
                end = start + section_length
                avg_energy = float(np.mean(rms[start:end]))
                
                # Classify energy level
                if avg_energy > 0.15:
                    level = "high"
                elif avg_energy > 0.08:
                    level = "medium"
                else:
                    level = "low"
                
                sections.append({
                    "section": i + 1,
                    "energy": round(avg_energy, 4),
                    "level": level
                })
            
            return sections
            
        except ImportError:
            return []
        except Exception as e:
            print(f"Energy analysis error: {e}")
            return []
    
    def get_waveform_data(self, file_path: str, points: int = 100) -> List[float]:
        """Get simplified waveform data for visualization"""
        try:
            import librosa
            import numpy as np
            
            y, sr = librosa.load(file_path, mono=True)
            
            # Downsample to requested points
            chunk_size = len(y) // points
            waveform = []
            
            for i in range(points):
                start = i * chunk_size
                end = start + chunk_size
                avg = float(np.abs(y[start:end]).mean())
                waveform.append(round(avg, 4))
            
            return waveform
            
        except ImportError:
            return []
        except Exception:
            return []


class AdlibGenerator:
    """Generate contextual adlibs for lyrics"""
    
    # Adlib categories
    ADLIBS = {
        "hype": ["Yeah!", "Let's go!", "Uh!", "Woo!", "Ayy!", "Skrrt!"],
        "emphasis": ["You know!", "Facts!", "Real talk!", "No cap!", "Straight up!"],
        "reaction": ["Damn!", "Sheesh!", "Whoa!", "Bruh!", "Yo!"],
        "flow": ["Uh", "Yeah", "Ayy", "Mmm", "Aye"],
        "braggadocio": ["Ice!", "Drip!", "Gang!", "Boss!", "King!"],
        "affirmation": ["That's right!", "You heard me!", "I said it!", "Period!"],
    }
    
    def generate_adlibs(self, line: str, style: str = "mixed") -> List[str]:
        """Generate adlib suggestions for a line"""
        suggestions = []
        
        if style == "mixed" or style == "all":
            for category, adlibs in self.ADLIBS.items():
                suggestions.extend(adlibs[:2])
        elif style in self.ADLIBS:
            suggestions = self.ADLIBS[style]
        else:
            suggestions = self.ADLIBS["flow"]
        
        return suggestions[:10]
    
    def suggest_placement(self, line: str) -> Dict:
        """Suggest where to place adlibs in a line"""
        words = line.split()
        
        placements = []
        
        # After emphasis words
        emphasis_words = ["never", "always", "every", "all", "best", "top"]
        for i, word in enumerate(words):
            if word.lower().rstrip(".,!?") in emphasis_words:
                placements.append({
                    "position": i + 1,
                    "after_word": word,
                    "suggested": "Yeah!"
                })
        
        # At end of line
        placements.append({
            "position": len(words),
            "after_word": words[-1] if words else "",
            "suggested": "Uh!"
        })
        
        return {
            "line": line,
            "placements": placements
        }
    
    def get_categories(self) -> List[str]:
        """Get all adlib categories"""
        return list(self.ADLIBS.keys())
