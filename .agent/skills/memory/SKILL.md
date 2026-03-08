---
name: Podcast Memory
description: Persistent SQLite + FTS5 memory system for the podcast pipeline. Stores episodes, sources, characters, quality feedback, visual styles, and timestamps. Enables cross-episode consistency and learning.
---

# 🧠 Podcast Memory System

Persistent memory using **SQLite + FTS5** full-text search. Remembers everything about the podcast production — episodes, sources, character traits, quality learnings, visual preferences, and timestamps.

## Why This Exists

Without memory, each episode starts from zero. With memory:
- **Character consistency** — Nova and Max stay in character across episodes
- **No topic repetition** — tracks what's been covered
- **Quality learning** — remembers what worked and what didn't
- **Source tracking** — knows which sources were good, avoids bad ones
- **Visual consistency** — remembers style preferences per topic type
- **Accurate timestamps** — stores real audio timestamps from transcription

## Setup

```bash
# Initialize the database (one time)
python .agent/skills/memory/scripts/memory.py init
```

Database is stored at `.agent/skills/memory/podcast_memory.db`

## Quick Reference

```bash
MEM="python .agent/skills/memory/scripts/memory.py"

# Episodes
$MEM episode add 1 1 "UFOs und Atomwaffen" "Nuclear UFOs" "UFOs and Nuclear Weapons"
$MEM episode list
$MEM episode get 1
$MEM episode update 1 status complete

# Sources
$MEM source add 1 youtube "Infographics Show" "https://youtube.com/..."
$MEM source rate 1 5 "Excellent primary source"

# Characters
$MEM char set Nova storyteller "Enthusiastic researcher, drops facts, builds tension"
$MEM char set Max reactor "Skeptical friend, asks questions, says 'Warte WAS?!'"
$MEM char list
$MEM char get Nova

# Quality Feedback
$MEM quality add 1 audio "Great pacing" "Intro too long" "Shorter cold open" 8

# Visual Styles
$MEM style set military "Dark cinematic, night vision green, thriller mood" "navy,black,cyan" "tense"
$MEM style get military

# Topics
$MEM topic add "Nuclear UFOs" paranormal 9 9
$MEM topic check "Nuclear UFOs"
$MEM topic list

# Production Log
$MEM log 1 research "Added YouTube source" "Infographics Show transcript"

# Full-Text Search
$MEM search "nuclear weapons"
$MEM search "Nova" character

# Skill Profiles (30 language × audience combos)
$MEM profile list                         # Show all 30 profiles
$MEM profile get de gen_z                 # Full JSON for one profile
$MEM profile context de gen_z             # Ready-to-use writing directive

# Build AI Context (feed to prompt)
$MEM context        # All memory
$MEM context 1      # With episode 1 focus
```

## Integration with Workflow

### At Pipeline Start
```bash
# 1. Check if topic was already covered
$MEM topic check "<topic>"

# 2. Load character bible for script writing
$MEM char get Nova
$MEM char get Max

# 3. Load writing profile for this episode's language × audience
$MEM profile context <lang> <audience>
# e.g. $MEM profile context de gen_z
# → Outputs tone, slang, vocab, cultural refs, hooks, avoid-list

# 4. Get quality learnings from previous episodes
$MEM context
```

### During Production
```bash
# Log each phase
$MEM log <ep_id> research "Started deep research" 
$MEM log <ep_id> script "Script written"
$MEM log <ep_id> audio "Podcast generated" "artifact_id: xyz"
$MEM log <ep_id> transcribe "Audio transcribed" "30:23 duration"
$MEM log <ep_id> visuals "17 images generated"
$MEM episode update <ep_id> status complete
```

### After Production
```bash
# Rate sources
$MEM source rate <id> 5 "Excellent factual content"

# Add quality feedback
$MEM quality add <ep_id> audio "Good chemistry" "Pacing dragged at act 2"
$MEM quality add <ep_id> visuals "Strong images" "Slide 9 didn't match"

# Register topic as covered
$MEM topic add "<topic>" <category> <controversy 1-10> <appeal 1-10>
```

## FTS5 Search

Search across ALL memory — episodes, sources, characters, quality notes, topics:
```bash
$MEM search "nuclear"           # Search everything
$MEM search "Nova" character    # Search only characters
$MEM search "failed" quality    # Search quality notes
```

## Context Builder

The `context` command generates a text summary of all memory — character bible, episode history, quality learnings, covered topics. Feed this to the AI prompt for maximum accuracy:

```bash
$MEM context > /tmp/memory_context.txt
# Then include in prompts for consistency
```
