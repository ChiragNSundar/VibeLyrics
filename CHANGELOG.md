# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] - 2026-01-12

### 🚀 Major: FastAPI Backend Migration

The backend has been completely rewritten from Flask to **FastAPI**, creating a modern, high-performance asynchronous foundation for the application.

#### Core Improvements

- **Async Architecture**: Fully asynchronous request handling and database operations using `asyncio` and `SQLAlchemy`.
- **Performance**: Significant reduction in latency for high-concurrency operations.
- **Type Safety**: End-to-end type validation using **Pydantic** models.
- **Documentation**: Automatic interactive API documentation via Swagger UI.

#### New Features

- **Advanced Analysis Engine**:
  - **Punchline Scoring**: AI analysis of wordplay, contrast, and callback techniques.
  - **Metaphor Generation**: Context-aware metaphor and simile suggestions.
  - **Imagery Analysis**: Density analysis of visual, auditory, and tactile imagery.
- **Audio Intelligence**:
  - **BPM Detection**: Built-in audio analysis to detect beats per minute.
  - **Waveform Data**: Generation of visualization data for audio tracks.
  - **Adlib Suggestion**: Intelligent placement of flow, hype, and reaction adlibs.
- **Enhanced Linguistics**:
  - **Stress Pattern Detection**: Automatic meter analysis (e.g., `/x/x`) for rhythm perfection.
  - **Brainstorming**: Dedicated endpoints for generating creative themes and song titles.
- **Learning System**:
  - **Style Extraction**: Learns from your writing to adapt future suggestions.
  - **Vocabulary Tracking**: Monitors your favorite words and slang preferences.

### 🧪 Technical

- **Unified Runner**: New `run.py` script launches both Backend (Uvicorn) and Frontend (Vite) simultaneously.
- **Testing**: Comprehensive async test suite using `pytest-asyncio`.
- **Cleanup**: Removed legacy Flask blueprints and synchronous dependencies.

## [2.0.0] - 2026-01-12

### 🚀 Major: React SPA Migration

This release migrates the frontend from Flask/Jinja + Alpine.js to a **React SPA** (Vite + TypeScript) while keeping the Flask backend as a REST API.

#### Frontend (`/frontend`)

- **React 18** with TypeScript and Vite build system
- **Zustand** for global state management with undo/redo support
- **Framer Motion** for premium animations and transitions
- **React Router** for client-side navigation
- **react-hot-toast** for notifications

#### New Components

- `SessionPage` - Main writing interface with panel toggles
- `WorkspacePage` - Session list with creation form
- `LyricsEditor` - Line input with real-time SSE ghost text
- `LineRow` - Individual lyric line with edit/delete actions
- `RhymeWavePanel` / `AIHelpPanel` - Side panels with glassmorphism

#### Backend API Additions

- `GET /api/session/<id>/full` - Get full session data with highlighted lines
- `POST /api/session/create` - Create session via JSON API
- `POST /api/session/<id>/delete` - Delete session via API
- Enhanced `/api/sessions` with mood, theme, audio_path fields

#### Design System

- Ported 2800-line CSS to modular React styles
- Enhanced glassmorphism with backdrop-filter
- CSS variables for consistent theming
- Premium typography with Plus Jakarta Sans

### ⚡ Improved

- **Build Size**: 380KB JS (123KB gzipped), 17KB CSS (4KB gzipped)
- **Developer Experience**: Hot Module Replacement with Vite
- **State Management**: Centralized Zustand store vs. scattered Alpine.js

## [1.2.0] - 2026-01-09

### 🚀 Added

- **Tailwind CSS Integration**:
  - Properly integrated Tailwind CSS with custom theme extension for VibeLyrics aesthetic.
  - Added glassmorphism effects (`tw-backdrop-blur-md`) to stats dashboard and panels.
  - Enhanced workspace cards with hover scale animations and glow effects.
  - Updated navbar with smooth transitions and hover interactions.
- **Robust AI Model Rotation**:
  - Implemented automatic model fallback hierarchy for Gemini provider.
  - Chain: `gemini-2.5-flash` → `gemini-2.0-flash` → `gemini-2.0-flash-lite` → `gemma-3n-e4b-it`.
  - Automatically handles quota exhaustion (429 errors) and rotates to available models.
- **Enhanced Rhyme Detection**:
  - **Multi-Language Support**: Added phonetic rhyme detection for **Hindi** and **Kannada**.
  - **Expanded Rhyme Families**: Integrated 50+ new rhyme families including common verb endings (e.g., -odu, -ana) and noun patterns.
  - **Phonetic Matching**: Improved algorithm to detect slant rhymes based on vowel sounds and coda compatibility across languages.

### ⚡ Improved

- **Session UI Redesign**:
  - Replaced right-side AI panel with **Left-Side Split Panels** for better workflow.
  - Added floating toggle buttons for **RhymeWave** (🌊) and **AI Help** (🤖).
  - Panels are non-intrusive and hidden by default.
- **Ghost Text UX**:
  - Enhanced visibility with brighter purple color and text shadow.
  - Added italic styling to better distinguish from user input.
- **Audio Upload**:
  - Added loading indicator during beat upload.
  - Improved error handling and initialization for the waveform player.

### 🐛 Fixed

- **Layout Stability**: Fixed broken HTML structure (extra closing tags) that caused buttons to malfunction.
- **AI Error Handling**: Fixed issue where API error JSON was displayed as ghost text suggestions.
- **CSS Conflicts**: Resolved specificity issues between vanilla CSS and Tailwind.

## [1.1.0] - 2026-01-08

### 🚀 Added

- **Real-Time AI Streaming**: Added Server-Sent Events (SSE) support for streaming lyric suggestions.
  - New endpoint: `/api/line/stream`
  - Updated `OpenAIProvider` to support streaming chunks.
  - Frontend integration with `EventSource` for ghost text.
- **Offline Support**: Implemented Service Worker (`sw.js`) to cache static assets and rhyme dictionaries.
- **Full-Text Search**: Integrated **Whoosh** for local, fuzzy search of past sessions.
- **Power Tools**:
  - **Undo/Redo**: 10-step history stack for text operations.
  - **Shortcuts**: `Ctrl+Enter` (Submit), `Ctrl+Z` (Undo), `?` (Help).
- **Frontend Architecture**:
  - Added **Alpine.js** for reactive UI components (`alpine-components.js`).
  - Added **Service Worker** registration.
- **Backend Architecture**:
  - Added **Celery** + **Redis** for asynchronous background tasks.
  - Added **Docker Compose** configuration for full stack deployment.

### ⚡ Improved

- **Performance**:
  - Implemented lazy-loading for RhymeWave iframe.
  - Added debouncing (300ms) to autocomplete inputs.
- **Code Quality**:
  - Extracted 50+ inline styles from `session.html` to `style.css`.
  - Added JSDoc type hints to core JavaScript functions.
  - Refactored `session.js` to use reusable `sidebarPanel` component.

### 🐛 Fixed

- Fixed HTML scope issue preventing RhymeWave tab from lazy-loading correctly.
- Cleaned up documentation structure and duplicate technology stack entries.
