# VibeLyrics Context for Claude / Cursor

This file provides detailed system instructions, coding conventions, and workflow rules for AI coding assistants working within the VibeLyrics workspace. Use this as your technical reference guide alongside `AGENTS.md`.

## 🏗️ 1. Project Architecture Detail
- **Frontend:** React 19, TypeScript, Vite 7.
- **Styling:** Tailwind CSS 4.
- **Components:** Functional components, strict TypeScript typing for props.
- **Backend:** FastAPI (Python 3.11+), returning JSON responses.
- **Database:** SQLAlchemy 2.0 (Async pattern) over AIOSQLite. Models map to `data/vibelyrics.db`.

## 🚀 2. Local Environment & Execution
The application strictly uses a unified launcher:
- **Run the Stack:** `python run.py`
- **Fast Restart:** `python run.py --skip-install`
- The script manages the `.venv` directory, handles port bindings (Frontend: 5173, Backend: 5001), and syncs requirements.
- **NEVER** instruct the user to run `npm run dev` or `uvicorn` in separate terminals unless explicitly debugging a crash that `run.py` masks.

## 💅 3. Frontend Coding Conventions
When writing React code, follow these patterns strictly:

### Tailwind & Aesthetic
- We utilize a **Dreamy Glassmorphism** aesthetic.
- **Always** combine Tailwind classes smartly. Use `clsx` and `twMerge` (via a utility `cn()` if available, or directly) when accepting `className` props.
- Avoid flat colors. Use transparency (`bg-white/10`, `border-white/20`), backdrop filters (`backdrop-blur-md`, `backdrop-blur-xl`), and intense glowing shadows (`shadow-[0_0_15px_rgba(255,255,255,0.1)]`).
- Elements should respond to hover: `hover:bg-white/20 hover:scale-[1.02] transition-all duration-300`.

### State Management
- Global state is handled by **Zustand** (look in `frontend/src/store/`).
- If you add a new global feature (like a new settings toggle or a training mode status), create or update a Zustand slice. 
- Avoid prop-drilling more than 2 levels deep.
- Local UI state (like dropdown open/close) should use `useState`.

### Animations
- Use **Framer Motion**.
- Lists rendering dynamic items should use `motion.ul` and `motion.li` with `{ layout: true, initial: { opacity: 0, y: 10 }, animate: { opacity: 1, y: 0 } }`.
- Modals, popovers, and conditional renders must be wrapped in `<AnimatePresence>`.

## ⚙️ 4. Backend Coding Conventions
When writing Python code for FastAPI:

### Async Everywhere
- We use AIOSQLite. **All database operations must be `await`ed.**
- Example: 
  ```python
  result = await db.execute(select(LyricLine).where(LyricLine.id == id))
  line = result.scalar_one_or_none()
  ```
- File I/O should preferably be an async operation if dealing with massive datasets, or offloaded to a background task (`BackgroundTasks` from FastAPI).

### Pydantic Validation
- Data payloads coming into routers must be validated via Pydantic `BaseModel` classes defined in `backend/schemas/`.
- Do not use raw dictionaries for incoming request bodies (`@app.post("/endpoint") async def endpoint(data: dict)` is strictly forbidden).

### Router & Service Separation
- **Routers (`backend/routers/`):** Should ONLY handle HTTP requests, path parameter validation, dependency injection (like getting the `db` session), and returning standard HTTP responses/errors.
- **Services (`backend/services/`):** All heavy lifting belongs here. If it involves regex, API calls to Gemini, filesystem manipulation, or complex math, it belongs in a service module and is imported by the router.

## 🐛 5. Known Quirks & Linter Exemptions
- **Pyre2 `.venv` Resolution:** Pyre2 will flag standard Python library imports (`os`, `json`) and installed packages (`fastapi`, `sqlalchemy`) as `Could not find import...`. This is a false positive due to the dynamic creation of `.venv` by `run.py`. 
  - **Your Action:** Ignore these completely. Do not comment on them, do not suggest fixing the Python interpreter path, and do not let them block your code generation.
- **Singletons in ASGI:** FastAPI runs workers asynchronously. If you need a service to preserve memory state (e.g., a buffer for Continual Learning or a dictionary holding RLHF votes), establish the class instance globally at the top of the router file, NOT inside the path operation function.

## 🤝 6. API Integration Workflow
If you are asked to create a new feature that spans the full stack, you must:
1. Create the Pydantic schema (`schemas/`).
2. Implement the logic in a service (`services/`).
3. Connect it to a FastAPI route (`routers/`).
4. **CRITICAL:** Update `frontend/src/services/api.ts` to include a typed helper function for the new endpoint.
5. Build the React component calling that `api.ts` function.
