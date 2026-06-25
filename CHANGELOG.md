# Changelog

All notable changes to the **VibeLyrics** project will be documented in this file.

## [3.6.0] - 2026-06-25

### 🎙️ Doppelreim Engine Optimization & Contextual Reranking

#### ⚡ Batched & 3-Word Combinatorial Search
- **Batched Database Queries** — Replaced the $N+1$ query loop in combinatorial lookups with a single, highly efficient SQL `IN` query for all sequence segments.
- **3-Word Combination Depth** — Extended phonetic matching to support 3-word combinations for long vowel sequences ($\ge 4$ syllables), capped at the top 10 candidates per segment.

#### 🌐 Syllable-Range Filtered Cross-Language Lookup
- **Syllable-Range Constraints** — Upgraded cross-language phonetic search to restrict database queries to words within a $\pm 1$ syllable range of the source word.
- **IPA-Key Database Indexes** — Added a precomputed, indexed `ipa_key` column to `MultisyllabicWord` with startup auto-migration support, resolving IPA keys on-the-fly and eliminating dynamic string normalizations.

#### 🧠 Optional Contextual Semantic Reranking
- **LLM Contextual Reranking** — Integrated Gemini-based semantic relevance grading (0.0 to 10.0) that compares doppelreim suggestions to the user's active lyric context.
- **UI Settings Panel & Badges** — Added an interactive toggle to the Doppelreim settings drawer and a brain score badge (🧠 `score`) next to reranked results.
- **Feedback Upvote Splitting** — Extended the upvote feedback system to split multi-word suggestions and credit/debit voting weight to each constituent word in the database.

## [3.5.0] - 2026-06-25

### 🧠 Permanent Learning State Retention & Scraper Isolation

#### 🎓 Permanent Style and Vocabulary Learning
- **No sliding-window truncation** — Removed length caps on `favorite_words` (formerly limited to 2000) and `favorite_phrases` (formerly limited to 1000) in `StyleExtractor` so all extracted style characteristics remain permanently.
- **Full vocabulary frequency persistence** — Replaced the `most_common(10000)` constraint with the complete `word_frequency` dictionary serialization in `VocabularyManager` to preserve the user's entire written/scraped vocabulary.
- **Uncapped interaction tracking** — Removed memory caps on user corrections (formerly capped at 100), suggestion logs (formerly 500), micro-feedback logs (formerly 1000), and AI Arena RLHF matches (formerly 500) to maintain an exhaustive historical record.

#### 🧪 Robust Test Isolation
- **Isolated Scraper Tests** — Patched `get_scraped_urls` and `save_scraped_url` in the scraper tests to prevent any read/write dependencies on the local `data/scraped_songs.json` file, ensuring reliable test suite execution.

## [3.4.0] - 2026-06-19

### 📖 Kannada Dictionary, Header Spacing Optimization & Caret Highlight Polish

#### 📚 Kannada-to-English Dictionary
- **Ingestion Pipeline** — Seeded a local database of **31,020** entries from the local Kannada-to-English PDF dictionary context with exact vowel sequences, stress, and syllable indexes.
- **SFT dataset builder** — Compiled Alpaca SFT JSON datasets for Kannada vocabulary fine-tuning.
- **Unified Dictionary Search Drawer** — Added a dictionary tab to the Doppelreim sidebar to search Kannada terms, copy definitions, insert words into active lines, and switch instantly to Kanglish rhyme search.
- **LLM Context Augmentation** — Automatically includes local dictionary definitions in Gemini/LM-Studio suggestions.

#### 🎨 Visual Layout & Spacing Efficiency
- **Global Navbar Hiding** — Conditionally collapses primary navbar on active session routes, saving 60px vertical height.
- **Single-Row Session Header** — Unified metronome and title onto a single row, and moved the Metronome to a centered `.session-metronome` block.
- **Collapsible Header Complexity Meter** — Relocated Complexity Meter next to the metronome as a mini clickable gauge circle, resolving absolute-positioned overlaps and letting users expand stats in a dropdown on click.
- **Compact Horizontal Blocks** — Layout elements in lyric lines are aligned horizontally inside a sleeker, compacted layout.

#### 🎙️ Caret Highlighting & Word Click Sync
- **Unified Sub-Word Calculations** — Clicking/hovering on split-highlights (like `m` and `uchkond`) dynamically walks boundaries in the line text to capture the full word `muchkond` cleanly.
- **Select-Deselect empty space clicks** — Whitespace clicks bubble to the parent row to toggle stress pattern timelines, while text-clicks selectively trigger doppelreim searches.
- **Dashed Perfect Rhymes** — Perfect rhymes now render with dashed colored borders and semi-transparent backgrounds to match the mockup layout, eliminating solid bright yellow block overlaps.

## [3.3.0] - 2026-06-19

### 🧠 Local Brain Mega-Upgrade & Multi-Language Enhancements

#### 🎙️ Rhyme Engine & Phonetics
- **Consonance-Weighted Slant Rhymes** — Custom phoneme edit distance weights vowel substitution at 0.5 (closer slant) vs 1.0 for consonants.
- **On-the-Fly Phrase Rhymes** — Dynamic compound phrase matching (e.g. *orange* -> *door hinge*) from CMUDict.
- **Cross-Language Matching** — IPA-bridge vowel alignment across English (CMUDict) and Hinglish/Kanglish (Indian romanizations).
- **Detailed Density Heatmap** — Return numeric 0-100 score per line with specific rhyming word pair highlights.
- **Phonetic Autocomplete** — Autocomplete suggestions using prefix searches synced with target vowel sequences.

#### 📈 Advanced Semantic Drift & Complexity
- **Multi-Algorithm Semantic Drift** — Added sliding window drift, TF-IDF weighted keywords, and section-aware anchoring.
- **Enhanced Complexity Scoring** — Added homophone/double entendre detection and rhyme scheme complexity bonuses.

#### 🎓 Style Learning & Brain Map
- **N-gram Pattern Extraction** — Track favorite bigrams and trigrams in the writing style profile.
- **Cliché Detector** — Scans lyrics against a corpus of ~100 hip-hop clichés and user-defined avoided words.
- **Vocabulary Staleness Alert** — Highlights stagnating vocabulary growth across sessions.
- **Brain Map Community Clustering** — Lightweight label propagation dynamically groups co-occurring words.

#### ⚡ Persistent Caching & Version History
- **Persistent Caching** — SQLite-backed `CacheEntry` storage with automatic in-memory fallback.
- **Session Diffing Summary** — Aggregates per-line revisions, content updates, and character deltas.
- **Expanded Imagery Radar** — Expanded lexicon (215+ sensory words) and balance radar scores per sense.

## [3.2.0] - 2026-06-19

### 🎛️ Advanced Cadence Writing Flow & Offline Brain Upgrades

#### 🎵 Stress & Flow Timeline UI
- **Interactive Syllable Grid** — Added a real-time stress pattern visualization timeline below active lyric rows, using Framer Motion. Shows stressed (`/` / Guru) and unstressed (`x` / Lagu) syllables.
- **Manual Overrides** — Users can click on a syllable node to manually toggle/override its stress state, marked with a pulsing gold glow and dashed border.

#### 🧠 Rhythmic Scoring & Flow-Aligned Sorting
- **Cadence & Stress Matching** — Enhanced the Doppelreim matching algorithm to accept target syllable counts and target stress patterns, prioritizing and ranking rhythmically equivalent matches.
- **Rhythmic Badges** — Result cards display `rhythmic_score` indicators and inline stress shapes so writers can see flow alignment at a glance.

#### 🤖 Offline Brain & AI Romanization Alignment
- **Hinglish/Kanglish AI Prompts** — Updated system instructions (`GHOSTWRITER_SYSTEM_INSTRUCTION`) and local polishing prompts across all providers (Gemini, OpenAI, LM Studio) to strictly enforce romanized script (Latin/English characters) for Hindi and Kannada suggestions.
- **Local Polish Endpoint** — Added `/api/ai/polish/local` (and a matching "Cadence Polisher" drawer in the frontend UI) to perform offline line polishing to fit syllable counts and inject active slang vocabulary.
- **OpenAI Local Polishing** — Implemented local polishing support in `OpenAIProvider`.

## [3.1.0] - 2026-06-18

### 🧠 Interactive Seeding Center & Phonetic Sandbox

#### 🚀 Seeding & Learning Cockpit
- **Interactive Redesign** — Transformed the static "Learning" display page into a dynamic, 4-tab dashboard featuring Vocabulary management, a Phonetic Sandbox, Brain Importer, and Word Explorer.
- **Relocated Vocabulary & Style Configuration** — Moved Favorite and Banned words out of SettingsPage into the new Cockpit dashboard, adding support for a "Slang" vocabulary category.
- **Vocabulary & Slang Builder** — Real-time lists displaying Favorite, Banned, and Slang words with forms to easily add words and instant deletion tags.

#### 🎙️ Phonetic Sandbox & SQLite Override Sync
- **Phonetic Database Overrides** — Enter any word in English, Devanagari (Hindi), or Kannada to extract syllables, vowel sequences, and ending keys.
- **Manual Adjustments** — Edit the extracted vowel sequence, syllable count, exact rhyme key, and slang status directly from the UI.
- **Direct Database Sync** — Saving writes the customized override directly into the local SQLite `MultisyllabicWord` table.

#### 📁 Brain Feed & Importer
- **Document Ingestion** — Pasting raw lyrics or importing documents (.pdf, .txt, .docx) parses text to update AI theme models.
- **Beat Audio Analyzer** — Drag and drop MP3 or WAV audio beats to instantly extract BPM and Musical Key parameters.

#### 🔍 Offline Word Explorer
- **Multi-Lookup Utility** — Integrated perfect rhymes, near rhymes, and semantic thesaurus synonyms lookup into a dedicated dashboard tab.

## [3.0.0] - 2026-06-18

### 🎤 Offline Doppelreim Engine & Visual Cadence Polish

#### 🎙️ Offline Phonetic Doppelreim Engine
- **Cross-Lingual Vowel Segmenters** — Implemented three offline rules-based phonetics segmenters for English (CMUDict), Hindi/Devanagari (incorporating schwa-deletion rules), and Kannada (handling vowels and ottaksharas).
- **Combinatorial Multi-Word Rhymes** — Pairs shorter words together recursively to match complex multi-syllabic targets.
- **LRU In-Memory Cache** — Added a backend `OrderedDict` cache (up to 500 queries) to make recursive lookups instantaneous. The cache is automatically cleared when users upvote or downvote rhymes to ensure rankings are updated.
- **Database Schema** — Added `MultisyllabicWord` and `RhymeFeedback` schemas, with automatic background seeding of ~135k English terms and standard Hindi/Kannada vocabularies on startup.

#### 🎨 Doppelreim UI & Layout Overhaul
- **Collapsible Settings Drawer** — Placed language, mode, and slang toggles inside an animated collapsible drawer triggered by a `SlidersHorizontal` gear icon inside the search row.
- **Dedicated Sidebar Toolbar** — Converted the left panel icons toolbar from absolute positioning to a static flex column, preventing overlap and blocking of sidebar content when panels are open.
- **Word Click Highlight Sync** — Clicking any word in the lyrics editor dynamically extracts the word (supporting unicode sets), slides open the Doppelreim sidebar, and loads phonetic matches.

#### 🌊 Cadence Meter & Metronome scroll
- **Cadence SVG Ring** — Real-time SVG circular progress ring next to the editor input line. Colors turn orange (short), red (long), or pulse emerald green (ideal range met) based on current syllable count.
- **Scroll-to-Change BPM** — Adjust metronome BPM by aiming and scrolling the mouse wheel on the BPM display. Updates the UI immediately and debounces saving to the DB by 500ms.
- **Cleaned Visualizer** — Removed the `Bar 1` counter element from the metronome display.

#### 🔧 Platform Dev Simplification
- **Global Python Execution** — Removed all virtual environment (`.venv`) checks. The launcher (`run.py`) now runs uvicorn and vite dev servers globally on the system python interpreter.

## [2.9.0] - 2026-03-18

### 🧠 Phase 8: Advanced Training Intelligence

#### 🏟️ Automated RLHF (AI Arena)
- **AI Arena Mode** — Generate 4 distinct AI line variants simultaneously. Pick the best one, and the 3 rejects automatically become DPO preference training pairs.
- **Arena Match History** — Track all arena votes and view generated DPO pair counts.
- **New Endpoint** — `POST /api/ai/arena` generates arena variants; `POST /api/training/rlhf/vote` submits votes.

#### 🔄 Continual Learning (Live LoRA Updating)
- **Auto-Buffer** — Every line you write with a complexity score above the threshold is automatically pushed into a training buffer.
- **Batch Auto-Train** — When the buffer fills up (default: 50 lines), the system can automatically trigger a re-training run.
- **Configurable** — Set `min_complexity`, `batch_size`, and `auto_retrain` via the Training Hub or API.

#### 🧽 Concept Erasure (Anti-Cliché)
- **Banned Word DPO** — Add banned words and the system generates synthetic negative DPO pairs to surgically remove those words from model output.
- **Two Strategies** — (1) Replace good line endings with banned words to create rejected versions; (2) Flag lines containing banned words as rejected examples.
- **Preview Mode** — Preview how many erasure pairs would be generated before committing.

## [2.8.0] - 2026-03-05

### 🚀 Phase 7: Advanced Training Pipeline

#### 🧠 Training Data & Quality Controls
- **Score-Gated Datasets** — Filter training data by complexity score to ensure the model only learns from your best lines.
- **Micro-Feedback System** — Granular feedback types (e.g., "more_complex", "change_rhyme") to create specific negative training signals.
- **RAG-Augmented Callbacks** — Automatically finds similar past lyrics to generate self-referential training pairs.

#### ⚖️ DPO Preference Training
- **Chosen/Rejected Pairs** — When you reject an AI suggestion and write your own, VibeLyrics creates preference data to teach the model what *not* to write.
- **DPO Phase Integration** — Seamlessly integrates Direct Preference Optimization into the fine-tuning script.

#### 🎭 Multi-LoRA Profiles & Auto-Train
- **Specialized Profiles** — Train distinct LoRA models for different moods and genres (e.g., Aggressive, Melodic, Trap).
- **Auto-Train Pipeline** — Launch the full Unsloth Python training script directly from the UI as a background process.
- **Import Support** — Ingest external Alpaca or ChatML JSONL datasets to augment your training corpus.

## [2.7.0] - 2026-03-04

#### 🤖 Advanced AI & NLP
- **Wordplay Engine** — New side panel that generates dual-meaning bars, puns, and metaphorical twists tailored to your song's theme and mood.
- **Complexity Meter** — Real-time, animated circular gauge (0-100) alongside the BeatTimer that analyzes rhyme density, multi-syllabics, assonance, and vocabulary.
- **Semantic Drift Indicator** — Visual pulsing bar below the editor that warns you if your verse starts drifting off-topic compared to the opening lines.

#### 🎵 Beat & Audio Integration
- **Beat Analysis Card** — Drag-and-drop audio directly into the session panel.
- **Smart Metrics** — Automatically extracts BPM, Musical Key (w/ mode and confidence), and suggests optimal Syllables-per-Bar.
- **Song Structure** — Analyzes the beat's energy to detect intros, verses, and drops.

#### 🧠 Visual Knowledge Base
- **Interactive 3D Theme Network** — Replaced flat lists with a Canvas-based 3D force-directed graph in the Learning Center. Watch how your recurring themes link together across all your sessions.

## [2.6.0] - 2026-02-27

### 🚀 Phase 5: The Intelligence Suite 

#### ✍️ Writing Tools
- **Git for Lyrics (Version History)** — Click the clock icon on any line to view its previous versions, see diffs, and restore old bars.
- **Beat Timer Overlay** — Visual metronome bar with play/pause that pulses to your session's BPM.
- **Syllable Target Guide** — Real-time indicator under the BPM that calculates whether your line is 'Free Flow' or matching a specific beat pattern constraint.

#### 🤖 AI Generators
- **Flow Pattern Templates** — A dropdown to strictly apply predefined flow constraints (e.g., Triplet, Double-Time, Boom-Bap) to your syllable targets.
- **Context-Aware Adlibs** — Click the floating 'Adlibs' chip to get instant, context-aware hype words based on your recent 4 lines and mood.
- **Auto-Hook Generator** — Generate catchy, thematic choruses based on your verse context straight from the AI Help Panel.
- **Song Structure Builder** — Scaffold entire song blueprints (Intro, Verse, Hook, Bridge, Outro) with AI suggestions mapped to your BPM and theme.

#### 📈 Analytics & Gamification (Group C)
- **Writing Streak Tracker** — Dashboard widget tracking daily check-ins and your longest streak with 🔥 badges.
- **Vocabulary Growth Chart** — A `recharts` AreaChart visualizing how your unique vocabulary count expands over time.
- **Rhyme Scheme Heatmap** — A GitHub-style contribution calendar color-coded by the dominant rhyme scheme used each day.

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

### 🧠 Intelligence Layer (Phase 4)

- **Interactive Brain Map** — Force-graph neural network that visualizes the AI's vocabulary as glowing, interconnected nodes. Drag, hover, and explore how words connect.
- **Lyrical DNA Matcher** — 6-axis Radar Chart comparing your writing across Vocabulary Richness, Rhyme Complexity, Punchline Power, Imagery Density, Line Length Variety, and Internal Rhyme %.
- **Auto-Annotations** — Automatic per-line lyric breakdown detecting double entendres, metaphors, similes, alliteration, and punchline quality—no Genius API needed.
- **Audio Rhythm Learning** — Upload `.mp3`/`.wav` beats for automatic BPM, key, and energy extraction via `librosa`.

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
