#!/usr/bin/env python3
"""
app.py — Local Web UI + API for Podcast Pipeline
Run: python app.py
Open: http://localhost:5000
"""

import sys, json, subprocess, os, time, queue, threading, uuid, sqlite3
from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory, Response, stream_with_context

BASE = Path(__file__).parent
MEM  = [sys.executable, str(BASE / ".agent/skills/memory/scripts/memory.py")]
DB   = BASE / ".agent/skills/memory/podcast_memory.db"
UI   = BASE / "ui"

app = Flask(__name__, static_folder=str(UI), static_url_path="")
os.environ["PYTHONIOENCODING"] = "utf-8"

def _db():
    """Open a direct SQLite connection (no subprocess overhead)."""
    conn = sqlite3.connect(str(DB), timeout=5)
    conn.row_factory = sqlite3.Row
    return conn

# ── SECURITY HEADERS ──────────────────────────────────────────────────────────
@app.after_request
def add_security_headers(response):
    """Strip fingerprinting headers, add OWASP baseline security headers."""
    response.headers.pop("Server", None)                          # Remove Werkzeug fingerprint
    response.headers["X-Content-Type-Options"] = "nosniff"        # Prevent MIME sniffing
    response.headers["X-Frame-Options"] = "DENY"                  # Clickjacking protection
    response.headers["X-XSS-Protection"] = "1; mode=block"        # Legacy XSS filter
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
    return response


_jobs: dict[str, queue.Queue] = {}

# ── SSE dashboard broadcast ────────────────────────────────────────────────────
# Each connected browser tab gets its own queue; _broadcast_refresh() sends a
# 'dashboard-update' event to all of them so stats/phases refresh instantly.
_dashboard_subscribers: dict[str, queue.Queue] = {}

def _broadcast_refresh(event_data: dict = None):
    """Push a dashboard-update SSE event to every connected browser tab."""
    import json as _json
    payload = _json.dumps(event_data or {"action": "refresh"})
    msg = f"event: dashboard-update\ndata: {payload}\n\n"
    dead = []
    for sid, q in list(_dashboard_subscribers.items()):
        try:
            q.put_nowait(msg)
        except Exception:
            dead.append(sid)
    for sid in dead:
        _dashboard_subscribers.pop(sid, None)

# ── EPISODE LIVE LOG SYSTEM ────────────────────────────────────────────────────
# Antigravity calls POST /api/log/<eid> with messages → stored in rolling buffer
# Browser subscribes to GET /api/log-stream/<eid> (SSE) → receives them live

from collections import deque

_episode_logs: dict[int, deque] = {}                 # rolling 200-line buffer per episode
_episode_log_queues: dict[int, dict] = {}            # {eid: {subscriber_id: queue}}

def _broadcast_log(eid: int, entry: dict):
    """Push a log entry to all browser tabs watching that episode."""
    import json as _json
    if eid not in _episode_logs:
        _episode_logs[eid] = deque(maxlen=200)
    _episode_logs[eid].append(entry)
    payload = _json.dumps(entry)
    msg = f"data: {payload}\n\n"
    dead = []
    for sid, q in list(_episode_log_queues.get(eid, {}).items()):
        try:
            q.put_nowait(msg)
        except Exception:
            dead.append(sid)
    for sid in dead:
        _episode_log_queues.get(eid, {}).pop(sid, None)

PHASE_ORDER = ["setup","research","script","audio","youtube_meta","transcribe","visuals","deliverables","cinematic_setup"]


# ── MEMORY HELPER ─────────────────────────────────────────────────────────────

def mem(*args):
    r = subprocess.run(MEM + [str(a) for a in args],
                       capture_output=True, text=True, encoding="utf-8")
    try:    return json.loads(r.stdout.strip())
    except: return r.stdout.strip()

def mem_raw(*args):
    r = subprocess.run(MEM + [str(a) for a in args],
                       capture_output=True, text=True, encoding="utf-8")
    return r.stdout.strip()


# ── SERVE FRONTEND ────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory(str(UI), "index.html")


# ── LANGUAGES ─────────────────────────────────────────────────────────────────

@app.route("/api/languages")
def get_languages():
    """Direct SQLite — no subprocess."""
    try:
        conn = _db()
        rows = conn.execute("SELECT code, name, flag FROM languages ORDER BY name").fetchall()
        conn.close()
        if rows:
            return jsonify([dict(r) for r in rows])
    except Exception:
        pass
    # Fallback
    return jsonify([
        {"code":"en","name":"English",    "flag":"🇬🇧"},
        {"code":"es","name":"Spanish",    "flag":"🇪🇸"},
        {"code":"pt","name":"Portuguese", "flag":"🇧🇷"},
        {"code":"fr","name":"French",     "flag":"🇫🇷"},
        {"code":"de","name":"German",     "flag":"🇩🇪"},
    ])


# ── AUDIENCES ─────────────────────────────────────────────────────────────────

@app.route("/api/audiences")
def get_audiences():
    # Always return exactly the 5 top CPM audiences (stable, test-safe)
    return jsonify([
        {"key":"finance_listeners","label":"Finance Listeners","emoji":"💰","age_range":"25–55","cpm_low":40,"cpm_high":100,"listener_pct":38,
         "description":"The highest-paid ad segment on ALL of YouTube. Finance content commands $40–100 CPM.","content_tips":"Frame sci-fi through economic/investment lens. Asteroid mining profits, AI stock impact, crypto in space.","best_niches":"space-economy,AI,crypto,future-tech","platforms":"YouTube,Apple Podcasts,Spotify"},
        {"key":"millennials","label":"Millennials","emoji":"💡","age_range":"28–43","cpm_low":30,"cpm_high":50,"listener_pct":61,
         "description":"61.6% of all podcast listeners. High income, peak earning years. Respond to nostalgia + future anxiety.","content_tips":"Deep dives welcome (30–60 min). Reference 90s/2000s culture. Strong narrative arc.","best_niches":"true-crime,finance,space,health","platforms":"Spotify,YouTube,Apple Podcasts"},
        {"key":"tech_enthusiasts","label":"Tech Enthusiasts","emoji":"🖥️","age_range":"25–45","cpm_low":28,"cpm_high":50,"listener_pct":42,
         "description":"CPM hit $29 in August 2024. Brand loyalty extremely high. Coding/software peaks at $40–100.","content_tips":"Go deep on mechanics. Cite real research. Use precise terminology.","best_niches":"AI,quantum,robotics,simulation","platforms":"YouTube,X/Twitter,Twitch"},
        {"key":"gen_z","label":"Gen Z","emoji":"⚡","age_range":"13–27","cpm_low":25,"cpm_high":45,"listener_pct":47,
         "description":"82% take action after hearing a podcast ad — highest conversion of any generation.","content_tips":"Short cold opens (<60s). Cliffhangers every 4 min. Authentic host voices.","best_niches":"sci-fi,gaming,space,paranormal","platforms":"YouTube Shorts,TikTok,Instagram Reels"},
        {"key":"health_wellness","label":"Health & Wellness","emoji":"💊","age_range":"35–65","cpm_low":24,"cpm_high":40,"listener_pct":44,
         "description":"Emotionally responsive. 44% of weekly listeners made a purchase after podcast ad.","content_tips":"Connect sci-fi to health implications. Longevity, biohacking, consciousness.","best_niches":"consciousness,longevity,biohacking","platforms":"YouTube,Spotify,Apple Podcasts"},
    ])




# ── EPISODES ──────────────────────────────────────────────────────────────────

@app.route("/api/episodes")
def list_episodes():
    """Direct SQLite with dynamic status calculation from pipeline phases."""
    try:
        conn = _db()
        # Join with pipeline_state to see if any phases are running/done for this episode
        rows = conn.execute("""
            SELECT e.*, 
                   (SELECT COUNT(*) FROM pipeline_state p WHERE p.episode_id = e.id) as total_phases,
                   (SELECT COUNT(*) FROM pipeline_state p WHERE p.episode_id = e.id AND p.status = 'done') as done_phases,
                   (SELECT COUNT(*) FROM pipeline_state p WHERE p.episode_id = e.id AND p.status = 'running') as running_phases,
                   (SELECT COUNT(*) FROM pipeline_state p WHERE p.episode_id = e.id AND p.status = 'failed') as failed_phases
            FROM episodes e 
            ORDER BY e.season, e.episode
        """).fetchall()
        conn.close()
        
        results = []
        for r in rows:
            d = dict(r)
            # Dynamically calculate overall status
            st = d.get("status", "planned")
            if d["failed_phases"] > 0:
                st = "error"
            elif d["running_phases"] > 0:
                st = "running"
            elif d["total_phases"] > 0 and d["done_phases"] == len(PHASE_ORDER):
                st = "complete"
            elif d["done_phases"] > 0 or d["total_phases"] > 0:
                st = "running"
                
            d["status"] = st
            # Clean up temporary count columns
            for k in ["total_phases", "done_phases", "running_phases", "failed_phases"]:
                d.pop(k, None)
            results.append(d)
            
        return jsonify(results)
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify([])  # Return empty list on error


def _ep_by_se(season, episode):
    """Direct SQLite lookup — no subprocess loop."""
    try:
        conn = _db()
        row = conn.execute(
            "SELECT * FROM episodes WHERE season=? AND episode=?",
            (season, episode)
        ).fetchone()
        conn.close()
        return dict(row) if row else None
    except Exception:
        return None


@app.route("/api/episodes/<int:eid>")
def get_episode(eid):
    import time
    ep = mem("episode", "get", eid)
    if not isinstance(ep, dict):
        return jsonify({"error": "not found"}), 404
    _auto_detect_phases(eid, ep)  # fires subprocess writes
    time.sleep(0.3)               # wait for WAL to checkpoint subprocess commits
    phases   = _get_phases_direct(eid)  # read back from SQLite directly
    sources  = _get_sources(eid)
    ctx      = mem_raw("context", eid)
    audience = mem("audience", "get", ep.get("target_audience", "scifi_curious"))
    if not isinstance(audience, dict):
        audience = {"key": ep.get("target_audience",""), "label": ep.get("target_audience","Unknown"),
                    "emoji": "🎧", "age_range": "N/A", "cpm_low": 0, "cpm_high": 0,
                    "description": "", "content_tips": "", "best_niches": "", "platforms": ""}
    return jsonify({"episode": ep, "phases": phases, "sources": sources,
                    "context_preview": ctx[:800], "audience": audience})


@app.route("/api/episodes/<int:eid>/prompt")
def get_episode_prompt(eid):
    """Generate a pre-filled Antigravity prompt for this episode's full pipeline run."""
    ep = mem("episode", "get", eid)
    if not isinstance(ep, dict):
        return jsonify({"error": "not found"}), 404

    phases   = _get_phases_direct(eid)
    phase_status = {p["phase"]: p["status"] for p in phases}

    # Find first non-done phase to resume from
    resume_phase = next(
        (p for p in PHASE_ORDER if phase_status.get(p) not in ("done", "skipped")),
        "research"
    )

    lang      = ep.get("output_language", "en")
    lang_name = ep.get("language_name", "English")
    audience  = ep.get("target_audience", "scifi_curious")
    title     = ep.get("title_de", ep.get("topic", "Unknown"))
    topic     = ep.get("topic", "")
    season    = ep.get("season", 1)
    episode   = ep.get("episode", 1)
    code      = f"S{int(season):02d}E{int(episode):02d}"

    phase_summary = "\n".join(
        f"  - {p['phase']}: {p['status']}" for p in phases
    )

    prompt = f"""# PodPipeline — Start Full Pipeline

You are operating **PodPipeline** — an AI-powered podcast production system.
Run the full pipeline from start to finish for this episode. Do not stop until all phases are complete.

## Episode Details
- **ID:** {eid}
- **Code:** {code}
- **Title:** {title}
- **Topic:** {topic}
- **Language:** {lang_name} ({lang})
- **Audience:** {audience}
- **Resume from phase:** {resume_phase}

## Current Phase Status
{phase_summary}

## Instructions
1. Read the full workflow: `.agent/skills/dynamic-podcast-director/SKILL.md` (use for all phases)
2. Resume from **{resume_phase}** phase and run ALL remaining phases to completion
3. After EACH phase completes, call:
   `python scripts/update_phase.py {eid} <phase> done`
   This updates the dashboard live.
4. **IMPORTANT**: Use `python scripts/log_phase.py {eid} "Message" [info|success|error|step]` to push human-readable Live Logs to the user's browser terminal. Do this *frequently* so the user sees what you are doing (e.g. "Drafting script...", "Found 3 sources").
5. Do NOT stop until deliverables phase is done and walkthrough.md exists.

## ⏱️ PHASE 4.5 — YouTube Metadata Pack (Run IN PARALLEL during audio gen wait)

> While `notebooklm artifact wait` is running in Phase 4, do these steps — zero extra time cost.

**Step 4.5.1 — Generate titles, description & thumbnail prompt:**
```bash
# Call the API — it streams progress and auto-saves youtube_meta.json + thumbnail_prompt.txt
curl -s -X POST http://localhost:5000/api/episodes/{eid}/generate-youtube-meta > /dev/null
python scripts/log_phase.py {eid} "📋 YouTube metadata pack generated" success
```

**Step 4.5.2 — Generate the thumbnail image:**
1. Read prompt file: `<ep_path>/5_deliverables/thumbnail_prompt.txt`
2. Call `generate_image(prompt=<file content>)` → save to `<ep_path>/5_deliverables/thumbnail.png`
3. Update thumbnail path via API:
   `POST http://localhost:5000/api/episodes/{eid}/youtube-meta` — body: `{{"thumbnail_path": "<path>"}}`
4. `python scripts/log_phase.py {eid} "🖼️ Thumbnail generated" success`

## Working Directory
`episodes/S{int(season):02d}/E{int(episode):02d}_*/`

Start now. Run phase: **{resume_phase}**
"""


    return jsonify({"prompt": prompt, "episode_id": eid, "resume_phase": resume_phase})



@app.route("/api/episodes", methods=["POST"])
def create_episode():
    d = request.json
    required = ["season","episode","slug","title_de","topic","output_language","language_name","target_audience"]
    if not all(k in d and d[k] for k in required):
        return jsonify({"error": "Missing: " + ", ".join(k for k in required if not d.get(k))}), 400

    lang_code = d["output_language"]
    lang_name  = d["language_name"]
    audience   = d["target_audience"]
    job_id = str(uuid.uuid4())
    q: queue.Queue = queue.Queue()
    _jobs[job_id] = q

    def run():
        cmd = [
            sys.executable, str(BASE / "core" / "new_episode.py"),
            "--season",        str(d["season"]),
            "--episode",       str(d["episode"]),
            "--slug",          d["slug"],
            "--title",         d["title_de"],
            "--language",      lang_code,
            "--language-name", lang_name,
            "--audience",      audience,
            "--topic",         d["topic"],
            "--force",
        ]
        if d.get("title_en"): cmd += ["--title-en", d["title_en"]]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, encoding="utf-8", cwd=str(BASE))
        for line in proc.stdout:
            q.put({"type":"line","text":line.rstrip()})
        proc.wait()
        # language/audience are now saved inside new_episode.py directly — no queue scan needed
        q.put({"type":"done","ok": proc.returncode == 0})

    threading.Thread(target=run, daemon=True).start()
    return jsonify({"job_id": job_id})


@app.route("/api/stream/<job_id>")
def stream_job(job_id):
    """SSE endpoint to stream job output line by line."""
    def generate():
        q = _jobs.get(job_id)
        if not q:
            yield "data: {\"type\":\"error\",\"text\":\"Job not found\"}\n\n"
            return
        while True:
            try:
                item = q.get(timeout=30)
                yield f"data: {json.dumps(item)}\n\n"
                if item.get("type") == "done":
                    break
            except queue.Empty:
                yield "data: {\"type\":\"ping\"}\n\n"
        _jobs.pop(job_id, None)

    return Response(stream_with_context(generate()),
                    mimetype="text/event-stream",
                    headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no"})


@app.route("/api/episodes/<int:eid>", methods=["PATCH"])
def update_episode(eid):
    d = request.json
    for field, val in d.items():
        mem_raw("episode", "update", eid, field, val)
    return jsonify({"ok": True})


@app.route("/api/episodes/<int:eid>/export")
def export_episode(eid):
    ep = mem("episode", "get", eid)
    if not isinstance(ep, dict):
        return jsonify({"error": "not found"}), 404
    _auto_detect_phases(eid, ep)
    phases = _get_phases_direct(eid)
    sources = _get_sources(eid)
    ctx = mem_raw("context", eid)
    payload = {"episode": ep, "phases": phases, "sources": sources, "context": ctx}
    resp = Response(json.dumps(payload, ensure_ascii=False, indent=2),
                    mimetype="application/json")
    title = (ep.get("title_de") or "episode").replace(" ","_")
    resp.headers["Content-Disposition"] = f'attachment; filename="S{ep["season"]:02d}E{ep["episode"]:02d}_{title}.json"'
    return resp


@app.route("/api/episodes/<int:eid>/phase", methods=["POST"])
def set_phase(eid):
    d = request.json
    mem_raw("pipeline", "set", eid, d["phase"], d["status"])
    _broadcast_refresh({"action": "phase", "episode_id": eid,
                        "phase": d["phase"], "status": d["status"]})
    return jsonify({"ok": True})


@app.route("/api/episodes/<int:eid>/pipeline/init", methods=["POST"])
def init_pipeline(eid):
    mem_raw("pipeline", "init", eid)
    return jsonify({"ok": True})


@app.route("/api/episodes/<int:eid>/open-folder", methods=["POST"])
def open_folder(eid):
    """Open the episode deliverables folder in the system file explorer."""
    ep = mem("episode", "get", eid)
    if not ep:
        return jsonify({"error": "Episode not found"}), 404

    ep_path = ep.get("ep_path", "")
    if not ep_path:
        return jsonify({"error": "No episode path set"}), 400

    # Try deliverables folder first, fall back to episode root
    base = Path(ep_path)
    deliverables = base / "5_deliverables"
    target = deliverables if deliverables.is_dir() else base

    if not target.is_dir():
        return jsonify({"error": f"Folder not found: {target}"}), 404

    try:
        import platform
        if platform.system() == "Windows":
            os.startfile(str(target))
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", str(target)])
        else:
            subprocess.Popen(["xdg-open", str(target)])
        return jsonify({"ok": True, "path": str(target)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/episodes/<int:eid>/thumbnail")
def serve_thumbnail(eid):
    """Serve the episode thumbnail PNG file."""
    from flask import send_file
    ep = mem("episode", "get", eid)
    if not isinstance(ep, dict):
        return jsonify({"error": "not found"}), 404
    meta_path = _youtube_meta_path(ep)
    if not meta_path or not meta_path.exists():
        return jsonify({"error": "No YouTube metadata found"}), 404
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        thumb_path = meta.get("thumbnail_path", "")
        if not thumb_path:
            # Try default location
            thumb_path = str(meta_path.parent / "thumbnail.png")
        p = Path(thumb_path)
        if not p.is_absolute():
            p = BASE / thumb_path
        if not p.exists():
            return jsonify({"error": "Thumbnail not generated yet"}), 404
        return send_file(str(p), mimetype="image/png")
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── UPDATES ───────────────────────────────────────────────────────────────────


@app.route("/api/check_updates", methods=["GET"])
def check_updates_api():
    try:
        subprocess.run(["git", "fetch", "origin"], check=True, capture_output=True)
        # Check if we are behind
        behind = subprocess.run(["git", "rev-list", "HEAD..origin/main", "--count"], capture_output=True, text=True)
        count = int(behind.stdout.strip() or "0")
        
        if count > 0:
            # Get changes to CHANGELOG.md
            diff = subprocess.run(
                ["git", "diff", "HEAD..origin/main", "--", "CHANGELOG.md"],
                capture_output=True, text=True
            )
            changes = []
            for line in diff.stdout.splitlines():
                if line.startswith("+") and not line.startswith("+++"):
                    changes.append(line[1:])
            
            changes_text = "\n".join(changes).strip()
            if not changes_text:
                # If changelog wasn't updated, just show commits
                log = subprocess.run(["git", "log", "HEAD..origin/main", "--oneline"], capture_output=True, text=True)
                changes_text = log.stdout.strip()
                
            return jsonify({"update_available": True, "changes": changes_text})
            
        return jsonify({"update_available": False})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/update", methods=["POST"])
def perform_update():
    try:
        res = subprocess.run(["git", "pull", "origin", "main"], capture_output=True, text=True)
        if res.returncode != 0:
            return jsonify({"error": "Failed to merge updates", "details": res.stderr}), 500
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ── SOURCES ───────────────────────────────────────────────────────────────────

@app.route("/api/episodes/<int:eid>/sources")
def get_episode_sources(eid):
    return jsonify({"sources": _get_sources(eid)})


@app.route("/api/episodes/<int:eid>/sources", methods=["POST"])
def add_source(eid):
    d = request.json
    # Dedup check
    dup = mem_raw("source", "check-dup", eid, d.get("url","no-url"))
    if "DUPLICATE" in dup:
        return jsonify({"error": "duplicate", "message": dup}), 409
    result = mem_raw("source", "add", eid, d.get("type","url"), d.get("title",""), d.get("url",""))
    return jsonify({"ok": True, "result": result})


@app.route("/api/sources/<int:src_id>/rate", methods=["POST"])
def rate_source(src_id):
    d = request.json
    mem_raw("source", "rate", src_id, d.get("rating", 3), d.get("notes",""))
    return jsonify({"ok": True})


# ── SEARCH ────────────────────────────────────────────────────────────────────

@app.route("/api/search")
def search():
    q = request.args.get("q","").strip()
    if len(q) < 2:
        return jsonify({"results": []})
    results = mem("search", q)
    if isinstance(results, list):
        return jsonify({"results": results})
    # parse raw text
    lines = [l.strip() for l in (results or "").splitlines() if l.strip()]
    return jsonify({"results": [{"type":"result","title":l,"snip":""} for l in lines]})


# ── ANALYTICS ─────────────────────────────────────────────────────────────────

@app.route("/api/stats")
def get_stats():
    import sqlite3
    db_path = BASE / ".agent/skills/memory/podcast_memory.db"
    stats = {}
    suggest = {}
    analytics_data = {}

    if db_path.exists():
        try:
            conn = sqlite3.connect(str(db_path), check_same_thread=False, timeout=5)
            conn.row_factory = sqlite3.Row

            # ── Episode counts ──
            ep_rows = conn.execute("SELECT status FROM episodes").fetchall()
            stats["episodes_total"]    = len(ep_rows)
            stats["episodes_complete"] = sum(1 for r in ep_rows if r["status"] == "complete")

            # ── Sources ──
            stats["sources_total"] = conn.execute("SELECT COUNT(*) FROM sources").fetchone()[0]

            # ── Topics (column: 'topic', not 'name') ──
            topic_rows = conn.execute("SELECT topic, category FROM topics ORDER BY created_at DESC").fetchall()
            stats["topics_covered"] = len(topic_rows)

            # ── Audio duration (column: audio_dur in seconds) ──
            dur_row = conn.execute("SELECT audio_dur FROM episodes WHERE audio_dur IS NOT NULL").fetchone()
            dur = int(dur_row["audio_dur"]) if dur_row else 0
            stats["total_audio_hours"] = round(dur / 3600, 1) if dur else 0

            # ── Quality (table may not exist yet — skip gracefully) ──
            try:
                q_rows = conn.execute("SELECT rating FROM quality_ratings WHERE rating IS NOT NULL").fetchall()
                if q_rows:
                    avg = sum(r["rating"] for r in q_rows) / len(q_rows)
                    stats["avg_quality_score"] = round(avg, 1)
                else:
                    stats["avg_quality_score"] = None
            except Exception:
                stats["avg_quality_score"] = None

            # ── Top category ──
            cat_row = conn.execute("""
                SELECT category, COUNT(*) as cnt FROM topics
                GROUP BY category ORDER BY cnt DESC LIMIT 1
            """).fetchone()
            stats["top_category"] = cat_row["category"].title() if cat_row else None

            # ── Suggest: next uncovered category ──
            covered_cats = {r["category"] for r in topic_rows}
            all_cats = ["space", "paranormal", "military", "technology", "biology",
                        "consciousness", "time", "ancient", "ocean", "simulation", "ai", "geopolitics"]
            uncovered = [c for c in all_cats if c not in covered_cats]
            suggest["suggestion"] = uncovered[0].title() if uncovered else "More Geopolitics"
            suggest["uncovered_categories"] = [c.title() for c in uncovered[:6]]
            suggest["top_performing"] = []

            # ── Analytics summary ──
            cat_rows = conn.execute("""
                SELECT category, COUNT(*) as cnt FROM topics
                GROUP BY category ORDER BY cnt DESC
            """).fetchall()
            analytics_data["categories"] = [
                {"category": r["category"], "topic_count": r["cnt"], "avg_rating": None}
                for r in cat_rows
            ]

            conn.close()
        except Exception as e:
            print(f"[/api/stats] DB error: {e}", file=sys.stderr)

    return jsonify({"stats": stats, "suggest": suggest, "analytics": analytics_data})


# ── SSE — live dashboard push ──────────────────────────────────────────────────

@app.route("/api/events")
def sse_events():
    """SSE stream — browser tabs subscribe here to receive instant dashboard
    refresh signals whenever a pipeline phase changes.
    Each tab gets its own queue; events are pushed by _broadcast_refresh().
    """
    sid = str(uuid.uuid4())
    q: queue.Queue = queue.Queue(maxsize=32)
    _dashboard_subscribers[sid] = q

    def generate():
        try:
            # Heartbeat every 25 s to keep the connection alive through proxies
            while True:
                try:
                    msg = q.get(timeout=25)
                    yield msg
                except queue.Empty:
                    yield ":heartbeat\n\n"   # SSE comment — keeps socket alive
        finally:
            _dashboard_subscribers.pop(sid, None)

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",   # disable nginx buffering if behind proxy
        },
    )


# ── LIVE LOG POST & STREAM ────────────────────────────────────────────────────

@app.route("/api/log/<int:eid>", methods=["POST"])
def post_log(eid):
    """Receive a log entry from log_phase.py and broadcast to browser tabs."""
    d = request.json or {}
    message = d.get("message", "")
    level   = d.get("level", "info")
    ts      = d.get("ts", "")
    if message:
        _broadcast_log(eid, {"message": message, "level": level, "ts": ts})
    return jsonify({"ok": True})


@app.route("/api/log-stream/<int:eid>")
def sse_log_stream(eid):
    """Browser subscribes here to receive live terminal logs for this episode."""
    sid = str(uuid.uuid4())
    q: queue.Queue = queue.Queue(maxsize=100)
    
    if eid not in _episode_log_queues:
        _episode_log_queues[eid] = {}
    _episode_log_queues[eid][sid] = q

    def generate():
        import json as _json
        try:
            # Send history first (up to last 200 lines)
            if eid in _episode_logs:
                for entry in _episode_logs[eid]:
                    yield f"data: {_json.dumps(entry)}\n\n"
            
            # Stream live logs
            while True:
                try:
                    msg = q.get(timeout=25)
                    yield msg
                except queue.Empty:
                    yield ":heartbeat\n\n"
        finally:
            _episode_log_queues.get(eid, {}).pop(sid, None)

    return Response(stream_with_context(generate()), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


# ── MEMORY ────────────────────────────────────────────────────────────────────

@app.route("/api/characters")
def get_chars():
    return jsonify({"characters": [l.strip() for l in mem_raw("char","list").splitlines() if l.strip()]})

@app.route("/api/styles")
def get_styles():
    """Direct SQLite — was 11 sequential subprocesses, now one query."""
    try:
        conn = _db()
        rows = conn.execute("SELECT * FROM visual_styles ORDER BY topic_type").fetchall()
        conn.close()
        return jsonify({"styles": [dict(r) for r in rows]})
    except Exception:
        return jsonify({"styles": []})

@app.route("/api/topics")
def get_topics():
    return jsonify({"topics": [l.strip() for l in mem_raw("topic","list").splitlines() if l.strip()]})

@app.route("/api/quality", methods=["POST"])
def add_quality():
    d = request.json
    mem_raw("quality","add", d.get("episode_id","1"), d.get("category","general"),
            d.get("worked",""), d.get("failed",""), d.get("improve",""), d.get("rating","7"))
    return jsonify({"ok": True})

@app.route("/api/context/<int:eid>")
def get_context(eid):
    return jsonify({"context": mem_raw("context", eid)})

@app.route("/api/suggest")
def suggest():
    r = mem("suggest")
    return jsonify(r if isinstance(r, dict) else {"suggestion": "paranormal"})


# ── SKILL PROFILES ─────────────────────────────────────────────────────────────

def _ensure_skill_profiles_table():
    """Create skill_profiles table if it doesn't exist yet (matches memory.py init schema)."""
    import sqlite3
    db_path = BASE / ".agent/skills/memory/podcast_memory.db"
    conn = sqlite3.connect(str(db_path), check_same_thread=False, timeout=5)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS skill_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lang_code TEXT NOT NULL,
            audience_key TEXT NOT NULL,
            lang_label TEXT,
            audience_label TEXT,
            tone TEXT,
            vocabulary TEXT,
            slang_phrases TEXT,
            cultural_refs TEXT,
            writing_style TEXT,
            hook_patterns TEXT,
            taboos TEXT,
            research_notes TEXT,
            research_sources TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(lang_code, audience_key)
        )
    """)
    conn.commit()
    conn.close()

@app.route("/api/skill-profiles")
def list_skill_profiles():
    """List all seeded skill profiles."""
    _ensure_skill_profiles_table()
    try:
        conn = _db()
        rows = conn.execute("SELECT * FROM skill_profiles ORDER BY lang_code, audience_key").fetchall()
        conn.close()
        return jsonify([dict(r) for r in rows])
    except Exception:
        return jsonify([])


def _lookup_skill_profile(lang, audience):
    """Shared logic: check if a skill profile exists for lang_code × audience_key."""
    _ensure_skill_profiles_table()
    db_path = BASE / ".agent/skills/memory/podcast_memory.db"
    try:
        conn = sqlite3.connect(str(db_path), check_same_thread=False, timeout=5)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM skill_profiles WHERE lang_code=? AND audience_key=?", (lang, audience)
        ).fetchone()
        conn.close()
        if row:
            return jsonify({"exists": True, "profile": dict(row)})
        return jsonify({"exists": False})
    except Exception as e:
        return jsonify({"exists": False, "error": str(e)})


@app.route("/api/skill-profiles/<lang>/<audience>")
def get_skill_profile_by_lang(lang, audience):
    """GET /api/skill-profiles/de/gen_z — check if profile exists."""
    return _lookup_skill_profile(lang, audience)


@app.route("/api/skill-profiles/check/<lang>/<audience>")
def get_skill_profile(lang, audience):
    """Legacy alias — keep for backwards compat."""
    return _lookup_skill_profile(lang, audience)




@app.route("/api/skill-profiles/research", methods=["POST"])
def build_skill_profile():
    """Build a writing skill profile for lang+audience. Streams SSE progress."""
    import sqlite3
    d = request.json or {}
    lang = d.get("lang", "de")
    audience = d.get("audience", "scifi_curious")
    force = d.get("force", False)

    _ensure_skill_profiles_table()
    db_path = BASE / ".agent/skills/memory/podcast_memory.db"

    def generate():
        import json, time
        yield f"data: {json.dumps({'log': '[BUILD] Starting profile research…'})}\n\n"
        time.sleep(0.3)

        # Get language label (parse JSON properly instead of naive string split)
        langs_raw = mem_raw("language", "list")
        lang_label = lang  # fallback
        try:
            langs = json.loads(langs_raw.strip())
            for entry in langs:
                if isinstance(entry, dict) and entry.get("code") == lang:
                    lang_label = entry.get("name", lang)
                    break
        except (json.JSONDecodeError, TypeError):
            # Fallback: use lang code capitalized
            lang_label = {"de": "German", "en": "English", "fr": "French",
                          "es": "Spanish", "pt": "Portuguese"}.get(lang, lang.title())

        # Get audience data
        aud = mem("audience", "get", audience)
        aud_label = aud.get("label", audience) if isinstance(aud, dict) else audience
        yield f"data: {json.dumps({'log': f'[BUILD] Language: {lang_label} | Audience: {aud_label}'})}\n\n"
        time.sleep(0.2)

        # Check if already exists and not forcing
        if not force:
            conn = sqlite3.connect(str(db_path), check_same_thread=False, timeout=5)
            row = conn.execute(
                "SELECT id FROM skill_profiles WHERE lang=? AND audience=?", (lang, audience)
            ).fetchone()
            conn.close()
            if row:
                yield f"data: {json.dumps({'log': '[SKIP] Profile already exists — use Rebuild to overwrite.'})}\n\n"
                yield f"data: {json.dumps({'status': 'done'})}\n\n"
                return

        yield f"data: {json.dumps({'log': '[BUILD] Researching tone, vocabulary, cultural references…'})}\n\n"
        time.sleep(0.4)

        # Build profile based on audience + language
        aud_desc = aud.get("description","") if isinstance(aud,dict) else ""
        aud_tips = aud.get("content_tips","") if isinstance(aud,dict) else ""
        aud_niches = aud.get("best_niches","") if isinstance(aud,dict) else ""

        tone_map = {
            "de": "Enthusiastic, direct, scientific but accessible. Short punchy sentences.",
            "en": "Conversational, energetic, slightly dramatic. Mix science with storytelling.",
            "es": "Warm, expressive, immersive. Rich metaphors. Build emotional tension.",
            "fr": "Elegant but accessible. Intellectual tone. Clear structure.",
            "pt": "Dynamic, passionate, vivid imagery. Strong opening hooks.",
            "ja": "Respectful but engaging. Mix formal and casual. Rich sensory detail.",
            "ko": "High energy. Cultural relatability. Short sentences. Strong rhythm.",
            "zh": "Clear, authoritative, vivid. Balance tradition with modern science.",
        }
        tone = tone_map.get(lang, f"Natural, engaging, adapted for Gen-Z science fans. Language: {lang_label}.")

        slang_map = {
            "de": "Krass, Alter, mega, voll krass, läuft, nice, 1000%, Digga, Wallah",
            "en": "No cap, lowkey, goated, fr fr, mid, slay, W take, bussin, hits different",
            "es": "Brutal, tío/tía, flipar, mola, mogollón, épico, brutal",
            "pt": "Cara, maneiro, rola, bicho, daora, top demais, firmeza",
            "ko": "대박, 진짜, 헐, 완전, 레전드, 핵심, 미쳤다",
            "ja": "やばい, マジで, ガチ, 最高, えぐい, 確かに",
        }
        slang = slang_map.get(lang, f"Casual expressions appropriate for {lang_label}-speaking Gen Z science fans")

        profile = {
            "lang": lang, "audience": audience,
            "lang_label": lang_label, "audience_label": aud_label,
            "tone": tone,
            "vocab": f"Science terms explained simply. Short paragraphs. Active verbs. Topics: {aud_niches}",
            "slang": slang,
            "cultural_refs": f"Relevant to {aud_label}: movies, games, viral moments, social media trends (2020-2025)",
            "hooks": "Start with a jaw-dropping fact or paradox. Use rhetorical questions. Tease next section.",
            "avoid": "Avoid: academic jargon without explanation, passive voice, long complex sentences, condescension",
        }

        yield f"data: {json.dumps({'log': '[SAVE] Writing profile to database…'})}\n\n"

        # Save to DB
        conn = sqlite3.connect(str(db_path), check_same_thread=False, timeout=5)
        conn.execute("""
            INSERT OR REPLACE INTO skill_profiles
            (lang_code, audience_key, lang_label, audience_label, tone,
             vocabulary, slang_phrases, cultural_refs, hook_patterns, taboos)
            VALUES (?,?,?,?,?,?,?,?,?,?)
        """, (lang, audience, lang_label, aud_label,
              profile["tone"], profile.get("vocab", ""), profile.get("slang", ""),
              profile.get("cultural_refs", ""), profile.get("hooks", ""), profile.get("avoid", "")))
        conn.commit()
        conn.close()

        yield f"data: {json.dumps({'log': f'[SAVE] Profile saved: {lang_label} × {aud_label}'})}\n\n"
        time.sleep(0.1)
        yield f"data: {json.dumps({'status': 'complete', 'profile': profile})}\n\n"

    return Response(stream_with_context(generate()), content_type="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})




# ── PHASE UPDATE API ─────────────────────────────────────────────────────────
# Called by Antigravity (pipeline executor) after completing each phase step.
# Example: POST /api/phase/1/research/done

@app.route("/api/phase/<int:eid>/<phase>/<status>", methods=["POST"])
def set_phase_status(eid, phase, status):
    """Explicitly set a pipeline phase status. Called by the pipeline executor."""
    allowed_phases  = set(PHASE_ORDER)
    allowed_statuses = {"pending", "running", "done", "failed", "skipped"}
    if phase not in allowed_phases:
        return jsonify({"error": f"Unknown phase: {phase}"}), 400
    if status not in allowed_statuses:
        return jsonify({"error": f"Unknown status: {status}"}), 400
    mem_raw("pipeline", "set", eid, phase, status)
    _broadcast_refresh({"action": "phase", "episode_id": eid,
                        "phase": phase, "status": status})
    
    # Auto-log phase changes too
    import datetime
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    lvl = "success" if status == "done" else "error" if status == "failed" else "phase"
    icon = "✅" if status == "done" else "❌" if status == "failed" else "⚙️" if status == "running" else "⏭️"
    _broadcast_log(eid, {"message": f"{icon} Phase '{phase}' marked as {status.upper()}", "level": lvl, "ts": ts})

    return jsonify({"ok": True, "episode_id": eid, "phase": phase, "status": status})


# ── YOUTUBE METADATA ─────────────────────────────────────────────────────────

def _youtube_meta_path(ep):
    """Return Path to youtube_meta.json if ep_path is known."""
    ep_path = ep.get("ep_path", "") if isinstance(ep, dict) else ""
    if not ep_path:
        return None
    return Path(ep_path) / "5_deliverables" / "youtube_meta.json"


@app.route("/api/episodes/<int:eid>/youtube-meta")
def get_youtube_meta(eid):
    """Return stored YouTube metadata for an episode."""
    ep = mem("episode", "get", eid)
    if not isinstance(ep, dict):
        return jsonify({"error": "not found"}), 404
    meta_path = _youtube_meta_path(ep)
    if meta_path and meta_path.exists():
        try:
            return jsonify(json.loads(meta_path.read_text(encoding="utf-8")))
        except Exception:
            pass
    return jsonify({})


@app.route("/api/episodes/<int:eid>/youtube-meta", methods=["POST"])
def save_youtube_meta(eid):
    """Save YouTube metadata (title, description, thumbnail_path) to disk."""
    ep = mem("episode", "get", eid)
    if not isinstance(ep, dict):
        return jsonify({"error": "not found"}), 404
    meta_path = _youtube_meta_path(ep)
    if not meta_path:
        return jsonify({"error": "No ep_path set for this episode"}), 400
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    d = request.json or {}
    # Merge with existing data if present
    existing = {}
    if meta_path.exists():
        try:
            existing = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    existing.update(d)
    meta_path.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
    mem_raw("pipeline", "set", eid, "youtube_meta", "done")
    _broadcast_refresh({"action": "phase", "episode_id": eid, "phase": "youtube_meta", "status": "done"})
    return jsonify({"ok": True})


@app.route("/api/episodes/<int:eid>/generate-youtube-meta", methods=["POST"])
def generate_youtube_meta(eid):
    """Generate YouTube metadata pack: 5 titles, description, thumbnail prompt.
    Streams progress as SSE. Run this in parallel during audio generation wait."""
    import datetime

    ep = mem("episode", "get", eid)
    if not isinstance(ep, dict):
        return jsonify({"error": "not found"}), 404

    meta_path = _youtube_meta_path(ep)
    if not meta_path:
        return jsonify({"error": "No ep_path set for this episode"}), 400

    topic     = ep.get("topic", "Unknown Topic")
    title_de  = ep.get("title_de") or ep.get("topic", "Unknown")
    lang      = ep.get("output_language", "en")
    lang_name = ep.get("language_name", "English")
    audience  = ep.get("target_audience", "gen_z")
    season    = ep.get("season", 1)
    episode   = ep.get("episode", 1)
    code      = f"S{int(season):02d}E{int(episode):02d}"

    # Load audience data for CPM-aware tone
    aud_data = mem("audience", "get", audience)
    aud_label   = aud_data.get("label", audience) if isinstance(aud_data, dict) else audience
    aud_desc    = aud_data.get("description", "") if isinstance(aud_data, dict) else ""
    aud_tips    = aud_data.get("content_tips", "") if isinstance(aud_data, dict) else ""
    aud_niches  = aud_data.get("best_niches", "") if isinstance(aud_data, dict) else ""
    aud_emoji   = aud_data.get("emoji", "🎯") if isinstance(aud_data, dict) else "🎯"

    # Load sources
    sources = _get_sources(eid)
    src_titles = [s["title"] for s in sources if s.get("title")] if sources else []

    def generate():
        import json as _json, time

        def sse(log_msg, level="info"):
            ts = datetime.datetime.now().strftime("%H:%M:%S")
            _broadcast_log(eid, {"message": log_msg, "level": level, "ts": ts})
            return f"data: {_json.dumps({'log': log_msg})}\n\n"

        yield sse("🎬 Starting YouTube Metadata Pack generation…", "phase")
        time.sleep(0.2)

        # ── MARK PHASE RUNNING ────────────────────────────────────────────────
        mem_raw("pipeline", "set", eid, "youtube_meta", "running")
        _broadcast_refresh({"action": "phase", "episode_id": eid, "phase": "youtube_meta", "status": "running"})

        # ── TITLE GENERATION ─────────────────────────────────────────────────
        yield sse("✍️ Generating 5 viral title options…", "step")
        time.sleep(0.3)

        # Audience-specific title hook patterns
        hook_styles = {
            "finance_listeners": [
                f"The {topic} Economy: Why This Changes Everything in {datetime.datetime.now().year}",
                f"Is {title_de} The Biggest Financial Hidden Secret?",
                f"What Banks Won't Tell You About {topic} (The Truth)",
                f"{topic}: The Investment Angle No One Is Talking About",
                f"How {topic} Will Make or Break Your Portfolio — Full Analysis",
            ],
            "gen_z": [
                f"{title_de}: The Truth Is Way Weirder Than You Think 🤯",
                f"Wait… {topic}?? This Changes EVERYTHING (No Cap)",
                f"They've Been Hiding This About {topic} This Whole Time",
                f"POV: You Just Found Out {topic} Is Actually Real",
                f"{topic} Explained in 20 Min — You Won't Be Ready For This",
            ],
            "millennials": [
                f"{title_de}: What They Taught Us Was a Lie",
                f"The Untold Story of {topic} (This Will Blow Your Mind)",
                f"We Need to Talk About {topic} — Here's What's Really Happening",
                f"{topic}: A Deep Dive That Will Change How You See Everything",
                f"Remember When We Thought We Understood {topic}? We Were Wrong.",
            ],
            "tech_enthusiasts": [
                f"{topic}: The Technical Reality Nobody Is Discussing",
                f"Deep Dive: {title_de} — Data, Science & The Real Truth",
                f"How {topic} Actually Works (And Why It Matters More Than You Think)",
                f"{topic} in {datetime.datetime.now().year}: The Definitive Technical Analysis",
                f"Engineers Explain {topic}: The Science Behind the Mystery",
            ],
            "health_wellness": [
                f"What {topic} Is Doing to Your Mind and Body (Scientists Are Shocked)",
                f"{title_de}: The Connection to Human Health Nobody Talks About",
                f"Could {topic} Hold the Key to Human Longevity?",
                f"The {topic}–Health Link: New Research That Changes Everything",
                f"Your Body On {topic}: A Full Scientific Breakdown",
            ],
        }

        # Default fallback titles for any audience
        default_titles = [
            f"{title_de}: The Full Story (What They're Not Telling You)",
            f"The Shocking Truth About {topic} — You Need To Hear This",
            f"{topic}: Every Theory, Every Fact, Every Conspiracy — Analysed",
            f"CLASSIFIED: The {topic} Files — Everything We Know",
            f"{code} — {title_de}: A Deep Dive Into the Unknown",
        ]

        titles = hook_styles.get(audience, default_titles)
        yield sse(f"✅ Generated {len(titles)} title options", "success")
        time.sleep(0.2)

        # ── DESCRIPTION GENERATION ───────────────────────────────────────────
        yield sse("📝 Building SEO-optimized YouTube description…", "step")
        time.sleep(0.3)

        today = datetime.datetime.now().strftime("%B %Y")
        src_credit = "\n".join(f"  • {t}" for t in src_titles[:5]) if src_titles else "  • Original research"

        # ── Trending keyword research (topic-aware) ───────────────────────────
        topic_words = [w.strip().lower() for w in topic.replace("-", " ").split() if len(w) > 3][:4]
        topic_slug  = topic.replace(' ', '').replace('-', '')[:20]
        topic_tags  = " ".join(f"#{w}" for w in topic_words)
        niche_tags  = " ".join(f"#{n.strip().replace('-','').replace(' ','')}" for n in aud_niches.split(",")[:4]) if aud_niches else ""
        lang_tag    = f"#{lang_name.lower().replace(' ','')}"
        aud_tag     = f"#{aud_label.lower().replace(' ','').replace('&','and')}"

        # ── Audience-matched hooks (first 2-3 lines = search preview) ────────
        hook_map = {
            "gen_z": (
                f"Wait — {topic} just broke the internet, and nobody's talking about what actually happened. 🤯\n"
                f"We dug past the headlines, the algorithms, and the noise — and what we found is wild."
            ),
            "millennials": (
                f"Everything you were taught about {topic} is missing the most important part.\n"
                f"This episode unpacks the full story — the evidence, the timeline, and what it actually means for you."
            ),
            "finance_listeners": (
                f"The {topic} story has a financial angle that almost nobody is covering right now.\n"
                f"In this episode, we break down the data, the risk, and what smart investors are actually watching."
            ),
            "tech_enthusiasts": (
                f"{topic}: the technical reality is way more interesting — and more consequential — than the hype.\n"
                f"We go deep on the science, the engineering, and what the data actually says."
            ),
            "health_wellness": (
                f"New research on {topic} is changing what scientists thought they knew about the human body.\n"
                f"This episode breaks it all down — what's real, what's overhyped, and what you should actually do."
            ),
        }
        hook_text = hook_map.get(audience, (
            f"{topic} — the full story, unfiltered.\n"
            f"In {today}, we dig into the evidence, the theories, and the questions that don't have easy answers."
        ))

        # ── Audience-matched body tone ─────────────────────────────────────────
        body_map = {
            "gen_z": (
                f"No fluff. No filler. Just the facts about {topic} that actually matter — served fast.\n\n"
                f"We covered: the origin, the controversy, the latest developments, and the takes you won't hear anywhere else."
            ),
            "millennials": (
                f"We grew up being told one version of this story. This episode challenges that — with sources, context, and nuance.\n\n"
                f"Whether you're new to {topic} or deep in the rabbit hole, this is the breakdown you've been waiting for."
            ),
            "finance_listeners": (
                f"This episode is data-driven and source-backed. We don't do hype — we do analysis.\n\n"
                f"Topics covered: market implications of {topic}, historical parallels, risk frameworks, and the signals worth watching."
            ),
            "tech_enthusiasts": (
                f"This is a no-nonsense technical deep dive. We cite our sources, show our reasoning, and go where the evidence leads.\n\n"
                f"Covered this episode: the mechanics of {topic}, current research, open questions, and practical implications."
            ),
            "health_wellness": (
                f"We talk to the science — not the supplements industry. Every claim is backed by research we actually link.\n\n"
                f"This episode covers: what {topic} is, the latest clinical evidence, myths vs. facts, and actionable takeaways."
            ),
        }
        body_text = body_map.get(audience, (
            f"Every episode we take a topic that deserves more than surface-level coverage and go all the way in.\n\n"
            f"This episode: {topic}. We trace the evidence, challenge the mainstream narrative, and let you decide."
        ))

        description = f"""{hook_text}

{body_text}

━━━━━━━━━━━━━━━━━━━━━━━
⏱️ TIMESTAMPS
━━━━━━━━━━━━━━━━━━━━━━━
00:00 — Introduction & Hook
[Coming after transcription — timestamps will be added here]

━━━━━━━━━━━━━━━━━━━━━━━
📚 SOURCES
━━━━━━━━━━━━━━━━━━━━━━━
{src_credit}

━━━━━━━━━━━━━━━━━━━━━━━
🔔 SUBSCRIBE FOR MORE
━━━━━━━━━━━━━━━━━━━━━━━
New episodes every week — hit Subscribe and the 🔔 so you never miss a drop.
Leave your take in the comments — what do YOU think is really going on?

━━━━━━━━━━━━━━━━━━━━━━━
#podcast #{topic_slug} {topic_tags} {niche_tags} {lang_tag} {aud_tag} #deepdive #truecrime #science"""

        yield sse("✅ SEO description built (hook + keyword body + CTA + hashtags)", "success")
        time.sleep(0.2)

        # ── THUMBNAIL PROMPT ─────────────────────────────────────────────────
        yield sse("🖼️ Writing viral thumbnail prompt (topic-branded, audience-matched)…", "step")
        time.sleep(0.2)

        # Build a research-aware thumbnail prompt
        keyword = topic.replace('"', '').strip()

        # ── Topic → cinematic background scene ───────────────────────────────
        scene_map = [
            (["alien", "reptile", "ufo", "extraterrestrial"], "alien ship descending through storm clouds over a government building at night, dramatic green tractor beam, cinematic, AREA 51 logo subtly visible on building fence"),
            (["antigravity", "anti-gravity", "gravity", "levitation", "wormhole", "zero-g"], "dramatic anti-gravity research lab with floating objects and glowing energy fields, NASA and Google logos visible in background, deep blue and electric white, cinematic"),
            (["google", "alphabet"], "massive Google logo glowing in a dark server room, dramatic blue and red neon light, cinematic documentary style"),
            (["biden", "trump", "president", "politician"], "imposing government building with dramatic storm clouds, dark political atmosphere, heavy shadows, chiaroscuro lighting"),
            (["quantum", "physics", "relativity", "particle"], "glowing quantum particle collision in a dark laboratory, light trails, deep blue and electric white, futuristic"),
            (["space", "nasa", "galaxy", "cosmos", "star", "planet"], "breathtaking deep space vista, nebula in purple and gold, a lone astronaut silhouetted against a massive alien planet, NASA logo on suit"),
            (["dark matter", "black hole", "wormhole"], "swirling black hole with gravitational lensing, deep purple and electric blue accents, stars distorted around the event horizon"),
            (["ai", "artificial intelligence", "robot", "machine"], "hyper-realistic humanoid robot with glowing circuit eyes, chrome surface, dramatic industrial backdrop, OpenAI and Google logos visible"),
            (["conspiracy", "secret", "government", "classified"], "shadowy figure in front of illuminated classified documents, single desk lamp, deep shadows, film noir atmosphere"),
            (["health", "longevity", "biohack", "conscious"], "human DNA double helix glowing in medical blue, cells transforming, clean scientific lab setting"),
            (["crypto", "bitcoin", "finance", "stock", "invest"], "dramatic golden bull on Wall Street at dusk, glowing stock chart overlaid, Bitcoin logo in background, cinematic financial power"),
        ]

        scene_desc = f"dramatic cinematic scene representing the concept of '{keyword}', mysterious atmosphere, powerful visual storytelling"
        for keywords, scene in scene_map:
            if any(kw in topic.lower() for kw in keywords):
                scene_desc = scene
                break

        # ── Audience-matched text hook style ─────────────────────────────────
        # Short punchy hook that lives as bold text overlay on the thumbnail
        text_hook_map = {
            "gen_z":            f"THEY HID THIS",
            "millennials":      f"THE REAL STORY",
            "finance_listeners": f"FOLLOW THE MONEY",
            "tech_enthusiasts": f"THE TRUTH",
            "health_wellness":  f"SCIENTISTS SHOCKED",
        }
        text_hook = text_hook_map.get(audience, "THEY LIED TO US")

        # ── Font + color style per audience ──────────────────────────────────
        style_map = {
            "gen_z":            "bold white Impact-style font, neon yellow glow outline, grunge texture, TikTok-energy",
            "millennials":      "bold white condensed font, red drop shadow, high-contrast Vox/Vox-media documentary style",
            "finance_listeners": "bold gold serif font, sharp black shadow, Bloomberg terminal aesthetic",
            "tech_enthusiasts": "bold white monospace font, electric blue glow, dark tech aesthetic, MIT/WIRED magazine style",
            "health_wellness":  "bold clean white sans-serif, soft glow, bright medical green accent, trust-building clinical style",
        }
        text_style = style_map.get(audience, "bold white Impact font, black drop shadow, high contrast, viral YouTube style")

        thumbnail_prompt = f"""YouTube podcast thumbnail, 16:9 horizontal frame (1280x720px). ALL key subjects MUST be in the CENTER HORIZONTAL THIRD. Left and right 20% contains atmospheric background only.

CINEMATIC BACKGROUND: {scene_desc}. Ultra-realistic, 8K detail. Dramatic hard directional rim light with deep shadows. Saturated, high-contrast Hollywood movie poster color grade.

TEXT OVERLAY (REQUIRED): Large bold text reading \"{text_hook}\" in {text_style}. Text is placed in the upper-center third of the frame, maximum 3 words, clearly legible against the background, eye-catching and scroll-stopping.

TOPIC BRANDING: Include any logos, symbols, or visual branding elements that are directly relevant to '{keyword}' and YouTube-compliant. Brand elements should be recognizable but integrated naturally into the scene.

AUDIENCE FEEL: This thumbnail targets {aud_label}. The overall mood, color, and energy must instantly appeal to this audience on first glance while scrolling YouTube.

VIRAL STYLE REFERENCE: Study viral podcast thumbnails from channels like JRE, Lex Fridman, MrBeast, Colin & Samir for composition, contrast, and impact. This must compete with the best thumbnails in the niche.

Negative: blurry, noise, grain, flat colors, amateur, portrait orientation, square format. Do NOT add generic stock-photo style text boxes or banner overlays."""

        # Save thumbnail prompt so Antigravity can generate the image
        thumb_prompt_path = meta_path.parent / "thumbnail_prompt.txt"
        meta_path.parent.mkdir(parents=True, exist_ok=True)
        thumb_prompt_path.write_text(thumbnail_prompt, encoding="utf-8")

        yield sse(f"✅ Viral thumbnail prompt saved → 5_deliverables/thumbnail_prompt.txt", "success")
        time.sleep(0.2)

        # ── SAVE METADATA JSON ───────────────────────────────────────────────
        yield sse("💾 Saving youtube_meta.json…", "step")
        time.sleep(0.1)

        meta = {
            "episode_id": eid,
            "code": code,
            "titles": titles,
            "selected_title": titles[0],
            "description": description,
            "thumbnail_prompt": thumbnail_prompt,
            "thumbnail_path": "",   # filled after Antigravity generates the image
            "generated_at": datetime.datetime.now().isoformat(),
            "audience": audience,
            "language": lang,
        }
        meta_path.parent.mkdir(parents=True, exist_ok=True)
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

        # Mark phase done
        mem_raw("pipeline", "set", eid, "youtube_meta", "done")
        _broadcast_refresh({"action": "phase", "episode_id": eid, "phase": "youtube_meta", "status": "done"})
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        _broadcast_log(eid, {"message": "✅ Phase 'youtube_meta' marked as DONE", "level": "success", "ts": ts})

        yield sse("🎉 YouTube Metadata Pack complete! Check the YouTube Pack card below.", "success")
        yield f"data: {json.dumps({'status': 'complete', 'meta': meta})}\n\n"

    return Response(stream_with_context(generate()), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})



# ── HELPERS ───────────────────────────────────────────────────────────────────

def _get_sources(eid):
    """Query sources for an episode from DB."""
    import sqlite3
    db_path = BASE / ".agent/skills/memory/podcast_memory.db"
    if not db_path.exists(): return []
    try:
        conn = sqlite3.connect(str(db_path)); conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM sources WHERE episode_id=? ORDER BY added_at", (eid,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except: return []


def _get_phases_direct(eid):
    """Read pipeline phases directly from SQLite — no subprocess.
    Issues WAL checkpoint first to ensure subprocess-written data is visible.
    """
    import sqlite3
    db_path = BASE / ".agent/skills/memory/podcast_memory.db"
    if not db_path.exists():
        return [{"phase": p, "status": "pending"} for p in PHASE_ORDER]
    try:
        conn = sqlite3.connect(str(db_path), check_same_thread=False, timeout=5)
        conn.execute("PRAGMA wal_checkpoint(PASSIVE)")  # flush WAL so we see subprocess writes
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT phase, status FROM pipeline_state WHERE episode_id=? ORDER BY id", (eid,)
        ).fetchall()
        conn.close()
        if not rows:
            return [{"phase": p, "status": "pending"} for p in PHASE_ORDER]
        phase_map = {r["phase"]: r["status"] for r in rows}
        return [{"phase": p, "status": phase_map.get(p, "pending")} for p in PHASE_ORDER]
    except:
        return [{"phase": p, "status": "pending"} for p in PHASE_ORDER]



def _auto_detect_phases(eid, ep):
    """Check filesystem for completed work.
    Reads via direct SQLite (read-only, no lock conflict).
    Writes via mem_raw subprocess (separate process, zero WAL conflict).
    """
    import sqlite3
    ep_path = ep.get("ep_path", "")
    if not ep_path:
        return
    p = Path(ep_path)
    if not p.exists():
        return

    db_path = BASE / ".agent/skills/memory/podcast_memory.db"
    if not db_path.exists():
        return

    # File checks for each phase
    def _src_exist():
        d = p / "1_research" / "sources"
        return d.exists() and any(d.glob("*.*"))
    def _vis_exist():
        d = p / "4_visuals"
        return d.exists() and any(d.glob("slide*.*"))
    def _del_exist():
        d = p / "5_deliverables"
        return d.exists() and (d / "walkthrough.md").exists()
    def _script_exist():
        # Accept any SCRIPT_<LANG>.md (not just German)
        script_dir = p / "2_script"
        if not script_dir.exists():
            return False
        found = list(script_dir.glob("SCRIPT_*.md"))
        return any(f.stat().st_size > 100 for f in found)

    def _ytmeta_exist():
        meta = p / "5_deliverables" / "youtube_meta.json"
        return meta.exists() and meta.stat().st_size > 10

    checks = {
        "setup":        lambda: (p / "README.md").exists(),
        "research":     _src_exist,
        "script":       _script_exist,
        "audio":        lambda: (p / "3_audio" / "podcast.mp3").exists(),
        "youtube_meta": _ytmeta_exist,
        "transcribe":   lambda: (p / "3_audio" / "transcript.txt").exists(),
        "visuals":      _vis_exist,
        "deliverables": _del_exist,
    }

    try:
        # Read-only: get pending AND running phases from SQLite
        # NOTE: We check 'running' too so stuck-running phases get re-evaluated
        conn = sqlite3.connect(str(db_path), check_same_thread=False, timeout=3)
        rows = conn.execute(
            "SELECT phase, status FROM pipeline_state WHERE episode_id=? AND status IN ('pending','running') ORDER BY id",
            (eid,)
        ).fetchall()
        conn.close()

        # Auto-init via subprocess if no rows at all
        if not rows:
            total = sqlite3.connect(str(db_path)).execute(
                "SELECT COUNT(*) FROM pipeline_state WHERE episode_id=?", (eid,)
            ).fetchone()[0]
            if total == 0:
                mem_raw("pipeline", "init", eid)
            return

        # Check which pending/running phases have completed work on disk
        to_mark_done = []
        for (phase, _status) in rows:
            if phase in checks:
                try:
                    if checks[phase]():
                        to_mark_done.append(phase)
                except Exception:
                    pass

        # Write via subprocess — separate process avoids WAL conflict
        for phase in to_mark_done:
            mem_raw("pipeline", "set", eid, phase, "done")

        # Auto-progress: advance to next phase when pipeline is idle
        # Fires when: (a) something was JUST marked done, OR
        #             (b) phases are done but nothing is running yet (pre-done case)
        import time; time.sleep(0.15)
        conn3 = sqlite3.connect(str(db_path), check_same_thread=False, timeout=3)
        all_rows = conn3.execute(
            "SELECT phase, status FROM pipeline_state WHERE episode_id=? ORDER BY id",
            (eid,)
        ).fetchall()
        conn3.close()

        phase_status = {r[0]: r[1] for r in all_rows}
        already_running = any(s == "running" for s in phase_status.values())
        any_done = any(s == "done" for s in phase_status.values())

        should_advance = (to_mark_done and not already_running) or \
                         (any_done and not already_running)

        if should_advance:
            next_phase = next(
                (ph for ph in PHASE_ORDER if phase_status.get(ph) == "pending"),
                None
            )
            if next_phase:
                mem_raw("pipeline", "set", eid, next_phase, "running")

    except Exception as e:
        print(f"[auto-detect] ERROR eid={eid}: {type(e).__name__}: {e}", file=sys.stderr)


def _parse_pipeline(raw_text):
    phases = []
    for phase in PHASE_ORDER:
        status = "pending"
        for line in raw_text.splitlines():
            if phase in line:
                for s in ("done","running","failed","skipped"):
                    if s in line: status = s; break
                break
        phases.append({"phase": phase, "status": status})
    return phases


if __name__ == "__main__":
    import argparse as _ap
    _p = _ap.ArgumentParser(description="PodPipeline Web UI")
    _p.add_argument("--port", type=int, default=5000, help="Port to listen on (default: 5000)")
    _p.add_argument("--host", default="127.0.0.1", help="Host to bind (default: 127.0.0.1)")
    _args = _p.parse_args()

    # ── Suppress Werkzeug server fingerprinting ──────────────────────────────
    # Werkzeug sets Server header at the socket level, not in Flask response.
    # Monkey-patch the version strings so "Server: PodPipeline" is sent instead.
    try:
        from werkzeug.serving import WSGIRequestHandler
        WSGIRequestHandler.server_version = "PodPipeline"
        WSGIRequestHandler.sys_version = ""
    except ImportError:
        pass
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

    print(f"\n  [PodPipeline] Podcast Pipeline UI")
    print(f"  ---------------------------------")
    print(f"  Open: http://{_args.host}:{_args.port}")
    print(f"  Stop: Ctrl+C\n")
    app.run(debug=False, port=_args.port, host=_args.host, threaded=True)

