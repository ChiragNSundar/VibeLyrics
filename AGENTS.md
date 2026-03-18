# Agents Guide to VibeLyrics

Welcome, AI Agent or Coding Assistant! This file (`AGENTS.md`) is your master manual for understanding, navigating, and building upon the VibeLyrics project. 

Whenever you enter this repository to assist a human developer, **read this entire document first**. It contains critical architectural decisions, strict aesthetic rules, and technical contexts that you must obey.

---

## 🎤 1. Core Mission & Vibe
**VibeLyrics** is a professional-grade hip-hop lyric writing assistant and analysis suite.
Our users are artists, rappers, and songwriters. They don't just want a "text editor." They want a creative environment that feels like a futuristic recording studio.

**Key Aesthetic: "Dreamy Glassmorphism"**
- The UI MUST feel premium, creative, immersive, and sleek.
- We use deep-space dark modes, aurora gradients, `backdrop-blur`, and frosted-glass cards.
- **Strict Rule:** Generic SaaS styling (plain white backgrounds, boring blue buttons, rigid grids) is strictly disallowed. Every UI change you make must include fluid transitions, hover effects, and a sense of depth (shadows/glows).

---

## 📐 2. Architecture & Tech Stack

VibeLyrics uses a robust, separated monolithic architecture:

### 💻 Frontend (React SPA)
- **Framework:** React 19 + TypeScript + Vite 7
- **Styling:** Tailwind CSS 4 (+ `clsx` and `tailwind-merge` for dynamic classes)
- **State Management:** Zustand 5. (We do NOT use Redux or Context API for heavy global state).
- **Animations:** Framer Motion 12. Most UI state changes should be wrapped in an `<AnimatePresence>` or `<motion.div>`.
- **Icons:** `@heroicons/react/24/outline` (and `solid`).

### 🔌 Backend (FastAPI Services)
- **Framework:** FastAPI (Python 3.11+)
- **Database:** SQLAlchemy 2 (Async) with `aiosqlite`. Persistence is handled locally via SQLite (`data/vibelyrics.db`).
- **Structure:**
  - `routers/`: API endpoints grouped by domain (`ai.py`, `lines.py`, `settings.py`).
  - `services/`: The brains. (`rhyme_detector.py`, `nlp_analysis.py`, `training_data.py`).
  - `schemas/`: Pydantic models for request/response validation.
  - `models/`: SQLAlchemy ORM definitions mapping to tables.

---

## 🧠 3. Advanced AI & NLP Engines (Read Carefully!)

This project contains several highly advanced mathematical and NLP-based engines. **Do not destructively modify these unless explicitly instructed.**

### 3.1 The Rhyme & Phonetic Engine
Located in `services/rhyme_detector.py`. This engine uses CMU dictionary sets and vowel/consonant matching algorithms to find multi-syllabic rhymes.
- It returns complex HTML highlighting data.
- The React frontend (`Editor.tsx` & `Lines.tsx`) relies on injecting this exact HTML to color-code assonance and consonance.

### 3.2 Automated RLHF & DPO (Phase 7 & 8)
VibeLyrics continuously learns from its user:
- **DPO (Direct Preference Optimization):** When a user rejects an AI suggestion and rewrites it, we log this as a (Chosen, Rejected) pair.
- **AI Arena:** A 4-way AI suggestion shootout. The winning line is "Chosen", the 3 losers are "Rejected" DPO pairs.
- **Concept Erasure:** We synthetically generate negative DPO pairs to teach the model to *unlearn* clichés (banned words).
- All of this logic happens inside `services/training_data.py`. Tracker classes (`SuggestionTracker`, `RLHFTracker`) act as **Singletons** instantiated inside the outer scope of the FastAPI router.

### 3.3 The Model Fallback Strategy
Located in `services/ai_provider.py`. The system attempts to generate text using Gemini 2.0. If rate-limited, it falls back to Gemini 2.0 Flash, then OpenAI, then a local LM Studio instance.

---

## 🚨 4. Iron-Clad Development Rules

As an AI, you must abide by these rules without exception:

1. **The `run.py` Rule:** The user *always* starts the app using `python run.py`. This script handles virtual environments (`.venv`), pip installations, npm installations, and environment variables. Do NOT instruct the user to run `npm start` or `uvicorn` manually.
2. **Do No Harm (Additive Changes):** When asked to add a feature, append it. Do not refactor core engine files (`rhyme_detector.py` or `.tsx` rendering logic) unless the user specifically asks you to "rewrite" or "repair" them.
3. **Absolute Imports over Relative:** In Python, use `from backend.services...`. In Vite/React, use standard relative paths that resolve correctly, avoiding deeply nested `../../../` if an alias (like `src/`) can be configured/used safely.
4. **No Skeleton Code:** If a user says "implement X", write the FULL code. Never return `// TODO: Implement logic here` inside a class/function.
5. **Stateful Singletons:** When you create a class to track state in FastAPI (like a buffer or vote logger), instantiate it globally outside the endpoint definitions. FastAPI endpoints are re-evaluated per request; local instances will get wiped.
6. **Linting Awareness (Fake Imports):** The user's IDE (`pyre2`) often cannot map the `run.py`-generated `.venv` paths. You will see fake lint errors complaining `Could not find import fastapi...`. **Ignore these.** The app runs perfectly. Do not try to fix these by injecting `sys.path.append()`.

---

## 🗺️ 5. Project Navigation Guide

If you need to know where something is, check this map:

- **Adding a new DB Table?** `backend/models/index.py` → run `db.create_all()` logic located in `database.py`.
- **Modifying the UI for the Editor?** `frontend/src/components/session/` (Look at `Editor.tsx`).
- **Adding a new API Endpoint?** Add it to the relevant file in `backend/routers/`, then immediately update `frontend/src/services/api.ts` with the corresponding fetch method.
- **Working on AI behavior?** `backend/services/ai_provider.py` (for models/prompts) and `backend/services/nlp_analysis.py` (for text analytics like complexity scores).
- **Training or LoRA config?** `backend/services/training_data.py` handles the file exports (JSONL Alpaca format) and LM Studio payload triggers.

*Stay creative, stay precise, and keep the vibes immaculate.*
