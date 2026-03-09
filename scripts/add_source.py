#!/usr/bin/env python3
"""
add_source.py — Add a source to the episode's context in the UI dashboard.

Calls POST /api/episodes/<eid>/sources on the running app.py server.
Run when you add a source to notebooklm, so the dashboard knows about it too.

Usage:
    python scripts/add_source.py <episode_id> <url_or_path> [title] [type]

Types: youtube | article | podcast | doc
"""
import sys
import urllib.request
import urllib.error
import urllib.parse
import json

PORT = 5000
BASE_URL = f"http://localhost:{PORT}"

def add_source(episode_id: int, url: str, title: str = "", src_type: str = "url"):
    api_url = f"{BASE_URL}/api/episodes/{episode_id}/sources"
    payload = json.dumps({
        "url": url,
        "title": title or url.split("/")[-1],
        "type": src_type
    }).encode("utf-8")
    
    try:
        req = urllib.request.Request(api_url, method="POST", data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = json.loads(resp.read().decode())
            if body.get("ok"):
                print(f"[add_source] [+] Episode {episode_id}: Added source {url}")
                return True
            else:
                print(f"[add_source] [-] API error: {body}")
                return False
    except urllib.error.URLError as e:
        # Fallback to direct DB write if server is down
        print(f"[add_source] Server not reachable ({e.reason}), falling back to memory.py directly...")
        import subprocess
        from pathlib import Path
        mem = [sys.executable, str(Path(__file__).parent.parent / ".agent/skills/memory/scripts/memory.py")]
        r = subprocess.run(mem + ["source", "add", str(episode_id), src_type, title, url],
                           capture_output=True, text=True, encoding="utf-8")
        if "Added" in r.stdout or r.returncode == 0:
            print(f"[add_source] [+] DB fallback: Episode {episode_id}: Added source {url}")
            return True
        print(f"[add_source] [-] DB fallback failed: {r.stdout} {r.stderr}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    eid_str = sys.argv[1]
    url = sys.argv[2]
    title = sys.argv[3] if len(sys.argv) > 3 else ""
    src_type = sys.argv[4] if len(sys.argv) > 4 else "url"
    
    # Auto-detect youtube type
    if "youtube.com" in url or "youtu.be" in url:
        src_type = "youtube"
    elif url.endswith(".pdf"):
        src_type = "doc"
        
    try:
        eid = int(eid_str)
    except ValueError:
        print(f"[add_source] ERROR: episode_id must be an integer, got: {eid_str}")
        sys.exit(1)

    add_source(eid, url, title, src_type)
