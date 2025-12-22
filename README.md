# VibeLyrics 🎤

**VibeLyrics** is a powerful, collaborative hip-hop lyric writing assistant and analysis tool. It combines traditional songwriting tools with advanced algorithmic analysis and AI assistance to help artists craft complex rhymes, study references, and improve their pen game.

---

## 🌟 Key Features

### 📝 Smart Lyric Editor
- **Distraction-free interface** for focused writing.
- **Real-time feedback** on syllable counts and line structures.
- **AI Assistance** for generating rhymes, metaphors, and continuing bars.

### 🧠 Advanced Analysis Engine
- **Rhyme Scheme Detection**: Automatically identifies AABB, ABAB, and complex multis utilizing phonetic algorithms.
- **Complexity Scoring**: Rates verses on syllable density, rhyme richness, and unique word count.
- **Phonetic Highlighting**: Visualizes perfect, slant, and multi-syllabic rhymes.

### 📚 Reference Library
- **Genius Integration**: Search and import lyrics directly from Genius.com.
- **Study Mode**: Analyze your favorite artists' tracks to understand their patterns and techniques.
- **Metadata Fetching**: Automatically retrieves album art, producer credits, and release dates.

### 📓 Journal & Learning
- **Daily Journaling**: Track your writing habit and creative thoughts.
- **Learning Modules**: (Coming Soon) Interactive lessons on poetic devices and hip-hop history.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.10+ with Flask
- **Frontend**: HTML5, CSS3 (Custom Design System), JavaScript (ES6)
- **Data**: JSON-based local storage (no heavy database setup required for local use)
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

To start the local development server:

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

3.  **Test specific component**:
    ```bash
    pytest tests/test_analysis.py
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
