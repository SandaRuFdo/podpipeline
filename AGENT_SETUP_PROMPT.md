# 🤖 PodPipeline — AI Agent Setup Prompt

> Paste this entire prompt to your AI agent (Antigravity / Claude / Gemini) on the new PC to have it set up PodPipeline autonomously.

---

## PROMPT (copy everything below this line)

---

You are setting up **PodPipeline** — an AI-powered podcast production tool — on this machine. Execute every step below autonomously. Do not stop until the final smoke test passes.

## Step 1 — Verify prerequisites

Run these checks. If any fail, tell the user exactly what to install before continuing:

```bash
python --version        # Must be 3.10 or higher
git --version           # Must be installed
ffmpeg -version         # Must be installed and in PATH
```

If Python < 3.10: stop and ask user to install Python 3.10+.
If ffmpeg missing: stop and ask user to install ffmpeg and add it to PATH.

## Step 2 — Clone the repository

```bash
git clone https://github.com/SandaRuFdo/podpipeline.git
cd podpipeline
```

## Step 3 — Run the automated setup

```bash
python start.py
```

This is interactive — when it asks you to choose a Whisper model, select `medium`.
When it asks about GPU, let it auto-detect.
When the server starts at `http://localhost:5000`, the setup is complete.

If `start.py` fails for any reason, run these manually in order:

```bash
pip install -r requirements.txt
pip install notebooklm-py
python scripts/mem.py init
python scripts/seed_all_profiles.py
python scripts/mem.py char set NOVA storyteller "Builds tension, drops shocking facts, uses vivid analogies. Drives narrative. Energy: excited, passionate."
python scripts/mem.py char set MAX reactor "Represents the listener. Challenges NOVA, asks clarifying questions. Energy: skeptical, curious."
python scripts/mem.py style set tech "Futuristic dark digital workspace, glowing neural networks, holographic UI panels" "deep black, electric teal, neon blue" "high-tech, cinematic"
python scripts/mem.py style set space "Cosmic deep space, swirling nebula, planetary surfaces" "deep black, violet, star white" "awe-inspiring, epic"
python scripts/mem.py style set health "Clean medical laboratory, DNA strands, cellular close-ups" "clinical white, medical blue, bio green" "precise, clean, trustworthy"
python app.py
```

## Step 4 — Authenticate NotebookLM

Open a second terminal and run:

```bash
notebooklm login
```

A browser window will open. Sign in with the Google account that has NotebookLM access.

Confirm it works:
```bash
notebooklm list
```

If `notebooklm list` returns without error, authentication is done.

## Step 5 — (Optional) GPU acceleration

If this machine has an NVIDIA GPU, run:

```bash
python scripts/install_gpu_support.py
```

This installs CUDA support for faster-whisper. Whisper transcription becomes 4–8× faster.

## Step 6 — Final smoke test

Run all of these. Every single one must pass without errors:

```bash
# 1. Core Python dependencies
python -c "import flask, faster_whisper; print('Core deps OK')"

# 2. NotebookLM CLI working
notebooklm list

# 3. ffmpeg available
ffmpeg -version

# 4. yt-dlp available
yt-dlp --version

# 5. Memory database working
python scripts/mem.py stats

# 6. Characters seeded
python scripts/mem.py char list

# 7. Visual styles seeded
python scripts/mem.py style get tech

# 8. Server reachable (run this after starting the server)
curl http://localhost:5000/api/languages
```

## Step 7 — Confirm ready

If all 8 checks pass, report:

```
✅ PodPipeline is ready on this machine.
- Python: [version]
- ffmpeg: [version]
- NotebookLM: authenticated
- Memory DB: initialized with [N] profiles
- Characters: NOVA + MAX seeded
- Visual styles: tech, space, health seeded
- Server: running at http://localhost:5000
- GPU: [CUDA / CPU]
```

The tool is ready. The user can now open http://localhost:5000 in their browser and create their first episode.
