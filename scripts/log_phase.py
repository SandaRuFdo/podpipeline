#!/usr/bin/env python3
"""
log_phase.py — Push a human-readable log message to the PodPipeline live terminal.

The message appears instantly in the browser's live log panel on the episode detail page.
Use this liberally throughout the pipeline to give the user visibility into what's happening.

Usage:
    python scripts/log_phase.py <episode_id> "<message>" [level]

Levels:  info | success | error | phase | step
         info    = white (default status messages)
         success = green (phase complete, file saved)
         error   = red   (failures, warnings)
         phase   = cyan  (phase starting/ending banners)
         step    = dim   (sub-steps, details)

Examples:
    python scripts/log_phase.py 1 "Starting research phase..." phase
    python scripts/log_phase.py 1 "Found 3 YouTube sources" info
    python scripts/log_phase.py 1 "Script written: 2,400 words" success
    python scripts/log_phase.py 1 "Audio generated: 12m 30s" success
    python scripts/log_phase.py 1 "Failed to download source" error
"""
import sys
import json
import urllib.request
import urllib.error
from datetime import datetime

PORT   = 5000
BASE   = f"http://localhost:{PORT}"
VALID  = {"info", "success", "error", "phase", "step"}


def log(episode_id: int, message: str, level: str = "info") -> bool:
    level = level if level in VALID else "info"
    payload = json.dumps({
        "message": message,
        "level":   level,
        "ts":      datetime.now().strftime("%H:%M:%S"),
    }).encode()
    try:
        req = urllib.request.Request(
            f"{BASE}/api/log/{episode_id}",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=3):
            pass
        return True
    except urllib.error.URLError:
        # Server not running — print locally only, no crash
        print(f"[log_phase] {level.upper()}: {message}")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    try:
        eid = int(sys.argv[1])
    except ValueError:
        print(f"[log_phase] ERROR: episode_id must be an integer, got: {sys.argv[1]}")
        sys.exit(1)

    msg    = sys.argv[2]
    level  = sys.argv[3] if len(sys.argv) > 3 else "info"
    ok     = log(eid, msg, level)
    sys.exit(0 if ok else 0)   # always exit 0 — logging is non-blocking
