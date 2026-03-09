# Changelog

All notable changes to PodPipeline are documented in this file.  
Format: [Semantic Versioning](https://semver.org) — `MAJOR.MINOR.PATCH`

---

## [2.3.0] — 2026-03-09

### 🐛 Bug Fixes

- **[UI] Click-to-Copy broken** — Rewrote clipboard handler with `navigator.clipboard` + `isSecureContext` check and a `_fallbackCopy()` textarea fallback. Works on both HTTPS and local network IPs. Affects title cards and description copy button in YouTube Pack.
- **[UI] Episode card stuck on `running`** — Added `_deriveStatus()` function: derives visual episode badge from phase completion. When all phases are `done`/`skipped`, card shows `complete`. No more stale `running` badge after pipeline finishes.
- **[UI] Phase stuck on `running` after pipeline completes** — Added `_safePhaseStatus()`: remaps any phase showing `running` to `pending` when `deliverables` phase is already `done` (i.e., pipeline main flow completed before that phase ran). Cinematic Setup no longer shows `running` when it was never started.
- **[UI] False `🎉 PIPELINE COMPLETE` log** — Suppressed the completion log message in the terminal if any phase row in the UI still has `running` class. Complete fires only when truly all phases are resolved.
- **[Pipeline] Visuals generated before transcript** — Added hard block in Phase 6: key visual generation is forbidden until `transcript.txt` exists and is fully written. Required order enforced: `audio → transcribe → SLIDE_SOURCE.md → key visuals`. No exceptions.
- **[Pipeline] Research adds only 1 source** — Research phase now enforces a **Source Count Gate**: minimum 5 diverse sources required (2+ YouTube SRTs, 1+ Wikipedia/docs, 1+ blog/community) before pipeline may advance to script writing. Gate is blocking — pipeline cannot proceed if it fails.
- **[Memory] Characters and Visual Styles empty on Memory page** — NOVA and MAX character bibles are now seeded into memory at pipeline start. Visual styles (`tech`, `space`, `health`, `finance`, `military`, `paranormal`) are seeded by topic type. Phase 1 now includes mandatory `char set` + `style set` steps.

### ✨ Improvements

- **[Workflow] Audio notebook: script only** — Enforced globally in both `podcast-pipeline.md` and `dynamic-podcast-director/SKILL.md`: the NotebookLM audio notebook must contain **one source only** — the target-language script file. No research docs, no YouTube transcripts. Prevents audio quality dilution.
- **[Workflow] Cinematic notebook: all English research sources** — Phase 8 now mandates that every English source from Phase 2 research is added to the cinematic notebook. Minimum 3 sources. Step-by-step commands added in workflow.
- **[Generator] Thumbnail: viral, topic-branded, YouTube-compliant** — Removed blanket `"no text, no logos"` restriction from thumbnail prompt. Generator now produces: cinematic topic-matched background + bold audience-matched text overlay + topic-relevant branding (logos, icons) + YouTube-compliant creative. References viral podcast channels (JRE, Lex Fridman, MrBeast) for style calibration.
- **[Generator] Descriptions: SEO-first, algorithm-optimized** — Description generator restructured: hook (first 2–3 lines, search-preview optimized) → keyword-rich body → timestamps placeholder → sources → CTA → hashtags. Audience-matched hook and body tone. Trending topic keywords extracted and woven in. Internal audience statistics block removed.
- **[Workflow] Two-tier visual system** — Key visuals (Tier 1) are transcript-locked and generated only after `transcript.txt` is ready. Supporting visuals (Tier 2) are topic/research-based and generated in a loop during idle wait time (audio gen + transcription). Loop stops immediately when `podcast.mp3` downloads OR `transcript.txt` completes. Supporting visuals saved with `support_` prefix.
- **[Workflow] Smart visual limit** — Visual budget calculated per episode: `podcast_duration_seconds ÷ audience_attention_span_seconds`. Attention spans documented per audience type (Gen Alpha 3–5s → Boomers 20–30s). Tier 1 fills slots first; Tier 2 fills remaining up to the limit. Limit stored in memory. Never generates beyond budget.

### 🔄 Global Rules Added

All fixes and improvements are global — applying to every episode permanently. Added to `podcast-pipeline.md`:
- `🔒 GLOBAL NOTEBOOK RULES` section at top of workflow (audio = script only, cinematic = all English sources)
- `🎯 VISUAL BUDGET` section (smart limit formula + attention span reference table)
- `PHASE 4.6 — Supporting Visuals` (idle-time loop spec with stop conditions)
- `PHASE 1 — Seed Characters & Visual Style` (mandatory character + style seeding at episode start)
- `BUG #5 HARD BLOCK` notice in Phase 6 (transcript gate with code snippet)
- `SOURCE COUNT GATE` in Phase 2 (blocking checklist before advancing to script)

---

## [2.2.0] — 2026-03-09

### Features
- **Live pipeline log stream** — Browser terminal streams real-time SSE logs from pipeline executor
- **Run Full Pipeline button** — Episode detail page now has a one-click pipeline launch button with a copyable mega-prompt
- **Dynamic episode status** — `/api/episodes` computes episode status from pipeline table, not static `planned` field

### Fixes
- EN flag now correctly maps to US flag emoji
- Clipboard copy in prompt modal works on non-HTTPS local network IPs

---

## [2.1.0] — 2026-03-08

### Features
- **Advanced Memory System v2** — 6 improvements implemented:
  - Evolving quality profiles: skill profiles auto-update from episode feedback
  - Phase outputs tracking: full pipeline resumability and state recovery
  - Smart context retrieval: topic-aware filtered memory for each episode
  - Session handoff: persistent JSON session state across conversations
  - Workflow contract enforcement: locked contract prevents pipeline deviations
  - Profile evolution log: tracks how skill profiles change over time

---

## [2.0.0] — 2026-03-08

### Breaking Changes
- Replaced `german-scifi-podcast` skill with `dynamic-podcast-director` — now supports any language and any audience dynamically
- Pipeline no longer hardcodes German; language and audience are fully runtime parameters

### Features
- Dynamic language × audience persona system
- Audience-specific analogy matrix
- Cultural adaptation (ADAPT, don't translate)
- Anti-AI-detection playbook for scripts

---

## [1.5.0] — 2026-03-07

### Features
- YouTube Podcast Researcher skill — finds viral English sci-fi podcasts, extracts SRT transcripts
- Source rating system (`source rate`)
- Duplicate source detection (`source check-dup`)

---

## [1.4.0] — 2026-03-06

### Features
- Audio Listener skill — faster-whisper transcription with GPU/CPU auto-detection
- SRT subtitle generation from podcast audio
- Timestamped content maps for visual production

---

## [1.3.0] — 2026-03-05

### Features
- NotebookLM skill — full programmatic API access
- Artifact download (audio MP3, video, quiz, slide deck)
- Multi-format source support (PDF, URL, plain text)

---

## [1.2.0] — 2026-03-04

### Features
- Podcast Memory skill — SQLite + FTS5 persistent memory
- Character bible, visual styles, quality notes, topic deduplication
- `mem.py` CLI with 25+ commands

---

## [1.1.0] — 2026-03-03

### Features
- Phase-by-phase pipeline dashboard with live status badges
- CapCut walkthrough generator with real timestamps from transcript
- YouTube metadata pack: 5 viral titles + description + thumbnail prompt

---

## [1.0.0] — 2026-03-01

### Initial Release
- 8-phase podcast production pipeline (setup → research → script → audio → youtube_meta → transcribe → visuals → deliverables)
- Multi-language, multi-audience support via NotebookLM
- Episode folder structure with season/episode organization
- Flask web UI dashboard with SSE live updates
