# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

### ⚡ Improved

- **Ghost Text UX**:
  - Enhanced visibility with brighter purple color and text shadow.
  - Added italic styling to better distinguish from user input.
- **Reference Panel**:
  - Improved split-view layout to prevent overlapping main content.
  - Panel is now hidden by default until split-view is toggled.

### 🐛 Fixed

- **AI Error Handling**: Fixed issue where API error JSON (e.g., "Your quota exceeded") was displayed as ghost text suggestions.
- **CSS Conflicts**: Resolved specificity issues between vanilla CSS and Tailwind by managing preflight and layer ordering.

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
