"""
PodPipeline — Automated Smoke Test
Run after fresh install to verify everything is working.
Usage: python scripts/smoke_test.py
"""
import subprocess, sys, os, json
from pathlib import Path

BASE = Path(__file__).parent.parent
PASS = "[PASS]"
FAIL = "[FAIL]"
results = []

def run(cmd, label, check_str=None):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30, cwd=BASE)
        out = r.stdout + r.stderr
        ok = r.returncode == 0
        if check_str and ok:
            ok = check_str in out
        status = PASS if ok else FAIL
        results.append((status, label))
        print(f"  {status} {label}")
        if not ok:
            for line in out.strip().splitlines()[-3:]:
                print(f"       {line}")
    except Exception as e:
        results.append((FAIL, label))
        print(f"  {FAIL} {label} — {e}")

def check_file(path, label):
    ok = Path(BASE / path).exists()
    status = PASS if ok else FAIL
    results.append((status, label))
    print(f"  {status} {label}")

print()
print("=" * 50)
print("  PodPipeline — Smoke Test")
print("=" * 50)
print()

# 1. Python version
v = sys.version_info
ok = v.major == 3 and v.minor >= 10
status = PASS if ok else FAIL
results.append((status, f"Python {v.major}.{v.minor} (need 3.10+)"))
print(f"  {status} Python {v.major}.{v.minor} (need 3.10+)")

# 2. Core Python deps
run([sys.executable, "-c", "import flask, faster_whisper; print('ok')"],
    "Core deps (flask, faster_whisper)")

# 3. ffmpeg
run(["ffmpeg", "-version"], "ffmpeg in PATH", check_str="ffmpeg version")

# 4. yt-dlp
run(["yt-dlp", "--version"], "yt-dlp installed")

# 5. notebooklm CLI
run(["notebooklm", "--help"], "notebooklm-py CLI installed")

# 6. Memory DB
run([sys.executable, "scripts/mem.py", "stats"], "Memory DB working", check_str="Episodes")

# 7. Characters seeded
run([sys.executable, "scripts/mem.py", "char", "list"], "Characters seeded (NOVA + MAX)", check_str="NOVA")

# 8. Visual styles seeded
run([sys.executable, "scripts/mem.py", "style", "get", "tech"], "Visual style 'tech' seeded", check_str="topic_type")

# 9. Config files exist
check_file(".agent/device_config.json", ".agent/device_config.json exists")
check_file(".agent/whisper_model.txt", ".agent/whisper_model.txt exists")

# 10. Server reachable (optional)
try:
    import urllib.request
    urllib.request.urlopen("http://localhost:5000/api/languages", timeout=3)
    results.append((PASS, "Server reachable at http://localhost:5000"))
    print(f"  {PASS} Server reachable at http://localhost:5000")
except Exception:
    results.append(("[SKIP]", "Server not running (start with: python start.py)"))
    print(f"  [SKIP] Server not running — start with: python start.py")

# Summary
print()
print("=" * 50)
passed = sum(1 for s, _ in results if s == PASS)
failed = sum(1 for s, _ in results if s == FAIL)
total  = sum(1 for s, _ in results if s != "[SKIP]")
print(f"  PASSED: {passed}/{total}")
if failed:
    print(f"  FAILED: {failed}")
    for s, label in results:
        if s == FAIL:
            print(f"    ✗ {label}")
    print()
    print("  ❌ Setup incomplete — fix the FAILED items above.")
else:
    print()
    print("  ✅ All checks passed — PodPipeline is ready!")
    print("  Open http://localhost:5000 to start your first episode.")
print("=" * 50)
print()

sys.exit(0 if failed == 0 else 1)
