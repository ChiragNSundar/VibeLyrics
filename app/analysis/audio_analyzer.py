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
