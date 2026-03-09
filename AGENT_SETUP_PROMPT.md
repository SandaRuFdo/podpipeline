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

This should open your browser for Google sign-in. Sign in with the Google account that has NotebookLM access.

After signing in, press ENTER in the terminal to save the session.

### ⚠️ If the browser does NOT open automatically:

**Option A — Copy auth from another PC that's already logged in:**
```bash
# On the OLD machine — copy this file:
# C:\Users\<username>\.notebooklm\storage_state.json

# On the NEW machine — paste it here:
# C:\Users\<username>\.notebooklm\storage_state.json
# (create the .notebooklm folder if it doesn't exist)
```

**Option B — Use the URL printed in the terminal:**
When the browser doesn't auto-open, `notebooklm login` usually prints a URL. Copy it and paste it manually into your browser.

**Verify authentication worked:**
```bash
notebooklm status
```
This must say `Authenticated as: your@email.com`. If it says "not authenticated" — repeat the login steps.

## Step 5 — (Optional) GPU acceleration

If this machine has an NVIDIA GPU, run:

```bash
python scripts/install_gpu_support.py
```

This installs CUDA support for faster-whisper. Whisper transcription becomes 4–8× faster.

## Step 6 — Final smoke test (automated)

Run the automated smoke test. It checks all 10 system requirements and reports PASS/FAIL:

```bash
python scripts/smoke_test.py
```

This runs 11 checks automatically:
1. Python 3.10+
2. Core deps (flask, faster-whisper)
3. ffmpeg in PATH
4. yt-dlp installed
5. notebooklm-py CLI installed
6. **NotebookLM authenticated (Google account)** ← catches missing login
7. Memory DB working
8. Characters seeded (NOVA + MAX)
9. Visual style 'tech' seeded
10. `.agent/device_config.json` exists
11. `.agent/whisper_model.txt` exists

Expected output:
```
==================================================
  PodPipeline — Smoke Test
==================================================

  [PASS] Python 3.x (need 3.10+)
  [PASS] Core deps (flask, faster_whisper)
  [PASS] ffmpeg in PATH
  [PASS] yt-dlp installed
  [PASS] notebooklm-py CLI installed
  [PASS] Memory DB working
  [PASS] Characters seeded (NOVA + MAX)
  [PASS] Visual style 'tech' seeded
  [PASS] .agent/device_config.json exists
  [PASS] .agent/whisper_model.txt exists

  PASSED: 10/10

  ✅ All checks passed — PodPipeline is ready!
  Open http://localhost:5000 to start your first episode.
==================================================
```

If any checks show `[FAIL]`, fix the listed issues and re-run `python scripts/smoke_test.py` until all pass.

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
