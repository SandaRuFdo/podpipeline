#!/usr/bin/env python3
"""
test_deployment.py — Final production deployment check for PodPipeline.

Runs all verification steps in order:
  1. Python syntax check (6 key files)
  2. pytest API suite (27 tests)
  3. Memory DB health check
  4. Config files existence check (.agent/whisper_model.txt + device_config.json)
  5. Browser UI test (5 dashboard pages, 20+ elements, Playwright)

Usage:
    python scripts/test_deployment.py
    python scripts/test_deployment.py --port 5001
    python scripts/test_deployment.py --skip-browser   (skip Playwright step)
"""
import sys
import subprocess
import time
import urllib.request
import json
import py_compile
from pathlib import Path

# ── Terminal colours ──────────────────────────────────────────────────────────
G  = "\033[92m"   # green
R  = "\033[91m"   # red
Y  = "\033[93m"   # yellow
C  = "\033[96m"   # cyan
B  = "\033[94m"   # blue
DIM = "\033[2m"
RST = "\033[0m"

BASE = Path(__file__).resolve().parent.parent   # repo root

def ok(msg):   print(f"{G}  [PASS]  {msg}{RST}")
def fail(msg): print(f"{R}  [FAIL]  {msg}{RST}")
def warn(msg): print(f"{Y}  [WARN]  {msg}{RST}")
def info(msg): print(f"{C}  -->  {msg}{RST}")
def head(msg): print(f"\n{B}{'─'*60}\n  {msg}\n{'─'*60}{RST}")

PASSED = []
FAILED = []

def record(name, success, note=""):
    if success:
        PASSED.append(name)
    else:
        FAILED.append(f"{name}{': ' + note if note else ''}")


# ═════════════════════════════════════════════════════════════════════════════
# CHECK 1 — Python syntax
# ═════════════════════════════════════════════════════════════════════════════
def check_syntax():
    head("CHECK 1 — Python syntax")
    files = [
        "start.py",
        "app.py",
        "scripts/mem.py",
        "scripts/force_16x9.py",
        "scripts/test_deployment.py",
        ".agent/skills/audio-listener/scripts/transcribe.py",
        "core/new_episode.py",
    ]
    all_ok = True
    for f in files:
        path = BASE / f
        if not path.exists():
            warn(f"{f} not found — skipping")
            continue
        try:
            py_compile.compile(str(path), doraise=True)
            ok(f"{f}")
        except py_compile.PyCompileError as e:
            fail(f"{f}: {e}")
            all_ok = False
    record("Syntax check", all_ok)
    return all_ok


# ═════════════════════════════════════════════════════════════════════════════
# CHECK 2 — pytest API suite
# ═════════════════════════════════════════════════════════════════════════════
def check_pytest(port: int):
    head("CHECK 2 — pytest API suite")

    # Start the app in background for pytest
    server = subprocess.Popen(
        [sys.executable, str(BASE / "app.py"), "--port", str(port)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        cwd=str(BASE), encoding="utf-8"
    )

    # Wait up to 15s for server
    base_url = f"http://localhost:{port}"
    for i in range(15):
        time.sleep(1)
        try:
            urllib.request.urlopen(f"{base_url}/api/languages", timeout=2)
            break
        except Exception:
            if i == 14:
                fail("Server didn't start for pytest")
                server.terminate()
                record("pytest suite", False, "server failed to start")
                return False

    info(f"Running pytest tests/test_api.py against port {port}...")
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_api.py", "-v",
         "--base-url", base_url],
        cwd=str(BASE), capture_output=True, text=True
    )
    server.terminate()
    try:
        server.wait(timeout=5)
    except Exception:
        pass

    # Print pytest output
    for line in result.stdout.splitlines():
        if "PASSED" in line:
            ok(line.strip())
        elif "FAILED" in line or "ERROR" in line:
            fail(line.strip())
        elif line.strip():
            print(f"  {DIM}{line.strip()}{RST}")

    success = result.returncode == 0
    # Parse summary line
    for line in result.stdout.splitlines():
        if "passed" in line or "failed" in line:
            info(line.strip())
    record("pytest suite", success, "" if success else "see output above")
    return success


# ═════════════════════════════════════════════════════════════════════════════
# CHECK 3 — Memory DB health
# ═════════════════════════════════════════════════════════════════════════════
def check_memory():
    head("CHECK 3 — Memory DB health")
    db_path = BASE / ".agent" / "skills" / "memory" / "podcast_memory.db"
    if not db_path.exists():
        fail(f"Memory DB not found: {db_path}")
        record("Memory DB", False)
        return False
    size_kb = db_path.stat().st_size // 1024
    ok(f"DB exists ({size_kb} KB)")

    result = subprocess.run(
        [sys.executable, str(BASE / "scripts" / "mem.py"), "stats"],
        capture_output=True, text=True, cwd=str(BASE)
    )
    if result.returncode == 0:
        for line in result.stdout.strip().splitlines():
            print(f"  {DIM}{line}{RST}")
        ok("mem.py stats returned successfully")
        record("Memory DB", True)
        return True
    else:
        fail(f"mem.py stats failed: {result.stderr[:200]}")
        record("Memory DB", False)
        return False


# ═════════════════════════════════════════════════════════════════════════════
# CHECK 4 — Config files
# ═════════════════════════════════════════════════════════════════════════════
def check_configs():
    head("CHECK 4 — Config files")
    configs = {
        ".agent/whisper_model.txt":  "Whisper model selection",
        ".agent/device_config.json": "GPU/device config",
    }
    all_ok = True
    for rel_path, label in configs.items():
        path = BASE / rel_path
        if path.exists():
            content = path.read_text(encoding="utf-8").strip()
            if rel_path.endswith(".json"):
                try:
                    data = json.loads(content)
                    ok(f"{label} → {data}")
                except Exception:
                    warn(f"{label} — invalid JSON in {rel_path}")
                    all_ok = False
            else:
                ok(f"{label} → {content!r}")
        else:
            warn(f"{label} NOT found ({rel_path}) — run python start.py first")
            all_ok = False
    record("Config files", all_ok)
    return all_ok


# ═════════════════════════════════════════════════════════════════════════════
# CHECK 5 — Browser UI (Playwright)
# ═════════════════════════════════════════════════════════════════════════════
def check_browser_ui(port: int):
    head("CHECK 5 — Browser UI test (Playwright)")

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        info("Installing playwright...")
        subprocess.run([sys.executable, "-m", "pip", "install", "playwright", "--quiet"])
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            warn("playwright unavailable — skipping browser UI check")
            record("Browser UI", False, "playwright not installed")
            return False

    subprocess.run(
        [sys.executable, "-m", "playwright", "install", "chromium", "--quiet"],
        capture_output=True
    )

    # Start app
    server = subprocess.Popen(
        [sys.executable, str(BASE / "app.py"), "--port", str(port)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        cwd=str(BASE), encoding="utf-8"
    )
    base_url = f"http://localhost:{port}"
    for i in range(15):
        time.sleep(1)
        try:
            urllib.request.urlopen(f"{base_url}/api/languages", timeout=2)
            break
        except Exception:
            if i == 14:
                fail("Server didn't start for browser UI test")
                server.terminate()
                record("Browser UI", False, "server failed to start")
                return False

    PAGE_CHECKS = [
        {
            "name":     "Dashboard",
            "click":    "[data-page='dashboard']",
            "wait_for": "#page-dashboard.active",
            "checks":   [
                ("#stats-grid",     "Stats grid"),
                ("#sv-eps",         "Episodes stat card"),
                ("#sv-langs",       "Languages stat card"),
                ("#recent-ep-list", "Recent episodes list"),
                ("#suggest-box",    "Next topic suggestion"),
            ],
        },
        {
            "name":     "Episodes",
            "click":    "[data-page='episodes']",
            "wait_for": "#page-episodes.active",
            "checks":   [
                ("#episodes-grid",    "Episodes grid"),
                ("#ep-filter-lang",   "Language filter"),
                ("#ep-filter-status", "Status filter"),
            ],
        },
        {
            "name":     "New Episode",
            "click":    "[data-page='new-episode']",
            "wait_for": "#page-new-episode.active",
            "checks":   [
                ("#new-episode-form",      "Form"),
                ("input[name='season']",   "Season field"),
                ("input[name='episode']",  "Episode number field"),
                ("input[name='slug']",     "Slug field"),
                ("#lang-selected",         "Language picker"),
                ("#audience-card-grid",    "Audience grid"),
                ("input[name='title_de']", "Title field"),
                ("input[name='topic']",    "Topic field"),
                ("#create-btn",            "Create button"),
            ],
        },
        {
            "name":     "Analytics",
            "click":    "[data-page='analytics']",
            "wait_for": "#page-analytics.active",
            "checks":   [
                ("#analytics-stats",   "Stats panel"),
                ("#analytics-suggest", "Topic suggestion"),
                ("#quality-form",      "Quality form"),
            ],
        },
        {
            "name":     "Memory",
            "click":    "[data-page='memory']",
            "wait_for": "#page-memory.active",
            "checks":   [
                ("#characters-list", "Characters"),
                ("#styles-list",     "Visual styles"),
                ("#topics-list",     "Topics"),
            ],
        },
    ]

    shots_dir = BASE / ".agent" / "ui_screenshots"
    shots_dir.mkdir(parents=True, exist_ok=True)

    total_pass = 0
    total_fail = 0

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.goto(base_url, wait_until="networkidle", timeout=15000)
            time.sleep(1)

            for pg in PAGE_CHECKS:
                print(f"\n{C}  [{pg['name']}]{RST}")
                try:
                    page.click(pg["click"], timeout=5000)
                    page.wait_for_selector(pg["wait_for"], timeout=5000)
                    time.sleep(0.8)
                except Exception as e:
                    fail(f"Navigation failed: {e}")
                    total_fail += 1
                    continue

                for selector, label in pg["checks"]:
                    try:
                        el = page.wait_for_selector(selector, timeout=3000)
                        if el and el.is_visible():
                            ok(f"  {label} ✓")
                            total_pass += 1
                        else:
                            warn(f"  {label} — not visible")
                            total_fail += 1
                    except Exception:
                        fail(f"  {label} — not found ({selector})")
                        total_fail += 1

                shot = shots_dir / f"deploy_{pg['name'].lower().replace(' ', '_')}.png"
                page.screenshot(path=str(shot))
                print(f"  {DIM}Screenshot: {shot.name}{RST}")

            browser.close()
    except Exception as e:
        warn(f"Browser test error: {e}")
        total_fail += 1
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except Exception:
            pass

    info(f"UI elements: {total_pass} passed, {total_fail} failed")
    record("Browser UI", total_fail == 0,
           "" if total_fail == 0 else f"{total_fail} element(s) missing")
    return total_fail == 0


# ═════════════════════════════════════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════════════════════════════════════
def main():
    import argparse
    parser = argparse.ArgumentParser(description="PodPipeline deployment test")
    parser.add_argument("--port",         type=int, default=5001,
                        help="Port for test server (default 5001 to avoid conflict)")
    parser.add_argument("--skip-browser", action="store_true",
                        help="Skip Playwright browser UI test")
    args = parser.parse_args()

    print(f"""
{B}╔══════════════════════════════════════════════════╗
║   PodPipeline — Deployment Readiness Test        ║
╚══════════════════════════════════════════════════╝{RST}
""")

    check_syntax()
    check_pytest(args.port)
    check_memory()
    check_configs()
    if not args.skip_browser:
        check_browser_ui(args.port + 1)   # use different port from pytest run
    else:
        warn("Browser UI test skipped (--skip-browser)")

    # ── Final summary ─────────────────────────────────────────────────────────
    print(f"\n{B}{'═'*60}")
    print(f"  DEPLOYMENT TEST SUMMARY")
    print(f"{'═'*60}{RST}")

    for name in PASSED:
        ok(f"{name}")
    for name in FAILED:
        fail(f"{name}")

    print()
    total = len(PASSED) + len(FAILED)
    if not FAILED:
        print(f"{G}  ✅  All {total} checks passed — PRODUCTION READY{RST}")
        sys.exit(0)
    else:
        print(f"{R}  ❌  {len(FAILED)}/{total} checks FAILED — fix before deploying{RST}")
        sys.exit(1)


if __name__ == "__main__":
    main()
