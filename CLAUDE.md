# System Prompt & Context for Claude / Cursor

This `.md` file provides direct system instructions, rigid coding conventions, and workflow rules for AI coding assistants working in the VibeLyrics workspace. Execute these parameters natively as if they were your system prompt.

## 🏗️ 1. Technical Baseline
- **Frontend Core:** React 19, TypeScript, Vite 7.
- **Frontend Design:** Tailwind CSS 4, Framer Motion 12, Zustand 5.
- **Backend Core:** FastAPI (Python 3.11+), Pydantic schemas.
- **Backend Database:** SQLAlchemy 2.0 (Async), AIOSQLite (`vibelyrics.db`).
- **Environment:** Unified project running locally.

## 🚀 2. Local Environment Execution
The user runs the application strictly through a unified auto-launcher:
- **`python run.py`**
- Do NOT advise the user to use standard package managers (`npm i`, `pip install`) or run servers (`uvicorn`, `npm run dev`) manually. `run.py` handles the `.venv`, port assignment (5173 / 5001), and dependency synchronization automatically.

## 💅 3. The React/Tailwind Dictate
When modifying or creating React files:
1. **Dreamy Glassmorphism:** We employ an ethereal, dark-space, frosted-glass aesthetic.
2. **Mandatory Classes:** Rely on `backdrop-blur-md`, `bg-black/30`, `bg-white/5`, `border-white/10`.
3. **Animations are Required:** Any modal, popover, dropping list, or toast notification MUST be wrapped in `<AnimatePresence>` and utilize `<motion.div>`.
4. **State Management:** Use `frontend/src/store/` (Zustand) for global states (e.g., active sessions, API keys). Do not add heavy Context API providers.
5. **Sanitization Rules:** The `Lines.tsx` component handles raw HTML from the backend RhymeEngine via `dangerouslySetInnerHTML`. Treat this specific implementation with extreme care.

## ⚙️ 4. The FastAPI/SQLAlchemy Dictate
When modifying or creating backend Python files:
1. **100% Async SQLite:** Use `await db.execute(select(Model))` and `result.scalars().all()`. Never write synchronous DB pulls on the main thread.
2. **Pydantic Validation:** All data entering a route in `routers/` must be mapped via a Schema in `schemas/`. Do not pass untyped dictionaries into routes.
3. **Service Segregation:** API Endpoint logic goes in `routers/`. Algorithmic calculation, database formatting, file I/O, and LLM polling go in `services/`.
4. **AI Generation Hierarchy:** Use the abstracted utilities in `services/ai_provider.py`. Do not import `google.generativeai` directly into random routers; filter it through the provider service for rate-limit fallbacks.
5. **Memory State Retention (Singletons):** FastAPI processes requests statelessly. To persist memory in-app (e.g., Continual Learning buffers or Session Trackers), declare class instances globally at the top of the Router file, rather than inside the endpoint definitions.

## 🔗 5. The API Pipeline Checklist
If the user asks you to implement a full feature spanning front and back, obey this sequence:
1. Add/modify `backend/schemas/` models.
2. Build heavy logic inside `backend/services/`.
3. Wire the endpoint up securely in `backend/routers/`.
4. Add the endpoint to `backend/main.py` if creating a completely new router.
5. **CRUCIAL:** Create a strictly-typed fetch wrapper inside `frontend/src/services/api.ts`.
6. Bind the `api.ts` call inside your React component or Zustand store.

## 🐛 6. Ignored Lint Errors (Pyre2 Virtual Environment issues)
Because `run.py` generates the `.venv` dynamically, IDEs using Pyre2 fail to resolve fundamental import paths (e.g., `fastapi`, `sqlalchemy`, or relative paths like `..services`).
- **You will inevitably see hundreds of `Could not find import...` errors in the IDE feedback.**
- **YOUR DICTATE:** Ignore them entirely. Do not attempt to fix them via `sys.path.append()` or writing stub files. Confidently write functional code and ignore these false flags.
