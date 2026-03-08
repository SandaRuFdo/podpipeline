---
name: Audio Listener
description: Transcribes audio files using faster-whisper to extract text with precise timestamps. Can analyze podcast audio to identify topic segments, generate SRT subtitles, and create timestamped content maps for visual production.
---

# Audio Listener Skill

This skill gives you the ability to **listen to audio files** — transcribe them with word-level and segment-level timestamps using the `faster-whisper` library (a fast, efficient implementation of OpenAI's Whisper model).

## When to Use

- When you need to know the **exact timestamps** of what's being said in an audio file
- When creating **visual slides/videos** that need to sync with podcast audio
- When you need to **transcribe** audio to text (any language)
- When you need to **verify** script timing against actual generated audio

## Setup (One-Time)

```bash
pip install faster-whisper
```

> **Note:** On first run, the model will be downloaded (~1.5 GB for `medium`, ~3 GB for `large-v3`). This only happens once.

## Available Scripts

### 1. `scripts/transcribe.py` — Full Transcription with Timestamps

Transcribes an audio file and outputs segments with timestamps.

```bash
python .agent/skills/audio-listener/scripts/transcribe.py <audio_file> [options]
```

**Options:**
- `--model` — Whisper model size: `tiny`, `small`, `medium`, `large-v3` (default: `medium`)
- `--language` — Force language (e.g., `de`, `en`). Auto-detected if not set.
- `--output` — Output file path (default: prints to stdout)
- `--format` — Output format: `txt`, `srt`, `json`, `segments` (default: `segments`)
- `--word-timestamps` — Include word-level timestamps (slower but more precise)

**Example — Get timestamped segments:**
```bash
python .agent/skills/audio-listener/scripts/transcribe.py episodes/S01/E01/podcast.mp3 --language de --format segments
```

**Example — Generate SRT subtitles:**
```bash
python .agent/skills/audio-listener/scripts/transcribe.py podcast.mp3 --format srt --output podcast.srt
```

**Example — JSON with word timestamps:**
```bash
python .agent/skills/audio-listener/scripts/transcribe.py podcast.mp3 --format json --word-timestamps --output transcript.json
```

### 2. `scripts/segment_topics.py` — Topic Segmentation

Analyzes a transcript to identify topic transitions and create a timestamped topic map. This is what you use to sync visuals to podcast audio.

```bash
python .agent/skills/audio-listener/scripts/segment_topics.py <audio_file> [options]
```

**Options:**
- `--model` — Whisper model size (default: `medium`)
- `--language` — Force language
- `--script` — Path to the original script file to match segments against
- `--output` — Output file path

This outputs a markdown file with topic segments, timestamps, and key phrases detected.

## Workflow: Syncing Visuals to Audio

1. **Transcribe the audio** with segment timestamps
2. **Compare transcript** to the podcast script to identify which section is being spoken when
3. **Extract exact timestamps** for each topic transition
4. **Update visual timestamps** in the slide source document

## Model Sizes

| Model | Size | Speed | Quality | Best For |
|-------|------|-------|---------|----------|
| `tiny` | 75 MB | Very fast | Lower | Quick checks |
| `small` | 500 MB | Fast | Good | Most tasks |
| `medium` | 1.5 GB | Medium | Very good | German/non-English |
| `large-v3` | 3 GB | Slow | Best | Perfect accuracy |

> **Recommendation:** Use `medium` for German podcast transcription. Use `small` for quick checks.

## Notes

- The audio file can be any format (MP3, WAV, M4A, FLAC, OGG, etc.) — `faster-whisper` handles conversion internally via ffmpeg
- If the file is named `.mp3` but is actually M4A/DASH (like NotebookLM outputs), it will still work
- German transcription quality is excellent with `medium` or larger models
