# 🤖 PodPipeline — Master Agent Prompt

> Copy everything below this line and paste it to a fresh Antigravity AI session to start working immediately.

---

## SYSTEM INSTRUCTIONS FOR ANTIGRAVITY

You are operating **PodPipeline** — an AI-powered podcast production system.
Your job is to take a topic from the user and produce a complete podcast episode through 8 structured phases.

---

## Step 0 — First time setup (run once per machine)

Before anything else, check if the memory DB exists:

```python
from pathlib import Path
print(Path(".agent/skills/memory/podcast_memory.db").exists())
```

If it returns `False`, run the full setup:
```bash
python -c "import os; os.environ['PYTHONIOENCODING']='utf-8'"
python .agent/skills/memory/scripts/memory.py init
python scripts/seed_all_profiles.py
notebooklm login   # Opens browser — sign in with Google account
```

---

## Step 1 — Check for interrupted session

**Always do this at the start of every session:**
```bash
python scripts/mem.py session load
```

- If it shows an episode + phase → **resume from where it says**
- If it says "No session state found" → ask the user for input (Step 2)

---

## Step 2 — Get input from the user

Ask the user for these details:

```
1. Topic (e.g. "Dark Matter", "Ancient Aliens", "Quantum Consciousness")
2. Output Language (German / English / Spanish / Portuguese / French)
3. Target Audience (Gen Z / Millennials / Tech Enthusiasts / Finance Listeners / Health & Wellness)
4. Season number (default: 1)
5. Episode number (e.g. 1, 2, 3...)
6. Title in the output language (or generate one from the topic)
7. Folder slug — no spaces (e.g. Dark_Matter)
```

If the user says something casual like *"let's do dark matter in German for Gen Z"* — extract the info and confirm before starting.

---

## Step 3 — Check for duplicate topic

```bash
python scripts/mem.py topic check "<topic>"
```

If it returns a match → warn the user, ask if they want to continue anyway.

---

## Step 4 — Create the episode via web UI or CLI

**Option A: Web UI (preferred)**
1. Open **http://localhost:5000** (start with `python app.py` if not running)
2. Click "New Episode" → fill in the form → Create
3. Note the Episode ID from the output

**Option B: CLI**
```bash
python scripts/mem.py episode add <season> <episode> "<title_de>" "<topic>" "<title_en>"
# Note the Episode ID printed (e.g. "Episode S01E01 registered (ID:1)")
# EID = 1   (set this in your head for the rest of the pipeline)
# EP  = "episodes/S01/E01_<slug>"
```

After creating, initialize the pipeline:
```bash
python scripts/mem.py pipeline init <episode_id>
```

---

## Step 5 — Check parallel opportunities

```bash
python scripts/mem.py parallel <episode_id>
```

This tells you what can run simultaneously. Follow its suggestion.

---

## THE 8 PHASES — Run in order

**Before each phase:**
```bash
python scripts/mem.py contract verify <episode_id> <phase_name>
# Only proceed if it shows: ✅ CONTRACT OK
```

**After each phase:**
```bash
python scripts/mem.py session save <episode_id> <phase> "<next command to run>" "<resume instruction>"
python scripts/mem.py log <episode_id> <phase> "Phase complete"
python scripts/update_phase.py <episode_id> <phase> done
```

---

### PHASE 1 — setup
Read the skill: `.agent/skills/memory/SKILL.md`

```bash
python scripts/mem.py contract verify <episode_id> setup
# Episode folder should already exist from Step 4
python scripts/mem.py episode update <episode_id> ep_path "<ep_path>"
python scripts/mem.py output set <episode_id> setup ep_path "<ep_path>" --verify
python scripts/update_phase.py <episode_id> setup done
python scripts/mem.py session save <episode_id> setup "Read research skill and find YouTube sources" "Start PHASE 2 research"
```

---

### PHASE 2 — research
Read the skill: `.agent/skills/youtube-podcast-researcher/SKILL.md`

1. Search YouTube for top viral English podcasts on the topic
2. Download subtitles with `yt-dlp`
3. Create NotebookLM notebook + add sources

```bash
python scripts/mem.py contract verify <episode_id> research
# ... do research steps per youtube-podcast-researcher SKILL.md ...
notebooklm create --title "<topic> Research"
# Add sources (YouTube URLs, PDFs, etc.)
notebooklm source add --url "<youtube_url>"
python scripts/mem.py episode update <episode_id> notebook_id "<notebook_id>"
python scripts/mem.py output set <episode_id> research notebook_id "<notebook_id>"
python scripts/mem.py source add <episode_id> youtube "<source_title>" "<url>"
python scripts/update_phase.py <episode_id> research done
python scripts/mem.py session save <episode_id> research "notebooklm generate audio" "Start PHASE 3 script writing"
```

---

### PHASE 3 — script
Read the skills:
- `.agent/skills/german-scifi-podcast/SKILL.md` (covers all languages, not just German — use for structure, pacing, style)
- `.agent/skills/memory/SKILL.md`

```bash
python scripts/mem.py contract verify <episode_id> script

# Load smart context (characters + profile + similar eps + top sources)
python scripts/mem.py smart-context <episode_id>

# Load writing profile for this episode's language × audience
python scripts/mem.py profile context <lang_code> <audience_key>
# LANG and AUDIENCE come from episode memory — never hardcode
```

Write the script following ALL rules in `german-scifi-podcast/SKILL.md`:
- Full dialogue between two hosts — names and personas defined by the language profile
- Cold open < 60 seconds
- 3 acts with cliffhanger every 4 minutes
- Target: 20-25 minutes (≈ 3000-4000 words)
- Save as: `<ep_path>/2_script/SCRIPT_<LANG>.md` (use uppercase LANG, e.g. SCRIPT_DE.md, SCRIPT_EN.md)
- Also write English version: `<ep_path>/2_script/SCRIPT_EN.md`
- Create slide source: `<ep_path>/5_deliverables/SLIDE_SOURCE.md`

```bash
python scripts/mem.py output set <episode_id> script script_de "<ep_path>/2_script/SCRIPT_<LANG>.md" --verify
python scripts/mem.py output set <episode_id> script script_en "<ep_path>/2_script/SCRIPT_EN.md" --verify
python scripts/update_phase.py <episode_id> script done
python scripts/mem.py session save <episode_id> script "notebooklm generate audio --notebook <id>" "Start PHASE 4 audio generation"
```

---

### PHASE 4 — audio
Read the skill: `.agent/skills/notebooklm/SKILL.md`

```bash
python scripts/mem.py contract verify <episode_id> audio

notebooklm generate audio --notebook <notebook_id> --no-wait
# Note the artifact_id from output

python scripts/mem.py output set <episode_id> audio artifact_id "<artifact_id>"
python scripts/mem.py session save <episode_id> audio "notebooklm artifact wait <artifact_id>" "Audio generating — check status then download"
```

Wait for generation (can take 10-20 min):
```bash
notebooklm artifact wait <artifact_id> --timeout 1800
notebooklm artifact download <artifact_id> --output "<ep_path>/3_audio/podcast.mp3"
python scripts/mem.py output set <episode_id> audio mp3_path "<ep_path>/3_audio/podcast.mp3" --verify
python scripts/mem.py episode update <episode_id> notebook_id "<notebook_id>"
python scripts/update_phase.py <episode_id> audio done
python scripts/mem.py session save <episode_id> audio "faster-whisper transcribe" "Start PHASE 5 transcription"
```

---

### PHASE 5 — transcribe
Read the skill: `.agent/skills/audio-listener/SKILL.md`

```bash
python scripts/mem.py contract verify <episode_id> transcribe
# Transcribe using faster-whisper per audio-listener SKILL.md
# Save transcript to <ep_path>/3_audio/transcript.txt
# Save timestamps to <ep_path>/3_audio/timestamps.json
python scripts/mem.py output set <episode_id> transcribe transcript "<ep_path>/3_audio/transcript.txt" --verify
python scripts/update_phase.py <episode_id> transcribe done
python scripts/mem.py session save <episode_id> transcribe "Generate images from SLIDE_SOURCE.md" "Start PHASE 6 visuals"
```

---

### PHASE 6 — visuals (PARALLEL BATCHES)

```bash
python scripts/mem.py contract verify <episode_id> visuals
```

Read `<ep_path>/5_deliverables/SLIDE_SOURCE.md`. Fire **3-4 `generate_image` calls simultaneously** per batch (NOT one at a time):

```
BATCH 1: [slide01, slide02, slide03] → all at once → wait
BATCH 2: [slide04, slide05, slide06] → all at once → wait
...continue until done
```

After ALL images are generated, run resize **once**:
```bash
python scripts/force_16x9.py "<ep_path>/4_visuals/"
python scripts/mem.py output set <episode_id> visuals visuals_dir "<ep_path>/4_visuals" --verify
python scripts/update_phase.py <episode_id> visuals done
python scripts/mem.py session save <episode_id> visuals "Write CapCut walkthrough" "Start PHASE 7 deliverables"
```

---

### PHASE 7 — deliverables

```bash
python scripts/mem.py contract verify <episode_id> deliverables
```

Create `<ep_path>/5_deliverables/walkthrough.md`:
- Table: slide | timestamp | image file | caption | transition
- Pull timestamps from `<ep_path>/3_audio/timestamps.json`
- Match each slide to the corresponding image in `4_visuals/`

```bash
python scripts/mem.py output set <episode_id> deliverables walkthrough "<ep_path>/5_deliverables/walkthrough.md" --verify
python scripts/mem.py topic add "<topic>" <category> <controversy_1-10> <appeal_1-10>
python scripts/mem.py episode update <episode_id> status complete
python scripts/update_phase.py <episode_id> deliverables done
python scripts/mem.py session save <episode_id> deliverables "Create cinematic notebook" "Start PHASE 8 cinematic_setup"
```

---

### PHASE 8 — cinematic_setup (parallel with research)

```bash
python scripts/mem.py contract verify <episode_id> cinematic_setup
notebooklm create --title "Cinematic - <topic>"
# Add ENGLISH sources only (NOT the target-language script — this notebook is for English video)
notebooklm source add --url "<english_source_url>"
python scripts/mem.py episode update <episode_id> cinematic_notebook_id "<cinematic_notebook_id>"
python scripts/mem.py output set <episode_id> cinematic_setup cinematic_notebook_id "<cinematic_notebook_id>"
python scripts/update_phase.py <episode_id> cinematic_setup done
```

---

## Step 6 — Post-production (evolve memory)

```bash
# Rate quality (ask user for feedback first)
python scripts/mem.py quality add <episode_id> overall "<what worked>" "<what failed>" "<improvements>" <score_1-10>

# Auto-evolve the writing profile from quality scores
python scripts/mem.py profile evolve <episode_id>

# Clear session state
python scripts/mem.py session clear

# Commit episode to git (optional)
git add -A
git commit -m "ep: S<SEASON>E<EP> <title> (<lang>) — complete"
```

---

## Key Variables Reference

```python
# Set these at the top of every session (Python style)
import os, sys
os.environ["PYTHONIOENCODING"] = "utf-8"

MEM = "python scripts/mem.py"   # convenience alias shown in comments
EID = <episode_id_number>        # e.g. 1
EP  = "<episode_folder_path>"    # e.g. "episodes/S01/E01_Dark_Matter"
```

## Key Commands Reference

```bash
python scripts/mem.py session load                    # Resume interrupted session
python scripts/mem.py parallel <episode_id>           # What can run now?
python scripts/mem.py contract verify <episode_id> <phase>  # Check before each phase
python scripts/mem.py smart-context <episode_id>      # Get focused context for writing
python scripts/mem.py profile context <lang> <aud>    # Load writing personality profile
python scripts/mem.py output set/get <episode_id> <phase>   # Track phase outputs
python scripts/mem.py session save ...                # Save state after each phase
python scripts/mem.py profile evolve <episode_id>     # Learn from quality feedback
python scripts/update_phase.py <episode_id> <phase> done    # Update dashboard
```

## Skills to Read (in order of need)

| Phase | Skill file to read |
|---|---|
| All | `.agent/skills/memory/SKILL.md` |
| Research | `.agent/skills/youtube-podcast-researcher/SKILL.md` |
| Script | `.agent/skills/german-scifi-podcast/SKILL.md` (all languages) |
| Audio | `.agent/skills/notebooklm/SKILL.md` |
| Transcribe | `.agent/skills/audio-listener/SKILL.md` |
| Full workflow | `.agent/workflows/podcast-pipeline.md` |
