#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
start.py — PodPipeline ONE-COMMAND setup + launch

After cloning the repo, just run:
    python start.py

This script will:
  1. Check Python 3.10+
  2. Check / install ffmpeg (warn if missing)
  3. Install all pip dependencies
  4. Initialize the memory database
  5. Seed all 30 writing profiles
  6. Run a self-test (API health checks)
  7. Launch the app at http://localhost:5000

Flags:
  --no-launch      Install + test only, don't launch the server
  --skip-tests     Skip the self-test phase
  --port PORT      Custom port (default: 5000)
  --reset-db       Wipe and re-init the memory database (⚠ destructive)
"""

import argparse
import importlib
import json
import os
import shutil
import subprocess
import sys
import time
import threading
import urllib.request
import urllib.error
from pathlib import Path

# ── Force UTF-8 stdout on Windows (must happen before any print) ──────────────
import sys as _sys, io as _io
if hasattr(_sys.stdout, "buffer"):
    _sys.stdout = _io.TextIOWrapper(_sys.stdout.buffer, encoding="utf-8", errors="replace")
if hasattr(_sys.stderr, "buffer"):
    _sys.stderr = _io.TextIOWrapper(_sys.stderr.buffer, encoding="utf-8", errors="replace")

# ── Colour helpers ────────────────────────────────────────────────────────────
R  = "\033[0m"
G  = "\033[92m"
Y  = "\033[93m"
B  = "\033[94m"
C  = "\033[96m"
RE = "\033[91m"
DIM= "\033[2m"

def ok(msg):   print(f"{G}  [OK]  {msg}{R}")
def info(msg): print(f"{C}  -->  {msg}{R}")
def warn(msg): print(f"{Y}  [!]  {msg}{R}")
def fail(msg): print(f"{RE}  [X]  {msg}{R}")
def head(msg): print(f"\n{B}{'-'*56}\n  {msg}\n{'-'*56}{R}")
def dim(msg):  print(f"{DIM}      {msg}{R}")

BASE = Path(__file__).parent
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

# ── Argument parsing ──────────────────────────────────────────────────────────
def parse_args():
    p = argparse.ArgumentParser(description="PodPipeline — one command setup + launch")
    p.add_argument("--no-launch",   action="store_true", help="Don't start the server after setup")
    p.add_argument("--skip-tests",  action="store_true", help="Skip self-test phase")
    p.add_argument("--port",        type=int, default=5000, help="Server port (default: 5000)")
    p.add_argument("--reset-db",    action="store_true", help="⚠ Wipe and re-init memory DB")
    return p.parse_args()


# ── Helpers ───────────────────────────────────────────────────────────────────
def run(cmd, check=True, capture=False, cwd=None):
    """Run a shell command, return CompletedProcess."""
    return subprocess.run(
        cmd, check=check,
        capture_output=capture,
        text=True, encoding="utf-8",
        cwd=cwd or str(BASE)
    )


def pip_install(packages: list[str]):
    run([sys.executable, "-m", "pip", "install", "--quiet", "--upgrade"] + packages)


def mem(*args, capture=True):
    """Call memory.py and return output."""
    script = BASE / ".agent/skills/memory/scripts/memory.py"
    result = subprocess.run(
        [sys.executable, str(script)] + list(args),
        capture_output=capture, text=True, encoding="utf-8",
        cwd=str(BASE)
    )
    return (result.stdout + result.stderr).strip()


def http_get(url, timeout=5):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, {}
    except Exception as e:
        return None, str(e)


# ═════════════════════════════════════════════════════════════════════════════
# STEP 1 — Python version
# ═════════════════════════════════════════════════════════════════════════════
def check_python():
    head("STEP 1 — Python version")
    major, minor = sys.version_info[:2]
    if major < 3 or (major == 3 and minor < 10):
        fail(f"Python 3.10+ required. You have {major}.{minor}.")
        fail("Download from https://python.org/downloads/")
        sys.exit(1)
    ok(f"Python {major}.{minor} ✓")


# ═════════════════════════════════════════════════════════════════════════════
# STEP 2 — ffmpeg
# ═════════════════════════════════════════════════════════════════════════════
def check_ffmpeg():
    head("STEP 2 — ffmpeg")
    if shutil.which("ffmpeg"):
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
        ver = result.stdout.splitlines()[0] if result.stdout else "found"
        ok(f"ffmpeg — {ver}")
    else:
        warn("ffmpeg not found in PATH.")
        warn("Audio resize (force_16x9.py) won't work without it.")
        warn("Install:")
        dim("  Windows:  winget install ffmpeg")
        dim("  macOS:    brew install ffmpeg")
        dim("  Ubuntu:   sudo apt install ffmpeg")
        warn("Continuing anyway — install ffmpeg before generating visuals.")


# ═════════════════════════════════════════════════════════════════════════════
# STEP 3 — pip install
# ═════════════════════════════════════════════════════════════════════════════
def install_deps():
    head("STEP 3 — Installing dependencies")
    req = BASE / "requirements.txt"
    if not req.exists():
        fail("requirements.txt not found — is the repo cloned correctly?")
        sys.exit(1)

    info("Running: pip install -r requirements.txt ...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(req), "--quiet"],
        capture_output=True, text=True, encoding="utf-8"
    )
    if result.returncode != 0:
        fail("Dependency install failed:")
        print(result.stderr[-3000:])
        sys.exit(1)
    ok("All dependencies installed ✓")

    # Verify critical imports
    info("Verifying critical imports...")
    missing = []
    for module, pkg in [
        ("flask", "Flask"),
        ("faster_whisper", "faster-whisper"),
        ("yt_dlp", "yt-dlp"),
    ]:
        try:
            importlib.import_module(module)
            ok(f"  {pkg} ✓")
        except ImportError:
            warn(f"  {pkg} — import failed, retrying pip install...")
            pip_install([pkg])
            try:
                importlib.import_module(module)
                ok(f"  {pkg} ✓ (re-installed)")
            except ImportError:
                fail(f"  {pkg} — still failing. Run: pip install {pkg}")
                missing.append(pkg)

    if missing:
        fail(f"Could not import: {missing}")
        sys.exit(1)


# ═════════════════════════════════════════════════════════════════════════════
# STEP 4 — Memory DB init
# ═════════════════════════════════════════════════════════════════════════════
def init_memory(reset: bool):
    head("STEP 4 — Memory database")
    db_path = BASE / ".agent/skills/memory/podcast_memory.db"
    memory_script = BASE / ".agent/skills/memory/scripts/memory.py"

    if not memory_script.exists():
        fail(f"memory.py not found at: {memory_script}")
        fail("Is the .agent/skills/memory/ folder in the repo?")
        sys.exit(1)

    if reset and db_path.exists():
        warn("--reset-db flag: deleting existing database...")
        db_path.unlink()
        ok("Old database removed.")

    if db_path.exists() and not reset:
        ok(f"Database already exists ({db_path.stat().st_size // 1024} KB) — skipping init.")
        dim("  Use --reset-db to wipe and re-init.")
    else:
        info("Initializing memory database...")
        out = mem("init")
        if "ready" in out.lower() or "database" in out.lower() or db_path.exists():
            ok("Memory database initialized ✓")
        else:
            warn(f"Unexpected init output: {out[:200]}")
            if db_path.exists():
                ok("Database file exists — probably fine.")
            else:
                fail("Database init may have failed.")
                sys.exit(1)


# ═════════════════════════════════════════════════════════════════════════════
# STEP 5 — Seed skill profiles
# ═════════════════════════════════════════════════════════════════════════════
def seed_profiles():
    head("STEP 5 — Seeding skill profiles")
    seed_script = BASE / "scripts/seed_all_profiles.py"
    if not seed_script.exists():
        warn("seed_all_profiles.py not found — skipping.")
        return

    # Check if already seeded
    out = mem("profile", "list")
    existing = [l for l in out.splitlines() if l.strip()]
    if len(existing) >= 20:
        ok(f"Profiles already seeded ({len(existing)} found) — skipping.")
        dim("  Use --reset-db to re-seed from scratch.")
        return

    info("Seeding 30 writing profiles (language × audience)...")
    result = subprocess.run(
        [sys.executable, str(seed_script)],
        capture_output=True, text=True, encoding="utf-8",
        cwd=str(BASE)
    )
    output = (result.stdout + result.stderr).strip()
    if result.returncode == 0:
        ok("Profiles seeded ✓")
    else:
        warn(f"Seed script returned non-zero exit. Output: {output[:300]}")
        warn("Continuing — profiles may partially exist.")
    dim(f"  {output[-200:]}" if output else "")


# ═════════════════════════════════════════════════════════════════════════════
# STEP 6 — Self-test
# ═════════════════════════════════════════════════════════════════════════════
def run_self_test(port: int):
    head("STEP 6 — Self-test")
    info("Starting temporary server for health checks...")

    # Start app.py in background thread for testing
    server_proc = subprocess.Popen(
        [sys.executable, str(BASE / "app.py"), "--port", str(port)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        cwd=str(BASE), encoding="utf-8"
    )

    base_url = f"http://localhost:{port}"
    max_wait = 15
    for i in range(max_wait):
        time.sleep(1)
        try:
            urllib.request.urlopen(f"{base_url}/api/languages", timeout=2)
            break
        except Exception:
            if i == max_wait - 1:
                fail("Server didn't start within 15s. Skipping API tests.")
                server_proc.terminate()
                return True  # Don't block launch
    else:
        fail("Server failed to start for tests.")
        server_proc.terminate()
        return True

    ok(f"Server up at {base_url}")

    tests_passed = 0
    tests_failed = 0
    fixes_applied = 0

    # ── Test suite ──
    checks = [
        ("GET /api/languages",   f"{base_url}/api/languages",   200),
        ("GET /api/audiences",   f"{base_url}/api/audiences",   200),
        ("GET /api/episodes",    f"{base_url}/api/episodes",    200),
        ("GET /api/stats",       f"{base_url}/api/stats",       200),
        ("GET /api/characters",  f"{base_url}/api/characters",  200),
        ("GET /api/styles",      f"{base_url}/api/styles",      200),
        ("GET /api/suggest",     f"{base_url}/api/suggest",     200),
    ]

    for name, url, expected_status in checks:
        status, data = http_get(url)
        if status == expected_status:
            ok(f"  {name} → {status} ✓")
            tests_passed += 1
        elif status is None:
            warn(f"  {name} → connection error: {data}")
            tests_failed += 1
        else:
            fail(f"  {name} → got {status}, expected {expected_status}")
            tests_failed += 1

    # ── Auto-fix: check languages returns German ──
    status, data = http_get(f"{base_url}/api/languages")
    if status == 200 and isinstance(data, list):
        codes = [l.get("code") for l in data]
        if "de" not in codes:
            warn("German (de) missing from /api/languages — DB may need re-seeding.")
            fixes_applied += 1

    # ── Auto-fix: check DB has skill profiles ──
    prof_out = mem("profile", "list")
    prof_count = len([l for l in prof_out.splitlines() if l.strip()])
    if prof_count < 5:
        warn(f"Only {prof_count} profiles found in DB. Re-seeding now...")
        seed_script = BASE / "scripts/seed_all_profiles.py"
        if seed_script.exists():
            subprocess.run([sys.executable, str(seed_script)], cwd=str(BASE))
            fixes_applied += 1
            ok("Re-seeded profiles ✓")

    server_proc.terminate()
    server_proc.wait(timeout=5)

    print()
    info(f"Test results: {tests_passed} passed, {tests_failed} failed, {fixes_applied} auto-fixes applied.")
    if tests_failed > 0:
        warn("Some tests failed — check the output above. App will still launch.")

    return tests_failed == 0


# ═════════════════════════════════════════════════════════════════════════════
# STEP 7 — NotebookLM auth reminder
# ═════════════════════════════════════════════════════════════════════════════
def check_notebooklm_auth():
    head("STEP 7 — NotebookLM auth")
    cred_dir = Path.home() / ".notebooklm"
    cred_files = list(cred_dir.glob("*.json")) if cred_dir.exists() else []

    if cred_files:
        ok(f"NotebookLM credentials found in {cred_dir} ✓")
    else:
        warn("NotebookLM credentials NOT found.")
        warn("Run this once to authenticate:")
        dim("    notebooklm login")
        warn("A browser tab will open — sign in with your Google account.")
        warn("Without this, Phase 4 (audio generation) will fail.")


# ═════════════════════════════════════════════════════════════════════════════
# STEP 8 — Launch app
# ═════════════════════════════════════════════════════════════════════════════
def launch_app(port: int):
    head("STEP 8 — Launching PodPipeline")
    app_file = BASE / "app.py"
    if not app_file.exists():
        fail("app.py not found!")
        sys.exit(1)

    print(f"\n{G}  PodPipeline is starting...{R}")
    print(f"{C}  Open:  http://localhost:{port}{R}")
    print(f"{C}  Stop:  Ctrl + C{R}\n")

    # Launch — replaces current process so Ctrl+C works cleanly
    os.execv(sys.executable, [sys.executable, str(app_file), "--port", str(port)])


# ═════════════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════════════
def main():
    args = parse_args()

    print(f"\n{B}{'='*56}")
    print(f"  PodPipeline -- Auto Setup & Launch")
    print(f"  Repository: https://github.com/SandaRuFdo/podpipeline")
    print(f"{'='*56}{R}\n")

    check_python()
    check_ffmpeg()
    install_deps()
    init_memory(reset=args.reset_db)
    seed_profiles()
    check_notebooklm_auth()

    if not args.skip_tests:
        run_self_test(args.port)
    else:
        info("Skipping self-test (--skip-tests).")

    if not args.no_launch:
        launch_app(args.port)
    else:
        print(f"\n{G}  ✅  Setup complete!{R}")
        print(f"  Run the app with:\n")
        print(f"    {Y}python app.py{R}\n")
        print(f"  Then open:  {C}http://localhost:{args.port}{R}\n")


if __name__ == "__main__":
    main()
