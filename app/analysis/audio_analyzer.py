import librosa
import numpy as np
import os

def detect_bpm(file_path):
    """
    Detect BPM of an audio file using Librosa.
    """
    try:
        # Load only 60 seconds to speed up
        y, sr = librosa.load(file_path, duration=60)
        
        # Detect tempo
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        
        # Librosa returns a scalar or array depending on version/confidence
        if isinstance(tempo, np.ndarray):
            bpm = tempo[0]
        else:
            bpm = tempo
            
        return int(round(bpm))
    except Exception as e:
        print(f"BPM Detection Error: {e}")
        return 0


def analyze_energy_sections(file_path, segment_duration=4.0):
    """
    Analyze audio energy to detect sections (intro, verse, drop, bridge, outro).
    Returns energy zones with suggested flow styles.
    
    Args:
        file_path: Path to audio file
        segment_duration: Duration of each segment in seconds
        
    Returns:
        List of energy sections: [{start, end, energy, zone, suggested_flow}]
    """
    try:
        # Load first 180 seconds (typical song length)
        y, sr = librosa.load(file_path, duration=180)
        
        # Calculate RMS energy for each segment
        hop_length = int(segment_duration * sr)
        n_segments = len(y) // hop_length
        
        if n_segments < 2:
            return []
        
        energies = []
        for i in range(n_segments):
            start_sample = i * hop_length
            end_sample = start_sample + hop_length
            segment = y[start_sample:end_sample]
            rms = np.sqrt(np.mean(segment ** 2))
            energies.append(rms)
        
        # Normalize energies to 0-1 scale
        if max(energies) > 0:
            energies = [e / max(energies) for e in energies]
        
        # Classify energy zones
        sections = []
        for i, energy in enumerate(energies):
            start_time = i * segment_duration
            end_time = start_time + segment_duration
            
            # Determine zone and flow based on energy level
            if energy < 0.3:
                zone = "calm"
                suggested_flow = "melodic"
            elif energy < 0.5:
                zone = "build"
                suggested_flow = "conversational"
            elif energy < 0.75:
                zone = "verse"
                suggested_flow = "rhythmic"
            else:
                zone = "drop"
                suggested_flow = "aggressive"
            
            sections.append({
                "start": round(start_time, 1),
                "end": round(end_time, 1),
                "energy": round(energy, 2),
                "zone": zone,
                "suggested_flow": suggested_flow
            })
        
        return sections
        
    except Exception as e:
        print(f"Energy Analysis Error: {e}")
        return []


def get_current_energy_zone(sections, current_time):
    """
    Get the energy zone for the current playback position.
    
    Args:
        sections: List of energy sections
        current_time: Current playback time in seconds
        
    Returns:
        Current section dict or None
    """
    for section in sections:
        if section["start"] <= current_time < section["end"]:
            return section
    return None
