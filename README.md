# VibeLyrics 🎤

**VibeLyrics** is a powerful, collaborative hip-hop lyric writing assistant and analysis tool. It combines traditional songwriting tools with advanced algorithmic analysis and AI assistance to help artists craft complex rhymes, study references, and improve their pen game.

---

## 🌟 Key Features

### 🌐 Real-Time Multiplayer Collaboration
- **Live Co-Writing**: Invite friends to your session and write together in real-time.
- **Instant Sync**: Updates appear instantly on all collaborators' screens.
- **Collaborative Flow**: Adding lines or editing bars happens seamlessly without refreshing.

### 📝 Smart Lyric Editor
- **Distraction-free interface** for focused writing with song structure blocks.
- **Smart Dictionary**: Right-click *any* word (or type in the input box) for a powerful lookup tool.
    - **Rhymes**: Improved engine detecting slant rhymes and slang.
    - **Synonyms & Antonyms**: powered by NLTK WordNet.
    - **Syllable Filtering**: Filter rhymes by 1, 2, or 3+ syllables to fit your pocket perfectly.
- **AI Assistance**: Get suggestions for next lines or improvements.

### 🎵 Studio Mode & Audio
- **Beat Player**: Upload and play instrumental tracks directly in your session.
- **Flow Visualization**: Real-time bar charts visualize syllable density and rhythm.

### 🧠 Advanced Analysis Engine
- **Rhyme Scheme Detection**: Automatically identifies AABB, ABAB, and complex multis.
- **Slang Heuristic Engine**: Intelligently handles modern slang ("thicc", "vibez") phonetic analysis.
- **Complexity Scoring**: Rates verses on syllable density, rhyme richness, and unique word count.
- **Phonetic Highlighting**: Visualizes perfect, slant, and multi-syllabic rhymes.

### 🎮 Gamification & Progress
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
- **AI Integration**: Support for OpenAI GPT-4, Google Gemini, and Perplexity AI
- **Testing**: Pytest

---

## 📂 Project Structure

```
vibelyrics/
├── app/
│   ├── ai/             # AI provider integrations (Gemini, OpenAI, etc.)
│   ├── analysis/       # Core algorithms for rhyme & complexity analysis
│   ├── models/         # Data classes (Lyrics, Journal, Corrections)
│   ├── references/     # Genius scraper and library management
│   ├── routes/         # Flask blueprints for web endpoints
│   ├── static/         # CSS, JS, and image assets
│   └── templates/      # Jinja2 HTML templates
├── data/               # Local storage for lyrics and journals
├── tests/              # Pytest suite
└── run.py              # Application entry point
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
