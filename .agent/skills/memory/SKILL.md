---
name: Podcast Memory
description: Persistent SQLite + FTS5 memory system for the podcast pipeline. Stores episodes, sources, characters, quality feedback, visual styles, timestamps, phase outputs, session state, and workflow contracts. Evolving, self-improving memory that gets smarter after every episode.
---

# 🧠 Podcast Memory System

Persistent memory using **SQLite + FTS5** full-text search. Remembers everything about podcast production — episodes, sources, characters, quality learnings, visual preferences, timestamps, and pipeline state.

## Setup

```bash
python .agent/skills/memory/scripts/memory.py init
```

Database: `.agent/skills/memory/podcast_memory.db`

---

## Quick Reference

```bash
MEM="python .agent/skills/memory/scripts/memory.py"

# ── EPISODES ──────────────────────────────────────────────────────
$MEM episode add 1 1 "UFOs und Atomwaffen" "Nuclear UFOs"
$MEM episode list
$MEM episode get 1
$MEM episode update 1 status complete

# ── SOURCES ───────────────────────────────────────────────────────
$MEM source add 1 youtube "Infographics Show" "https://youtube.com/..."
$MEM source rate 1 5 "Excellent primary source"

# ── CHARACTERS ────────────────────────────────────────────────────
$MEM char set Nova storyteller "Enthusiastic researcher, builds tension"
$MEM char set Max reactor "Skeptical friend, says 'Warte WAS?!'"
$MEM char list / get Nova

# ── QUALITY FEEDBACK ──────────────────────────────────────────────
$MEM quality add 1 audio "Great pacing" "Intro too long" "Shorter cold open" 8

# ── VISUAL STYLES ─────────────────────────────────────────────────
$MEM style set military "Dark cinematic, night vision green" "navy,black,cyan" "tense"
$MEM style get military

# ── TOPICS ────────────────────────────────────────────────────────
$MEM topic add "Nuclear UFOs" paranormal 9 9
$MEM topic check "Nuclear UFOs"
$MEM topic list

# ── PRODUCTION LOG ────────────────────────────────────────────────
$MEM log 1 research "Added YouTube source" "Infographics Show"

# ── SKILL PROFILES (30 combos) ────────────────────────────────────
$MEM profile list                   # All 30
$MEM profile get de gen_z           # Full profile JSON
$MEM profile context de gen_z       # Writing directive for AI
$MEM profile evolve 1               # [NEW] Auto-update profile from quality scores

# ── PHASE OUTPUTS TRACKING [NEW] ──────────────────────────────────
$MEM output set 1 script script_path "episodes/S01/E01/2_script/SCRIPT_DE.md" --verify
$MEM output set 1 audio notebook_id "abc123"
$MEM output get 1               # All outputs for episode
$MEM output get 1 script        # Only script phase outputs

# ── SMART CONTEXT [NEW] ───────────────────────────────────────────
$MEM smart-context 1            # Topic-filtered context (not a wall of text)

# ── SESSION HANDOFF [NEW] ─────────────────────────────────────────
$MEM session save 1 audio "notebooklm artifact wait xyz" "Audio generating, check status"
$MEM session load                   # Read where we left off
$MEM session clear                  # After episode complete

# ── WORKFLOW CONTRACT [NEW] ───────────────────────────────────────
$MEM contract list                  # Show all 8 phases and their rules
$MEM contract verify 1 audio        # Check ALL preconditions before starting

# ── PARALLEL DETECTION [NEW] ──────────────────────────────────────
$MEM parallel 1                     # Which phases can run RIGHT NOW simultaneously

# ── SEARCH + CONTEXT ──────────────────────────────────────────────
$MEM search "nuclear"
$MEM context 1
```

---

## Integration with Workflow

### ⚡ At Pipeline Start (every new session)
```bash
# 1. Load session state — resume if interrupted
$MEM session load

# 2. Check parallel opportunities
$MEM parallel $EID

# 3. Load smart context for this episode
$MEM smart-context $EID
```

### 🔒 Before EVERY phase — verify contract
```bash
# Always verify before starting any phase
$MEM contract verify $EID <phase>
# → If ❌ FAILED: fix the issues shown before continuing
# → If ✅ OK: proceed
```

### 📝 During each phase — track outputs
```bash
# Record every significant output as you produce it
$MEM output set $EID <phase> <key> <value> --verify
```

### 💾 After each phase — save session state
```bash
$MEM session save $EID <phase> "<next_command_to_run>" "<resume_instruction>"
$MEM log $EID <phase> "Phase complete"
```

### 🧬 After episode complete — evolve profile
```bash
$MEM quality add $EID overall "what worked" "what failed" "improvement" <score>
$MEM profile evolve $EID       # Auto-updates avoid/hooks from quality scores
$MEM session clear             # Clean up session state
```

---

## Smart Context vs Regular Context

| Command | What it returns |
|---|---|
| `$MEM context 1` | ALL memory — characters, every episode, all topics |
| `$MEM smart-context 1` | ONLY what matters: profile + chars + similar eps + top sources + quality failures |

Use `smart-context` for script writing — it's focused, fast, and directly actionable.

---

## Evolving Profiles

Profiles get smarter automatically after every episode:

- **score < 7** → failure notes appended to profile `avoid` list
- **score ≥ 9** → success notes promoted to profile `hooks`

Every change is logged in `profile_evolution_log` for auditability. By episode 10, your Gen Z German profile knows exactly what bombed and what worked from real production experience.
