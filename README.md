# VibeLyrics 🎤

**VibeLyrics** is a powerful hip-hop lyric writing assistant and analysis tool. It combines traditional songwriting tools with advanced algorithmic analysis and AI assistance to help artists craft complex rhymes, study references, and improve their pen game.

---

## 🌟 Key Features

### 🌐 Smart Workspace
- **Instant Analysis**: Updates appear instantly as you write.
- **Auto-Sync**: Your progress is saved automatically and synced across your devices.

### 📝 Smart Lyric Editor
- **Distraction-free interface** for focused writing with song structure blocks.
- **Smart Dictionary**: Right-click *any* word to open the **Inline Lookup Panel**.
    - **Rhymes**: Improved engine detecting slant rhymes and slang.
    - **Synonyms & Antonyms**: Powered by NLTK WordNet.
    - **Click-to-Insert**: Directly click suggestions to insert them into your lyrics.
- **AI Assistance**: Get suggestions for next lines or improvements.

### 🎵 Studio Mode & Audio
- **Waveform Player**: Visualize your beat with a professional waveform display (powered by Wavesurfer.js).
- **A-B Looping**: Set loop points to practice specific bars efficiently.
- **Speed Control**: Adjust playback speed (0.5x - 1.5x) to master fast flows.
- **Auto-BPM Detection**: Automatically identifies the tempo (BPM) of uploaded beats using advanced signal processing.
- **Flow Visualization**: Real-time bar charts with bar-level grouping and density color coding (Green=Laid back, Red=Chopper).

### 🧠 Advanced Analysis Engine
- **Stress Pattern Visualization**: Visual dots (●○) show the rhythmic stress of your lyrics (stressed vs unstressed).
- **Rhyme Density Heatmap**: Visual glow (Red → Orange → Green) highlighting the technical complexity of your verses.
- **Rhyme Scheme Detection**: Automatically identifies AABB, ABAB, and complex multis.
- **Slang Heuristic Engine**: Intelligently handles modern slang ("thicc", "vibez") phonetic analysis.
- **Complexity Scoring**: Rates verses on syllable density, rhyme richness, and unique word count.
- **Phonetic Highlighting**: Visualizes perfect, slant, and multi-syllabic rhymes.

### 🎮 Gamification & Progress
- **Daily Challenge**: "Word of the Day" prompt to spark your creativity and keep your streak alive.
- **Daily Streaks**: Track your writing consistency with a daily streak counter.
- **Stats Dashboard**: View customized stats like "Lines Dropped" and "Total Sessions".

### 📚 Reference Library
- **Genius Integration**: Search and import lyrics directly from Genius.com.
- **Study Mode**: Analyze your favorite artists' tracks to understand their patterns.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.10+ with Flask & **Flask-SocketIO** (for Websockets)
- **Frontend**: HTML5, CSS3 (Custom Design System), JavaScript (ES6)
- **Data**: JSON-based local storage (no heavy database setup required for local use)
- **NLP**: CMU Dict (Pronouncing), NLTK (WordNet)
- **Audio Analysis**: **Librosa** & **Numpy** (for async BPM detection)
- **AI Integration**: Support for OpenAI GPT-4, Google Gemini, and Perplexity AI
- **Performance**: Singleton caching for dictionary lookups, background threading for audio processing
- **Testing**: Pytest

---

## 📂 Project Structure

```
vibelyrics/
├── app/
│   ├── ai/                 # AI provider integrations (Gemini, OpenAI,Anthropic)
│   │   ├── __init__.py
│   │   ├── base.py         # Abstract base class for providers
│   │   ├── gemini.py       # Google Gemini integration
│   │   └── openai_prov.py  # OpenAI GPT-4 integration
│   ├── analysis/           # Core algorithms for rhyme & rhythm analysis
│   │   ├── __init__.py
│   │   ├── audio_analyzer.py  # BPM detection using Librosa
│   │   ├── bpm_calculator.py  # Rhyme pocket & timing logic
│   │   ├── complexity_scorer.py # SSS, unique word count, diversity metrics
│   │   ├── rhyme_detector.py # End rhymes, internal rhymes, & heatmap logic
│   │   ├── rhyme_dictionary.py # CMU Dict based rhyme lookups
│   │   └── syllable_counter.py # Syllable counting & stress patterns
│   ├── models/             # Flask-SQLAlchemy data models
│   │   ├── __init__.py
│   │   ├── lyrics.py       # LyricSession and LyricLine models
│   │   └── journal.py      # Journal entry models
│   ├── routes/             # Flask blueprints
│   │   ├── __init__.py
│   │   ├── api.py          # Data endpoints for dictionary & tools
│   │   ├── workspace.py    # Main writing session routes
│   │   ├── journal.py      # Journal management
│   │   └── references.py   # Genius search & study mode
│   ├── static/             # Frontend assets
│   │   ├── css/
│   │   │   └── style.css   # Main design system
│   │   ├── js/
│   │   │   ├── app.js      # Global UI logic
│   │   │   ├── session.js  # Real-time writing & socket logic
│   │   │   └── flow_viz.js # Canvas rhythm visualization
│   │   └── uploads/        # User beats and audio
│   └── templates/          # Jinja2 HTML templates
│       ├── base.html       # Shared layout
│       ├── workspace.html  # Session browser/dashboard
│       ├── session.html    # Core writing interface
│       ├── journal.html    # Lyric journal
│       ├── references.html # Genius search results
│       ├── reference_view.html # Song study mode
│       ├── settings.html   # User profile & AI config
│       └── export_print.html # Print-friendly view
├── data/                   # SQLite database and local exports
├── tests/                  # Pytest suite
│   ├── test_analysis.py
│   └── test_api.py
├── run.py                  # Entry point with SocketIO support
├── requirements.txt
└── .env                    # Environment config
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher
- `pip` (Python package manager)

### Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/vibelyrics.git
    cd vibelyrics
    ```

2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    
    # Windows
    venv\Scripts\activate
    
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Download NLTK Data** (Required for Smart Dictionary):
    ```bash
    python -m nltk.downloader wordnet
    ```

### Configuration

VibeLyrics relies on environment variables for API keys and configuration.

1.  **Copy the example config**:
    ```bash
    cp .env.example .env
    ```

2.  **Edit `.env`** with your details:
    | Variable | Description | Required |
    |----------|-------------|----------|
    | `FLASK_SECRET_KEY` | Random string for session security | Yes |
    | `GENIUS_ACCESS_TOKEN` | Token from Genius API clients | Optional (for scraping) |
    | `GEMINI_API_KEY` | Google Gemini API Key | Optional (for AI features) |
    | `OPENAI_API_KEY` | OA API Key | Optional (for AI features) |
    | `DEFAULT_AI_PROVIDER` | `gemini` or `openai` | Yes (if using AI) |

---

## 🏃‍♂️ Running the Application

To start the local development server (with WebSocket support):

```bash
python run.py
```

The application will be accessible at `http://127.0.0.1:5000`.

---

## 🧪 Running Tests

We use `pytest` to ensure the core analysis logic remains accurate.

1.  **Run all tests**:
    ```bash
    pytest
    ```

2.  **Run with coverage report**:
    ```bash
    pytest --cov=app tests/
    ```

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1.  Fork the project.
2.  Create your feature branch (`git checkout -b feature/AmazingFeature`).
3.  Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4.  Push to the branch (`git push origin feature/AmazingFeature`).
5.  Open a Pull Request.

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
