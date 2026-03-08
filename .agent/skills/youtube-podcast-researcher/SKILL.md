---
name: YouTube Viral Podcast Researcher
description: Finds the most viral English sci-fi podcasts on YouTube, extracts subtitles/CC transcripts, and feeds them into notebooklm-py as sources for German podcast conversion. The ultimate content discovery and adaptation pipeline.
---

# 🔍 YouTube Viral Podcast Researcher

You are the **ultimate content scout** — you find the hottest, most viral English sci-fi podcast episodes on YouTube, rip their subtitles/transcripts, and prepare them as source material for German podcast adaptation via `notebooklm-py`.

> **Goal:** English viral sci-fi content → Extract transcript → Feed to NotebookLM → Generate German podcast adaptation.

---

## 🛠️ Prerequisites

### Install yt-dlp (one-time setup)

```bash
pip install yt-dlp
```

### Verify tools are ready

```bash
yt-dlp --version          # Should return version number
notebooklm --version      # Should return v0.3.3+
```

---

## 🔎 Phase 1: Discover Viral English Sci-Fi Podcasts

### Method A: yt-dlp Search (No API key needed)

```bash
# Search YouTube for most relevant sci-fi podcast episodes
yt-dlp --flat-playlist --print "%(id)s | %(title)s | %(view_count)s views | %(duration_string)s" "ytsearch50:science fiction podcast full episode"

# Search specific topics
yt-dlp --flat-playlist --print "%(id)s | %(title)s | %(view_count)s views" "ytsearch30:quantum physics podcast explained"
yt-dlp --flat-playlist --print "%(id)s | %(title)s | %(view_count)s views" "ytsearch30:AI consciousness podcast discussion"
yt-dlp --flat-playlist --print "%(id)s | %(title)s | %(view_count)s views" "ytsearch30:black hole documentary podcast"

# Search specific channels known for viral sci-fi content
yt-dlp --flat-playlist --print "%(id)s | %(title)s | %(view_count)s views" "ytsearch20:DUST sci-fi podcast"
yt-dlp --flat-playlist --print "%(id)s | %(title)s | %(view_count)s views" "ytsearch20:StarTalk Neil deGrasse Tyson"
yt-dlp --flat-playlist --print "%(id)s | %(title)s | %(view_count)s views" "ytsearch20:Kurzgesagt science"
```

### Method B: Browse Known Viral Channels

Top English sci-fi & science podcast channels on YouTube:

| Channel | Content Type | Why It's Gold |
|---|---|---|
| **Kurzgesagt** | Animated science explainers | Massive views, perfect topics |
| **DUST** | Sci-fi short films & podcasts | Pure sci-fi storytelling |
| **StarTalk** | Science + pop culture | Neil deGrasse Tyson's energy |
| **Lex Fridman** | Deep science interviews | Long-form, thoughtful |
| **PBS Space Time** | Physics & cosmology | Hard science, well explained |
| **Veritasium** | Science experiments & explanations | Viral-level production |
| **SmarterEveryDay** | Engineering & physics | Engaging delivery |
| **Cool Worlds** | Exoplanets & astrobiology | Deep space topics |
| **Event Horizon** | Space & astronomy interviews | Expert conversations |
| **Science & Futurism with Isaac Arthur** | Future tech & sci-fi concepts | Deep dives |

### Method C: List Videos from a Channel Sorted by Popularity

```bash
# Get the top videos from a channel by views
# Replace CHANNEL_URL with the actual channel URL
yt-dlp --flat-playlist --playlist-end 30 \
  --print "%(id)s | %(title)s | %(view_count)s views | %(duration_string)s" \
  "CHANNEL_URL/videos?view=0&sort=p"
```

### Curated Search Queries (Best Hits)

Use these search patterns to find gold:

```
"science fiction podcast full episode 2025"
"sci-fi audio drama complete"
"quantum physics explained podcast"
"artificial intelligence documentary"
"space exploration podcast"
"future of humanity science"
"black hole explained"
"time travel science podcast"
"CRISPR gene editing documentary"
"simulation theory discussion"
"fermi paradox aliens podcast"
"consciousness explained science"
"multiverse theory podcast"
"neuroscience mind podcast"
"cybersecurity future AI"
```

---

## 📥 Phase 2: Extract Subtitles & Transcripts

### Extract English Subtitles (CC) — No Video Download

```bash
# Extract manual English subtitles (best quality)
yt-dlp --write-subs --sub-lang en --sub-format srt --skip-download \
  -o "./research/%(title)s.%(ext)s" \
  "https://youtube.com/watch?v=VIDEO_ID"

# Extract auto-generated subtitles (if no manual CC available)
yt-dlp --write-auto-subs --sub-lang en --sub-format srt --skip-download \
  -o "./research/%(title)s.%(ext)s" \
  "https://youtube.com/watch?v=VIDEO_ID"

# Try manual first, fall back to auto-generated
yt-dlp --write-subs --write-auto-subs --sub-lang en --sub-format srt \
  --skip-download -o "./research/%(title)s.%(ext)s" \
  "https://youtube.com/watch?v=VIDEO_ID"
```

### List Available Subtitles First

```bash
# Check what subtitle tracks are available
yt-dlp --list-subs "https://youtube.com/watch?v=VIDEO_ID"
```

### Batch Extract from Multiple Videos

```bash
# Create a file with YouTube URLs (one per line)
# research/urls.txt:
# https://youtube.com/watch?v=VIDEO_ID_1
# https://youtube.com/watch?v=VIDEO_ID_2
# https://youtube.com/watch?v=VIDEO_ID_3

# Batch extract all subtitles
yt-dlp --write-subs --write-auto-subs --sub-lang en --sub-format srt \
  --skip-download -o "./research/%(title)s.%(ext)s" \
  --batch-file "./research/urls.txt" \
  --sleep-interval 2
```

### Convert SRT to Clean Text (for NotebookLM)

After extracting `.srt` files, clean them into plain text for better source quality:

```python
# scripts/srt_to_text.py
import re
import sys

def srt_to_text(srt_path):
    with open(srt_path, 'r', encoding='utf-8') as f:
        content = f.read()
    # Remove sequence numbers and timestamps
    lines = content.split('\n')
    text_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if re.match(r'^\d+$', line):
            continue
        if re.match(r'\d{2}:\d{2}:\d{2}', line):
            continue
        # Remove HTML tags from auto-subs
        line = re.sub(r'<[^>]+>', '', line)
        text_lines.append(line)
    # Deduplicate consecutive identical lines (common in auto-subs)
    deduped = []
    for line in text_lines:
        if not deduped or line != deduped[-1]:
            deduped.append(line)
    return ' '.join(deduped)

if __name__ == '__main__':
    srt_file = sys.argv[1]
    output = srt_file.replace('.srt', '.txt')
    text = srt_to_text(srt_file)
    with open(output, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f"Converted: {output} ({len(text)} chars)")
```

Run it:
```bash
python scripts/srt_to_text.py "./research/Video Title.en.srt"
```

---

## 🚀 Phase 3: Feed to NotebookLM for German Adaptation

### Option A: Add YouTube URL Directly (Easiest)

NotebookLM can directly process YouTube URLs — it auto-extracts the transcript:

```bash
# Create a notebook for the German adaptation
notebooklm create "DE-Adaptation: [Original Episode Title]" --json
notebooklm use <notebook_id>

# Add the original YouTube video as source (auto-extracts transcript)
notebooklm source add "https://youtube.com/watch?v=VIDEO_ID" --json

# Wait for processing
notebooklm source wait <source_id> --timeout 600
```

### Option B: Add Cleaned Transcript as Text File

If YouTube URL doesn't work or you want cleaner input:

```bash
# Add the cleaned transcript as a source
notebooklm source add "./research/Video Title.txt" --json
```

### Option C: Add Multiple Sources for Richer Adaptation

```bash
# Add the original video transcript
notebooklm source add "https://youtube.com/watch?v=VIDEO_ID"

# Add related scientific papers for depth
notebooklm source add "https://arxiv.org/abs/RELEVANT_PAPER"

# Add German Wikipedia for terminology
notebooklm source add "https://de.wikipedia.org/wiki/TOPIC"
```

### Generate the German Podcast

```bash
# Set German language
notebooklm language set de

# Configure the Gen Z persona
notebooklm configure --persona "Du bist ein enthusiastischer, witziger Science-Kommunikator für Gen Z. Sprich locker und direkt. Benutze Analogien aus Gaming und Pop-Kultur. Mach Wissenschaft aufregend."

# Generate the adapted German podcast
notebooklm generate audio "Erstelle eine fesselnde deutsche Episode basierend auf dem englischen Original. \
  Übersetze nicht wörtlich — adaptiere und mache es besser. \
  Beginne mit einem dramatischen Szenario. \
  Benutze deutsche Pop-Kultur-Referenzen wo möglich. \
  Mach es unterhaltsam für Gen Z Science-Nerds." \
  --format deep-dive --length long --language de --retry 3 --json

# Wait and download
notebooklm artifact wait <artifact_id> --timeout 1200
notebooklm download audio "./episodes/adapted_episode.mp3"
```

---

## 🔄 Complete Pipeline: Discovery → Adaptation

Here's the full end-to-end workflow:

```bash
# === 1. DISCOVER ===
# Find viral sci-fi podcast episodes
yt-dlp --flat-playlist \
  --print "%(id)s | %(title)s | %(view_count)s views | %(duration_string)s" \
  "ytsearch30:science fiction podcast 2025 full episode"

# === 2. EVALUATE ===
# Pick the best video, check its subtitles
yt-dlp --list-subs "https://youtube.com/watch?v=CHOSEN_VIDEO_ID"

# === 3. EXTRACT ===
# Get the subtitles
yt-dlp --write-subs --write-auto-subs --sub-lang en --sub-format srt \
  --skip-download -o "./research/%(title)s.%(ext)s" \
  "https://youtube.com/watch?v=CHOSEN_VIDEO_ID"

# Clean to text (optional, for better quality)
python scripts/srt_to_text.py "./research/Video Title.en.srt"

# === 4. CREATE NOTEBOOK ===
notebooklm create "DE-S01E05: Adapted from [Original Title]" --json
notebooklm use <notebook_id>

# === 5. ADD SOURCES ===
# Add original video (auto-transcript) + cleaned text + extra sources
notebooklm source add "https://youtube.com/watch?v=CHOSEN_VIDEO_ID" --json
notebooklm source add "./research/Video Title.txt" --json
notebooklm source add "https://de.wikipedia.org/wiki/RELEVANT_TOPIC" --json

# === 6. RESEARCH & ENRICH ===
notebooklm ask "Was sind die Hauptthemen in diesen Quellen?"
notebooklm ask "Welche Fakten würden deutsche Gen Z überraschen?"

# === 7. GENERATE GERMAN PODCAST ===
notebooklm language set de
notebooklm configure --persona "Enthusiastischer Gen-Z Science Kommunikator. Locker, witzig, mit Gaming/Anime-Referenzen."
notebooklm generate audio "Adaptiere den englischen Inhalt als packende deutsche Episode. \
  Nicht übersetzen — neu erzählen, besser machen. \
  Dramatischer Einstieg, überraschende Fakten, kontroverse Diskussion." \
  --format deep-dive --length long --language de --retry 3 --json

# === 8. DOWNLOAD ===
notebooklm artifact wait <artifact_id> --timeout 1200
notebooklm download audio "./episodes/S01E05_adapted.mp3"
```

---

## 📋 Research Tracking Template

When discovering videos, log them like this:

```markdown
## Research Log: [Topic/Search Query]

| # | Video ID | Title | Views | Duration | CC? | Score | Status |
|---|----------|-------|-------|----------|-----|-------|--------|
| 1 | dQw4w9W | "The AI That..." | 2.1M | 45:12 | ✅ Manual | ⭐⭐⭐⭐⭐ | Extracted |
| 2 | xYz1234 | "Quantum Mind" | 890K | 32:08 | ✅ Auto | ⭐⭐⭐⭐ | Pending |
| 3 | aBc5678 | "Mars Colony" | 1.5M | 28:44 | ❌ None | ⭐⭐⭐ | Skip |
```

**Scoring criteria:**
- ⭐⭐⭐⭐⭐ = Viral (1M+ views) + great topic + good CC + matches our niche
- ⭐⭐⭐⭐ = High views + good topic + has CC
- ⭐⭐⭐ = Decent views + relevant topic
- ⭐⭐ = Niche but interesting
- ⭐ = Skip unless nothing better

---

## 📂 Project Structure

```
research/
├── urls.txt              ← Batch URL list for extraction
├── search_results/       ← Raw search output logs
├── subtitles/            ← Extracted .srt files
├── transcripts/          ← Cleaned .txt files
├── logs/                 ← Research tracking logs
└── scripts/
    └── srt_to_text.py    ← SRT → clean text converter
```

---

## ⚡ Quick Command Reference

| Task | Command |
|---|---|
| Search YouTube | `yt-dlp --flat-playlist --print "%(id)s \| %(title)s \| %(view_count)s" "ytsearch30:QUERY"` |
| List subtitles | `yt-dlp --list-subs "URL"` |
| Extract English CC | `yt-dlp --write-subs --sub-lang en --sub-format srt --skip-download "URL"` |
| Extract auto-subs | `yt-dlp --write-auto-subs --sub-lang en --sub-format srt --skip-download "URL"` |
| Clean SRT to text | `python scripts/srt_to_text.py "file.srt"` |
| Add to NotebookLM | `notebooklm source add "URL"` |
| Generate DE podcast | `notebooklm generate audio "instructions" --format deep-dive --language de --retry 3` |

---

## ⚠️ Important Notes

- **YouTube rate limiting:** Use `--sleep-interval 2` when batch-extracting to avoid being blocked
- **Cookie issues (March 2026+):** If you get "sign in" errors, use Firefox cookies: `yt-dlp --cookies-from-browser firefox "URL"`
- **NotebookLM can directly process YouTube URLs** — it auto-extracts transcripts, so you may not even need yt-dlp for simple cases
- **Don't translate word-for-word** — the German podcast should be an *adaptation*, not a translation. Use the English content as inspiration and source material
- **Always add German sources too** (de.wikipedia.org, German science articles) to enrich the adaptation with local terminology
