# VibeLyrics Enhancement Roadmap

## 1. Intelligence & Analysis
- **Heuristic Slang Engine (G2P):** Currently, unknown words fall back to spelling matches. A "Grapheme-to-Phoneme" converter would let the system "read" new slang (e.g., knowing "thicc" rhymes with "stick" without a dictionary definition).
- **Audio BPM Detection:** Integrate `librosa` or `essentia` to automatically detect the BPM of uploaded beats instead of asking the user.
- **Vocal Alignment Scoring:** Analyze users' recorded takes against the beat grid to give a "Flow Score" (e.g., "You were 20ms late on bar 4").

## 2. Collaborative Features
- **Real-Time Multiplayer:** Use WebSockets (Flask-SocketIO) to let multiple writers edit the same session simultaneously (Google Docs style).
- **Crew Management:** Create "Crews" (Teams) with shared project folders.

## 3. Production Tools
- **DeepFake/AI Vocal Demo:** Use RVC (Retrieval-based Voice Conversion) to let the user hear their lyrics performed by an AI voice (e.g., "Sound like Drake").
- **Rhyme Density Heatmap:** A visual overlay that glows hotter (Red/Orange) where rhyme density is highest.

## 4. Mobile Experience
- **PWA (Progressive Web App):** Make the site installable on iOS/Android with offline support for writing on the go.
- **Voice Dictation Mode:** A specialized mode for freestyle writers that transcribes audio to text in real-time.
