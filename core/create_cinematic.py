#!/usr/bin/env python3
"""
create_cinematic.py — Create an English NotebookLM notebook and add sources.

Runs after Phase 7. Creates the cinematic notebook and loads all English
sources from 1_research/sources/ + SCRIPT_EN.md. You generate the video
manually whenever you're ready.

Usage:
    python create_cinematic.py --episode-id 1 --topic "UFOs at Nuclear Weapons Sites"
"""

import argparse
import subprocess
import sys
import json
import time
from pathlib import Path

BASE = Path(__file__).parent.parent
MEM  = [sys.executable, str(BASE / ".agent/skills/memory/scripts/memory.py")]


def run_nlm(cmd):
    """Run notebooklm CLI, return parsed JSON or raw string."""
    result = subprocess.run(f"notebooklm {cmd}", shell=True, capture_output=True, text=True, encoding="utf-8")
    try:
        return json.loads(result.stdout.strip())
    except Exception:
        return result.stdout.strip()


def mem(*args):
    result = subprocess.run(MEM + list(args), capture_output=True, text=True, encoding="utf-8")
    return result.stdout.strip()


def ok(text):   print(f"  \033[92m✓ {text}\033[0m")
def warn(text): print(f"  \033[91m⚠ {text}\033[0m")
def step(n, t): print(f"\n\033[93m[{n}] {t}\033[0m")


def main():
    p = argparse.ArgumentParser(description="Create English cinematic notebook + add sources")
    p.add_argument("--episode-id", "-e", type=int, required=True)
    p.add_argument("--topic",      "-t", required=True, help="English topic (used in notebook title)")
    args = p.parse_args()

    import os; os.environ["PYTHONIOENCODING"] = "utf-8"

    print(f"\n\033[96m{'='*55}\033[0m")
    print(f"\033[96m  Cinematic Setup — {args.topic}\033[0m")
    print(f"\033[96m{'='*55}\033[0m")

    # ── Load episode from memory ──────────────────────────────────────────────
    step(1, "Loading episode from memory...")
    ep_json = mem("episode", "get", str(args.episode_id))
    try:
        ep = json.loads(ep_json)
    except Exception:
        warn(f"Could not load episode ID {args.episode_id}"); sys.exit(1)

    ep_path = Path(ep.get("ep_path", ""))
    ok(f"Episode: S{ep['season']:02d}E{ep['episode']:02d} — {ep['title_de']}")

    # ── Collect English source files ──────────────────────────────────────────
    step(2, "Finding English source files...")
    sources_dir = ep_path / "1_research" / "sources"
    if not sources_dir.exists():
        warn(f"Sources folder not found: {sources_dir}"); sys.exit(1)

    en_sources = list(sources_dir.glob("*.txt")) + list(sources_dir.glob("*.md"))
    script_en  = ep_path / "2_script" / "SCRIPT_EN.md"
    if script_en.exists():
        en_sources.append(script_en)

    if not en_sources:
        warn("No source files found!"); sys.exit(1)

    for s in en_sources:
        ok(f"Found: {s.name}")

    # ── Create English notebook ───────────────────────────────────────────────
    step(3, "Creating English NotebookLM notebook...")
    nb_title = f"Cinematic - English - {args.topic}"
    result   = run_nlm(f'create "{nb_title}" --json')

    import re
    cin_nb_id = None
    if isinstance(result, dict):
        cin_nb_id = result.get("id")
    elif isinstance(result, str):
        m = re.search(r'"id":\s*"([^"]+)"', result)
        if m: cin_nb_id = m.group(1)

    if not cin_nb_id:
        warn(f"Could not parse notebook ID. Response: {str(result)[:200]}")
        sys.exit(1)

    ok(f"Notebook: {nb_title}")
    ok(f"ID: {cin_nb_id}")

    run_nlm(f"use {cin_nb_id}")
    mem("episode", "update", str(args.episode_id), "cinematic_notebook_id", cin_nb_id)
    mem("log", str(args.episode_id), "cinematic", f"Notebook created: {cin_nb_id}")

    # ── Add sources ───────────────────────────────────────────────────────────
    step(4, f"Adding {len(en_sources)} source(s)...")
    for src in en_sources:
        result = run_nlm(f'source add "{src}" --json')
        src_id = None
        if isinstance(result, dict):
            src_id = result.get("source", {}).get("id") or result.get("id")
        ok(f"Added: {src.name}" + (f" → {src_id}" if src_id else ""))
        time.sleep(2)  # avoid rate limiting

    mem("log", str(args.episode_id), "cinematic", f"{len(en_sources)} sources added")

    # ── Done ──────────────────────────────────────────────────────────────────
    print(f"\n\033[92m{'='*55}\033[0m")
    print(f"\033[92m  DONE — Notebook ready for cinematic video!\033[0m")
    print(f"\033[92m{'='*55}\033[0m")
    print(f"  Notebook: {nb_title}")
    print(f"  ID:       {cin_nb_id}")
    print()
    print("  When you're ready to generate the video:")
    print(f"    notebooklm use {cin_nb_id}")
    print(f"    notebooklm generate video \"<instructions>\" --style auto --language en")
    print()


if __name__ == "__main__":
    main()
