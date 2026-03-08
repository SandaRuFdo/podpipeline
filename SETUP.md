# 🚀 PodPipeline — Setup Guide for a New Machine

> Hand this entire file to your **Antigravity AI** and say:
> *"Follow SETUP.md step by step to install PodPipeline on my laptop"*

---

## Clone URL

```
https://github.com/SandaRuFdo/podpipeline.git
```

---

## Step 1 — Prerequisites

Make sure you have:
- **Python 3.10+** (check: `python --version`)
- **Git** (check: `git --version`)
- **ffmpeg** (check: `ffmpeg -version`) — needed for audio/image processing
  - Windows: `winget install ffmpeg` or download from https://ffmpeg.org/download.html
- A **Google account** (for NotebookLM audio generation)

---

## Step 2 — Clone the project

```powershell
git clone https://github.com/SandaRuFdo/podpipeline.git
cd podpipeline
```

> Choose a good home folder, e.g. `C:\Users\YourName\Documents\podpipeline`

---

## Step 3 — Install Python dependencies

```powershell
pip install -r requirements.txt
```

This installs:
- `Flask` — web server
- `faster-whisper` — audio transcription
- `yt-dlp` — YouTube subtitle downloader  
- `notebooklm-py` — AI audio generation
- `google-genai`, `google-auth` — Google AI APIs

---

## Step 4 — Authenticate with NotebookLM

This **opens a browser tab** for Google login. Required to generate podcast audio.

```powershell
notebooklm login
```

1. Browser opens → Sign in with your Google account
2. Grant permissions
3. Terminal shows: `✅ Login successful`

> You only do this once. Credentials are saved to `~/.notebooklm/`

---

## Step 5 — Initialize the memory database

```powershell
$env:PYTHONIOENCODING="utf-8"
python .agent/skills/memory/scripts/memory.py init
```

Expected output: `Database ready: ...podcast_memory.db`

---

## Step 6 — Seed skill profiles (30 writing profiles)

```powershell
$env:PYTHONIOENCODING="utf-8"
python scripts/seed_all_profiles.py
```

Expected output: `✅ Seeded 30 skill profiles`

> These are the AI writing personality profiles (language × audience combos)

---

## Step 7 — Launch the web tool

```powershell
$env:PYTHONIOENCODING="utf-8"
python app.py
```

Open your browser at: **http://localhost:5000**

---

## Quick Verify — Everything works

Run this to check the memory system is ready:

```powershell
$env:PYTHONIOENCODING="utf-8"
python .agent/skills/memory/scripts/memory.py stats
python .agent/skills/memory/scripts/memory.py profile list
python .agent/skills/memory/scripts/memory.py contract list
```

You should see:
- Stats with 0 episodes (fresh start)
- 30 skill profiles listed
- 8 workflow phases listed

---

## Creating Your First Episode

1. Go to **http://localhost:5000**
2. Click **New Episode** in the sidebar
3. Fill in:
   - Season / Episode number (e.g. 1 / 1)
   - Folder slug (e.g. `Dark_Matter`)
   - German title + topic
   - Pick language + audience
4. Click **Create Episode**
5. Your Antigravity AI will run the 8-phase pipeline

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` again |
| `notebooklm: command not found` | Run `pip install notebooklm-py` |
| Port 5000 in use | Kill the process or change port in `app.py` |
| Database errors | Run `python .agent/skills/memory/scripts/memory.py init` |
| Auth expired | Run `notebooklm login` again |
| ffmpeg not found | Install ffmpeg and add to PATH |

---

## Project Folder Structure

```
podpipeline/
├── app.py                  ← Start here: python app.py
├── setup.py                ← Alternative: python setup.py
├── requirements.txt
├── .agent/
│   ├── skills/
│   │   ├── memory/         ← SQLite DB + 30 writing profiles
│   │   ├── notebooklm/     ← Audio generation skill
│   │   ├── german-scifi-podcast/ ← Podcast director skill
│   │   ├── audio-listener/ ← Whisper transcription skill
│   │   └── youtube-podcast-researcher/
│   └── workflows/
│       └── podcast-pipeline.md  ← The full 8-phase workflow
├── core/                   ← Episode creation + pipeline logic
├── scripts/                ← force_16x9.py, seed profiles
├── ui/                     ← Web frontend (HTML/CSS/JS)
└── episodes/               ← Your output (git-ignored)
```

---

## For Antigravity — One-Shot Setup Command

Tell your Antigravity AI:

> *"Clone https://github.com/SandaRuFdo/podpipeline.git, run pip install -r requirements.txt, run notebooklm login in a browser tab, init the memory DB, seed the profiles, then launch the app and open http://localhost:5000"*
