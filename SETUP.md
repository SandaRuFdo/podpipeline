# 🚀 PodPipeline — Setup Guide

> **TL;DR — One command after cloning:**
> ```bash
> python start.py
> ```
> That's it. Install, init, test, launch — all automatic.

---

## Prerequisites

Make sure you have installed:
- **Python 3.10+** — check: `python --version`
- **Git** — check: `git --version`
- **ffmpeg** — needed for image resize (Phase 6)
  - Windows: `winget install ffmpeg`
  - macOS: `brew install ffmpeg`
  - Ubuntu: `sudo apt install ffmpeg`
- A **Google account** (for NotebookLM audio generation)

---

## Clone the repo

```bash
git clone https://github.com/SandaRuFdo/podpipeline.git
cd podpipeline
```

---

## Run the starter command

```bash
python start.py
```

**What it does automatically:**

| Step | Action |
|------|--------|
| 1 | Python 3.10+ version check |
| 2 | ffmpeg detection (warns if missing) |
| 3 | `pip install -r requirements.txt` |
| 4 | Memory database init (SQLite) |
| 5 | Seed 30 writing profiles (language × audience) |
| 6 | Self-test — checks all API endpoints, auto-fixes if broken |
| 7 | NotebookLM auth check (warns if not logged in) |
| 8 | Launches the app at http://localhost:5000 |

---

## NotebookLM login (one-time, manual step)

`start.py` will warn you if this hasn't been done. Run once:

```bash
notebooklm login
```

A browser tab opens → sign in with Google → done.  
Credentials saved to `~/.notebooklm/` — never needs repeating.

---

## Optional flags

```bash
python start.py --no-launch     # Install + test only, don't start server
python start.py --skip-tests    # Skip self-test (faster)
python start.py --port 8080     # Use a different port
python start.py --reset-db      # ⚠ Wipe DB and re-init from scratch
```

---

## Quick verify after launch

```bash
python scripts/mem.py stats
python scripts/mem.py profile list
```

You should see: 0 episodes (fresh start) + 30 skill profiles.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError` | `pip install -r requirements.txt` |
| `notebooklm: command not found` | `pip install notebooklm-py` |
| Port 5000 in use | `python start.py --port 8080` |
| Database errors | `python start.py --reset-db` |
| Auth expired | `notebooklm login` |
| ffmpeg not found | Install ffmpeg and add to PATH |

---

## Project Structure

```
podpipeline/
├── start.py                ← START HERE: python start.py
├── app.py                  ← Web UI server
├── requirements.txt
├── .agent/
│   ├── skills/
│   │   ├── memory/         ← SQLite DB + 30 writing profiles
│   │   ├── notebooklm/     ← Audio generation skill
│   │   ├── dynamic-podcast-director/
│   │   ├── audio-listener/ ← Whisper transcription
│   │   └── youtube-podcast-researcher/
│   └── workflows/
│       └── podcast-pipeline.md  ← Full 8-phase workflow
├── core/                   ← Episode creation + pipeline logic
├── scripts/                ← mem.py, force_16x9.py, seed profiles
├── ui/                     ← Web frontend (HTML/CSS/JS)
└── episodes/               ← Your output (git-ignored)
```
