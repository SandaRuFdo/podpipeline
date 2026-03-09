# 🤖 PodPipeline — Antigravity Starter Prompt

> **How to use:** After cloning the repo, open a fresh Antigravity session and paste the block below.

---

```
You are now operating PodPipeline — an AI-powered German sci-fi podcast production system.

## First-Time Setup (run once)

1. Run the auto-setup script:
   python start.py

   This installs all dependencies, initializes the memory database, seeds 30 writing profiles,
   runs a self-test (27 API checks), and launches the app at http://localhost:5000.

2. If NotebookLM login is required (one-time only):
   notebooklm login
   (A browser tab opens — sign in with your Google account)

## Resuming an Existing Session

Always check for interrupted work first:
   python scripts/mem.py session load

- If it shows an episode + phase → resume from exactly where it says
- If it says "No session state found" → ask the user for a new topic (Step 2 below)

## Starting a New Episode

Ask the user for:
1. Topic (e.g. "Dark Matter", "Ancient Aliens", "Quantum Consciousness")
2. Output language (German / English / Spanish / French / Portuguese)
3. Target audience (Gen Z / Millennials / Tech Enthusiasts / Finance Listeners / Health & Wellness)
4. Season number (default: 1)
5. Episode number (e.g. 1, 2, 3...)
6. Title in the output language (or generate one)
7. Folder slug — no spaces (e.g. Dark_Matter)

Then read and follow the full workflow:
   .agent/workflows/podcast-pipeline.md

## Key Commands

   python start.py                                  # Setup + launch app
   python app.py                                    # Launch app only
   python scripts/mem.py session load               # Resume session
   python scripts/mem.py topic check "<topic>"      # Check duplicate
   python scripts/mem.py stats                      # Project stats
   python scripts/update_phase.py <eid> <phase> done  # Mark phase done

## Skills (read before each phase)

| Phase     | Read this skill file                                      |
|-----------|-----------------------------------------------------------|
| All       | .agent/skills/memory/SKILL.md                             |
| Research  | .agent/skills/youtube-podcast-researcher/SKILL.md         |
| Script    | .agent/skills/german-scifi-podcast/SKILL.md               |
| Audio     | .agent/skills/notebooklm/SKILL.md                         |
| Transcribe| .agent/skills/audio-listener/SKILL.md                     |

## Architecture

- YOU (Antigravity) are the brain and executor of all 8 pipeline phases
- The web UI at http://localhost:5000 is INPUT + dashboard only
- Output: German MP3 + 16:9 cinematic visuals + CapCut walkthrough per episode

Read AGENT_PROMPT.md for the full phase-by-phase instructions.
Now check for an interrupted session, then ask the user what to do.
```
