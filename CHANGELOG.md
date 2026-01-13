# Changelog

All notable changes to the **VibeLyrics** project will be documented in this file.

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
- **Redis Caching**: Optional Docker-based Redis service for caching heavy AI and rhyme operations.
- **Keyboard Shortcuts**: Added support for power user actions (e.g., `Ctrl+N` for new session).
- **Auto-Save**: Smart debounced auto-saving for sessions to prevent data loss.
- **Loading Skeletons**: Replaced spinners with content-aware skeleton loaders.
- **Empty States**: Added animated illustrations for empty dashboards.
- **E2E Testing**: Full Playwright test suite for workspace and session flows.

### 🛠 Technical Improvements

- **Performance**: Implemented code splitting with `React.lazy()` and `Suspense` for faster initial load.
- **Error Handling**: Added global `ErrorBoundary` to catch and gracefully display UI crashes.
- **Hooks Library**: Created reusable hooks `useKeyboardShortcuts` and `useAutoSave`.

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
