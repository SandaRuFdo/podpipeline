#!/usr/bin/env python3
"""
mem.py — Thin convenience wrapper for memory.py.

Replaces the PowerShell `& $MEM ...` pattern with a clean cross-platform:
    python scripts/mem.py <command> [args...]

This delegates 100% to .agent/skills/memory/scripts/memory.py.
No logic here — just path resolution.

Usage examples:
    python scripts/mem.py session load
    python scripts/mem.py topic check "dark matter"
    python scripts/mem.py log 1 research "Sources downloaded"
    python scripts/mem.py context 1
    python scripts/mem.py profile context de gen_z
    python scripts/mem.py contract verify 1 research
    python scripts/mem.py pipeline init 1
    python scripts/mem.py episode update 1 ep_path "episodes/S01/E01_Dark_Matter"
    python scripts/mem.py output set 1 research notebook_id "abc123"
    python scripts/mem.py session save 1 research "next command" "resume note"
    python scripts/mem.py session clear
    python scripts/mem.py quality add 1 overall "what worked" "what failed" "improvements" 8
    python scripts/mem.py profile evolve 1
    python scripts/mem.py parallel 1
    python scripts/mem.py smart-context 1
    python scripts/mem.py stats
    python scripts/mem.py suggest
"""
import sys
import subprocess
import os
from pathlib import Path

# Force UTF-8 output (critical on Windows)
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

BASE = Path(__file__).parent.parent
MEMORY_SCRIPT = BASE / ".agent" / "skills" / "memory" / "scripts" / "memory.py"


def main():
    if not MEMORY_SCRIPT.exists():
        print(f"[mem.py] ERROR: memory.py not found at {MEMORY_SCRIPT}", file=sys.stderr)
        print("[mem.py] Run setup first: python .agent/skills/memory/scripts/memory.py init", file=sys.stderr)
        sys.exit(1)

    cmd = [sys.executable, str(MEMORY_SCRIPT)] + sys.argv[1:]
    result = subprocess.run(cmd, encoding="utf-8")
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
