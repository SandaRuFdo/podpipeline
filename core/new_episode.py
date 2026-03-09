#!/usr/bin/env python3
"""
new_episode.py — Start a new podcast episode.

Sets up the folder structure from _template, checks memory for topic
conflicts, registers the episode in memory, and prints the next steps.

Usage:
    python new_episode.py --season 1 --episode 2 --slug "Dark_Matter" \
        --title-de "Dunkle Materie" --title-en "Dark Matter" \
        --topic "dark matter science mystery"
"""

import argparse
import shutil
import subprocess
import sys
import io
import re
from pathlib import Path

# Force UTF-8 output so emoji/unicode don't crash on Windows cp1252 terminals
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

BASE = Path(__file__).parent.parent
MEM  = [sys.executable, str(BASE / ".agent/skills/memory/scripts/memory.py")]


def run_mem(*args, capture=True):
    result = subprocess.run(MEM + list(args), capture_output=capture, text=True, encoding="utf-8")
    return result.stdout.strip() if capture else None


def banner(text, color="\033[96m"):
    reset = "\033[0m"
    print(f"\n{color}{'='*50}{reset}")
    print(f"{color}  {text}{reset}")
    print(f"{color}{'='*50}{reset}")


def step(n, text):
    print(f"\n\033[93m[{n}] {text}\033[0m")


def ok(text):
    print(f"  \033[92m✓ {text}\033[0m")


def warn(text):
    print(f"  \033[91m[!] {text}\033[0m")


def main():
    p = argparse.ArgumentParser(description="Start a new podcast episode")
    p.add_argument("--season",   "-s", type=int, default=1)
    p.add_argument("--episode",  "-e", type=int, required=True)
    p.add_argument("--slug",          required=True,  help="Short folder name e.g. Dark_Matter")
    p.add_argument("--title",    "-d", required=True,  help="Episode title in output language")
    p.add_argument("--title-en", "-n", default=None,   help="English title (optional)")
    p.add_argument("--lang",           default="en",    help="Output language code (e.g. de, en, es)")
    p.add_argument("--lang-name",      default="English", help="Output language name (e.g. German)")
    p.add_argument("--topic",    "-t", required=True,  help="Topic description")
    p.add_argument("--force",         action="store_true", help="Overwrite existing folder")
    args = p.parse_args()

    # Paths
    slug_clean = re.sub(r"[^\w\-_]", "_", args.slug)
    ep_dir     = BASE / f"episodes/S{args.season:02d}/E{args.episode:02d}_{slug_clean}"
    template   = BASE / "_template"

    banner(f"NEW EPISODE: S{args.season:02d}E{args.episode:02d} — {args.title} [{args.lang.upper()}]")

    # ── Step 1: Check topic in memory ────────────────────────────────────────
    step(1, "Checking topic in memory...")
    result = run_mem("topic", "check", args.topic)
    if "COVERED" in result:
        warn(f"Topic '{args.topic}' was already covered — continuing anyway (web mode).")
        print(f"  {result[:200]}")
    else:
        ok("Topic is fresh — not covered before.")

    # ── Step 2: Create folder ────────────────────────────────────────────────
    step(2, f"Creating episode folder: {ep_dir.relative_to(BASE)}")
    if ep_dir.exists():
        if args.force:
            shutil.rmtree(ep_dir)
            ok("Existing folder removed.")
        else:
            warn("Folder already exists! Use --force to overwrite.")
            sys.exit(1)

    if not template.exists():
        warn("_template folder not found! Creating folders manually...")
        for sub in ["1_research/sources", "2_script", "3_audio", "4_visuals", "5_deliverables"]:
            (ep_dir / sub).mkdir(parents=True, exist_ok=True)
    else:
        shutil.copytree(template, ep_dir)

    ok(f"Folder created: episodes/S{args.season:02d}/E{args.episode:02d}_{slug_clean}/")

    # ── Step 3: Write README ─────────────────────────────────────────────────
    step(3, "Writing README.md...")
    readme = f"""# {args.title} ({args.title_en or args.topic})

## Episode Info
- Season: {args.season}
- Episode: {args.episode}
- Language: {args.lang_name} ({args.lang})
- Topic: {args.topic}
- Status: planned
- NotebookLM ID: (pending)

## Folder Structure
- `1_research/` — Source files (YouTube transcripts, PDFs, Wikipedia)
- `2_script/`   — Script in {args.lang_name} (SCRIPT_{args.lang.upper()}.md) + English translation (SCRIPT_EN.md)
- `3_audio/`    — podcast.mp3 + transcript.txt (with timestamps)
- `4_visuals/`  — 16:9 cinematic images (slide01_*.png ...)
- `5_deliverables/` — walkthrough.md (CapCut guide) + SLIDE_SOURCE.md
"""
    (ep_dir / "README.md").write_text(readme, encoding="utf-8")
    ok("README.md written.")

    # ── Step 4: Register in memory ───────────────────────────────────────────
    step(4, "Registering in memory...")
    mem_args = ["episode", "add", str(args.season), str(args.episode), args.title, args.topic]
    if args.title_en:
        mem_args.append(args.title_en)
    result = run_mem(*mem_args)
    print(f"  {result}")

    # Extract episode ID
    eid = None
    match = re.search(r"ID:(\d+)", result)
    if match:
        eid = match.group(1)
        run_mem("episode", "update", eid, "ep_path", str(ep_dir))
        run_mem("pipeline", "init", eid)
        run_mem("pipeline", "set", eid, "setup", "done")
        run_mem("log", eid, "setup", "Episode created")

    ok(f"Memory ID: {eid or '?'}")

    # ── Step 5: Show character bible ─────────────────────────────────────────
    step(5, "Character Bible (for script consistency):")
    ctx = run_mem("context")
    # Print only the Character Bible section
    in_chars = False
    for line in ctx.splitlines():
        if line.startswith("## Character"):
            in_chars = True
        elif line.startswith("##") and in_chars:
            break
        if in_chars:
            print(f"  {line}")

    # ── Done ─────────────────────────────────────────────────────────────────
    banner(f"READY! S{args.season:02d}E{args.episode:02d} — {args.title} [{args.lang.upper()}]", "\033[92m")
    print(f"  Episode folder : episodes/S{args.season:02d}/E{args.episode:02d}_{slug_clean}/")
    print(f"  Language       : {args.lang_name} ({args.lang})")
    print(f"  Memory ID      : {eid or '?'}")
    print()
    print("  Next steps:")
    print("  1. Research sources → 1_research/sources/")
    print(f"  2. Write script     → 2_script/SCRIPT_{args.lang.upper()}.md + SCRIPT_EN.md")
    print("  3. Run /podcast-pipeline")
    print()


if __name__ == "__main__":
    main()
