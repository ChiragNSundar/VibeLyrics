# Changelog

All notable changes to the **VibeLyrics** project will be documented in this file.

## [2.5.0] - 2026-02-26

### 🧠 AI Quality

- **System instruction** — Ghostwriter persona set at model level via `system_instruction`, not repeated per prompt
- **Temperature 0.9** — Creative output with `top_p=0.95`, `top_k=40` for better variety
- **Few-shot examples** — 3 style-matching examples included in every prompt for better adherence
- **Prompt caching** — Session context cached per `session_id`, avoids rebuilding on every keystroke

### 🎓 AI Learning Center (New Dashboard)

- **Live Web Scraper** — Enter an artist and era (e.g., "Kendrick Lamar DAMN") to automatically search DDG and scrape their latest lyrics directly into the AI's brain.
- **Terminal Feed** — Watch the scraper work in real-time via a Server-Sent Events (SSE) terminal UI.
- **Manual Document Uploads** — Paste raw lyrics or upload `.txt`, `.pdf`, and `.docx` files to teach the AI specific songs or poetry.
- **Visual Knowledge Base** — See exactly what the AI has learned: Dominant Themes, Rhyme Preferences, Signature Words, Slangs, and Avoided Words.
- **Brain Wiper** — Safely delete specific words from the AI's vocabulary, or wipe the brain completely to start fresh.

### ✨ New Features

- **Export lyrics** — Copy to clipboard (📋) and download as `.txt` (⬇️) buttons in stats bar
- **Syllable target guide** — BPM-based target range with color-coded indicator (under/good/over)
- **Auto-save indicator** — ⏳ Saving → ✅ Saved badge in stats bar
- **Word/line/syllable stats** — Real-time running totals at top of editor
- **Drag-to-reorder lines** — Grab and drag lines to rearrange verse structure

### 🔧 Backend

- **`GET /learning/scrape/stream`** — New SSE endpoint for live scraping progress
- **`POST /learning/upload`** — New endpoint handling file uploads (`python-docx`, `PyPDF2`)
- **`POST /lines/reorder`** — New endpoint for persisting line order with re-highlighting

## [2.4.4] - 2026-02-26

### 🔴 Critical Fix: AI Provider

- **Updated Gemini models** — `gemini-2.0-flash` (discontinued) → `gemini-2.5-flash-lite` with fallback to `gemini-2.5-flash`
- **Fixed async blocking** — All Gemini calls now use `generate_content_async()` instead of sync `generate_content()` which was freezing the event loop and causing timeouts
- **Fixed SSE streaming** — Streaming now uses `async for chunk` instead of sync `for chunk`, so autocomplete suggestions actually stream to the frontend
- **Model fallback chain** — If `gemini-2.5-flash-lite` fails (404/deprecated), automatically tries `gemini-2.5-flash`
- **Preferred model cached** — After first successful call, the working model is remembered for speed
- **Better error handling** — Rate limit (429), quota, and transient errors trigger model fallback instead of silent failure

## [2.4.3] - 2026-02-26

### 🐛 Bug Fixes

- **Provider switch endpoint fixed** — Frontend was calling `/api/provider/switch` instead of `/api/ai/switch-provider`
- **Singleton `RhymeDetector` in rhymes router** — Consistent with lines/sessions routers
- **LM Studio availability dynamic** — Settings page now detects if LM Studio is actually running
- **Vocabulary CRUD wired to DB** — `add_vocabulary` / `remove_vocabulary` actually persist to UserProfile

### ✨ New Features

- **404 page** — Catch-all route with on-brand "This verse doesn't exist yet" page
- **`useKeyboardShortcuts` hook** — Undo/redo now uses centralized hook instead of inline listeners

### 🔧 Improvements

- **`requirements.txt` cleaned** — Removed dead `redis` dep, replaced `duckduckgo-search` with `ddgs`, removed duplicate `requests`
- **Backend tests updated** — Tests now verify `all_lines`, `complexity_score`, empty input rejection, and `has_internal_rhyme` backfill

## [2.4.2] - 2026-02-26

### 🐛 Bug Fixes

- **LineRow save now refreshes all highlights** — Editing a line re-renders cross-line rhyme highlighting via `all_lines` response
- **Session delete endpoint fixed** — Was using wrong path and method (`POST /session/{id}/delete` → `DELETE /sessions/{id}`)
- **✨ Improve button wired up** — Now calls `/api/ai/improve` and presents the AI-improved line for review
- **Lyrics scraper fixed** — DuckDuckGo result key corrected from `href` to `link`
- **`complete_rhyme` fixed** — Was calling non-existent `provider.generate()`, now uses `answer_question()`
- **Store undo/redo uses `all_lines`** — Both `addLine` and `updateLine` in Zustand store update all highlights

### ✨ New Features

- **LM Studio provider** — Full local AI support via OpenAI-compatible API at `localhost:1234`
- **Keyboard shortcuts** — `Ctrl+Z` / `Cmd+Z` for undo, `Ctrl+Y` / `Cmd+Shift+Z` for redo
- **Complexity badge** — Each line shows 🔥 (high), 📝 (mid), or 💡 (low) complexity indicator
- **Loading states** — Save and improve buttons show ⏳ while processing

### 🔧 Improvements

- **Undo history increased** — From 10 to 50 actions
- **`rhymeScheme` prop connected** — Session's rhyme scheme flows through to `AnalysisStrip`

## [2.4.1] - 2026-02-26

### 🐛 Bug Fixes & Logic Improvements

- **Fixed version string** — API now correctly reports v2.4.0 at `/docs` and `/`
- **Replaced dead Redis cache** — Rewrote `cache.py` with a thread-safe in-memory TTL cache (no external deps)
- **Fixed rhyme highlights not appearing** — Frontend now uses `all_lines` response to re-render all highlights after adding a line
- **Complexity scoring** — `complexity_score` is now computed on every line add/update (vocabulary diversity, multi-syllable ratio, word length)
- **Singleton RhymeDetector** — Avoids re-loading the CMU dictionary on every API request
- **Fixed `datetime.utcnow` deprecation** — All model timestamps now use `datetime.now(timezone.utc)`
- **Fixed README port mismatch** — Manual mode docs now show correct port 5001
- **Backfill `has_internal_rhyme`** — Pre-v2.4.0 lines are automatically detected on session load
- **Input validation** — API now rejects empty/whitespace-only line content with 400 error
- **Disabled SQL echo by default** — `debug` defaults to `False`, no more spammed SQL logs
- **`rhymeScheme` prop connected** — Session's detected rhyme scheme now passed to `AnalysisStrip`
- **Secured file upload** — `upload_audio` now has 50MB limit, audio-only type whitelist, and filename sanitization

## [2.4.0] - 2026-02-25

### ✨ New Features

- **Advanced Rhyme Analysis Engine**: Upgraded the rhyme detector to a 7-layer phonemic analysis system:
  - **Perfect Rhymes**: Solid highlight (e.g., *bars/scars/mars*)
  - **Near/Slant Rhymes**: Dashed border for words with 1 phoneme difference (e.g., *time/mind*)
  - **Assonance**: Colored bottom-border for shared stressed vowels
  - **Consonance**: Dotted underline for shared consonant skeletons
  - **Internal Rhymes**: Purple left-border for within-line rhymes (+ 🔗 badge on the line)
  - **Multi-syllable Rhymes**: Gold glow and pulse effect for 2+ syllable matches
  - **Alliteration**: Italic underline for shared starting consonants
- **Sub-word Highlighting**: Only the rhyming *portion* of a word gets colored (e.g., sc**ars**) via phoneme-to-grapheme alignment.
- **Rhyme Legend**: Added a collapsible, interactive visual legend beneath the lyrics editor.

### 🛠 Technical Improvements

- **Robust Unified Runner (`run.py`)**: Rewrote the launcher script to be production-ready for local dev. It now:
  - Automatically installs Python dependencies (`pip install -r requirements.txt`)
  - Automatically installs Node dependencies (`npm install`)
  - Automatically detects and kills conflicting port processes on 5001
  - Monitors for crashes and ensures graceful shutdown
  - Supports `--skip-install` flag for faster restarts

## [2.3.0] - 2026-02-25

### ✨ New Features

- **AI-Powered Punchline Engine**: Generate context-aware punchline bars using Gemini AI, with scoring for wordplay, contrast, double entendres, and alliteration. Rule-based fallback when AI is unavailable.
- **AI-Powered Metaphor & Simile Generator**: Create vivid, hip-hop-appropriate metaphors and similes powered by AI with session context awareness.
- **Contextual Ad-lib Generator**: Tone-aware ad-lib suggestions with artist-style emulation (Travis Scott, Drake, Kendrick, Future, Migos, 21 Savage, J. Cole, Kanye). Includes syllable-based placement suggestions.
- **Key Detection**: Musical key detection for uploaded audio using chromagram + Krumhansl-Schmuckler algorithm. Returns key, mode, and confidence score.
- **Dynamic Beat Arranger**: Detect beat structure sections (Intro, Verse, Chorus, Bridge, Outro) using spectral features and energy analysis. Per-section waveform data for looping.
- **Journal Semantic Search**: Search journal entries by meaning using sentence-transformers embeddings. Supports semantic, keyword, and auto modes. Graceful fallback to keyword search.
- **Vocabulary Age Analytics**: Track vocabulary complexity evolution over time using Flesch-Kincaid grade levels. Per-session metrics and cumulative growth tracking with reading level labels.

### 🎨 UI Enhancements

- **PunchlinePanel**: New 3-tab sidebar panel (🔥 Bars / 💎 Metaphors / 🎤 Ad-libs) with glassmorphism styling, click-to-copy, and scoring display.
- **Journal Search Bar**: Semantic/keyword search toggle on the Journal page with match-type badges and similarity scores.
- **Vocabulary Age Dashboard**: Bar chart showing grade level evolution, reading level badge, trend indicators, and unique word tracking on the Stats page.

### 🔧 Backend

- New services: `vector_search.py`, `vocabulary_analyzer.py`
- New router: `vocabulary.py` (`GET /api/vocabulary/age`, `GET /api/vocabulary/session/{id}`)
- Updated routers: `advanced.py` (AI punchline/metaphor/adlib endpoints, audio sections), `journal.py` (semantic search endpoint)
- New dependencies: `sentence-transformers>=2.2.0` (optional), `scikit-learn>=1.3.0`

## [2.2.1] - 2026-01-13

### Fixed

- **Audio Visualizer**: Fixed TypeScript type mismatch error in audio buffer handling.
- **Frontend Testing**: Fixed Vite configuration to correctly support Vitest globals and test properties.
- **Version Consistency**: Unified version numbers across backend, frontend, and documentation.

## [2.2.0] - 2026-01-13

### 🎨 Design Restoration & Enhancement

- **Dreamy Aesthetic**: Restored the original "dreamy" design system with deep space backgrounds, aurora gradients, and glassmorphism.
- **Glassmorphism**: Enhanced UI depth with frosted glass effects on cards, navbar, and modals.
- **Micro-Interactions**: Added smooth button ripple effects, hover lifts, and glowing focus states.
- **Animations**: Implementation of `Framer Motion` for:
  - smooth page transitions (fade + slide).
  - staggered list entrances.
  - skeleton loading shimmers.

### ✨ New Features

- **Audio Visualizer**: Real-time frequency bars and waveform visualization using Web Audio API (`AudioVisualizer.tsx`).
- **Lyrics Scraper**: New backend service to scrape lyrics from web sources without API keys (DuckDuckGo + BeautifulSoup).
- **Rhyme Completer**: AI-powered inline rhyme suggestions with specific line context (`RhymeCompleter.tsx`).
- **Style Dashboard**: Comprehensive analysis view with Radar Charts comparing user style to famous artists (`StyleDashboard.tsx`).
- **In-Memory Caching**: Optional caching layer for heavy AI and rhyme operations.
- **Keyboard Shortcuts**: Added support for power user actions (e.g., `Ctrl+N` for new session).
- **Auto-Save**: Smart debounced auto-saving for sessions to prevent data loss.
- **Loading Skeletons**: Replaced spinners with content-aware skeleton loaders.
- **Empty States**: Added animated illustrations for empty dashboards.
- **E2E Testing**: Full Playwright test suite for workspace and session flows.

### 🛠 Technical Improvements

- **Performance**: Implemented code splitting with `React.lazy()` and `Suspense` for faster initial load.
- **Error Handling**: Added global `ErrorBoundary` to catch and gracefully display UI crashes.
- **Hooks Library**: Created reusable hooks `useKeyboardShortcuts` and `useAutoSave`.

### 🧪 Testing Infrastructure (New)

- **Backend**: Complete `pytest` suite for rhyme engine, scraper, and API endpoints (moved to `backend/tests`).
- **Frontend**: Added `Vitest` and `React Testing Library` for fast component unit testing.
- **E2E**: maintained `Playwright` suite for critical user flows.

## [2.1.0] - 2026-01-12

### Added

- **Journal Integration**: A private space for users to write free-form thoughts, which the AI now reads to understand mood and context (`/journal`).
- **Advanced Rhyme Scheme Detection**:
  - Real-time identification of specific 4-line patterns: **ABAB (Alternating)**, **AABB (Couplets)**, **XAXA (Ballad)**, **AAAA (Monorhyme)**.
  - Displayed prominently in the Analysis Strip during session.
- **User Preferences**:
  - **Favorite Words**: Users can define a list of words they love, which the AI prioritizes.
  - **Banned Words**: Users can block specific words to prevent clichés.
  - **Slang Preferences**: Regional slang settings (e.g., "finna", "lit") injected into AI context.
- **Deep Style Adaptation**: The "Vibe" AI persona now analyzes user vocabulary density, slang usage, and flow patterns to mimic the user's specific voice.

### Changed

- **Visual Highlighting**:
  - Overhauled highlighting engine to use a **dense phonetic analysis**.
  - Words now light up based on shared **vowel sounds** (assonance) and **consonant families** (alliteration) using a multi-colored palette.
- **Analysis Strip**: Updated to show "Rhyme Scheme" (e.g., "ABAB") instead of generic "Odd/Even Flow".
- **AI Prompt**: Significantly expanded system prompt to be a "collaborative partner" rather than an assistant, with instructions to be "gritty", "human", and "emotional".

### Fixed

- **Flow Analysis**: Improved syllable counting logic to better handle complex words and slang.
- **CORS Issues**: Broadened CORS settings for local development stability.
- **UI Responsiveness**: Fixed layout issues in the Sidebar and LyricsEditor on smaller screens.

## [2.0.0] - 2026-01-10

### Initial Release

- **Basic Session Management**: Create, edit, and delete lyric sessions.
- **AI Suggestions**: Real-time "Ghost text" suggestions.
- **Rhyme Dictionary**: Integrated `pronouncing` library for basic rhyme lookups.
- **Beat Player**: Simple audio player for uploaded beats.
