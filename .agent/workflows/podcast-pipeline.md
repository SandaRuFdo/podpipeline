---
description: End-to-end multi-language, multi-audience podcast production — from topic to YouTube-ready deliverables
---
// turbo-all

# 🎬 Podcast Production Pipeline

> **ARCHITECTURE (never forget this):**  
> The UI/dashboard is **INPUT ONLY** — it collects the topic, language, audience, and shows progress.  
> **Antigravity is the brain and executor.** After input is received, I run all phases autonomously.  
> No other AI, no automation bot. Just me, the tools, and the output folders.

**Input:** Topic, output language, and target audience from user via UI  
**Output:** MP3 in the selected language + 16:9 visuals + CapCut walkthrough — all in the episode folder

> **Windows note:** Always ensure `PYTHONIOENCODING=utf-8` is set. All scripts do this automatically.


---

## BEFORE STARTING — Check Memory

```bash
# Check if topic was already covered
python scripts/mem.py topic check "<topic>"

# Load character bible for script consistency
python scripts/mem.py context
```

---

## PHASE 1 — Create Episode Folder

```bash
# One command does everything: folder + memory + README
python core/new_episode.py \
  --season 1 --episode 2 \
  --slug "Dark_Matter" \
  --title-de "Dunkle Materie" \
  --title-en "Dark Matter" \
  --topic "dark matter physics mystery"

# → Script prints the episode Memory ID — note it as EID
# → Folder created: episodes/S01/E02_Dark_Matter/
```

```python
# Set these vars for the rest of the pipeline
EP  = "episodes/S01/E02_Dark_Matter"
EID = 2   # from new_episode.py output
```

---

## PHASE 2 — Research (English Sources for Understanding Only)

> ⚠️ English sources are **research fuel only** — they do NOT go into the audio notebook.
> The German script is the **single source** for audio generation (Phase 4).

### 2.1 Find viral English content on the topic

```bash
# Search YouTube for relevant podcasts/documentaries
yt-dlp --flat-playlist --print "%(id)s | %(title)s | %(view_count)s views | %(duration_string)s" \
  "ytsearch20:<topic> documentary science"

# Pick the best video, check subtitles
yt-dlp --list-subs "https://youtube.com/watch?v=VIDEO_ID"

# Download subtitles only (no video)
yt-dlp --write-subs --write-auto-subs --sub-lang en --sub-format srt --skip-download \
  -o "<ep_path>/1_research/sources/%(title)s.%(ext)s" \
  "https://youtube.com/watch?v=VIDEO_ID"

# Convert SRT to clean text
python .agent/skills/youtube-podcast-researcher/scripts/srt_to_text.py \
  "<ep_path>/1_research/sources/<title>.en.srt"
```

### 2.2 Log sources in memory

```bash
python scripts/mem.py source add <episode_id> youtube "<video title>" "https://youtube.com/..."
python scripts/mem.py source add <episode_id> wikipedia "<article title>" "https://en.wikipedia.org/..."
python scripts/mem.py log <episode_id> research "English sources downloaded for script writing"

# ✅ Update UI dashboard after phase complete
python scripts/update_phase.py <episode_id> research done
```

---

## PHASE 3 — Script Writing (Profile-Driven)

> Read the English sources from `<ep_path>/1_research/sources/` to deeply understand the topic.
> Then write a script guided by the matching **skill profile** for this episode's language + audience.

### 3.1 Load writing profile + memory context

```bash
# Load the tailored writing profile for this episode's language × audience
# This outputs tone, slang, vocab, cultural refs, hooks, and avoid-list
python scripts/mem.py profile context <lang_code> <audience_key>
# Example: python scripts/mem.py profile context de gen_z

# Load episode memory for character consistency
python scripts/mem.py context <episode_id>
```

> **The profile context IS the writing directive.** It tells you exactly:
> - **How to sound** (tone & voice)
> - **What slang to use** (expressions the audience recognizes)
> - **What terms to use** (vocab adapted to audience knowledge level)
> - **What to reference** (shows, creators, memes the audience knows)
> - **How to hook them** (attention strategies for that audience)
> - **What kills it** (things that lose engagement for this specific audience)

### 3.2 Write the script

Use **German SciFi Podcast Director** skill + the loaded profile. Save to `<ep_path>/2_script/SCRIPT_<LANG>.md`:

- **Structure:** Cold Open → Theme Intro → Act 1 → Act 2 (Twist) → Act 3 → Outro
- **Tone:** As defined in the skill profile (NOT hardcoded)
- **Length:** 15–25 minutes of dialogue
- **Start mid-action** — no generic intros
- **Use English sources as reference** — adapt, don't translate
- **Weave in** the profile's slang, cultural refs, and hook patterns naturally

### 3.3 Write English translation

Save to `<ep_path>/2_script/SCRIPT_EN.md` — section-by-section for user review.

```bash
python scripts/mem.py log <episode_id> script "Script written with profile: <lang> × <audience>"

# ✅ Update UI dashboard after phase complete
python scripts/update_phase.py <episode_id> script done
```

---

## PHASE 4 — Generate Podcast (Script-Only Notebook)

> 🎯 **KEY RULE:** The script is the ONLY source for audio generation.
> Do NOT add English research sources to this notebook.

### 4.1 Create a fresh notebook for audio generation

```bash
notebooklm create "S<SEASON>E<EP> - <Topic Title>" --json
# → Save notebook ID
notebooklm use <notebook_id>

# Update memory with notebook ID
python scripts/mem.py episode update <episode_id> notebook_id <notebook_id>
```

### 4.2 Add ONLY the target-language script as source

```bash
# This is the ONLY source — no English transcripts, no Wikipedia
# File is SCRIPT_<LANG>.md where LANG = episode output language code (DE, EN, ES, etc.)
notebooklm source add "<ep_path>/2_script/SCRIPT_<LANG>.md" --json

# Wait for source to be ready
notebooklm source list --json   # Check "status": "ready"
```

### 4.3 Generate audio

> ⚠️ **NEVER run `notebooklm language set <lang>`** — that is a GLOBAL setting that
> changes the language for ALL notebooks in the account. It will corrupt other episodes
> running in different languages.
>
> ✅ **ALWAYS use `--language <code>` on the `generate audio` command** — this is scoped
> to that single generation call only and does not affect any other notebook.

```bash
# Get memory context and inject into prompt
python scripts/mem.py context <episode_id>

# Load the writing profile for this language + audience
python scripts/mem.py profile context <LANG> <AUDIENCE>

# LANG = episode output language code (de / en / es / fr / pt_BR etc.)
# AUDIENCE = target audience slug (gen_z / millennials / tech_enthusiasts etc.)
# Use the values stored in memory from Phase 1 — never hardcode.

# Generate audio — language scoped to THIS notebook only via --language flag
notebooklm generate audio \
  "<Inject writing profile tone + style from memory here. Describe hosts, format, \
   structure, and energy in the TARGET LANGUAGE. Pull exact tone descriptors from \
   the skill profile loaded above. Tailor slang, references, and humor for AUDIENCE.>" \
  --language <LANG> \
  --format deep-dive --length long \
  --retry 3 --json
# → Save artifact_id

# Wait for generation (10-20 min)
notebooklm artifact wait <artifact_id> -n <notebook_id> --timeout 1200

# Download
notebooklm download audio "<ep_path>/3_audio/podcast.mp3" -a <artifact_id> -n <notebook_id>

python scripts/mem.py episode update <episode_id> ep_path "<ep_path>"
python scripts/mem.py log <episode_id> audio "Podcast generated in <LANG> for <AUDIENCE>"

# ✅ Update UI dashboard after phase complete
python scripts/update_phase.py <episode_id> audio done
```

---

## PHASE 5 — Transcribe Audio (Get Real Timestamps)

```bash
# Use <LANG> from episode memory — matches whatever language was used in Phase 4
python .agent/skills/audio-listener/scripts/transcribe.py \
  "<ep_path>/3_audio/podcast.mp3" \
  --language <LANG> --format segments \
  --output "<ep_path>/3_audio/transcript.txt"
# --model is auto-loaded from .agent/whisper_model.txt (set during start.py setup)
# --device is auto-loaded from .agent/device_config.json (GPU or CPU)

# Update duration in memory
python scripts/mem.py episode update <episode_id> audio_dur <seconds>
python scripts/mem.py log <episode_id> transcribe "Audio transcribed (<LANG>)"

# ✅ Update UI dashboard after phase complete
python scripts/update_phase.py <episode_id> transcribe done
```

### 5.1 Map topic transitions

Read `transcript.txt` and create `<ep_path>/5_deliverables/SLIDE_SOURCE.md`:

```markdown
| Slide | Start | End   | Section      | Visual Description                    |
|-------|-------|-------|--------------|---------------------------------------|
| 01    | 00:00 | 00:45 | Cold Open    | Dark scene, dramatic atmosphere        |
| 02    | 00:45 | 02:00 | Theme Intro  | Topic reveal, wide establishing shot  |
...
```

---

## PHASE 6 — Generate 16:9 Visuals (Parallel Batches)

> 🎨 **IMAGE QUALITY RULE — MAXIMUM PRO:**
> The `generate_image` tool selects quality based on prompt specificity.
> **Ultra-detailed = Pro model. Vague = Fast model. Never be vague.**

> ⚡ **SPEED RULE — PARALLEL BATCHES:**
> Fire **3–4 `generate_image` calls simultaneously** per batch, not one at a time.
> Wait for each batch to finish, then fire the next batch.
> This is 3–4× faster than sequential generation.

### 6.1 Read the slide source and prepare all prompts

Read `<ep_path>/5_deliverables/SLIDE_SOURCE.md`. Write ALL prompts upfront before generating anything.

**MAXIMUM QUALITY prompt template (mandatory for every single slide):**
```
CRITICAL COMPOSITION RULE: This image MUST be composed as a wide horizontal 16:9 cinematic
frame. Place ALL key subjects, faces, and focal points in the CENTER HORIZONTAL THIRD of the
frame — never at the extreme left or right edges. The left and right 20% of the frame should
contain only background/atmosphere (sky, fog, space, terrain). This ensures a perfect
center-crop to 1920×1080 with zero detail loss.

Ultra-wide cinematic 16:9 aspect ratio. Hyper-realistic, 8K resolution, shot on
RED MONSTRO cinema camera, 24mm anamorphic lens, f/1.8 bokeh. [Extremely specific scene:
every element, every light source, color temperature, time of day, weather, distance,
texture]. Masterful film-grade color grading — [specific color palette].
Volumetric atmospheric haze. Award-winning cinematography composition.
No text, no watermarks, no logos, no UI.
Negative: cartoon, anime, illustration, painting, sketch, blurry, noise, grain,
flat colors, amateur, low quality, portrait orientation, square crop, vertical frame.
```

> **Why this matters:** `force_16x9.py` uses **crop-to-fill** (not pad). It scales the
> image up to cover 1920×1080 then center-crops. If subjects are at the edges they get cut.
> Always keep key content in the center horizontal band.

**Always describe light specifically:**
- "Hard directional rim light from upper left, casting long shadows..."
- "Soft diffused natural window light, golden hour glow..."
- "Practical light from glowing screens, cool blue-green tones..."

**Check visual style from memory:**
```bash
python scripts/mem.py style get <topic_type>
# e.g. military, space, biology, tech, paranormal
```

### 6.2 Generate in parallel batches of 3–4

```
BATCH 1 (fire all at once, wait for all to finish):
  → generate_image(slide01 prompt) ┐
  → generate_image(slide02 prompt) ├── ALL FIRED SIMULTANEOUSLY
  → generate_image(slide03 prompt) ┘

BATCH 2 (fire all at once):
  → generate_image(slide04 prompt) ┐
  → generate_image(slide05 prompt) ├── ALL FIRED SIMULTANEOUSLY
  → generate_image(slide06 prompt) ┘

... continue until all slides done
```

Save all images to `<ep_path>/4_visuals/` as `slide01_<desc>.png`, `slide02_<desc>.png`, etc.

### 6.3 Force 1920×1080 (ONE batch run at the end)

```bash
python scripts/force_16x9.py "<ep_path>/4_visuals/"
```

> Run this **ONCE after all slides are generated** — not after every image.
> This uses **crop-to-fill**: scale up to cover 1920×1080, then center-crop. No black bars.

```bash
python scripts/mem.py log <episode_id> visuals "N slides generated in parallel batches + force_16x9 → 1920x1080"

# ✅ Update UI dashboard after phase complete
python scripts/update_phase.py <episode_id> visuals done
```



---

## PHASE 7 — Build Deliverables

### 7.1 Create CapCut walkthrough

Save to `<ep_path>/5_deliverables/walkthrough.md`:

```markdown
# CapCut Walkthrough — [Episode Title]
Audio: 3_audio/podcast.mp3

| # | Image | Start | End | Happening |
|---|-------|-------|-----|-----------|
| 01 | slide01_xxx.png | 00:00 | 00:45 | [description] |
| 02 | slide02_xxx.png | 00:45 | 02:00 | [description] |
```

### 7.2 Register topic & quality in memory

```bash
python scripts/mem.py topic add "<topic>" <category> <controversy 1-10> <appeal 1-10>
python scripts/mem.py quality add <episode_id> overall "what worked well" "what to improve" "specific change" <rating>
python scripts/mem.py episode update <episode_id> status complete
python scripts/mem.py log <episode_id> package "Episode complete"

# ✅ Update UI dashboard after phase complete
python scripts/update_phase.py <episode_id> deliverables done
```

---

## PHASE 8 — Cinematic Video (English, Background)

> 🎬 **This uses a SEPARATE notebook** with English sources ONLY.
> The cinematic video is an English-language visual companion — NOT the podcast itself.
> Start this right after Phase 7 so it generates in the background.

### 8.1 Create cinematic notebook

```bash
# Create a SEPARATE notebook — English sources only
notebooklm create "Cinematic - <topic>" --json
# → Save notebook ID as CIN_NB
notebooklm use <cin_notebook_id>
```

### 8.2 Add ONLY English sources

```bash
# Add the English research sources from Phase 2
# These are the YouTube transcripts, Wikipedia articles, etc.
notebooklm source add "<ep_path>/1_research/sources/<english_transcript>.txt" --json
notebooklm source add "https://en.wikipedia.org/wiki/<topic>" --json
# Add any other English URLs used during research
notebooklm source add "<english_source_url>" --json

# Wait for sources to be ready
notebooklm source list --json   # Check all "status": "ready"
```

> ⚠️ Do NOT add the German script here. This notebook is English-only for cinematic generation.

```bash
python scripts/mem.py log <episode_id> cinematic "Cinematic notebook created with English sources"

# ✅ Update UI dashboard
python scripts/update_phase.py <episode_id> cinematic done
```

---

## FINAL OUTPUT STRUCTURE

```
episodes/S<SEASON>/E<EP>_<SLUG>/
├── README.md
├── 1_research/sources/     ← YouTube SRT/TXT, Wikipedia exports
├── 2_script/
│   ├── SCRIPT_<LANG>.md    ← Script in target language (e.g. SCRIPT_DE.md, SCRIPT_EN.md)
│   └── SCRIPT_EN.md        ← English translation for review (always present)
├── 3_audio/
│   ├── podcast.mp3         ← Generated podcast in <LANG>
│   └── transcript.txt      ← Timestamped segments
├── 4_visuals/
│   ├── slide01_*.png       ← 16:9 cinematic images (1920×1080, crop-to-fill)
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
