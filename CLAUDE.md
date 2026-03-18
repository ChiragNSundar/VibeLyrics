# VibeLyrics Context for Claude / Cursor

This file provides system instructions for AI coding assistants working in this repository. 

## Project Architecture
- **Frontend:** React 19, TypeScript, Vite 7, Tailwind 4, Zustand 5, Framer Motion
- **Backend:** FastAPI (Python 3.11+), SQLAlchemy 2 (Async), AIOSQLite
- **Local State/Data:** Handled in the `data/` directory at the project root.

## Development Workflows

### 1. Running the App
The user runs the app exclusively via `python run.py`. This script starts both the FastAPI backend and the Vite frontend. Do not tell the user to run `npm start` or `uvicorn` manually.

### 2. Frontend Conventions
- **Styling:** We use Tailwind CSS 4 with a "dreamy glassmorphism" aesthetic. Heavy use of `backdrop-blur`, `bg-black/50`, gradients, and glowing borders.
- **State:** Use Zustand (`src/store/`) for global state. Do not use Redux.
- **Animations:** Use `framer-motion` for page transitions, popovers, and list staggering.
- **Icons:** Use `@heroicons/react/24/outline` or `solid`.
- **Components:** Functional components only, strict TypeScript types.

### 3. Backend Conventions
- **Routing:** API endpoints are grouped by module under `backend/routers/` (e.g., `ai.py`, `lines.py`, `training.py`).
- **Services:** Heavy business logic (NLP, AI prompting, phonetics) lives in `backend/services/`.
- **Database:** All database calls must be async (`db.execute(select(...))`). We use Pydantic models for validation in `backend/schemas/`.
- **Global State:** Trackers (like Suggestion logs, RLHF logs) should be instantiated as global singletons inside the router files or module scope to persist across requests.

### 4. Ignore False Positive Lints
The `pyre2` linter configured in the user's environment struggles to resolve the dynamic `.venv` paths created by `run.py`.
**Crucial:** You will see fake `Could not find import...` errors for packages like `fastapi`, `pydantic`, `sqlalchemy`, and local module paths. Ignore these errors. Do not try to rewrite paths or `sys.path.append()` to fix them.

## Key Features to Respect
- **AI Arena & RLHF:** `training_data.py` handles DPO pairs generated from rejected UI suggestions and AI Arena votes.
- **Complex Highlighting:** The RhymeEngine highlights internal rhymes using HTML span injection. Do not break the HTML sanitization flow in `frontend/src/components/session/Lines.tsx`.
- **Dynamic Training:** The app allows exporting datasets and auto-triggering local fine-tuning scripts via LM Studio. When modifying `training.py`, ensure the export paths to `data/training/` remain intact.
