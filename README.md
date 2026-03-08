# 🎬 PodPipeline

> AI-powered podcast production control centre. Research → Script → Audio → done.

---

## What it does

PodPipeline lets you produce full podcast episodes using AI:
- Pick a **language** (German, English, Spanish, Portuguese, French)
- Pick a **target audience** (Gen Z, Millennials, Finance Listeners, Tech, Health)
- Enter a **topic** — the AI researches, writes a tailored script, and generates audio
- Manages your episode library, analytics, and writing memory across episodes

---

## Requirements

| Requirement | Version |
|------------|---------|
| Python | **3.10+** |
| pip | any recent |
| Google Account | for NotebookLM audio generation |

---

## Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/podpipeline.git
cd podpipeline
```

### 2. Run setup (checks everything + installs deps)

```bash
python setup.py
```

This will:
- Check your Python version (needs 3.10+)
- Install all dependencies from `requirements.txt`
- Verify all imports work
- Create the `episodes/` output folder
- Check for Google credentials

### 3. Configure Google credentials

PodPipeline uses Google NotebookLM to generate podcast audio. You need a service account:

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project → Enable **Vertex AI API** + **NotebookLM API**
3. Create a **Service Account** → Download the JSON key
4. Either:
   - Place the file here as `service_account.json`, **OR**
   - Set the environment variable:
     ```bash
     # Windows
     set GOOGLE_APPLICATION_CREDENTIALS=C:\path\to\your-key.json

     # Mac / Linux
     export GOOGLE_APPLICATION_CREDENTIALS=/path/to/your-key.json
     ```

### 4. Start the app

```bash
python app.py
```

Open your browser at: **http://localhost:5000**

---

## Project Structure

```
podpipeline/
│
├── 📄 app.py                        # ← Entry point: run this to start
├── ⚙️  setup.py                     # One-click setup & dependency check
├── 📋 requirements.txt              # Runtime dependencies
├── 📋 requirements-dev.txt          # + Dev / testing tools
├── 📋 README.md                     # This file
├── 🚫 .gitignore                    # Git ignore rules
│
├── 🛠️  core/                        # CLI pipeline tools
│   ├── pipeline.py                  # Episode phase tracker & orchestrator
│   ├── new_episode.py               # Episode creation script
│   └── create_cinematic.py          # Cinematic video generation
│
├── 🌐 ui/                           # Frontend (served by Flask)
│   ├── index.html                   # Single-page app shell
│   ├── styles.css                   # Dark theme + full-screen layout
│   └── app.js                       # Frontend logic (routing, API calls)
│
├── 🤖 .agent/
│   ├── skills/
│   │   ├── memory/
│   │   │   ├── SKILL.md
│   │   │   └── scripts/
│   │   │       ├── memory.py        # SQLite episode DB + skill profiles
│   │   │       └── skill_researcher.py  # AI audience research engine
│   │   ├── notebooklm/
│   │   │   └── SKILL.md             # NotebookLM API skill
│   │   ├── german-scifi-podcast/
│   │   │   └── SKILL.md             # Podcast director skill
│   │   ├── audio-listener/
│   │   │   └── SKILL.md             # Audio transcription (faster-whisper)
│   │   └── youtube-podcast-researcher/
│   │       └── SKILL.md             # Viral YouTube content research
│   └── workflows/
│       └── podcast-pipeline.md      # End-to-end production workflow
│
├── 🧪 tests/
│   ├── conftest.py                  # pytest config
│   ├── test_api.py                  # 27 API tests
│   └── test_e2e.py                  # 30 Playwright E2E tests
│
├── 📁 _template/                    # New episode folder template
│   ├── 1_research/
│   ├── 2_script/
│   ├── 3_audio/
│   ├── 4_visuals/
│   └── 5_deliverables/
│
└── 📁 episodes/                     # Episode output (git-ignored)
    └── .gitkeep
```



---

## Running Tests

```bash
# Install dev dependencies first
pip install -r requirements-dev.txt
python -m playwright install chromium

# API tests (fast, ~70 sec)
python -m pytest tests/test_api.py -v

# E2E browser tests (opens Chromium)
python -m pytest tests/test_e2e.py --headed

# Security scan
python -m bandit -r app.py -ll
```

---

## Supported Languages

| Flag | Language | Target Markets |
|------|----------|---------------|
| 🇩🇪 | German | Germany, Austria, Switzerland |
| 🇬🇧 | English | US, UK, Australia |
| 🇪🇸 | Spanish | Latin America, US Hispanic |
| 🇧🇷 | Portuguese | Brazil |
| 🇫🇷 | French | France + Francophone Africa |

---

## Troubleshooting

**`ModuleNotFoundError`** → Run `python setup.py` again or `pip install -r requirements.txt`

**Port 5000 already in use** → Run `python app.py` with `--port 5001` or kill the existing process

**Google auth error** → Check your `GOOGLE_APPLICATION_CREDENTIALS` path or `service_account.json`

**NotebookLM audio not generating** → Ensure your Google project has Vertex AI + NotebookLM APIs enabled

---

## License

Private — shared with permission only. Not for public distribution.
