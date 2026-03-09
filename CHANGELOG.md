# Changelog

All notable changes to **PodPipeline** are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) — versions follow [Semantic Versioning](https://semver.org/).

---

## [2.2.0] — 2026-03-09

### Added
- **▶ Run Full Pipeline button** on episode detail page — generates a pre-filled Antigravity prompt with episode ID, language, audience, phase status, and resume instructions
- `GET /api/episodes/<eid>/prompt` backend endpoint — smart auto-detects which phase to resume from
- Glassmorphism copy modal — shows prompt preview, one-click copy, click-outside-to-close
- Glowing green animated button style (`.btn-run-pipeline`) with pulse glow keyframe

### Fixed
- Episode detail header no longer falls back to German flag/language name for episodes without a saved language

---

## [2.1.0] — 2026-03-09

### Changed
- **Language and audience are now 100% dynamic** — zero hardcoded defaults anywhere in the stack
- Language picker auto-selects first language from `/api/languages` on page load (hidden inputs always populated)
- Audience picker auto-selects first audience from `/api/audiences` (was hardcoded to `finance_listeners`)
- Post-submit form reset uses `_languages[0]` / `_audiences[0]` dynamically

### Fixed
- `create_episode()` in `app.py` now **requires** `output_language`, `language_name`, `target_audience` — returns 400 if missing (no silent German default)
- `new_episode.py` `--language`, `--language-name`, `--audience` are now **required args** — no defaults
- Dashboard episode rows no longer show German flag for episodes missing a language
- Language summary pills skip episodes with no language set

---

## [2.0.1] — 2026-03-09

### Fixed
- `new_episode.py` — language and audience now saved **directly to DB** inside the script after getting the episode ID (removed fragile queue-scanning fallback in `app.py`)
- Added `--language`, `--language-name`, `--audience` args to `new_episode.py`
- `app.py` passes all 3 args via subprocess — no post-hoc mem scan needed
- ID regex made robust: handles spaces, Chinese colon variant (`ID：3`)
- Done terminal output confirms: `✓ Language saved: Spanish (es)` / `✓ Audience saved: gen_z`

---

## [2.0.0] — 2026-03-09

### Added
- **SSE Live Dashboard** — server pushes `dashboard-update` events to all open browser tabs on every phase change
- `GET /api/events` SSE endpoint with per-client queue system
- `_broadcast_refresh()` called after every `set_phase` and `/api/phase/<eid>/<phase>/<status>` update
- 30-second fallback polling for dashboard when SSE is unavailable
- `--reset-db` flag in `start.py` — wipes and re-initialises the database cleanly
- Deployment readiness test suite (`scripts/test_deployment.py`) with 7 checks including browser UI test via Playwright

### Fixed
- `skill_profiles` schema mismatch after `--reset-db` — `seed_all_profiles.py` and all `app.py` queries updated to use correct column names: `lang_code`, `audience_key`, `vocabulary`, `slang_phrases`, `hook_patterns`, `taboos`
- `_auto_detect_phases()` — was matching hardcoded `SCRIPT_DE.md`; now matches any `SCRIPT_*.md`
- Emoji print `UnicodeEncodeError` on Windows cp1252 terminal in seed script — replaced emoji flags with ASCII labels `[DE]`, `[EN]`, etc.

---

## [1.5.0] — 2026-03-09

### Added
- **30 tailored writing skill profiles** — 5 languages × 6 audience types, seeded via `scripts/seed_all_profiles.py`
- Skill profiles wired into memory CLI (`mem profile get <lang> <audience>`)
- Skill profile status badge on New Episode form — shows if a profile exists for selected lang × audience
- `GET /api/skill-profiles`, `GET /api/skill-profiles/<lang>/<audience>` API routes
- `POST /api/skill-profiles/research` — stream SSE to build a profile on demand
- **Phase 8 — Cinematic Setup**: creates separate English-only NotebookLM notebook + adds sources for international distribution
- **Open Deliverables** button appears when all phases complete
- 16 audience types with CPM ranges, emoji, age range, content tips, and platform tags
- flagcdn.com flag images replace emoji flags (better cross-platform rendering)

### Changed
- All tone/profile fields stored in English only (UI readability)
- Phase 8 simplified: creates notebook + adds sources only (no video generation)

### Fixed
- Skill profile status bar — no longer dumps raw JSON
- Full tone sentence shown in status bar (no truncation)

---

## [1.4.0] — 2026-03-09

### Added
- **Whisper model selection** on first setup (Step 3.5) — choice saved to `.agent/whisper_model.txt`
- **GPU detection** on first setup (Step 3.6) — auto-selects CUDA/CPU, saved to `.agent/device_config.json`
- Browser UI test step (Step 6.5) using Playwright in `start.py`
- `START_HERE.md` — master Antigravity onboarding prompt with multi-language multi-audience architecture

### Fixed
- Replaced all hardcoded German/language references in pipeline workflow with dynamic variables
- NotebookLM per-notebook language scoping (correct language passed to audio generation)
- Image crop-to-fill 16:9 — no more black bars on visuals

---

## [1.3.0] — 2026-03-09

### Added
- `start.py` — unified auto-setup script with 7 steps: deps check, pip install, whisper setup, GPU detection, memory DB init, seeding, NotebookLM auth
- `SETUP.md` — complete beginner install guide for new machines
- Force 16:9 + professional quality visuals pipeline

### Fixed
- `new_episode.py` moved to `core/` subfolder — path updated in `app.py` subprocess call
- `--force` flag added to `new_episode.py` call so web UI never fails on existing folder
- UTF-8 stdout wrapper added to prevent Windows encoding crashes

---

## [1.2.0] — 2026-03-08

### Added
- **Advanced memory system** — all 6 improvements:
  1. Evolving quality profiles (auto-update skill profiles from feedback)
  2. Phase outputs tracking (full resumability)
  3. Smart context retrieval (topic-aware filtered memory)
  4. Session handoff (persistent JSON session state)
  5. Workflow contract enforcement (locked pipeline steps)
  6. Character bible persistence
- Direct SQLite hot paths — replaced subprocess memory calls for `list_episodes`, `get_phases`, `get_sources` (major performance improvement)
- Parallel image generation pipeline
- Auto-detect pipeline phases on episode detail load
- Auto-progress pipeline — phases advance automatically when files are detected
- `script-only audio strategy` — generates audio directly from script, no YouTube dependency

### Fixed
- Auto-detect phase progress no longer snowballs on page refresh
- `scifi_curious` audience seeded correctly with fallback for missing audience in API
- Dashboard phase updates fire correctly for all 8 phases
- Analytics + Memory dashboards show real data from DB
- Platform tag SVG brand logos + spacing fixed

---

## [1.1.0] — 2026-03-08

### Added
- **Live Output streaming** for episode creation — SSE streams subprocess stdout line by line to browser terminal
- Expanded sidebar with icon + text labels
- Audio duration display on episode detail
- `POST /api/episodes` — create episode via web UI with streaming job system
- `GET /api/stream/<job_id>` — SSE endpoint for live job output

### Fixed
- Episode creation subprocess streaming fully working
- `new_episode.py` no longer hangs on blocking `input()` call

---

## [1.0.0] — 2026-03-08

### Added
- Initial release — **PodPipeline AI Podcast Production Suite**
- Full-stack dashboard: Flask backend + vanilla JS/CSS frontend
- 8-phase pipeline tracker: Setup → Research → Script → Audio → Transcribe → Visuals → Deliverables → Cinematic Setup
- Episode management: create, list, detail view, status tracking
- Source management: add YouTube / article / podcast / document sources per episode
- Memory system: SQLite-backed episode registry, topic conflict detection, quality scoring
- Analytics page: episode stats, topic coverage, quality scores, audience breakdown
- Memory page: context preview, character bible, session state
- Quality feedback form
- NotebookLM integration (audio generation, notebook management)
- `faster-whisper` transcription integration
- `yt-dlp` YouTube source downloading
- Multi-language support: EN, DE, ES, FR, PT
- Multi-audience support: 16 audience profiles with CPM data

---

*PodPipeline — AI-powered podcast production from topic to YouTube-ready deliverables.*
