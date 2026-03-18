# Agents Guide to VibeLyrics

Welcome, fellow agent! This file (`AGENTS.md`) provides critical context on the VibeLyrics project. Whenever you interact with this repository, read this document to understand the architecture, guidelines, and philosophy before making changes.

---

## 🎤 Project Overview
**VibeLyrics** is a professional-grade hip-hop lyric writing assistant and analysis suite.
It uses advanced AI (Gemini, Claude, OpenAI, Local LLMs), NLP algorithms (syllable detection, rhyme matching), and a robust React/FastAPI architecture to help artists write better lyrics.

**Key Aesthetic:** "Dreamy Glassmorphism." The UI should feel premium, creative, and immersive. Deep-space backgrounds, frosted-glass cards, and smooth Framer Motion animations. Generic styling is strictly disallowed.

---

## 📐 Architecture Snapshot

- **Frontend:** React 19, TypeScript, Vite 7, Tailwind CSS 4, Zustand 5, Framer Motion 12.
- **Backend:** FastAPI (Python 3.11+), SQLAlchemy 2 (Async), AIOSQLite.
- **AI Core:** LangChain concepts without the bloat. Custom endpoints in `backend/routers/ai.py` handle context management. Support for multi-provider fallback.
- **Advanced Features:** Rhyme scoring, complexity meters, semantic drift detection, AI Arena (Automated RLHF), Continual Learning, and Concept Erasure.
- **Persistence:** Local SQLite (`data/vibelyrics.db`). Training logs, DPO pairs, and session exports live in `data/`.

---

## 🛠️ The `run.py` Script (Your Best Friend)
**DO NOT manually run standard npm/pip commands unless debugging.**
The user relies on `run.py` to launch the app. It handles virtual environments, dependency syncing, and port management automatically.

- Start app: `python run.py`
- Fast start (skip installs): `python run.py --skip-install`

---

## 🚨 Strict Development Rules

1. **Do No Harm:** When modifying existing files, your edits should be additive or strictly non-destructive unless the user explicitly requests a rewrite. Never break existing features (e.g., the complex rhyme highlighting logic in `Lines.tsx`).
2. **Absolute Imports:** Always use absolute paths or proper relative paths that resolve correctly in both Vite and Python.
3. **Handle Fast Feedback Loops:** If making UI changes, ensure they are responsive and animated. Use Framer Motion (`<motion.div>`) for state transitions.
4. **Backend Singletons:** When adding stateful classes to FastAPI routers (like `SuggestionTracker` or `ContinualLearningManager`), instantiate them globally near the top of the router to avoid wiping state on every request.
5. **No Placeholders:** If you are asked to implement a feature, write the actual working code. Do not write `// TODO: implement logic here`.
6. **Linting Awareness:** The Pyre2 linter in this IDE setup often fails to resolve the virtual environment correctly. You may see fake `ImportError: Could not find import...` for standard library or installed packages (`fastapi`, `sqlalchemy`). **Ignore these fake import errors and proceed.**

---

## 🗺️ Navigation Highlights

- **`frontend/src/components/session/`**: The heart of the app. Look here for `Editor.tsx`, `RhymeCompleter.tsx`, `WordExplorer.tsx`, and `Lines.tsx`.
- **`backend/services/`**: The core intelligence.
  - `rhyme_detector.py` (Phonetics and highlighting)
  - `nlp_analysis.py` (Complexity, drift, wordplay)
  - `training_data.py` (DPO, RLHF, Continual Learning)
- **`backend/routers/`**: The API surface. `ai.py` (Ghostwriter, Arena), `lines.py` (CRUD, streaming), `training.py` (Fine-tuning orchestration).

---

## 🚀 Recent Upgrades (Phase 7 & 8)
If you are modifying AI or Training features, be aware that VibeLyrics currently supports:
- **DPO Preference Pairs:** Rejecting an AI suggestion + writing your own sends a negative training signal.
- **AI Arena:** 4-way shootout for the best line, generating RLHF data.
- **Continual Learning:** Silent buffering of high-complexity lyrics to auto-train background LoRAs.
- **Concept Erasure:** Synthetic DPO pairs designed to surgically unlearn clichés.
- **LM Studio Integration:** Automated API triggers to launch model training runs locally.

*Stay creative, write clean code, and keep the vibes immaculate.*
