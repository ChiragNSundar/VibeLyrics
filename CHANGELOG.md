# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
