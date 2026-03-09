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

## 🔒 GLOBAL NOTEBOOK RULES (Apply to EVERY Episode, Forever)

> These rules are permanent and non-negotiable. They apply to every single episode produced by this pipeline — current and future.

### 🎙️ RULE 1: Audio Generation Notebook — SCRIPT ONLY

> **The audio notebook MUST contain ONLY the custom-written podcast script** (`SCRIPT_<LANG>.md`).
> - ❌ Do NOT add YouTube transcripts
> - ❌ Do NOT add Wikipedia URLs or articles
> - ❌ Do NOT add blog posts, research docs, or any other source
> - ✅ One source only: the target-language script file
>
> **Why:** The script has the exact tone, Gen Z voice, slang, and narrative structure already baked in.
> Adding extra sources dilutes audio quality and makes the output generic.

### 🎬 RULE 2: Cinematic Notebook — ALL English Research Sources

> **The cinematic notebook MUST add ALL English sources found during Phase 2 research** — no exceptions.
> - ✅ Every YouTube SRT/TXT file downloaded during research
> - ✅ Every Wikipedia URL referenced
> - ✅ Every blog article, official doc, or web source used
> - ✅ Multiple diverse sources = richer cinematic output
> - ❌ Do NOT add the podcast script (wrong language, wrong purpose)
>
> **Why:** Cinematic = factual English visual companion. More sources = richer, more accurate output.
> The notebook AI needs full context to generate a great English-language visual video.

---


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
> The target-language script is the **single source** for audio generation (Phase 4).

> 🚨 **GLOBAL RULE (permanent, applies to ALL episodes):**
> Phase 2 MUST find and add **MINIMUM 5 diverse sources** before proceeding to Phase 3.
> The pipeline is **BLOCKED** until the Source Count Gate (§2.5) passes.

---

### 2.1 — YouTube Videos (REQUIRED: 2–3 videos)

Find 2–3 relevant YouTube videos and download their English subtitles as transcripts.

```bash
# SEARCH — run 2-3 variations to get good candidates
yt-dlp --flat-playlist --print "%(id)s | %(title)s | %(view_count)s views | %(duration_string)s" \
  "ytsearch20:<topic> explained science"
yt-dlp --flat-playlist --print "%(id)s | %(title)s | %(view_count)s views | %(duration_string)s" \
  "ytsearch20:<topic> documentary podcast"

# For each chosen video — check available subtitles first
yt-dlp --list-subs "https://youtube.com/watch?v=VIDEO_ID"

# Download English subtitles (manual CC preferred, auto-subs fallback)
yt-dlp --write-subs --write-auto-subs --sub-lang en --sub-format srt --skip-download \
  -o "<ep_path>/1_research/sources/%(title)s.%(ext)s" \
  "https://youtube.com/watch?v=VIDEO_ID_1"

yt-dlp --write-subs --write-auto-subs --sub-lang en --sub-format srt --skip-download \
  -o "<ep_path>/1_research/sources/%(title)s.%(ext)s" \
  "https://youtube.com/watch?v=VIDEO_ID_2"

# Optional 3rd video
yt-dlp --write-subs --write-auto-subs --sub-lang en --sub-format srt --skip-download \
  -o "<ep_path>/1_research/sources/%(title)s.%(ext)s" \
  "https://youtube.com/watch?v=VIDEO_ID_3"

# Convert each SRT → clean plain text
python .agent/skills/youtube-podcast-researcher/scripts/srt_to_text.py \
  "<ep_path>/1_research/sources/<title1>.en.srt"
python .agent/skills/youtube-podcast-researcher/scripts/srt_to_text.py \
  "<ep_path>/1_research/sources/<title2>.en.srt"
```

> If a video has no subtitles at all, skip it and pick another — no subtitleless videos count toward the minimum.

```bash
# Log each YouTube source
python scripts/mem.py source add <episode_id> youtube "<video 1 title>" "https://youtube.com/watch?v=VIDEO_ID_1"
python scripts/mem.py source add <episode_id> youtube "<video 2 title>" "https://youtube.com/watch?v=VIDEO_ID_2"
# (add video 3 if used)
```

---

### 2.2 — Wikipedia / Official Documentation (REQUIRED: 1–2 pages)

Fetch at least 1 Wikipedia article and/or official documentation page on the topic.

```bash
# Use read_url_content to fetch full article text, then save it
# Example URLs:
#   https://en.wikipedia.org/wiki/<Topic>
#   https://en.wikipedia.org/wiki/<Related_Concept>
#   https://docs.python.org/... / official RFC / spec page

# Save the text content to:
#   <ep_path>/1_research/sources/wikipedia_<topic>.txt
#   <ep_path>/1_research/sources/official_docs_<topic>.txt
```

> Use `read_url_content` tool on the URL. Save the returned markdown/text to the sources folder.

```bash
# Log Wikipedia / official doc sources
python scripts/mem.py source add <episode_id> wikipedia "<article title>" "https://en.wikipedia.org/wiki/<Topic>"
# (add 2nd if applicable)
```

---

### 2.3 — Blogs / Community Discussions (REQUIRED: 1–2 pages)

Find at least 1 high-quality blog post, Reddit thread, or GitHub discussion related to the topic.

```bash
# Use search_web to find relevant community sources, e.g.:
#   "site:reddit.com <topic> discussion"
#   "site:github.com <topic> issue OR discussion"
#   "<topic> explained blog 2024 OR 2025"

# Once found, use read_url_content to fetch the page text
# Save to: <ep_path>/1_research/sources/community_<source_name>.txt
```

```bash
# Log community sources
python scripts/mem.py source add <episode_id> blog "<source title>" "<url>"
# (add 2nd if applicable)
```

---

### 2.4 — Official Release Notes / Announcements (ADD IF APPLICABLE)

If the topic has an official release, announcement page, or academic paper — add it.

```bash
# Examples:
#   https://arxiv.org/abs/<paper-id>          ← Academic papers
#   https://blog.google/...                   ← Google/company announcements
#   https://github.com/<org>/<repo>/releases  ← Software release notes

# Save to: <ep_path>/1_research/sources/official_<name>.txt

python scripts/mem.py source add <episode_id> official "<announcement title>" "<url>"
```

---

### 2.5 — ✅ SOURCE COUNT GATE (BLOCKING — must pass before Phase 3)

> 🛑 **DO NOT START PHASE 3 UNTIL THIS GATE PASSES.**

Before proceeding, verify the following checklist. Every line must be ✅:

```
SOURCE COUNT GATE — Episode: <episode_id>
──────────────────────────────────────────────────────
[ ] YouTube sources:    ___ / 2 minimum  (SRT transcript saved as .txt)
[ ] Wikipedia/Docs:     ___ / 1 minimum  (page text saved as .txt)
[ ] Blog/Community:     ___ / 1 minimum  (page text saved as .txt)
[ ] TOTAL sources:      ___ / 5 minimum
──────────────────────────────────────────────────────
[ ] All source .txt files saved in <ep_path>/1_research/sources/
[ ] All sources logged to memory (mem.py source add)
──────────────────────────────────────────────────────
GATE STATUS: [ ] PASS  /  [ ] FAIL — add more sources if FAIL
```

To check the current count in memory:

```bash
python scripts/mem.py source list <episode_id>
# Count the rows — must be 5+ with at least 1 youtube row
```

> If the gate fails (< 5 sources or missing a YouTube transcript), **go back and add more sources** before continuing. Do not skip this check.

---

### 2.6 — Log & Complete Phase

```bash
python scripts/mem.py log <episode_id> research "Research complete: <N> sources collected (YouTube: X, Wikipedia: Y, Blog: Z)"

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

> 🔒 **GLOBAL RULE #1 — SCRIPT ONLY. NO EXCEPTIONS. EVER.**
> The audio notebook must contain **one and only one source**: the target-language podcast script.
> No YouTube transcripts. No Wikipedia. No research docs. Script only.
> The script already has perfect tone + Gen Z voice baked in — extra sources dilute audio quality.

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
# ✅ ONLY THIS ONE FILE — nothing else
# File is SCRIPT_<LANG>.md where LANG = episode output language code (DE, EN, ES, etc.)
notebooklm source add "<ep_path>/2_script/SCRIPT_<LANG>.md" --json

# Verify: source list must show EXACTLY 1 source before proceeding
notebooklm source list --json   # Must show only the script, status: "ready"

# ⛔ STOP AND FIX if more than 1 source is listed — remove any extra sources before generating audio
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

## PHASE 4.5 — YouTube Metadata Pack (Run IN PARALLEL During Audio Gen Wait)

> ⏱️ **Fire this while `notebooklm artifact wait` is running in Phase 4.**
> Audio gen takes 15–20 min. Use that time — zero extra cost to total runtime.

### 4.5.1 Generate metadata (titles + description + thumbnail prompt)

```bash
# POST to the API — it generates 5 viral titles, a full description, and a thumbnail prompt
# SSE streams progress to the browser terminal live
curl -s -X POST http://localhost:5000/api/episodes/<eid>/generate-youtube-meta > /dev/null
python scripts/log_phase.py <eid> "📋 YouTube Pack: titles + description generated" success
```

→ Auto-saves to `<ep_path>/5_deliverables/youtube_meta.json`
→ Auto-saves to `<ep_path>/5_deliverables/thumbnail_prompt.txt`

### 4.5.2 Generate the thumbnail image

```bash
# Read the research-aware thumbnail prompt
cat "<ep_path>/5_deliverables/thumbnail_prompt.txt"
```

Then call `generate_image` with that exact prompt text and save the PNG:

```python
# Save result to: <ep_path>/5_deliverables/thumbnail.png
# The prompt is already optimised: 16:9, hyper-realistic, no text
```

Finally register the path so the UI can show the thumbnail preview:

```bash
# Update path in metadata so the UI preview works
curl -s -X POST http://localhost:5000/api/episodes/<eid>/youtube-meta \
  -H "Content-Type: application/json" \
  -d '{"thumbnail_path": "<ep_path>/5_deliverables/thumbnail.png"}'

python scripts/log_phase.py <eid> "🖼️ Thumbnail generated → 5_deliverables/thumbnail.png" success

# ✅ Update UI dashboard after phase complete
python scripts/update_phase.py <eid> youtube_meta done
```

---

## 🎯 VISUAL BUDGET — Calculate BEFORE Generating Any Visuals

> ⚠️ **GLOBAL RULE — applies to every episode permanently.**
> Calculate the visual budget ONCE here in Phase 4.5, then enforce it for ALL visual generation.

### Audience Attention Span Reference

| Audience Type | Avg Attention per Image |
|---|---|
| Gen Alpha (< 13) | 3–5 sec |
| Gen Z (13–28) | 5–8 sec |
| Millennials (29–44) | 10–15 sec |
| Gen X (45–60) | 15–20 sec |
| Boomers (60+) | 20–30 sec |
| Tech Enthusiasts | 8–12 sec |
| Academic / Research | 15–25 sec |

### Formula

```
total_visual_limit = podcast_duration_seconds ÷ audience_attention_span_seconds

Example:
  37-min podcast = 2220 sec
  Gen Z audience = ~6 sec/image (midpoint of 5–8)
  → 2220 ÷ 6 = 370 visuals MAX

  37-min podcast + Millennials = 2220 ÷ 12 = 185 visuals MAX
```

> **Note:** Use the **midpoint** of the attention span range (e.g., Gen Z 5–8 → use 6).
> Podcast duration comes from memory: `python scripts/mem.py episode get <episode_id>` (field: `audio_dur`).
> If audio isn't transcribed yet, estimate from script (~150 words/min) or use Phase 5 result.

### Slot Priority

```
1. TIER 1 — Key Visuals (mandatory):   fill slots first
2. TIER 2 — Supporting Visuals:        fill remaining slots only up to the limit
3. NEVER generate beyond the limit
```

```bash
# Store the calculated limit in memory for use across phases
python scripts/mem.py episode update <episode_id> visual_limit <N>
```

---

## PHASE 4.6 — Supporting Visuals (Tier 2 — Idle-Time Generation)

> 🔄 **GLOBAL RULE — applies to every episode permanently.**
> This phase runs ONLY during idle wait time. It NEVER blocks the pipeline.
> Supporting visuals are topic/research-based — NOT transcript-based (transcript doesn't exist yet).

### When to Run

Start this loop as soon as Phase 4.5 (YouTube Metadata) is done. Run it during:
- **Wait 1:** While `notebooklm artifact wait <artifact_id>` is processing (audio gen, 15–20 min)
- **Wait 2:** While `transcribe.py` is processing in Phase 5 (5–8 min)

### STOP LOOP Triggers — Stop immediately when EITHER:
- `podcast.mp3` download completes (end of Phase 4 wait)
- `transcript.txt` finishes writing (end of Phase 5 transcription)

### What to Generate

Use the episode topic + Phase 2 research sources as inspiration. Generate visuals such as:
- **Infographics** — key facts, stats, timelines about the topic
- **Concept explainers** — visual analogies for complex ideas in the episode
- **Charts / diagrams** — data or comparisons mentioned in the research
- **Atmosphere shots** — thematic imagery establishing the topic's world

Use the **same ultra-detailed prompt template** as Phase 6 (16:9 cinematic, no text, etc.).

### Visual Budget Check (Per Iteration)

```bash
# Before generating each supporting visual, check remaining budget:
# remaining_budget = visual_limit - key_visual_count - supporting_visual_count_so_far
# If remaining_budget <= 0: STOP LOOP immediately
```

### Save & Name Supporting Visuals

Save to `<ep_path>/4_visuals/` with `support_` prefix:
```
support_01_<desc>.png
support_02_<desc>.png
...
```

Keep a running log of what each supporting visual depicts — you'll need this for the walkthrough estimated timecodes.

```bash
python scripts/mem.py log <episode_id> visuals "Tier 2: <N> supporting visuals generated during idle wait"
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

## PHASE 6 — Generate Key Visuals (Tier 1 — Transcript-Locked, Parallel Batches)

> 🚫 **BUG #5 HARD BLOCK — GLOBAL RULE:**
> **NEVER start Phase 6 until `<ep_path>/3_audio/transcript.txt` exists and is fully written.**
> Check before doing anything:
> ```bash
> # Abort if transcript is missing
> if not os.path.exists("<ep_path>/3_audio/transcript.txt"):
>     raise RuntimeError("STOP: transcript.txt does not exist. Run Phase 5 first.")
> ```
> Required order: **audio done → transcribe → read transcript → SLIDE_SOURCE.md → THEN key visuals**
> There are NO exceptions. No skipping. No pre-generating.

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

### 7.1 Create CapCut walkthrough (Both Tiers)

Save to `<ep_path>/5_deliverables/walkthrough.md`. The walkthrough **must include both visual tiers**:

- **Tier 1 (Key Visuals):** use real timestamps from `SLIDE_SOURCE.md`
- **Tier 2 (Supporting Visuals):** use estimated timecodes — place them in gaps between key visuals or as B-roll where the content matches

```markdown
# CapCut Walkthrough — [Episode Title]
Audio: 3_audio/podcast.mp3
Visual Budget: <N> total slots (<key_count> key + <support_count> supporting)

## Tier 1 — Key Visuals (Transcript-Locked)
| # | Image | Start | End | Happening |
|---|-------|-------|-----|-----------|
| 01 | slide01_xxx.png | 00:00 | 00:45 | [description from SLIDE_SOURCE.md] |
| 02 | slide02_xxx.png | 00:45 | 02:00 | [description from SLIDE_SOURCE.md] |

## Tier 2 — Supporting Visuals (Estimated Timecodes)
| # | Image | Est. Start | Est. End | Content Match |
|---|-------|-----------|----------|---------------|
| S01 | support_01_xxx.png | 01:00 | 01:30 | [why this fits here — topic/concept shown] |
| S02 | support_02_xxx.png | 03:15 | 03:45 | [why this fits here — topic/concept shown] |
```

> Supporting visual timecodes are **estimates** — place them where the topic context matches the visual content.

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

> 🔒 **GLOBAL RULE #2 — ALL ENGLISH RESEARCH SOURCES. NO EXCEPTIONS. EVER.**
> The cinematic notebook must contain **every English source** found during Phase 2 research.
> YouTube SRTs, Wikipedia URLs, blog articles, official docs — all of them. The more, the better.
> Do NOT add the podcast script here. Do NOT skip sources. Add everything from 1_research/sources/.

> 🎬 This uses a SEPARATE notebook from the audio notebook. It is an English-language visual companion.
> Start this right after Phase 7 so it generates in the background.

### 8.1 Create cinematic notebook

```bash
# Create a SEPARATE notebook — English sources ONLY
notebooklm create "Cinematic - <topic>" --json
# → Save notebook ID as CIN_NB
notebooklm use <cin_notebook_id>
```

### 8.2 Add ALL English research sources (every single one)

```bash
# ✅ STEP 1: List all files collected in Phase 2
ls "<ep_path>/1_research/sources/"   # Find every .txt and .srt file

# ✅ STEP 2: Add every .txt transcript file (YouTube SRTs converted to text)
notebooklm source add "<ep_path>/1_research/sources/<video1_transcript>.txt" --json
notebooklm source add "<ep_path>/1_research/sources/<video2_transcript>.txt" --json
# ... repeat for every .txt file in sources/

# ✅ STEP 3: Add every Wikipedia URL used during research (check mem.py source list)
python scripts/mem.py source list <episode_id>  # Get all logged URLs
notebooklm source add "https://en.wikipedia.org/wiki/<topic>" --json
# ... repeat for every Wikipedia/blog/doc URL from the research phase

# ✅ STEP 4: Add any additional English URLs from research notes
# Include: blog articles, official documentation, news articles, academic sources
notebooklm source add "<any_other_english_url>" --json

# ✅ STEP 5: Verify all sources loaded
notebooklm source list --json   # All must show status: "ready" before generating video

# ⛔ MINIMUM: At least 3 sources required before generating cinematic video.
# More sources = richer, more factually accurate cinematic output.
```

> ⚠️ Do NOT add the podcast script (wrong language + purpose).
> ⚠️ Do NOT skip any English source from Phase 2 — completeness is the goal here.

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
│   └── transcript.txt      ← Timestamped segments ← REQUIRED before key visuals
├── 4_visuals/
│   ├── slide01_*.png       ← Tier 1: Key visuals (transcript-locked, real timestamps)
│   ├── slide02_*.png
│   ├── support_01_*.png    ← Tier 2: Supporting visuals (idle-time, estimated timecodes)
│   ├── support_02_*.png
│   └── ...
└── 5_deliverables/
    ├── SLIDE_SOURCE.md     ← Timestamp → visual mapping (Tier 1 only)
    ├── walkthrough.md      ← CapCut guide with BOTH tiers + visual budget summary
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
| 4.5 | YouTube metadata + visual budget calc | parallel during Phase 4 wait |
| 4.6 | **Tier 2: Supporting visuals (idle-time)** | **0 min extra** (runs during wait) |
| 5 | Transcribe | 5–8 min |
| 6 | **Tier 1: Key visuals** (transcript-locked) | 5–10 min |
| 7 | Walkthrough (both tiers) + memory | 2 min |
| 8 | Cinematic video (EN) | 15–45 min (background) |
| **Total** | | **~60–80 min** |

> **Tip:** Phase 4.6 (supporting visuals) costs zero extra time — it runs during the wait for audio generation and transcription. Start Phase 8 right after Phase 7 for background cinematic video generation.

---

## CHARACTER BIBLE (Memory-Backed)

**Nova** (storyteller) — builds tension, drops facts, uses analogies ("Stellt euch mal vor...")  
**Max** (reactor) — says "Warte, WAS?!", challenges Nova, represents the listener

> NotebookLM generates its own two hosts — our mega-prompt guides their dynamic to match Nova/Max exactly.

---

## PHASE 1 — Seed Characters & Visual Style (MANDATORY — run at start of every episode)

> 🔒 **GLOBAL RULE — applies to every episode permanently.**
> These must run BEFORE research. They populate the Memory page and guide the entire visual aesthetic.

### 1.1 — Seed host characters into memory

```bash
# Seed the two permanent podcast hosts — do this ONCE per pipeline run
python scripts/mem.py char set "NOVA" "storyteller" "Builds tension, drops shocking facts, uses vivid analogies. Opens with hook. Drives the narrative forward. Energy: excited, passionate, slightly dramatic."
python scripts/mem.py char set "MAX" "reactor" "Represents the listener. Says 'Wait, WHAT?!', challenges NOVA's claims, asks clarifying questions. Grounds the conversation. Energy: skeptical, curious, relatable."
```

### 1.2 — Set visual style for this episode's topic type

> Pick the closest topic_type from the list below. If unsure, use "tech" as default.

```bash
# Topic type → visual_style mapping (pick ONE that matches the episode)
# tech       → dark digital workspace, glowing data streams, neon blue/teal
# space      → cosmic deep space, nebula, planetary surfaces, violet/star white
# health     → medical lab, DNA strands, cellular close-ups, clinical white/green
# finance    → Wall Street, gold tones, stock charts, Bloomberg aesthetic
# military   → dark ops, dramatic shadows, tactical green
# paranormal → mysterious fog, low-key lighting, deep shadows

python scripts/mem.py style set "<topic_type>" "<description>" "<palette>" "<mood>"

# Example for a tech episode:
python scripts/mem.py style set "tech" "Futuristic dark digital workspace, glowing neural networks, holographic UI panels, neon data streams" "deep black, electric teal, neon blue, amber accent" "high-tech, cinematic, mysterious"
```

```bash
# Verify both are saved before continuing
python scripts/mem.py char list
python scripts/mem.py style get <topic_type>
```
