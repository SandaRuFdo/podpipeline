# 🎙️ PodPipeline — AI-Powered Multi-Language Podcast Factory

> **One command to start. One topic to give. A fully produced, YouTube-ready podcast episode in ~60–80 minutes.**

PodPipeline is an **agentic audio production system** that takes any topic and automatically produces a culturally adapted podcast in any language — complete with a generated script, AI audio, timestamped visuals, YouTube metadata, and a CapCut editing walkthrough. The AI (Antigravity) is the brain and executor; the web UI is just the dashboard.

---

## What It Does

| Input | Output |
|-------|--------|
| Topic + language + target audience | MP3 podcast in target language |
| | Cinematic 1920×1080 images synced to audio |
| | CapCut editing walkthrough |
| | YouTube titles, description & thumbnail |
| | English cinematic video (background) |

The pipeline runs **8 fully automated phases**, tracked in a persistent SQLite memory database so it can resume from exactly where it left off if interrupted.

---

## Architecture Overview

```
┌────────────────────────────────────────────────────────────┐
│                   Web UI (browser)                         │
│   Input: topic, language, audience → shows live progress   │
└──────────────────────┬─────────────────────────────────────┘
                       │ HTTP / SSE
┌──────────────────────▼─────────────────────────────────────┐
│              app.py — Flask API (localhost:5000)            │
│   REST endpoints + Server-Sent Events for live log stream  │
└──────────────────────┬─────────────────────────────────────┘
                       │
┌──────────────────────▼─────────────────────────────────────┐
│           Antigravity AI (the brain & executor)             │
│   Runs all 8 phases autonomously using skills below        │
└──┬──────────────┬────────────────┬───────────┬─────────────┘
   │              │                │           │
   ▼              ▼                ▼           ▼
NotebookLM   Audio Listener   Memory DB   yt-dlp / ffmpeg
(audio gen)  (Whisper trans.) (SQLite)    (source research)
```

**Key principle:** The UI is *input only*. Antigravity does all the work.

---

## Quick Start

### 1. Prerequisites

- **Python 3.10+**
- **ffmpeg** — required for audio processing  
  Install: [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH
- **Google NotebookLM account** — free at [notebooklm.google.com](https://notebooklm.google.com)

### 2. First-Time Setup (One Command)

```bash
python start.py
```

`start.py` automatically:
1. Checks Python version (3.10+ required)
2. Checks ffmpeg installation
3. Installs all Python dependencies (`requirements.txt`)
4. Asks you to choose a Whisper model for transcription
5. Detects your GPU (CUDA/CPU) and saves device config
6. Initialises the SQLite memory database with 30 skill profiles
7. Launches the web server at `http://localhost:5000`

> **Reset everything:** `python start.py --reset` — wipes and re-initialises memory.

### 3. Authenticate with NotebookLM

```bash
notebooklm login       # Opens your browser for Google sign-in
notebooklm list        # Confirm it's working
```

### 4. Open the Dashboard

Navigate to **http://localhost:5000** in your browser.

### 5. Future Launches

After the first setup:
```bash
python start.py        # Launches directly (skip setup if already done)
# OR
run_server.bat         # Windows double-click shortcut
```

---

## The 8-Phase Pipeline

Every episode goes through these phases in order. Each phase updates the dashboard and writes its outputs to the episode folder.

```
Phase 1 → Setup        (2 min)    Create folder + register in memory
Phase 2 → Research     (5-10 min) Find English YouTube/Wikipedia sources  
Phase 3 → Script       (10-15 min) Write culturally adapted script
Phase 4 → Audio Gen    (15-20 min) NotebookLM generates the MP3 podcast
Phase 4.5 → YouTube Meta (parallel) 5 titles, description, thumbnail image
Phase 5 → Transcribe   (5-8 min)  Whisper timestamps the audio
Phase 6 → Visuals      (5-10 min) Generate 16:9 cinematic images
Phase 7 → Deliverables (2 min)    Build CapCut walkthrough + log quality
Phase 8 → Cinematic    (15-45 min, background) English video via NotebookLM
```

**Total: ~60–80 minutes** (most of which is waiting for AI generation).

### Folder Structure Per Episode

```
episodes/S01/E01_UFOs/
├── README.md
├── 1_research/sources/     ← YouTube SRT + TXT transcripts, Wikipedia
├── 2_script/
│   ├── SCRIPT_DE.md        ← Script in target language
│   └── SCRIPT_EN.md        ← English translation for review
├── 3_audio/
│   ├── podcast.mp3         ← Generated podcast audio
│   └── transcript.txt      ← Timestamped segments from Whisper
├── 4_visuals/
│   └── slide01_*.png       ← 1920×1080 cinematic images
└── 5_deliverables/
    ├── SLIDE_SOURCE.md     ← Timestamp → slide mapping
    ├── walkthrough.md      ← CapCut editing guide
    ├── youtube_meta.json   ← Titles + description
    ├── thumbnail_prompt.txt
    ├── thumbnail.png       ← AI-generated thumbnail
    └── cinematic.mp4       ← NotebookLM English video
```

---

## Skills (AI Capabilities)

The pipeline uses 5 skills — each is a set of instructions + scripts that extend what the AI can do.

### 🎙️ Dynamic Global Podcast Director
**File:** `.agent/skills/dynamic-podcast-director/SKILL.md`

The creative brain. Adapts tone, cultural references, slang, and analogies to any language × audience combination. It does **not** translate — it *adapts*. A concept explained to German Gen Z sounds completely different than the same concept explained to Japanese Millennials.

- Supports 80+ languages via NotebookLM
- 30 pre-seeded skill profiles (language × audience combos)
- Profiles **evolve automatically** — after each episode, quality scores update what works and what to avoid
- Standard episode structure: Cold Open → Theme Intro → Act 1 → Twist → Revelation → Outro

### 📓 NotebookLM
**File:** `.agent/skills/notebooklm/SKILL.md`

Full programmatic access to Google NotebookLM via the `notebooklm-py` CLI. Used to generate the podcast audio and the cinematic video.

Key commands used by the pipeline:
```bash
notebooklm create "Episode Title" --json
notebooklm source add ./SCRIPT_DE.md --json
notebooklm generate audio "instructions" --language de --format deep-dive --length long --retry 3 --json
notebooklm artifact wait <artifact_id> -n <notebook_id> --timeout 1200
notebooklm download audio ./3_audio/podcast.mp3
```

> **Important rule:** Always use `--language <code>` on the `generate` command. Never use `notebooklm language set` globally — it would corrupt all your notebooks.

### 🎧 Audio Listener
**File:** `.agent/skills/audio-listener/SKILL.md`

Transcribes the generated MP3 using **faster-whisper** (local, offline, no API cost). Produces timestamped segments that drive visual sync.

```bash
python .agent/skills/audio-listener/scripts/transcribe.py \
  episodes/S01/E01/3_audio/podcast.mp3 \
  --language de --format segments \
  --output episodes/S01/E01/3_audio/transcript.txt
```

Model choices (set during `start.py` setup):
| Model | Size | Speed | Best For |
|-------|------|-------|----------|
| tiny | 75 MB | Very fast | Quick checks |
| small | 500 MB | Fast | Most tasks |
| medium | 1.5 GB | Medium | German/non-English |
| large-v3 | 3 GB | Slow | Max quality |

### 🔍 YouTube Viral Podcast Researcher
**File:** `.agent/skills/youtube-podcast-researcher/SKILL.md`

Finds viral English content on YouTube relevant to the episode topic, downloads subtitles (no video download), and converts them to clean text for use as research material. Uses `yt-dlp`.

```bash
# Find and score viral videos
yt-dlp --flat-playlist --print "%(id)s | %(title)s | %(view_count)s views" "ytsearch20:UFO nuclear documentary"

# Download subtitles only
yt-dlp --write-subs --write-auto-subs --sub-lang en --sub-format srt --skip-download \
  -o "episodes/S01/E01/1_research/sources/%(title)s.%(ext)s" "https://youtube.com/watch?v=VIDEO_ID"
```

> **Key distinction:** English research sources are for *writing* the script. They do NOT go into the NotebookLM audio notebook.

### 🧠 Podcast Memory
**File:** `.agent/skills/memory/SKILL.md`

A persistent **SQLite + FTS5** database that remembers everything across episodes and sessions. This is what makes the pipeline resumable and self-improving.

What it stores:
- Episodes, sources, characters (Nova & Max)
- Phase outputs — where every file was saved
- Quality feedback per episode
- Skill profiles for every language × audience combo
- Visual styles per topic category
- Session state — so AI can resume mid-episode after interruption
- Workflow contract — phase rules and preconditions
- Topics used — prevents duplicates

```bash
MEM="python .agent/skills/memory/scripts/memory.py"

$MEM episode list                      # All episodes
$MEM smart-context 1                   # Focused AI context for episode 1
$MEM session load                      # Resume where we left off
$MEM contract verify 1 audio           # Check all preconditions before a phase
$MEM profile context de gen_z          # Get writing directive for German Gen Z
$MEM quality add 1 overall "Hooks worked" "Intro too long" "Shorter cold open" 8
$MEM profile evolve 1                  # Auto-update profile from quality score
```

---

## Core Scripts

### `start.py` — Setup & Launcher
One-command entry point. Handles all installation, configuration, and launches the server.

```bash
python start.py           # Normal launch
python start.py --reset   # Reset memory and reconfigure
```

### `app.py` — Web API Server
Flask server powering the dashboard. Provides REST endpoints and **Server-Sent Events (SSE)** for real-time log streaming to the browser.

Key API endpoints:
| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/episodes` | List all episodes |
| POST | `/api/episodes` | Create new episode |
| GET | `/api/episodes/<id>` | Get episode detail |
| GET | `/api/episodes/<id>/prompt` | Get the Antigravity prompt for this episode |
| POST | `/api/episodes/<id>/generate-youtube-meta` | Generate YouTube metadata |
| GET | `/api/episodes/<id>/thumbnail` | Serve episode thumbnail |
| GET | `/api/episodes/<id>/logs/stream` | Real-time log SSE stream |
| GET | `/api/languages` | List available languages |
| GET | `/api/audiences` | List target audiences |

### `core/pipeline.py` — Pipeline Orchestrator
CLI tool to inspect and control pipeline phase state.

```bash
python core/pipeline.py --episode-id 1 --status       # Show all phase progress
python core/pipeline.py --episode-id 1 --next          # What's next to run
python core/pipeline.py --episode-id 1 --dry-run       # Preview without doing anything
python core/pipeline.py --episode-id 1 --mark audio done  # Manually mark a phase
python core/pipeline.py --stats                        # Project-wide stats
python core/pipeline.py --suggest                      # Suggest next episode topic
```

### `core/new_episode.py` — Episode Initialiser
Creates the episode folder structure and registers it in memory.

```bash
python core/new_episode.py \
  --season 1 --episode 2 \
  --slug "Dark_Matter" \
  --title-de "Dunkle Materie" \
  --title-en "Dark Matter" \
  --topic "dark matter physics mystery"
```

### `scripts/force_16x9.py` — Image Resizer
Converts all images in a folder to exact 1920×1080 using crop-to-fill (no black bars).

```bash
python scripts/force_16x9.py "episodes/S01/E01/4_visuals/"
```

> Run this **once after all slides are generated**, not after each individual image.

### `scripts/update_phase.py` — Dashboard Updater
Marks a phase as done in the database and triggers a live dashboard refresh.

```bash
python scripts/update_phase.py <episode_id> <phase_name> done
```

### `scripts/log_phase.py` — Live Log Writer
Writes a timestamped log entry that streams live to the browser terminal.

```bash
python scripts/log_phase.py <episode_id> "📋 YouTube Pack generated" success
```

### `scripts/seed_all_profiles.py` — Profile Seeder
Seeds all 30 language × audience skill profiles into memory. Run automatically during `start.py`.

```bash
python scripts/seed_all_profiles.py
```

---

## Configuration Files

### `.agent/device_config.json`
Auto-generated by `start.py`. Stores GPU detection results.

```json
{
  "device": "cpu",
  "compute_type": "int8",
  "device_label": "CPU",
  "gpu_name": "None",
  "vram_gb": null,
  "speedup": "1x"
}
```

If you have an NVIDIA GPU, this will say `"device": "cuda"` and Whisper transcription will be **2-4× faster**.

### `.agent/whisper_model.txt`
Stores your chosen Whisper model name (e.g., `medium`). Set during `start.py` setup and automatically used by all transcription calls.

---

## How a Full Episode Is Produced

Here's the end-to-end flow, step by step:

**1. You open the dashboard** at `http://localhost:5000`, enter a topic (e.g., *"Are UFOs near nuclear weapons real?"*), pick a language (German), and pick an audience (Gen Z).

**2. Antigravity reads the pipeline prompt** generated by the UI (`/api/episodes/<id>/prompt`) and starts executing autonomously.

**3. Research phase:** yt-dlp searches YouTube for viral English content about the topic. Subtitles are downloaded and converted to clean text. Sources are logged in memory.

**4. Script phase:** The Dynamic Podcast Director skill loads the `de × gen_z` profile from memory — which tells it exactly what slang to use, what not to say, what cultural references resonate, and what hooks work. The script is written natively in German (not translated). An English version is also saved for review.

**5. Audio generation:** A fresh NotebookLM notebook is created with **only the German script** as the sole source. The `generate audio` command fires with a rich prompt describing the Nova/Max host dynamic and the Gen Z tone. Generation takes 15–20 minutes. YouTube metadata (5 viral title variants, full description, thumbnail prompt) are generated in parallel during this wait. A thumbnail image is generated with `generate_image`.

**6. Transcription:** Once the MP3 is downloaded, faster-whisper transcribes it locally, producing timestamped segments that map exactly to the generated audio.

**7. Visuals:** The transcript timestamps are used to plan one cinematic image per topic segment. `generate_image` is called in parallel batches of 3–4 images simultaneously. All images are resized to 1920×1080 with crop-to-fill.

**8. Deliverables:** A CapCut walkthrough markdown file is generated — a table mapping each image to its exact start/end timestamp so you can assemble the video in minutes. Quality feedback is logged and used to evolve the Gen Z German writing profile for future episodes.

**9. Cinematic video (background):** A separate NotebookLM notebook is created with English sources only. NotebookLM generates an AI cinematic video in English. It runs in the background — the episode is otherwise complete.

---

## Supported Languages & Audiences

**Languages:** Any of the 80+ languages supported by Google NotebookLM.  
Common codes: `de` (German), `en` (English), `es` (Spanish), `fr` (French), `ja` (Japanese), `ko` (Korean), `pt_BR` (Brazilian Portuguese), `zh_Hans` (Simplified Chinese).

**Audiences (skill profiles seeded):**
- `gen_z` — Gen Z (16–26)
- `millennials` — Millennials (27–42)  
- `tech_enthusiasts` — Tech professionals
- `families` — Family-friendly
- `academics` — University / research audiences
- *(and more)*

---

## Characters (The Hosts)

The podcast uses two recurring characters, guided by the generation prompts so NotebookLM's AI hosts match their personalities:

| Character | Role | Style |
|-----------|------|-------|
| **Nova** | Storyteller & expert | Builds tension, drops facts, uses analogies ("Stellt euch mal vor...") |
| **Max** | Reactor & listener's voice | Skeptical, says "Warte, WAS?!", challenges Nova |

These characters are stored in memory and loaded before every episode script and audio prompt.

---

## Dependencies

```
Flask==3.1.3                  # Web server for the dashboard
requests==2.32.5               # HTTP utilities
faster-whisper==1.2.1          # Local audio transcription (OpenAI Whisper)
yt-dlp==2026.3.3               # YouTube subtitle extraction
notebooklm-py==0.3.3           # Programmatic Google NotebookLM access
google-genai>=1.0.0            # Google AI SDK
google-generativeai>=0.8.0     # Gemini model access
google-api-python-client>=2.0  # Google API client
google-auth>=2.20.0            # Google authentication
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `notebooklm` auth fails | Run `notebooklm login` — session may have expired |
| Audio generation times out | Wait 5–10 min and retry; Google rate limits AI generation |
| Whisper transcription is slow | Run `python start.py` again and choose a smaller model |
| Images come out in wrong aspect ratio | Run `python scripts/force_16x9.py <visuals_folder>` |
| Episode pipeline broke mid-run | Run `python core/pipeline.py --episode-id <id> --status` to see where it stopped, then resume |
| yt-dlp gives "sign in" error | Use `yt-dlp --cookies-from-browser firefox "URL"` |
| Dashboard not loading | Make sure `python start.py` (or `run_server.bat`) is running |

---

## Project Structure

```
Content Translator/
├── start.py                  ← One-command setup + launch
├── app.py                    ← Flask web API + SSE log server
├── run_server.bat             ← Windows launch shortcut
├── requirements.txt           ← Python dependencies
├── core/
│   ├── pipeline.py            ← Phase orchestrator CLI
│   ├── new_episode.py         ← Episode folder + memory initialiser
│   └── create_cinematic.py    ← Cinematic notebook creator
├── scripts/
│   ├── force_16x9.py          ← Batch image resizer → 1920×1080
│   ├── update_phase.py        ← Dashboard phase status updater
│   ├── log_phase.py           ← Live log writer
│   ├── mem.py                 ← Memory CLI shortcut
│   ├── add_source.py          ← Source logger
│   ├── seed_all_profiles.py   ← Seeds 30 skill profiles into DB
│   └── install_gpu_support.py ← CUDA + cuDNN installer helper
├── ui/
│   ├── index.html             ← Dashboard HTML
│   ├── app.js                 ← Dashboard JS
│   └── styles.css             ← Dashboard styles
├── episodes/                  ← All episode output folders
└── .agent/
    ├── device_config.json     ← GPU/CPU config (auto-generated)
    ├── whisper_model.txt      ← Chosen Whisper model (auto-generated)
    ├── skills/
    │   ├── notebooklm/        ← NotebookLM CLI automation skill
    │   ├── audio-listener/    ← Whisper transcription skill
    │   ├── youtube-podcast-researcher/ ← YouTube research skill
    │   ├── dynamic-podcast-director/   ← Creative writing/directing skill
    │   └── memory/            ← Persistent SQLite memory system
    └── workflows/
        └── podcast-pipeline.md ← The master 8-phase workflow
```
