#!/usr/bin/env python3
"""
setup.py — PodPipeline one-click setup
Run: python setup.py
"""
import sys
import subprocess
import importlib
import os
from pathlib import Path

# ── Colours ───────────────────────────────────────────────────────────────────
G = "\033[92m"; Y = "\033[93m"; R = "\033[91m"; B = "\033[94m"; E = "\033[0m"

def ok(msg):  print(f"{G}  ✔  {msg}{E}")
def info(msg): print(f"{B}  →  {msg}{E}")
def warn(msg): print(f"{Y}  ⚠  {msg}{E}")
def fail(msg): print(f"{R}  ✘  {msg}{E}")

print(f"\n{B}{'─'*52}")
print(f"  🎬  PodPipeline — Setup")
print(f"{'─'*52}{E}\n")

# ── Step 1: Python version check ──────────────────────────────────────────────
info("Checking Python version...")
major, minor = sys.version_info[:2]
if major < 3 or (major == 3 and minor < 10):
    fail(f"Python 3.10+ required. You have {major}.{minor}. Please upgrade.")
    sys.exit(1)
ok(f"Python {major}.{minor} ✓")

# ── Step 2: pip check ─────────────────────────────────────────────────────────
info("Checking pip...")
try:
    subprocess.run([sys.executable, "-m", "pip", "--version"],
                   check=True, capture_output=True)
    ok("pip available ✓")
except Exception:
    fail("pip not found. Install pip first: https://pip.pypa.io/en/stable/installation/")
    sys.exit(1)

# ── Step 3: Install dependencies ──────────────────────────────────────────────
info("Installing dependencies from requirements.txt...")
req_file = Path(__file__).parent / "requirements.txt"
if not req_file.exists():
    fail("requirements.txt not found. Is the repo cloned correctly?")
    sys.exit(1)

result = subprocess.run(
    [sys.executable, "-m", "pip", "install", "-r", str(req_file), "--quiet"],
    capture_output=True, text=True
)
if result.returncode != 0:
    fail("Dependency install failed:")
    print(result.stderr[-2000:])
    sys.exit(1)
ok("All dependencies installed ✓")

# ── Step 4: Check critical imports ───────────────────────────────────────────
info("Verifying imports...")
REQUIRED = {
    "flask": "Flask",
    "requests": "requests",
    "notebooklm": "notebooklm-py",
    "yt_dlp": "yt-dlp",
}
all_good = True
for module, pkg in REQUIRED.items():
    try:
        importlib.import_module(module)
        ok(f"  {pkg} ✓")
    except ImportError:
        fail(f"  {pkg} — import failed!")
        all_good = False

if not all_good:
    fail("Some imports failed. Try: pip install -r requirements.txt")
    sys.exit(1)

# ── Step 5: Create episodes folder ───────────────────────────────────────────
eps = Path(__file__).parent / "episodes"
eps.mkdir(exist_ok=True)
(eps / ".gitkeep").touch(exist_ok=True)
ok("episodes/ folder ready ✓")

# ── Step 6: Check for Google credentials ─────────────────────────────────────
info("Checking Google credentials...")
cred_env = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
cred_file = Path(__file__).parent / "service_account.json"

if cred_env or cred_file.exists():
    ok("Google credentials found ✓")
else:
    warn("Google credentials not detected.")
    warn("Set GOOGLE_APPLICATION_CREDENTIALS env var or place service_account.json here.")
    warn("See README.md → Setup → Step 3 for details.")

# ── Done ─────────────────────────────────────────────────────────────────────
print(f"\n{G}{'─'*52}")
print("  ✅  Setup complete!")
print(f"{'─'*52}{E}")
print(f"\n  Run the app with:\n")
print(f"    {Y}python app.py{E}\n")
print(f"  Then open:  {B}http://localhost:5000{E}\n")
