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
- **Ultra-Detailed Thesaurus**: Right-click *any* word for 6-layer analysis:
  - **Formal**: Standard English synonyms/antonyms
  - **Slang**: 50+ street/hip-hop terms ("money" → "guap", "racks")
  - **Emotional**: 4-level intensity spectrum ("sad" → "devastated")
  - **Indian**: 200+ Hindi/Kannada words
  - **AI Fallback**: Auto-generates suggestions for unknown words
- **Hindi/Kannada Engine**: Full romanized support:
  - **Syllable Counting**: Accurate counts for 150+ common words + phonetic heuristic.
  - **Rhyme Finder**: Detects Kannada verb endings (*-odu*, *-ali*), pronouns (*naanu/neenu*), and Hindi patterns.
  - **Vowel-Based Rhymes**: Phonetic matching for Indian languages (last 2 vowels).
- **Complexity Scoring**: Rates verses on syllable density, rhyme richness, and unique word count.
- **Phonetic Highlighting**: Visualizes perfect, slant, and multi-syllabic rhymes.

### � Continuous Learning Engine

- **Style DNA**: The app learns your unique voice—syllable counts, favorite rhyme schemes, and flow patterns.
- **Reference Absorption**: Simply viewing lyrics in the library adds them to your knowledge base.
- **Adaptive Suggestions**: AI suggestions get smarter the more you use them, prioritized by your writing history.
- **Vocabulary Tracking**: Maintains a dynamic list of your favorite words, slangs, and avoided terms.

### 🧠 Infinite Memory (RAG)

- **Lyric Recall**: Every bar you write is indexed for instant retrieval later.
- **Context-Aware AI**: AI suggestions reference your past lyrics for callbacks.
- **TF-IDF Search**: Fast similarity matching across all your work.

### 🎹 Audio-Reactive AI

- **Energy Detection**: Detects calm/build/verse/drop sections in your beat.
- **Flow Suggestions**: AI adjusts style based on beat energy (melodic vs aggressive).

### 💡 Semantic Concept Rhymes

- **Meaning + Sound**: Find words that both rhyme AND relate conceptually (King → reign, throne, crown).
- **Hip-Hop Vocabulary**: 20+ curated concept clusters (money → bands, racks, paper, bread).
- **Mind Map**: Auto-generates a "concept cloud" from your verse.

### 🎤 Auto-Adlib Generator

- **Mood Detection**: Analyzes line energy (hype, flex, aggressive, smooth, emotional).
- **Pattern Insertion**: Finds optimal positions for adlibs (line endings, emphasis words).
- **Contextual Adlibs**: 100+ hip-hop adlibs organized by mood (Yeah!, Skrrt!, What!, Brr!).

### 🥊 Elite Lyric Tools

- **Punch Line Engine**: Detects wordplay, double meanings ("bars" → prison/lyrics), and contrast ("love" vs "hate") to score your lines 1-10.
- **Multi-Syllable Rhymes**: Finds complex 3-4 syllable rhymes (elevation → celebration, dedication).
- **Metaphor Generator**: Instantly generates creative imagery ("Money like water", "Heart cold like December").
- **RhymeWave Integration**: Built-in access to RhymeWave.com for phoneme-based rhyme finding.

### 🧬 Adaptive Learning System

- **Correction Tracking**: When you edit an AI suggestion, the system learns your preferences (shorter lines, simpler words, etc.).
- **Explicit Feedback**: Thumbs up/down on suggestions teaches the AI what you like.
- **Ultra-Detailed Highlighting**: End rhymes, internal rhymes, cross-line rhymes, alliteration, and assonance are all visually marked.
- **Preference Injection**: Learned patterns are injected directly into AI prompts for personalized suggestions.
- **Learning Status API**: Check what the AI has learned about your style (`/api/learning/status`).

### ✍️ Elite Ghostwriting Engine

- **Few-Shot Examples**: AI is primed with high-quality original examples for each mood (introspective, confident, storytelling).
- **Technique Library**: Multi-syllabic rhymes, double entendres, metaphor chains, punchy closers, and more.
- **Cliché Avoidance**: Automatically avoids overused rhyme pairs (love/above, heart/start).
- **BPM-Aware Syllable Targets**: Suggests optimal syllable counts based on your beat's tempo.

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
│   │   ├── openai_prov.py  # OpenAI GPT-4 integration
│   │   └── elite_knowledge.py # Technique library & few-shot examples
│   ├── analysis/           # Core algorithms for rhyme & rhythm analysis
│   │   ├── __init__.py
│   │   ├── audio_analyzer.py  # BPM detection using Librosa
│   │   ├── bpm_calculator.py  # Rhyme pocket & timing logic
│   │   ├── complexity_scorer.py # SSS, unique word count, diversity metrics
│   │   ├── indian_rhyme_finder.py # Rhyme groups & pattern matching for IN langs
│   │   ├── indian_thesaurus.py # Hindi/Kannada synonyms & antonyms
│   │   ├── rhyme_detector.py # End rhymes, internal rhymes, & heatmap logic
│   │   ├── rhyme_dictionary.py # CMU Dict based rhyme lookups
│   │   ├── syllable_counter.py # Syllable counting & stress patterns
│   │   └── ultra_thesaurus.py # Unified engine (WordNet + Slang + Indian + AI)
│   ├── learning/           # Adaptive learning inputs
│   │   ├── correction_analyzer.py # Learns from user edits
│   │   └── self_enhancer.py # Background learning thread
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

1. **Clone the repository**:

    ```bash
    git clone https://github.com/yourusername/vibelyrics.git
    cd vibelyrics
    ```

2. **Create a virtual environment**:

    ```bash
    python -m venv venv
    
    # Windows
    venv\Scripts\activate
    
    # macOS/Linux
    source venv/bin/activate
    ```

3. **Install dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

4. **Download NLTK Data** (Required for Smart Dictionary):

    ```bash
    python -m nltk.downloader wordnet
    ```

### Configuration

VibeLyrics relies on environment variables for API keys and configuration.

1. **Copy the example config**:

    ```bash
    cp .env.example .env
    ```

2. **Edit `.env`** with your details:

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

1. **Run all tests**:

    ```bash
    pytest
    ```

2. **Run with coverage report**:

    ```bash
    pytest --cov=app tests/
    ```

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the project.
2. Create your feature branch (`git checkout -b feature/AmazingFeature`).
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
