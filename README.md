# VibeLyrics 🎤

**VibeLyrics** is a professional-grade hip-hop lyric writing assistant and analysis suite. It combines a distraction-free writing environment with advanced algorithmic analysis, AI styling, and full production tools to help artists craft complex rhymes and flows.

---

## 🌟 Key Features

### 📖 Smart Writing Interface

- **Split View Mode**: View reference tracks or past sessions side-by-side while writing.
- **Teleprompter View**: Auto-scrolling, high-contrast view for recording sessions.
- **Smart Dictionary**: Right-click *any* word for 6-layer analysis (Rhymes, Synonyms, Slang, Emotional intensity).
- **Export Options**: Export to PDF (styled), TXT, or JSON backup.

### 🎨 AI Style Transfer

Write in the signature style of legendary artists:
- **Available Styles**: Eminem, Kendrick Lamar, Drake, J. Cole, Nas, Travis Scott, Jay-Z, Kanye West.
- **Style Characteristics**: Mimics rhyme patterns, vocabulary density, and flow structures.
- **Transformation**: Rewrite your lines to match a specific artist's voice.

### 📊 Stats & Gamification

- **Writing Dashboard**: Track lines written, vocabulary growth, and daily consistency.
- **Rhyme Scheme Analysis**: See which schemes you use most (AABB, ABAB, Compound).
- **Achievements**: Unlock badges for streaks, complex multi-syllabics, and flow mastery.

### 🔍 Search & Recall

- **Full-Text Search**: Instantly find any line you've ever written, even with typos (fuzzy matching).
- **Phonetic Search**: Find lines from your history that *sound* like your current idea.
- **Callback Detection**: Automatic alerts when you reference your past work (perfect for callbacks).

### ⚡ Background Processing

- **Async AI Generation**: Get suggestions without freezing your interface.
- **Audio Analysis**: Background BPM detection and waveform generation.
- **Task Queue**: Robust job processing powered by Celery & Redis.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.10+ with Flask
- **Frontend**: Custom HTML5/CSS3 Design System + Vanilla JS
- **Search Engine**: **Whoosh** (Pure Python Full-Text Search)
- **Task Queue**: **Celery** + **Redis** (Async processing)
- **Real-time**: Flask-SocketIO (WebSockets)
- **AI**: OpenAI GPT-4, Google Gemini, Perplexity
- **Audio**: Librosa & Wavesurfer.js

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Docker & Docker Compose (Recommended)

### Quick Start (Docker)

The easiest way to run VibeLyrics with all features (Search, Redis, Celery) enabled.

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/vibelyrics.git
   cd vibelyrics
   ```

2. **Configure Environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys (OPENAI_API_KEY, GEMINI_API_KEY)
   ```

3. **Launch**:
   ```bash
   docker-compose up -d
   ```
   Access the app at `http://localhost:5000`

### Manual Installation (Local)

1. **Install Dependencies**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Run Redis** (Required for background tasks):
   ```bash
   redis-server
   ```

3. **Start Worker** (In data terminal):
   ```bash
   celery -A app.celery_app:celery_app worker --loglevel=info
   ```

4. **Start App**:
   ```bash
   python run.py
   ```

---

## 🔍 API Documentation

### Search API
- `GET /api/search?q=<query>` - Full text search
- `GET /api/search/rhymes?word=<word>` - Phonetic rhyme search
- `POST /api/search/reindex` - Rebuild search index

### Style API
- `GET /api/styles` - List available artist styles
- `POST /api/line/transform` - Style transfer

### Stats API
- `GET /stats/api/overview` - Writing stats
- `GET /stats/api/history` - Activity charts

---

## 🐳 Docker Services

| Service | Description | Port |
|---------|-------------|------|
| `vibelyrics` | Main Web Application | 5000 |
| `vibelyrics-redis` | Message Broker & Cache | 6379 |
| `vibelyrics-celery` | Background Task Worker | - |
| `vibelyrics-beat` | Scheduled Tasks | - |

---

## 🤝 Contributing

Contributions are welcome! Please run tests before submitting PRs:

```bash
pytest
```

## 📄 License

Distributed under the MIT License.
