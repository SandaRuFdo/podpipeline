#!/usr/bin/env python3
"""
pipeline.py — Stateful Podcast Production Orchestrator

Tracks which phase each episode is at in memory (SQLite).
Can resume from any failed phase — never restart from scratch.

Usage:
    python pipeline.py --episode-id 1 --status         # Show phase progress
    python pipeline.py --episode-id 1 --next            # Show next incomplete phase
    python pipeline.py --episode-id 1 --phase research  # Mark a phase manually
    python pipeline.py --episode-id 1 --dry-run         # Preview all phases
    python pipeline.py --episode-id 1 --suggest         # Suggest next topic
    python pipeline.py --stats                           # Project-wide stats
"""

import argparse
import subprocess
import sys
import json
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).parent.parent
MEM  = [sys.executable, str(BASE / ".agent/skills/memory/scripts/memory.py")]

# ── Colour helpers ────────────────────────────────────────────────────────────
R = "\033[0m"
BOLD  = lambda t: f"\033[1m{t}{R}"
GREEN = lambda t: f"\033[92m{t}{R}"
YELLOW= lambda t: f"\033[93m{t}{R}"
CYAN  = lambda t: f"\033[96m{t}{R}"
RED   = lambda t: f"\033[91m{t}{R}"
DIM   = lambda t: f"\033[2m{t}{R}"

PHASE_ICONS = {
    "setup":           "📁",
    "research":        "🔍",
    "script":          "✍️ ",
    "audio":           "🎙️ ",
    "transcribe":      "🎧",
    "visuals":         "🖼️ ",
    "deliverables":    "📦",
    "cinematic_setup": "🎬",
}

PHASE_DESC = {
    "setup":           "Create episode folder + register in memory",
    "research":        "Find English sources (YouTube, Wikipedia) for understanding",
    "script":          "Write German script (Nova + Max) from English sources + English translation",
    "audio":           "Script-only notebook → generate podcast via NotebookLM → download MP3",
    "transcribe":      "Transcribe audio with real timestamps",
    "visuals":         "Generate 16:9 cinematic images for each segment",
    "deliverables":    "Build CapCut walkthrough + register topic/quality in memory",
    "cinematic_setup": "Create English NotebookLM notebook + add sources",
}

STATUS_ICONS = {
    "pending": "⏳",
    "running": "🔄",
    "done":    "✅",
    "failed":  "❌",
    "skipped": "⏭️ ",
}


def mem(*args, raw=False):
    """Run a memory command and return JSON or raw string."""
    result = subprocess.run(MEM + list(args), capture_output=True, text=True, encoding="utf-8")
    out = result.stdout.strip()
    if raw:
        return out
    try:
        return json.loads(out)
    except Exception:
        return out


def banner(text):
    w = 58
    print()
    print(CYAN("═" * w))
    print(CYAN(f"  {text}"))
    print(CYAN("═" * w))


def show_status(eid):
    """Print the phase progress table for an episode."""
    ep_raw = mem("episode", "get", str(eid), raw=False)
    if isinstance(ep_raw, str):
        print(RED(f"Episode {eid} not found."))
        return

    ep = ep_raw
    banner(f"S{ep['season']:02d}E{ep['episode']:02d} — {ep['title_de']}")
    print(f"  Status  : {BOLD(ep['status'])}")
    print(f"  Topic   : {ep['topic']}")
    print(f"  Path    : {DIM(ep.get('ep_path') or '(not set)')}")
    print(f"  Notebook: {DIM(ep.get('notebook_id') or '(none)')}")
    print()

    phases_raw = mem("pipeline", "status", str(eid), raw=True)
    if not phases_raw or "not found" in phases_raw.lower():
        print(YELLOW("  No pipeline state found. Run: python pipeline.py --episode-id " + str(eid) + " --init-pipeline"))
        return

    # Parse phase lines back into dicts by calling episode get for full data
    # Memory returns status as a tabular text, so we call episode get for full data
    phases = []
    ep_full = mem("episode", "get", str(eid), raw=False)
    if isinstance(ep_full, dict):
        # Re-fetch from DB directly via a dedicated context call
        pass

    # Parse raw status lines: "  ✅ setup     done"
    all_phases = ["setup","research","script","audio","transcribe","visuals","deliverables","cinematic_setup"]
    status_map = {}
    for line in phases_raw.splitlines():
        line = line.strip()
        for phase in all_phases:
            if phase in line:
                if "done" in line:    status_map[phase] = "done"
                elif "running" in line: status_map[phase] = "running"
                elif "failed" in line:  status_map[phase] = "failed"
                elif "skipped" in line: status_map[phase] = "skipped"
                else:                  status_map[phase] = "pending"

    if not status_map:
        print(YELLOW("  No pipeline state found. Run with --init-pipeline first."))
        return

    print(f"  {'Phase':<22} {'Status':<10} Info")
    print(f"  {'─'*22} {'─'*10} {'─'*20}")
    for phase in all_phases:
        status = status_map.get(phase, "pending")
        icon  = STATUS_ICONS.get(status, "?")
        picon = PHASE_ICONS.get(phase, "  ")
        desc  = PHASE_DESC.get(phase, "")[:40]
        color = GREEN if status == "done" else (RED if status == "failed" else (YELLOW if status == "running" else DIM))
        print(f"  {picon} {color(phase):<31} {icon} {status}")


    print()
    nxt = mem("pipeline", "next", str(eid), raw=True)
    if "All phases" in nxt:
        print(GREEN("  🏁 All phases complete!"))
    else:
        phase_name = nxt.replace("Next phase: ", "").strip()
        print(YELLOW(f"  ▶ Resume from: {BOLD(phase_name)}"))
        print(DIM(f"    {PHASE_DESC.get(phase_name, '')}"))
    print()


def dry_run(eid):
    """Show what would happen for each phase without doing anything."""
    banner(f"DRY RUN — Episode {eid}")
    print(DIM("  No changes will be made.\n"))

    ep_raw = mem("episode", "get", str(eid), raw=False)
    ep = ep_raw if isinstance(ep_raw, dict) else {}

    phases = mem("pipeline", "status", str(eid), raw=False) or []
    done_set = {p["phase"] for p in phases if p["status"] == "done"}
    fail_set = {p["phase"] for p in phases if p["status"] == "failed"}

    all_phases = ["setup","research","script","audio","transcribe","visuals","deliverables","cinematic_setup"]

    for i, phase in enumerate(all_phases, 1):
        icon  = PHASE_ICONS.get(phase, "  ")
        desc  = PHASE_DESC.get(phase, "")
        if phase in done_set:
            print(f"  {icon} {GREEN('[done]'):<16} {phase}: {DIM(desc)}")
        elif phase in fail_set:
            print(f"  {icon} {RED('[retry]'):<16} {phase}: {desc}")
        else:
            print(f"  {icon} {YELLOW('[will run]'):<16} {phase}: {desc}")

    print()
    print(DIM("  Run without --dry-run to execute."))
    print()


def show_stats():
    """Print project-wide stats."""
    s = mem("stats", raw=True)
    print()
    print(s)

    # Also show suggestion
    print()
    sug = mem("suggest", raw=True)
    print(sug)


def mark_phase(eid, phase, status):
    """Manually mark a phase as done/failed/skipped/running."""
    result = mem("pipeline", "set", str(eid), phase, status, raw=True)
    print(GREEN(f"  Phase '{phase}' marked as {status}."))
    if status == "done":
        mem("log", str(eid), phase, f"Manually marked done via pipeline.py")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    import os
    os.environ["PYTHONIOENCODING"] = "utf-8"

    p = argparse.ArgumentParser(
        description="Podcast Pipeline Orchestrator — track, resume, inspect episodes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pipeline.py --episode-id 1 --status
  python pipeline.py --episode-id 1 --next
  python pipeline.py --episode-id 1 --dry-run
  python pipeline.py --episode-id 1 --mark research done
  python pipeline.py --stats
  python pipeline.py --suggest
        """
    )
    p.add_argument("--episode-id", "-e", type=int, help="Episode memory ID")
    p.add_argument("--status",  "-s", action="store_true", help="Show phase progress")
    p.add_argument("--next",    "-n", action="store_true", help="Show next incomplete phase")
    p.add_argument("--dry-run", "-d", action="store_true", help="Preview phases without running")
    p.add_argument("--mark",         nargs=2, metavar=("PHASE","STATUS"), help="Manually set phase status")
    p.add_argument("--init-pipeline", action="store_true", help="Initialize pipeline state for episode")
    p.add_argument("--stats",        action="store_true", help="Show project stats")
    p.add_argument("--suggest",      action="store_true", help="Suggest next topic")
    p.add_argument("--context",      action="store_true", help="Print AI context from memory")
    args = p.parse_args()

    if args.stats or (not args.episode_id and not args.suggest):
        if not args.episode_id:
            show_stats()
            return

    if args.suggest:
        print(mem("suggest", raw=True))
        return

    eid = args.episode_id
    if not eid:
        p.print_help()
        return

    if args.init_pipeline:
        result = mem("pipeline", "init", str(eid), raw=True)
        print(GREEN(result))

    elif args.status or (not any([args.next, args.dry_run, args.mark, args.context])):
        show_status(eid)

    elif args.next:
        nxt = mem("pipeline", "next", str(eid), raw=True)
        print(f"\n  {YELLOW('▶ Next phase:')} {BOLD(nxt.replace('Next phase: ','').strip())}")
        phase = nxt.replace("Next phase: ", "").strip()
        if phase in PHASE_DESC:
            print(f"  {DIM(PHASE_DESC[phase])}")
        print()

    elif args.dry_run:
        dry_run(eid)

    elif args.mark:
        mark_phase(eid, args.mark[0], args.mark[1])
        show_status(eid)  # Show updated status after marking

    elif args.context:
        print(mem("context", str(eid), raw=True))


if __name__ == "__main__":
    main()
