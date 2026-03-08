---
description: End-to-end German sci-fi podcast production — from topic to YouTube-ready deliverables
---
// turbo-all

# 🎬 Podcast Production Pipeline

> **ARCHITECTURE (never forget this):**  
> The UI/dashboard is **INPUT ONLY** — it collects the topic, language, audience, and shows progress.  
> **Antigravity is the brain and executor.** After input is received, I run all phases autonomously.  
> No other AI, no automation bot. Just me, the tools, and the output folders.

**Input:** Topic from user via UI  
**Output:** German MP3 + 16:9 visuals + CapCut walkthrough — all in the episode folder

> **Windows note:** Always set `$env:PYTHONIOENCODING="utf-8"` before any Python command.


---

## BEFORE STARTING — Check Memory

```powershell
$env:PYTHONIOENCODING="utf-8"
$MEM = "python .agent/skills/memory/scripts/memory.py"

# Check if topic was already covered
& $MEM topic check "<topic>"

# Load character bible for script consistency
& $MEM context
```

---

## PHASE 1 — Create Episode Folder

```bash
# One command does everything: folder + memory + README
python new_episode.py \
  --season 1 --episode 2 \
  --slug "Dark_Matter" \
  --title-de "Dunkle Materie" \
  --title-en "Dark Matter" \
  --topic "dark matter physics mystery"

# → Script prints the episode Memory ID — note it as $EID
# → Folder created: episodes/S01/E02_Dark_Matter/
```

```python
# Set these vars for the rest of the pipeline
EP  = "episodes/S01/E02_Dark_Matter"
EID = 2   # from new_episode.py output
MEM = "python .agent/skills/memory/scripts/memory.py"
```

---

## PHASE 2 — Research (English Sources for Understanding Only)

> ⚠️ English sources are **research fuel only** — they do NOT go into the audio notebook.
> The German script is the **single source** for audio generation (Phase 4).

### 2.1 Find viral English content on the topic

```powershell
# Search YouTube for relevant podcasts/documentaries
yt-dlp --flat-playlist --print "%(id)s | %(title)s | %(view_count)s views | %(duration_string)s" `
  "ytsearch20:<topic> documentary science"

# Pick the best video, check subtitles
yt-dlp --list-subs "https://youtube.com/watch?v=VIDEO_ID"

# Download subtitles only (no video)
yt-dlp --write-subs --write-auto-subs --sub-lang en --sub-format srt --skip-download `
  -o "$EP/1_research/sources/%(title)s.%(ext)s" `
  "https://youtube.com/watch?v=VIDEO_ID"

# Convert SRT to clean text
python .agent/skills/youtube-podcast-researcher/scripts/srt_to_text.py `
  "$EP/1_research/sources/<title>.en.srt"
```

### 2.2 Log sources in memory

```powershell
& $MEM source add $EID youtube "<video title>" "https://youtube.com/..."
& $MEM source add $EID wikipedia "<article title>" "https://en.wikipedia.org/..."
& $MEM log $EID research "English sources downloaded for script writing"
```

---

## PHASE 3 — Script Writing (German, Gen Z, Nova + Max)

> Read the English sources from `$EP/1_research/sources/` to deeply understand the topic.
> Then write an amazing German script — this is where the magic happens.

### 3.1 Load memory context for consistency

```powershell
& $MEM context $EID
```

### 3.2 Write the German script

Use **German SciFi Podcast Director** skill. Save to `$EP/2_script/SCRIPT_DE.md`:

- **Structure:** Cold Open → Theme Intro → Act 1 → Act 2 (Twist) → Act 3 → Outro
- **Tone:** Nova (storyteller) + Max (reactor) — casual German, Gen Z analogies
- **Length:** 15–25 minutes of dialogue
- **No „Willkommen bei..."** — start mid-action
- **Use English sources as reference** — adapt, don't translate

### 3.3 Write English translation

Save to `$EP/2_script/SCRIPT_EN.md` — section-by-section for user review.

```powershell
& $MEM log $EID script "Script written"
```

---

## PHASE 4 — Generate Podcast (Script-Only Notebook)

> 🎯 **KEY RULE:** The script is the ONLY source for audio generation.
> Do NOT add English research sources to this notebook.

### 4.1 Create a fresh notebook for audio generation

```powershell
$env:PYTHONIOENCODING="utf-8"

notebooklm create "S{0:D2}E{1:D2} - <Topic Title>" --json
# → Save notebook ID
notebooklm use <notebook_id>

# Update memory with notebook ID
& $MEM episode update $EID notebook_id <notebook_id>
```

### 4.2 Add ONLY the German script as source

```powershell
# This is the ONLY source — no English transcripts, no Wikipedia
notebooklm source add "$EP/2_script/SCRIPT_DE.md" --json

# Wait for source to be ready
notebooklm source list --json   # Check "status": "ready"
```

### 4.3 Generate audio

```powershell
# Set German language
notebooklm language set de

# Get memory context and inject into prompt
$CTX = & $MEM context $EID

# Generate audio with full Nova/Max mega-prompt
notebooklm generate audio "KONTEXT: Deutsche Sci-Fi Podcast-Serie fuer Gen Z Science-Nerds. HOSTS: Zwei Freunde — einer erzhlt die Story, der andere reagiert mit 'Warte, WAS?!' und stellt Fragen. STIL: Locker, witzig, Gaming und Anime Analogien. STRUKTUR: Dramatischer Einstieg, ueberraschender Twist, nachdenkliches Ende mit Cliffhanger." `
  --format deep-dive --length long --language de --retry 3 --json
# → Save artifact_id

# Wait for generation (10-20 min)
notebooklm artifact wait <artifact_id> --timeout 1200

# Download
notebooklm download audio "$EP/3_audio/podcast.mp3"

& $MEM episode update $EID ep_path $EP
& $MEM log $EID audio "Podcast generated and downloaded"
```

---

## PHASE 5 — Transcribe Audio (Get Real Timestamps)

```powershell
$env:PYTHONIOENCODING="utf-8"

python .agent/skills/audio-listener/scripts/transcribe.py `
  "$EP/3_audio/podcast.mp3" `
  --model small --language de --format segments `
  --output "$EP/3_audio/transcript.txt"

# Update duration in memory
& $MEM episode update $EID audio_dur <seconds>
& $MEM log $EID transcribe "Audio transcribed with timestamps"
```

### 5.1 Map topic transitions

Read `transcript.txt` and create `$EP/5_deliverables/SLIDE_SOURCE.md`:

```markdown
| Slide | Start | End   | Section      | Visual Description                    |
|-------|-------|-------|--------------|---------------------------------------|
| 01    | 00:00 | 00:45 | Cold Open    | Dark scene, dramatic atmosphere        |
| 02    | 00:45 | 02:00 | Theme Intro  | Topic reveal, wide establishing shot  |
...
```

---

## PHASE 6 — Generate 16:9 Visuals

> 🎨 **IMAGE QUALITY RULE — MAXIMUM PRO:**  
> The `generate_image` tool selects quality based on prompt specificity.  
> **Ultra-detailed = Pro model. Vague = Fast model. Never be vague.**

For each row in `SLIDE_SOURCE.md`, generate a cinematic image.

**MAXIMUM QUALITY prompt template (mandatory for every single slide):**
```
Ultra-wide cinematic 16:9 aspect ratio. Hyper-realistic, 8K resolution, shot on 
RED MONSTRO cinema camera, 24mm anamorphic lens, f/1.8 bokeh. [Extremely specific scene: 
every element, every light source, color temperature, time of day, weather, distance, 
texture]. Masterful film-grade color grading — [specific color palette: e.g. 
deep teal shadows, warm orange highlights, desaturated midtones]. 
Volumetric atmospheric haze. Award-winning cinematography composition. 
No text, no watermarks, no logos, no UI, no watermarks. 
Negative: cartoon, anime, illustration, painting, sketch, blurry, noise, grain, 
flat colors, amateur, low quality.
```

**Always describe light specifically:**
- "Hard directional rim light from upper left, casting long shadows..."
- "Soft diffused natural window light, golden hour glow..."  
- "Practical light from glowing screens, cool blue-green tones..."
- "Drone-mounted LED array, clinical white, forensic clarity..."

**Check visual style from memory:**
```powershell
& $MEM style get <topic_type>
# e.g. military, space, biology, tech, paranormal
```

Save all images to `$EP/4_visuals/` as `slide01_<desc>.png`, `slide02_<desc>.png`, etc.

**MANDATORY STEP: Force 1920×1080 after every batch:**
```powershell
$env:PYTHONIOENCODING="utf-8"
python scripts/force_16x9.py "$EP/4_visuals/"
```
This ffmpeg scale+pad step is **non-negotiable**. Every image in the pipeline must be exactly 1920×1080 before CapCut.

```powershell
& $MEM log $EID visuals "N slides generated (PRO prompts) + force_16x9 → 1920x1080"
```



---

## PHASE 7 — Build Deliverables

### 7.1 Create CapCut walkthrough

Save to `$EP/5_deliverables/walkthrough.md`:

```markdown
# CapCut Walkthrough — [Episode Title]
Audio: 3_audio/podcast.mp3

| # | Image | Start | End | Happening |
|---|-------|-------|-----|-----------|
| 01 | slide01_xxx.png | 00:00 | 00:45 | [description] |
| 02 | slide02_xxx.png | 00:45 | 02:00 | [description] |
```

### 7.2 Register topic & quality in memory

```powershell
& $MEM topic add "<topic>" <category> <controversy 1-10> <appeal 1-10>
& $MEM quality add $EID overall "what worked well" "what to improve" "specific change" <rating>
& $MEM episode update $EID status complete
& $MEM log $EID package "Episode complete"
```

---

## FINAL OUTPUT STRUCTURE

```
episodes/S01/E02_Dark_Matter/
├── README.md
├── 1_research/sources/     ← YouTube SRT/TXT, Wikipedia exports
├── 2_script/
│   ├── SCRIPT_DE.md        ← German script (Nova + Max)
│   └── SCRIPT_EN.md        ← English translation for review
├── 3_audio/
│   ├── podcast.mp3         ← Generated German podcast
│   └── transcript.txt      ← Timestamped segments
├── 4_visuals/
│   ├── slide01_*.png       ← 16:9 cinematic images
│   └── ...
└── 5_deliverables/
    ├── SLIDE_SOURCE.md     ← Timestamp → visual mapping
    ├── walkthrough.md      ← CapCut timing guide for user
    └── cinematic.mp4       ← NotebookLM AI-generated cinematic video (English)
```

---

## ESTIMATED TIMELINE

| Phase | What | Time |
|-------|------|------|
| 1 | Setup folder + memory | 2 min |
| 2 | Research + sources | 5–10 min |
| 3 | Script writing | 10–15 min |
| 4 | NotebookLM audio gen | 15–20 min (wait) |
| 5 | Transcribe | 5–8 min |
| 6 | Generate visuals | 5–10 min |
| 7 | Walkthrough + memory | 2 min |
| 8 | Cinematic video (EN) | 15–45 min (background) |
| **Total** | | **~60–80 min** |

> **Tip:** Start Phase 8 (`--no-wait`) right after Phase 7 so the video generates in the background while you work on other things.

---

## CHARACTER BIBLE (Memory-Backed)

**Nova** (storyteller) — builds tension, drops facts, uses analogies ("Stellt euch mal vor...")  
**Max** (reactor) — says "Warte, WAS?!", challenges Nova, represents the listener

> NotebookLM generates its own two hosts — our mega-prompt guides their dynamic to match Nova/Max exactly.
