# 🤖 Master Agents Guide to VibeLyrics

Welcome, AI Agent, LLM Coding Assistant, or Human Contributor! This file (`AGENTS.md`) is your master structural manual for fully understanding, navigating, and building upon the VibeLyrics project. 

Whenever you are summoned into this repository, **parse this entire document first**. It provides critical architectural flow, strict UI rules, and backend state paradigms to prevent breaking existing systems.

---

## 🎤 1. Core Mission & Design Philosophy
**VibeLyrics** is a professional-grade hip-hop lyric writing assistant and analysis suite.
It uses advanced AI (Gemini, Claude, OpenAI, Local LLMs), NLP algorithms (syllable detection, rhyme matching), and a robust React/FastAPI architecture to help artists write better lyrics.

**Key Aesthetic: "Dreamy Glassmorphism"**
- The UI MUST feel premium, creative, immersive, and sleek.
- We use deep-space dark modes, aurora gradients, `backdrop-blur`, and frosted-glass cards.
- **Strict Rule:** Generic SaaS styling (plain white backgrounds, boring blue buttons, rigid grids) is strictly disallowed. Every UI change you make must include fluid transitions, hover effects, and a sense of depth (shadows/glows).

---

## 📐 2. The Complete Architecture Stack

VibeLyrics uses a robust, separated monolithic architecture running locally on the user's machine.

### 💻 Frontend (React SPA)
- **Core Framework:** React 19 + TypeScript + Vite 7
- **Styling:** Tailwind CSS 4 (+ `clsx` and `tailwind-merge` for safe dynamic classes).
- **State Management:** Zustand 5. Global state is split into `sessionStore.ts` (lyrics, editor state) and `settingsStore.ts` (API keys, preferences). We do NOT use Redux or Context API for heavy global state.
- **Animations:** Framer Motion 12. Most UI state changes, popups, and lists should be wrapped in an `<AnimatePresence>` and `<motion.div>`.
- **Icons:** `@heroicons/react/24/outline` (and `solid`).

### 🔌 Backend (FastAPI Services)
- **Framework:** FastAPI (Python 3.11+) handles REST and Event-Stream APIs via `backend/main.py`.
- **Database:** SQLAlchemy 2 (Async) with `aiosqlite`. Persistence is handled locally via SQLite (`vibelyrics.db`).
- **Data Models:** Lives in `backend/models/`. Key tables: `LyricSession`, `LyricLine`, `JournalEntry`, `UserSetting`, `SuggestionLog`.
- **Configuration:** Settings are loaded via `pydantic_settings` in `backend/config.py` (reads `.env` for `GEMINI_API_KEY`, etc.).

---

## 🧠 3. Advanced NLP & AI Engines (Read Carefully!)

This project contains several highly complex NLP-based engines. **Do not destructively modify these unless explicitly instructed. Always build alongside them.**

### 3.1 The Rhyme & Phonetic Engine (`services/rhyme_detector.py`)
- This engine uses CMU dictionary sets (`pronouncing` library) and custom phonetic algorithms to find multi-syllabic rhymes.
- **Critical Flow:** It returns complex HTML strings with injected `<span>` tags for syntax highlighting (assonance, consonance). The React frontend (`Lines.tsx`) relies on injecting this exact HTML using `dangerouslySetInnerHTML`. Do not break this contract.

### 3.2 Automated RLHF, DPO & Continual Learning (`services/training_data.py`)
VibeLyrics continuously learns from the artist's style:
- **DPO (Direct Preference Optimization):** When users reject AI ghostwritten lines, we generate (Chosen, Rejected) pairs.
- **AI Arena:** A 4-way suggestion shootout that creates massive amounts of DPO data.
- **Concept Erasure:** Synthetic negative DPO generation to unlearn clichés via banned words lists.
- **Continual Learning:** A `ContinualLearningManager` buffers high-complexity lines from `lines.py` to auto-trigger downstream PyTorch/Unsloth LoRA training.
- **Stateful Singletons:** Trackers for these systems (`SuggestionTracker`, `RLHFTracker`, `ContinualLearningManager`) act as **Singletons** instantiated in router files (like `training.py`) to bypass FastAPI's stateless workers.

### 3.3 Semantic Analysis & Drift (`services/nlp_analysis.py`)
- Calculates semantic complexity, text flow, vocabulary age, and "Semantic Drift" (to warn the user if verse 2 loses the topic of verse 1).

---

## 🚨 4. Iron-Clad Development Rules

As an AI, you must abide by these rules without exception:

1. **The `run.py` Rule:** The user runs the entire app exclusively through `python run.py`. It manages the `.venv`, pip installs, npm installs, and starts both frontend/backend concurrently. **DO NOT** instruct the user to run `npm run dev` or `uvicorn` manually.
2. **Do No Harm (Additive Changes):** When asked to add a feature, append it. Do not refactor core engine files unless explicitly asked.
3. **Absolute Imports over Relative:** In Python, use `from .database import ...` or `from ..services import ...`. In Vite/React, refer to the path clearly.
4. **No Skeleton Code:** Write the FULL code for a file structure. Avoid dumping `// TODO: Implement logic here` inside classes/functions.
5. **Linting Awareness (Fake Imports):** The Pyre2 linter struggles to map `run.py`-generated `.venv` paths dynamically. You will see fake lint errors like `Could not find import fastapi...`. **Ignore these.** Do not inject `sys.path.append()` hacks to fix IDE ghosts.
6. **Database Schema Changes:** We rely on `Base.metadata.create_all()` on startup and do not use Alembic. If you add a new column or table, you must inform the user to either run a manual SQL `ALTER TABLE` or delete `data/vibelyrics.db` and restart to recreate the schema.
7. **Quality Assurance:** If building new core features, remember we have `backend/tests/` (Pytest) and frontend tests (Vitest/Playwright). Ensure your code is testable and robust.

---

## 🗺️ 5. Directory Navigation Map

When you need to know where a specific piece of logic lives:

### Backend structure (`frontend` omitted here)
```text
backend/
 ├── main.py             # Loads all 14+ routers (`/api/*`) and sets CORS
 ├── config.py           # Pydantic BaseSettings (.env loading config)
 ├── database.py         # SQLAlchemy AsyncEngine setup
 ├── models/             # ORM declarations (tables structure)
 ├── schemas/            # Pydantic input/output validation models
 ├── routers/            # API endpoints mapping (e.g. ai.py, lines.py, training.py)
 └── services/           # Heavy compute and integrations
     ├── ai_provider.py  # LLM fallbacks (Gemini -> OpenAI -> Local)
     ├── rhyme_detector.py # CMU Dict syllable processing
     ├── nlp_analysis.py # Concept and complexity math
     └── training_data.py# Singletons tracking RLHF, Arena, DPO
```

### Frontend structure
```text
frontend/
 ├── index.html
 ├── src/
 │   ├── App.tsx         # Main entry, global UI wrappers
 │   ├── components/     # UI
 │   │   ├── session/    # Editor components, AudioVisualizer, RhymeCompleter
 │   │   └── stats/      # Charts (Recharts), Dashboards
 │   ├── pages/          # Full screen routable views
 │   ├── services/       # api.ts (ALL FETCH CALLS GO HERE)
 │   └── store/          # Zustand global state
 │       ├── sessionStore.ts
 │       └── settingsStore.ts
```

*Final Directive: Analyze the context, preserve the dreamy vibe, write robust async connections, and execute flawlessly.*
