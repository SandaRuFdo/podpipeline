#!/usr/bin/env python3
"""
update_phase.py — Update a pipeline phase status in the UI dashboard.

Calls POST /api/phase/<eid>/<phase>/<status> on the running app.py server.
Run after completing each pipeline step so the UI dashboard reflects reality.

Usage:
    python scripts/update_phase.py <episode_id> <phase> <status>

Phases:   setup | research | script | audio | transcribe | visuals | deliverables | cinematic_setup
Statuses: pending | running | done | failed | skipped

Examples:
    python scripts/update_phase.py 1 research done
    python scripts/update_phase.py 1 script running
    python scripts/update_phase.py 1 audio done
    python scripts/update_phase.py 1 visuals failed
"""
import sys
import urllib.request
import urllib.error
import json

PORT = 5000
BASE_URL = f"http://localhost:{PORT}"

VALID_PHASES = {"setup", "research", "script", "audio", "transcribe", "visuals", "deliverables", "cinematic_setup"}
VALID_STATUSES = {"pending", "running", "done", "failed", "skipped"}


def update_phase(episode_id: int, phase: str, status: str) -> bool:
    if phase not in VALID_PHASES:
        print(f"[update_phase] ERROR: Unknown phase '{phase}'. Valid: {sorted(VALID_PHASES)}")
        return False
    if status not in VALID_STATUSES:
        print(f"[update_phase] ERROR: Unknown status '{status}'. Valid: {sorted(VALID_STATUSES)}")
        return False

    url = f"{BASE_URL}/api/phase/{episode_id}/{phase}/{status}"
    try:
        req = urllib.request.Request(url, method="POST", data=b"")
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = json.loads(resp.read().decode())
            if body.get("ok"):
                print(f"[update_phase] ✓ Episode {episode_id}: {phase} → {status}")
                return True
            else:
                print(f"[update_phase] ✗ API error: {body}")
                return False
    except urllib.error.URLError as e:
        # Server not running — fall back to direct DB write via memory.py
        print(f"[update_phase] Server not reachable ({e.reason}), falling back to memory.py directly...")
        import subprocess, sys
        from pathlib import Path
        mem = [sys.executable, str(Path(__file__).parent.parent / ".agent/skills/memory/scripts/memory.py")]
        r = subprocess.run(mem + ["pipeline", "set", str(episode_id), phase, status],
                           capture_output=True, text=True, encoding="utf-8")
        if "Updated" in r.stdout or r.returncode == 0:
            print(f"[update_phase] ✓ DB fallback: Episode {episode_id}: {phase} → {status}")
            return True
        print(f"[update_phase] ✗ DB fallback failed: {r.stdout} {r.stderr}")
        return False


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(1)

    eid_str, phase, status = sys.argv[1], sys.argv[2], sys.argv[3]
    try:
        eid = int(eid_str)
    except ValueError:
        print(f"[update_phase] ERROR: episode_id must be an integer, got: {eid_str}")
        sys.exit(1)

    ok = update_phase(eid, phase, status)
    sys.exit(0 if ok else 1)
