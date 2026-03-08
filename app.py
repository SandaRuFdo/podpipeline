#!/usr/bin/env python3
"""
app.py — Local Web UI + API for Podcast Pipeline
Run: python app.py
Open: http://localhost:5000
"""

import sys, json, subprocess, os, time, queue, threading, uuid
from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory, Response, stream_with_context

BASE = Path(__file__).parent
MEM  = [sys.executable, str(BASE / ".agent/skills/memory/scripts/memory.py")]
UI   = BASE / "ui"

app = Flask(__name__, static_folder=str(UI), static_url_path="")
os.environ["PYTHONIOENCODING"] = "utf-8"

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

PHASE_ORDER = ["setup","research","script","audio","transcribe","visuals","deliverables","cinematic_setup"]


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
    langs = mem("language", "list")
    if isinstance(langs, list) and langs:
        return jsonify(langs)
    # Fallback — strong CPM + viral reach (no sub-$5 CPM markets)
    return jsonify([
        {"code":"en","name":"English",    "flag":"🇬🇧"},  # US 158M listeners (#1), $15–$50 CPM
        {"code":"es","name":"Spanish",    "flag":"🇪🇸"},  # LatAm fastest growth, US Hispanic $8–$20
        {"code":"pt","name":"Portuguese", "flag":"🇧🇷"},  # Brazil 51.8M listeners, #3 market
        {"code":"fr","name":"French",     "flag":"🇫🇷"},  # France + 300M African speakers, $10–$20
        {"code":"de","name":"German",     "flag":"🇩🇪"},  # Strong EU podcast culture, $18–$30 CPM
    ])


# ── AUDIENCES ─────────────────────────────────────────────────────────────────

@app.route("/api/audiences")
def get_audiences():
    result = mem("audience", "list")
    if isinstance(result, list) and result:
        return jsonify(result)
    # Fallback — top 5 CPM audiences
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



# ── SKILL PROFILES ────────────────────────────────────────────────────────────

RESEARCHER = [sys.executable, str(BASE / ".agent/skills/memory/scripts/skill_researcher.py")]

@app.route("/api/skill-profiles")
def list_skill_profiles():
    try:
        result = mem("skill-profile", "list")
        if isinstance(result, list):
            return jsonify(result)
        # Call researcher --list directly
        r = subprocess.run(RESEARCHER + ["--list", "en", "gen_z"],
                           capture_output=True, text=True, encoding="utf-8")
        return jsonify([])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/skill-profiles/<lang>/<audience>")
def get_skill_profile(lang, audience):
    """Check if profile exists. Returns profile or {exists: false}."""
    try:
        import sys as _sys
        _sys.path.insert(0, str(BASE / ".agent/skills/memory/scripts"))
        import memory as _mem
        profile = _mem.skill_profile_get(lang, audience)
        if profile:
            return jsonify({"exists": True, "profile": profile})
        return jsonify({"exists": False, "lang": lang, "audience": audience})
    except Exception as e:
        return jsonify({"exists": False, "error": str(e)})


@app.route("/api/skill-profiles/research", methods=["POST"])
def research_skill_profile():
    """
    Trigger profile research for a lang+audience combo (SSE streaming).
    Body: { "lang": "en", "audience": "gen_z", "force": false }
    """
    body = request.json or {}
    lang     = body.get("lang", "en")
    audience = body.get("audience", "gen_z")
    force    = body.get("force", False)

    job_id = str(uuid.uuid4())[:8]
    q: queue.Queue = queue.Queue()
    _jobs[job_id] = q

    def run():
        cmd = RESEARCHER + [lang, audience]
        if force:
            cmd.append("--force")
        try:
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, encoding="utf-8"
            )
            # Stream stderr ([INFO]/[BUILD]/[SAVE] lines) live
            for line in proc.stderr:
                q.put(line.rstrip())
            proc.wait()
            stdout = proc.stdout.read().strip()
            if proc.returncode == 0:
                try:
                    profile = json.loads(stdout)
                    q.put(f"[DONE] profile:{json.dumps(profile, ensure_ascii=False)}")
                except Exception:
                    q.put("[DONE] profile:null")
            else:
                q.put(f"[ERROR] Research failed (exit {proc.returncode})")
        except Exception as ex:
            q.put(f"[ERROR] {ex}")
        finally:
            q.put(None)  # sentinel

    threading.Thread(target=run, daemon=True).start()

    def stream():
        yield f"data: {json.dumps({'job': job_id, 'status': 'started'})}\n\n"
        while True:
            line = _jobs[job_id].get()
            if line is None:
                yield "data: {\"status\":\"done\"}\n\n"
                break
            if line.startswith("[DONE] profile:"):
                payload = line[len("[DONE] profile:"):]
                yield f"data: {json.dumps({'status':'complete','profile': json.loads(payload) if payload != 'null' else None})}\n\n"
            else:
                yield f"data: {json.dumps({'log': line})}\n\n"

    return Response(stream_with_context(stream()), mimetype="text/event-stream")


# ── EPISODES ──────────────────────────────────────────────────────────────────

@app.route("/api/episodes")
def list_episodes():
    raw = mem_raw("episode", "list")
    episodes = []
    for line in raw.splitlines():
        line = line.strip()
        if not line: continue
        import re
        m = re.match(r"S(\d+)E(\d+)\s+\[([^\]]+)\]\s+(.+)", line)
        if m:
            s, e = int(m[1]), int(m[2])
            ep = _ep_by_se(s, e)
            if ep: episodes.append(ep)
    return jsonify(episodes)


def _ep_by_se(season, episode):
    for i in range(1, 200):
        ep = mem("episode", "get", i)
        if not isinstance(ep, dict): break
        if ep.get("season") == season and ep.get("episode") == episode:
            return ep
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
    return jsonify({"episode": ep, "phases": phases, "sources": sources,
                    "context_preview": ctx[:800], "audience": audience})



@app.route("/api/episodes", methods=["POST"])
def create_episode():
    d = request.json
    required = ["season","episode","slug","title_de","topic"]
    if not all(k in d for k in required):
        return jsonify({"error": "Missing: " + ", ".join(required)}), 400

    lang_code = d.get("output_language", "de")
    lang_name  = d.get("language_name", "German")
    audience   = d.get("target_audience", "scifi_curious")
    job_id = str(uuid.uuid4())
    q: queue.Queue = queue.Queue()
    _jobs[job_id] = q

    def run():
        cmd = [
            sys.executable, str(BASE / "core" / "new_episode.py"),

            "--season", str(d["season"]), "--episode", str(d["episode"]),
            "--slug", d["slug"], "--title-de", d["title_de"],
            "--topic", d["topic"],
            "--force",  # always overwrite from web UI

        ]
        if d.get("title_en"): cmd += ["--title-en", d["title_en"]]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, encoding="utf-8", cwd=str(BASE))
        for line in proc.stdout:
            q.put({"type":"line","text":line.rstrip()})
        proc.wait()

        # Store language + audience in memory
        import re
        lines_so_far = list(q.queue)
        for item in lines_so_far:
            m = re.search(r"ID\s*[:：]\s*(\d+)", item.get("text",""))
            if m:
                eid = int(m.group(1))
                mem_raw("episode", "update", eid, "output_language", lang_code)
                mem_raw("episode", "update", eid, "language_name", lang_name)
                mem_raw("episode", "update", eid, "target_audience", d.get("target_audience", "scifi_curious"))
                mem_raw("pipeline", "init", eid)
                break

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
    return jsonify({"ok": True})


@app.route("/api/episodes/<int:eid>/pipeline/init", methods=["POST"])
def init_pipeline(eid):
    mem_raw("pipeline", "init", eid)
    return jsonify({"ok": True})


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
    return jsonify({
        "stats":     mem("stats")     if isinstance(mem("stats"), dict)     else {},
        "suggest":   mem("suggest")   if isinstance(mem("suggest"), dict)   else {},
        "analytics": mem("analytics","summary") if isinstance(mem("analytics","summary"), dict) else {}
    })


# ── MEMORY ────────────────────────────────────────────────────────────────────

@app.route("/api/characters")
def get_chars():
    return jsonify({"characters": [l.strip() for l in mem_raw("char","list").splitlines() if l.strip()]})

@app.route("/api/styles")
def get_styles():
    TYPES = ["space","paranormal","military","technology","biology","consciousness","time","ancient","ocean","simulation","ai"]
    styles = [s for t in TYPES for s in [mem("style","get",t)] if isinstance(s, dict)]
    return jsonify({"styles": styles})

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
        s = p / "2_script" / "SCRIPT_DE.md"
        return s.exists() and s.stat().st_size > 100

    checks = {
        "setup":        lambda: (p / "README.md").exists(),
        "research":     _src_exist,
        "script":       _script_exist,
        "audio":        lambda: (p / "3_audio" / "podcast.mp3").exists(),
        "transcribe":   lambda: (p / "3_audio" / "transcript.txt").exists(),
        "visuals":      _vis_exist,
        "deliverables": _del_exist,
    }

    try:
        # Read-only: get pending phases directly from SQLite
        conn = sqlite3.connect(str(db_path), check_same_thread=False, timeout=3)
        rows = conn.execute(
            "SELECT phase FROM pipeline_state WHERE episode_id=? AND status='pending' ORDER BY id",
            (eid,)
        ).fetchall()
        conn.close()
        print(f"[trace] eid={eid} pending_rows={[r[0] for r in rows]}", file=sys.stderr)

        # Auto-init via subprocess if no rows
        if not rows:
            total = sqlite3.connect(str(db_path)).execute(
                "SELECT COUNT(*) FROM pipeline_state WHERE episode_id=?", (eid,)
            ).fetchone()[0]
            if total == 0:
                mem_raw("pipeline", "init", eid)
            return

        # Check which pending phases have files on disk
        to_mark_done = []
        for (phase,) in rows:
            if phase in checks:
                try:
                    if checks[phase]():
                        to_mark_done.append(phase)
                except Exception:
                    pass

        print(f"[trace] to_mark_done={to_mark_done}", file=sys.stderr)
        # Write via subprocess — separate process avoids WAL conflict
        for phase in to_mark_done:
            r = mem_raw("pipeline", "set", eid, phase, "done")
            print(f"[trace] set {phase} done: {r[:50]}", file=sys.stderr)

        # Auto-progress: always ensure first pending phase is marked 'running'
        # Re-read state after subprocess writes (mem_raw is synchronous)
        import time; time.sleep(0.1)  # tiny delay to let WAL checkpoint
        conn3 = sqlite3.connect(str(db_path), check_same_thread=False, timeout=3)
        all_rows = conn3.execute(
            "SELECT phase, status FROM pipeline_state WHERE episode_id=? ORDER BY id",
            (eid,)
        ).fetchall()
        conn3.close()

        phase_status = {r[0]: r[1] for r in all_rows}
        any_done = any(s == "done" for s in phase_status.values())
        if any_done:
            next_phase = next(
                (ph for ph in PHASE_ORDER if phase_status.get(ph) == "pending"),
                None
            )
            if next_phase:
                print(f"[trace] marking next_phase={next_phase} as running", file=sys.stderr)
                r2 = mem_raw("pipeline", "set", eid, next_phase, "running")
                print(f"[trace] running result: {r2[:80]}", file=sys.stderr)



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

    print("\n  [PodPipeline] Podcast Pipeline UI")
    print("  ---------------------------------")
    print("  Open: http://localhost:5000")
    print("  Stop: Ctrl+C\n")
    app.run(debug=False, port=5000, host="127.0.0.1", threaded=True)

