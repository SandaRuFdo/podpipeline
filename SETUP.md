# 🚀 PodPipeline — Fresh PC Setup Guide

Get the tool running on a brand new machine in under 10 minutes.

---

## Prerequisites

Install these first — all free:

| Tool | Download | Check |
|------|----------|-------|
| **Python 3.10+** | [python.org](https://python.org/downloads) | `python --version` |
| **Git** | [git-scm.com](https://git-scm.com/downloads) | `git --version` |
| **ffmpeg** | [ffmpeg.org/download](https://ffmpeg.org/download.html) | `ffmpeg -version` |
| **Google NotebookLM account** | [notebooklm.google.com](https://notebooklm.google.com) | Log in once in browser |

> ⚠️ **ffmpeg must be in PATH.** On Windows: download the zip, extract it, and add `ffmpeg/bin` to your System Environment Variables → PATH. Then open a new terminal and run `ffmpeg -version` to confirm.

---

## Step-by-Step Setup

### Step 1 — Clone the repo

```bash
git clone https://github.com/SandaRuFdo/podpipeline.git
cd podpipeline
```

### Step 2 — Run the one-command setup

```bash
python start.py
```

This single command does **everything**:
1. ✅ Checks Python 3.10+
2. ✅ Checks ffmpeg
3. ✅ Installs all Python packages from `requirements.txt`
4. ✅ Installs `notebooklm-py` CLI tool
5. ✅ Asks you to pick a Whisper model (choose `medium` for best quality)
6. ✅ Detects your GPU (CUDA) or falls back to CPU
7. ✅ Creates and initialises the SQLite memory database
8. ✅ Seeds 30 language × audience skill profiles
9. ✅ Seeds host characters (NOVA + MAX) and visual styles
10. ✅ Launches the web server at `http://localhost:5000`

> 💡 **GPU tip:** If you have an NVIDIA GPU, run `python scripts/install_gpu_support.py` after setup to install CUDA support. Whisper transcription becomes 4–8× faster.

### Step 3 — Authenticate with NotebookLM

In a new terminal (keep `start.py` running in the first one):

```bash
notebooklm login
```

This opens your browser for Google sign-in. Sign in with the Google account that has NotebookLM access. You only need to do this once — the session is saved.

Confirm it's working:
```bash
notebooklm list
```

### Step 4 — Open the dashboard

Open your browser and go to:
```
http://localhost:5000
```

You should see the PodPipeline dashboard. ✅

---

## Future Launches

After the one-time setup, to start the tool:

```bash
python start.py
```

Or on Windows, double-click:
```
run_server.bat
```

---

## Quick Smoke Test

Run this to verify everything is installed correctly:

```bash
python -c "import flask, faster_whisper; print('Core deps OK')"
notebooklm list
ffmpeg -version
yt-dlp --version
python scripts/mem.py stats
```

All 5 should return without errors. If all pass — you're ready to produce your first episode.

---

## Resetting Everything

To wipe all episode data and start completely fresh:

```bash
python start.py --reset
```

This deletes the memory database and reinitialises it clean. Your code, workflow, and skill files are untouched.

To also delete all episode output files:
```bash
# Windows
Remove-Item -Recurse -Force episodes\

# Then re-init
python start.py --reset
```

---

## Common Issues

| Problem | Fix |
|---------|-----|
| `python: command not found` | Use `python3` instead, or add Python to PATH |
| `notebooklm: command not found` | Run `pip install notebooklm-py` manually |
| `ffmpeg: command not found` | Add ffmpeg/bin to your PATH and restart terminal |
| `notebooklm login` fails | Make sure you have a Google account with NotebookLM access |
| Dashboard shows blank page | Check `python start.py` is still running in the other terminal |
| Transcription is very slow | No GPU detected — run `python scripts/install_gpu_support.py` |

---

## Need Help?

Read the full docs in **README.md** — it covers the architecture, all 8 phases, every script, and the complete workflow in detail.
