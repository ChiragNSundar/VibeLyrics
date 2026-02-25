"""
Audio Analysis Service
- BPM detection
- Key detection (Krumhansl-Schmuckler)
- Waveform analysis
- Dynamic beat section detection
- Contextual adlib generation
"""
import os
from typing import Dict, Optional, List


class AudioAnalyzer:
    """Analyze audio files for BPM, key, energy, and structure"""
    
    def detect_bpm(self, file_path: str) -> int:
        """Detect BPM from audio file"""
        try:
            import librosa
            y, sr = librosa.load(file_path)
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            return int(tempo)
        except ImportError:
            return 0
        except Exception as e:
            print(f"BPM detection error: {e}")
            return 0
    
    def detect_key(self, file_path: str) -> Dict:
        """
        Detect musical key using chromagram + Krumhansl-Schmuckler algorithm.
        Returns {"key": "C", "mode": "minor", "confidence": 0.85}
        """
        try:
            import librosa
            import numpy as np
            
            y, sr = librosa.load(file_path)
            
            # Compute chromagram
            chroma = librosa.feature.chroma_stft(y=y, sr=sr)
            chroma_mean = np.mean(chroma, axis=1)
            
            # Krumhansl-Schmuckler key profiles
            major_profile = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09,
                                       2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
            minor_profile = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53,
                                       2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
            
            key_names = ['C', 'C#', 'D', 'D#', 'E', 'F',
                         'F#', 'G', 'G#', 'A', 'A#', 'B']
            
            best_corr = -1
            best_key = 'C'
            best_mode = 'major'
            
            for i in range(12):
                rotated = np.roll(chroma_mean, -i)
                
                # Major correlation
                major_corr = np.corrcoef(rotated, major_profile)[0, 1]
                if major_corr > best_corr:
                    best_corr = major_corr
                    best_key = key_names[i]
                    best_mode = 'major'
                
                # Minor correlation
                minor_corr = np.corrcoef(rotated, minor_profile)[0, 1]
                if minor_corr > best_corr:
                    best_corr = minor_corr
                    best_key = key_names[i]
                    best_mode = 'minor'
            
            return {
                "key": best_key,
                "mode": best_mode,
                "confidence": round(max(0, float(best_corr)), 3),
                "label": f"{best_key} {best_mode}"
            }
            
        except ImportError:
            return {"key": "Unknown", "mode": "unknown", "confidence": 0, "label": "Unknown"}
        except Exception as e:
            print(f"Key detection error: {e}")
            return {"key": "Unknown", "mode": "unknown", "confidence": 0, "label": "Unknown"}
    
    def detect_sections(self, file_path: str) -> List[Dict]:
        """
        Detect beat structure sections (Intro, Verse, Chorus, Bridge, Outro)
        using spectral features and energy.
        Returns list of sections with start/end times, labels, and energy levels.
        """
        try:
            import librosa
            import numpy as np
            
            y, sr = librosa.load(file_path)
            duration = librosa.get_duration(y=y, sr=sr)
            
            # Detect tempo and beats
            tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
            beat_times = librosa.frames_to_time(beat_frames, sr=sr)
            
            # Compute spectral features for segmentation
            hop_length = 512
            rms = librosa.feature.rms(y=y, hop_length=hop_length)[0]
            spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=hop_length)[0]
            
            # Normalize features
            rms_norm = (rms - rms.min()) / (rms.max() - rms.min() + 1e-8)
            sc_norm = (spectral_centroid - spectral_centroid.min()) / (spectral_centroid.max() - spectral_centroid.min() + 1e-8)
            
            # Combined feature for segmentation
            combined = 0.6 * rms_norm + 0.4 * sc_norm
            
            # Divide into segments based on energy changes
            # Use ~4 bar segments (assuming 4/4 time)
            bars_per_section = 8
            beats_per_bar = 4
            beats_per_section = bars_per_section * beats_per_bar
            
            sections = []
            section_labels = ["Intro", "Verse 1", "Chorus", "Verse 2", "Chorus", "Bridge", "Outro"]
            
            if len(beat_times) < 4:
                # Not enough beats, split by duration
                section_count = min(4, max(2, int(duration / 15)))
                section_dur = duration / section_count
                for i in range(section_count):
                    start = i * section_dur
                    end = min((i + 1) * section_dur, duration)
                    label = section_labels[i] if i < len(section_labels) else f"Section {i + 1}"
                    sections.append({
                        "label": label,
                        "start_sec": round(start, 2),
                        "end_sec": round(end, 2),
                        "bars": bars_per_section,
                        "energy": "medium"
                    })
                return sections
            
            # Group beats into sections
            section_idx = 0
            i = 0
            while i < len(beat_times):
                start_beat = i
                end_beat = min(i + beats_per_section, len(beat_times))
                
                start_sec = beat_times[start_beat]
                end_sec = beat_times[end_beat - 1] if end_beat > start_beat else start_sec
                
                # Calculate average energy for this section
                start_frame = librosa.time_to_frames(start_sec, sr=sr, hop_length=hop_length)
                end_frame = librosa.time_to_frames(end_sec, sr=sr, hop_length=hop_length)
                start_frame = max(0, min(start_frame, len(rms) - 1))
                end_frame = max(start_frame + 1, min(end_frame, len(rms)))
                
                avg_energy = float(np.mean(rms[start_frame:end_frame]))
                
                if avg_energy > 0.15:
                    energy_label = "high"
                elif avg_energy > 0.08:
                    energy_label = "medium"
                else:
                    energy_label = "low"
                
                # Determine section label
                if section_idx < len(section_labels):
                    label = section_labels[section_idx]
                else:
                    label = f"Section {section_idx + 1}"
                
                # Refine labels based on energy patterns
                if section_idx == 0 and avg_energy < 0.06:
                    label = "Intro"
                elif energy_label == "high" and "Verse" in label:
                    label = label.replace("Verse", "Chorus")
                
                bars = (end_beat - start_beat) // beats_per_bar
                
                sections.append({
                    "label": label,
                    "start_sec": round(float(start_sec), 2),
                    "end_sec": round(float(end_sec), 2),
                    "bars": max(1, bars),
                    "energy": energy_label
                })
                
                section_idx += 1
                i = end_beat
            
            # Add final section extending to end if needed
            if sections and sections[-1]["end_sec"] < duration - 2:
                sections.append({
                    "label": "Outro",
                    "start_sec": sections[-1]["end_sec"],
                    "end_sec": round(duration, 2),
                    "bars": 4,
                    "energy": "low"
                })
            
            return sections
            
        except ImportError:
            return []
        except Exception as e:
            print(f"Section detection error: {e}")
            return []
    
    def get_section_waveform(self, file_path: str, start_sec: float, end_sec: float, points: int = 100) -> List[float]:
        """Get waveform data for a specific section (for looping)"""
        try:
            import librosa
            import numpy as np
            
            y, sr = librosa.load(file_path, mono=True, offset=start_sec, duration=end_sec - start_sec)
            
            chunk_size = max(1, len(y) // points)
            waveform = []
            
            for i in range(min(points, len(y) // max(1, chunk_size))):
                start = i * chunk_size
                end = start + chunk_size
                avg = float(np.abs(y[start:end]).mean())
                waveform.append(round(avg, 4))
            
            return waveform
            
        except ImportError:
            return []
        except Exception:
            return []
    
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
    """Generate contextual adlibs — static categories + AI-powered context awareness"""
    
    # Adlib categories
    ADLIBS = {
        "hype": ["Yeah!", "Let's go!", "Uh!", "Woo!", "Ayy!", "Skrrt!"],
        "emphasis": ["You know!", "Facts!", "Real talk!", "No cap!", "Straight up!"],
        "reaction": ["Damn!", "Sheesh!", "Whoa!", "Bruh!", "Yo!"],
        "flow": ["Uh", "Yeah", "Ayy", "Mmm", "Aye"],
        "braggadocio": ["Ice!", "Drip!", "Gang!", "Boss!", "King!"],
        "affirmation": ["That's right!", "You heard me!", "I said it!", "Period!"],
    }
    
    # Artist-specific adlib patterns
    ARTIST_ADLIBS = {
        "travis_scott": ["It's lit!", "Straight up!", "La Flame!", "Yeah yeah!", "Cactus Jack!"],
        "drake": ["Huh?", "Woi!", "Yeah yeah", "Ayy", "Ting!"],
        "kendrick": ["Yah yah!", "Sit down!", "Be humble!", "DNA!", "Kung fu!"],
        "future": ["Hendrix!", "Pluto!", "Freebandz!", "Dirty!", "Mask off!"],
        "migos": ["Mama!", "Skrrt!", "Cookie!", "Raindrop!", "Brrr!"],
        "21_savage": ["On God!", "Straight up!", "21!", "Gang gang!", "Pussy!"],
        "j_cole": ["Yeah", "Cole World!", "For real!", "Huh", "Listen!"],
        "kanye": ["Yeezy!", "Hah!", "You see?", "Ye!", "GOOD!"],
    }
    
    # Mood-to-category mapping
    MOOD_MAP = {
        "hype": ["hype", "braggadocio"],
        "confident": ["braggadocio", "affirmation"],
        "aggressive": ["hype", "emphasis", "reaction"],
        "melancholy": ["flow", "reaction"],
        "chill": ["flow", "affirmation"],
        "emotional": ["reaction", "emphasis"],
        "dark": ["reaction", "emphasis"],
        "playful": ["hype", "flow"],
    }
    
    def generate_adlibs(self, line: str, style: str = "mixed") -> List[str]:
        """Generate adlib suggestions for a line (static fallback)"""
        suggestions = []
        
        if style == "mixed" or style == "all":
            for category, adlibs in self.ADLIBS.items():
                suggestions.extend(adlibs[:2])
        elif style in self.ADLIBS:
            suggestions = self.ADLIBS[style]
        else:
            suggestions = self.ADLIBS["flow"]
        
        return suggestions[:10]
    
    def generate_contextual_adlibs(
        self, line: str, mood: str = None,
        artist_style: str = None, recent_lines: List[str] = None
    ) -> Dict:
        """
        Generate context-aware adlib suggestions based on mood, artist style,
        and line content analysis.
        """
        suggestions = []
        source = "contextual"
        
        # 1. Artist style adlibs
        artist_suggestions = []
        if artist_style and artist_style.lower().replace(" ", "_") in self.ARTIST_ADLIBS:
            artist_key = artist_style.lower().replace(" ", "_")
            artist_suggestions = self.ARTIST_ADLIBS[artist_key]
            source = f"artist:{artist_style}"
        
        # 2. Mood-based selection
        mood_suggestions = []
        if mood and mood.lower() in self.MOOD_MAP:
            categories = self.MOOD_MAP[mood.lower()]
            for cat in categories:
                if cat in self.ADLIBS:
                    mood_suggestions.extend(self.ADLIBS[cat][:3])
        
        # 3. Content analysis — detect tone from the line itself
        line_lower = line.lower()
        detected_tone = self._detect_tone(line_lower)
        tone_categories = self.MOOD_MAP.get(detected_tone, ["flow"])
        tone_suggestions = []
        for cat in tone_categories:
            if cat in self.ADLIBS:
                tone_suggestions.extend(self.ADLIBS[cat][:2])
        
        # Combine: artist > mood > tone > generic
        if artist_suggestions:
            suggestions.extend(artist_suggestions[:4])
        if mood_suggestions:
            suggestions.extend(mood_suggestions[:3])
        if tone_suggestions:
            suggestions.extend(tone_suggestions[:3])
        
        # Deduplicate while preserving order
        seen = set()
        unique = []
        for s in suggestions:
            if s not in seen:
                seen.add(s)
                unique.append(s)
        
        if not unique:
            unique = self.ADLIBS["flow"][:5]
        
        return {
            "adlibs": unique[:10],
            "detected_tone": detected_tone,
            "source": source,
            "placements": self.suggest_placement(line)["placements"]
        }
    
    async def generate_ai_adlibs(
        self, line: str, mood: str = None,
        artist_style: str = None, recent_lines: List[str] = None
    ) -> Dict:
        """Generate adlibs using AI for maximum creativity"""
        from .ai_provider import get_ai_provider
        
        provider = get_ai_provider()
        if not provider.is_available():
            return self.generate_contextual_adlibs(line, mood, artist_style, recent_lines)
        
        context_str = "\n".join(recent_lines[-3:]) if recent_lines else "None"
        artist_note = f"Mimic {artist_style}'s signature ad-lib style." if artist_style else ""
        mood_note = f"The mood is: {mood}." if mood else ""
        
        prompt = f"""You are a hip-hop ad-lib specialist. Suggest 8 perfect ad-libs for this bar:

"{line}"

{mood_note}
{artist_note}
Recent bars: {context_str}

Rules:
- Each ad-lib should be 1-3 words max
- Include where to place it (start, middle, end of bar)
- Mix between hype ad-libs, reaction ad-libs, and flow ad-libs
- Make them feel natural and on-beat

Return in format: [ad-lib] (placement)
One per line, no numbering."""

        try:
            response = await provider.answer_question(prompt, None)
            ai_adlibs = []
            for raw_line in response.strip().split('\n'):
                raw_line = raw_line.strip("- •").strip()
                if raw_line and len(raw_line) > 1:
                    ai_adlibs.append(raw_line)
            
            return {
                "adlibs": ai_adlibs[:8],
                "detected_tone": self._detect_tone(line.lower()),
                "source": "ai",
                "placements": self.suggest_placement(line)["placements"]
            }
        except Exception:
            return self.generate_contextual_adlibs(line, mood, artist_style, recent_lines)
    
    def _detect_tone(self, line_lower: str) -> str:
        """Detect emotional tone from line content"""
        hype_words = ["top", "best", "king", "boss", "rich", "win", "money", "ice", "drip"]
        aggressive_words = ["kill", "war", "fight", "enemy", "gun", "bang", "dead"]
        emotional_words = ["cry", "miss", "love", "heart", "soul", "pain", "feel"]
        dark_words = ["dark", "shadow", "death", "blood", "demon", "hell", "grave"]
        chill_words = ["vibe", "chill", "wave", "float", "smooth", "lean", "slow"]
        
        for w in aggressive_words:
            if w in line_lower:
                return "aggressive"
        for w in dark_words:
            if w in line_lower:
                return "dark"
        for w in emotional_words:
            if w in line_lower:
                return "emotional"
        for w in hype_words:
            if w in line_lower:
                return "hype"
        for w in chill_words:
            if w in line_lower:
                return "chill"
        
        return "confident"
    
    def suggest_placement(self, line: str) -> Dict:
        """Suggest where to place adlibs in a line using syllable analysis"""
        words = line.split()
        
        placements = []
        
        # After emphasis words
        emphasis_words = ["never", "always", "every", "all", "best", "top",
                          "real", "true", "facts", "swear", "god"]
        for i, word in enumerate(words):
            if word.lower().rstrip(".,!?") in emphasis_words:
                placements.append({
                    "position": i + 1,
                    "after_word": word,
                    "suggested": "Yeah!",
                    "type": "emphasis"
                })
        
        # After rhyme words (end of line)
        if words:
            placements.append({
                "position": len(words),
                "after_word": words[-1],
                "suggested": "Uh!",
                "type": "end_of_bar"
            })
        
        # Before punchline (mid-bar pause)
        if len(words) > 4:
            mid = len(words) // 2
            placements.append({
                "position": mid,
                "after_word": words[mid] if mid < len(words) else "",
                "suggested": "Ayy",
                "type": "mid_bar"
            })
        
        return {
            "line": line,
            "placements": placements
        }
    
    def get_categories(self) -> List[str]:
        """Get all adlib categories"""
        return list(self.ADLIBS.keys())
    
    def get_artist_styles(self) -> List[str]:
        """Get available artist styles for adlibs"""
        return list(self.ARTIST_ADLIBS.keys())
