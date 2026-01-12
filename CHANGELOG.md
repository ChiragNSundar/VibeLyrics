# Changelog

All notable changes to the **VibeLyrics** project will be documented in this file.

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
