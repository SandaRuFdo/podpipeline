#!/usr/bin/env python3
"""
Persistent Memory System for Podcast Pipeline
SQLite + FTS5 full-text search for accurate cross-episode memory.

Usage: python memory.py <command> [args]
"""

import sqlite3
import json
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "podcast_memory.db"


def get_db():
    db = sqlite3.connect(str(DB_PATH))
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA foreign_keys=ON")
    return db


def init_db():
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS episodes (
            id                    INTEGER PRIMARY KEY AUTOINCREMENT,
            season                INTEGER NOT NULL DEFAULT 1,
            episode               INTEGER NOT NULL,
            title_de              TEXT NOT NULL,
            title_en              TEXT,
            topic                 TEXT NOT NULL,
            output_language       TEXT NOT NULL DEFAULT 'de',
            language_name         TEXT NOT NULL DEFAULT 'German',
            notebook_id           TEXT,
            cinematic_notebook_id TEXT,
            cinematic_task_id     TEXT,
            ep_path               TEXT,
            audio_dur             REAL,
            status                TEXT DEFAULT 'planned',
            created_at            TEXT DEFAULT (datetime('now')),
            notes                 TEXT,
            target_audience       TEXT DEFAULT 'scifi_curious',
            UNIQUE(season, episode)
        );

        CREATE TABLE IF NOT EXISTS languages (
            code        TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            flag        TEXT,
            nlm_code    TEXT
        );

        CREATE TABLE IF NOT EXISTS audiences (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            key          TEXT UNIQUE NOT NULL,
            label        TEXT NOT NULL,
            emoji        TEXT,
            age_range    TEXT,
            cpm_low      INTEGER,
            cpm_high     INTEGER,
            listener_pct INTEGER,
            description  TEXT,
            content_tips TEXT,
            best_niches  TEXT,
            platforms    TEXT
        );

        CREATE TABLE IF NOT EXISTS sources (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            episode_id      INTEGER REFERENCES episodes(id) ON DELETE CASCADE,
            source_type     TEXT NOT NULL,
            url             TEXT,
            file_path       TEXT,
            title           TEXT,
            nlm_source_id   TEXT,
            language        TEXT DEFAULT 'en',
            quality         INTEGER,
            notes           TEXT,
            added_at        TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS characters (
            name            TEXT PRIMARY KEY,
            role            TEXT NOT NULL,
            personality     TEXT,
            catchphrases    TEXT DEFAULT '[]',
            analogy_style   TEXT,
            voice_notes     TEXT,
            updated_at      TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS quality_notes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            episode_id  INTEGER REFERENCES episodes(id) ON DELETE CASCADE,
            category    TEXT NOT NULL,
            worked      TEXT,
            failed      TEXT,
            improve     TEXT,
            rating      INTEGER,
            created_at  TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS visual_styles (
            topic_type  TEXT PRIMARY KEY,
            prompt      TEXT,
            palette     TEXT,
            mood        TEXT,
            notes       TEXT,
            updated_at  TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS timestamps (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            episode_id  INTEGER REFERENCES episodes(id) ON DELETE CASCADE,
            slide_num   INTEGER NOT NULL,
            start_time  TEXT NOT NULL,
            end_time    TEXT NOT NULL,
            start_sec   REAL,
            end_sec     REAL,
            label       TEXT,
            summary     TEXT,
            visual_file TEXT
        );

        CREATE TABLE IF NOT EXISTS topics (
            topic       TEXT PRIMARY KEY,
            category    TEXT,
            controversy INTEGER DEFAULT 5,
            appeal      INTEGER DEFAULT 5,
            sub_topics  TEXT DEFAULT '[]',
            episode_ids TEXT DEFAULT '[]',
            notes       TEXT,
            created_at  TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS prod_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            episode_id  INTEGER REFERENCES episodes(id) ON DELETE CASCADE,
            phase       TEXT NOT NULL,
            action      TEXT NOT NULL,
            details     TEXT,
            success     INTEGER DEFAULT 1,
            error       TEXT,
            ts          TEXT DEFAULT (datetime('now'))
        );

        CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts USING fts5(
            type, entity_id, title, content, tags,
            tokenize='porter unicode61'
        );

        CREATE TABLE IF NOT EXISTS pipeline_state (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            episode_id  INTEGER NOT NULL REFERENCES episodes(id) ON DELETE CASCADE,
            phase       TEXT NOT NULL,
            status      TEXT NOT NULL DEFAULT 'pending',
            started_at  TEXT,
            done_at     TEXT,
            error       TEXT,
            attempts    INTEGER DEFAULT 0,
            UNIQUE(episode_id, phase)
        );

        CREATE TABLE IF NOT EXISTS analytics (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            episode_id  INTEGER REFERENCES episodes(id) ON DELETE CASCADE,
            metric      TEXT NOT NULL,
            value       REAL NOT NULL,
            recorded_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS skill_profiles (
            id               TEXT PRIMARY KEY,
            lang_code        TEXT NOT NULL,
            audience_key     TEXT NOT NULL,
            lang_label       TEXT,
            audience_label   TEXT,
            tone             TEXT,
            vocabulary       TEXT,
            slang_phrases    TEXT DEFAULT '[]',
            cultural_refs    TEXT DEFAULT '[]',
            writing_style    TEXT,
            hook_patterns    TEXT DEFAULT '[]',
            taboos           TEXT DEFAULT '[]',
            research_notes   TEXT,
            research_sources TEXT,
            created_at       TEXT DEFAULT (datetime('now')),
            updated_at       TEXT DEFAULT (datetime('now')),
            UNIQUE(lang_code, audience_key)
        );

        -- ── FEATURE 2: Phase outputs tracking ─────────────────────────────────
        CREATE TABLE IF NOT EXISTS phase_outputs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            episode_id  INTEGER NOT NULL REFERENCES episodes(id) ON DELETE CASCADE,
            phase       TEXT NOT NULL,
            output_key  TEXT NOT NULL,
            output_val  TEXT,
            verified    INTEGER DEFAULT 0,
            created_at  TEXT DEFAULT (datetime('now'))
        );

        -- ── FEATURE 4: Session handoff state ──────────────────────────────────
        CREATE TABLE IF NOT EXISTS session_state (
            id                   INTEGER PRIMARY KEY AUTOINCREMENT,
            episode_id           INTEGER REFERENCES episodes(id) ON DELETE CASCADE,
            current_phase        TEXT,
            next_action          TEXT,
            resume_instruction   TEXT,
            saved_at             TEXT DEFAULT (datetime('now'))
        );

        -- ── FEATURE 5: Workflow contract ──────────────────────────────────────
        CREATE TABLE IF NOT EXISTS workflow_contract (
            phase            TEXT PRIMARY KEY,
            step_order       INTEGER NOT NULL,
            description      TEXT,
            required_inputs  TEXT DEFAULT '[]',
            required_outputs TEXT DEFAULT '[]',
            verify_cmd       TEXT,
            depends_on       TEXT DEFAULT '[]'
        );

        -- ── FEATURE 1: Profile evolution audit log ────────────────────────────
        CREATE TABLE IF NOT EXISTS profile_evolution_log (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            lang         TEXT NOT NULL,
            audience     TEXT NOT NULL,
            episode_id   INTEGER,
            quality_score INTEGER,
            field_changed TEXT,
            old_value    TEXT,
            new_value    TEXT,
            created_at   TEXT DEFAULT (datetime('now'))
        );
    """)
    db.commit()
    db.close()
    # Seed lookup tables
    _seed_languages()
    _seed_audiences()
    print(f"Database ready: {DB_PATH}")


LANGUAGES = [
    # Top 5: STRONG CPM + VIRAL REACH (2020–2024 data, no sub-$5 CPM markets)
    ("en", "English",    "🇬🇧", "en"),  # US 158M listeners (#1), $15–50 CPM
    ("es", "Spanish",    "🇪🇸", "es"),  # LatAm fastest growth, US Hispanic $8–20 CPM
    ("pt", "Portuguese", "🇧🇷", "pt"),  # Brazil 51.8M listeners, #3 global, $5–12 CPM
    ("fr", "French",     "🇫🇷", "fr"),  # France + 300M African speakers, $10–20 CPM
    ("de", "German",     "🇩🇪", "de"),  # Germany = strong EU podcast culture, $18–30 CPM
    # Dropped: Indonesian (CPM $2–5, too low) — Japanese (only 10% weekly listeners per YouGov)
]


def _seed_languages():
    db = get_db()
    for code, name, flag, nlm in LANGUAGES:
        db.execute(
            "INSERT INTO languages(code,name,flag,nlm_code) VALUES(?,?,?,?) ON CONFLICT(code) DO NOTHING",
            (code, name, flag, nlm)
        )
    db.commit(); db.close()


def language_list():
    db = get_db()
    rows = db.execute("SELECT * FROM languages ORDER BY name").fetchall()
    db.close()
    return [dict(r) for r in rows]


# ── AUDIENCES (Top 5 by CPM, 2024 research) ──────────────────────────────────

AUDIENCES = [
    {
        "key": "finance_listeners",
        "label": "Finance Listeners",
        "emoji": "💰",
        "age_range": "25–55",
        "cpm_low": 40,
        "cpm_high": 100,
        "listener_pct": 38,
        "description": "Highest-paid ad segment on ALL of YouTube ($40–100 CPM). 56% of podcast listeners earn $75k+. 5-year trend: this segment GREW fastest in absolute ad spend — finance podcast downloads up 180% from 2020–2024.",
        "content_tips": "Frame sci-fi through economic/investment lens. Asteroid mining profits, AI stock impact, crypto in space. Make it actionable and plausible. Real numbers attract this crowd.",
        "best_niches": "space-economy,AI,crypto,future-tech,resource-mining,biotech",
        "platforms": "YouTube,Apple Podcasts,Spotify,LinkedIn Audio"
    },
    {
        "key": "millennials",
        "label": "Millennials",
        "emoji": "💡",
        "age_range": "28–43",
        "cpm_low": 30,
        "cpm_high": 50,
        "listener_pct": 61,
        "description": "Largest podcast segment: 61% monthly listeners (5yr average). 35–44 age group is THE most popular for podcast consumption per Edison Research. Peak income years = premium advertisers. Stable growth 2020–2024.",
        "content_tips": "Deep dives welcome (30–60 min). Reference 90s/2000s culture. Balance optimism with realism. Strong narrative arc. Include expert credibility. Bonus episodes they’ll pay for.",
        "best_niches": "true-crime,finance,space,health,relationships,self-improvement,tech",
        "platforms": "Spotify,YouTube,Apple Podcasts,Instagram"
    },
    {
        "key": "tech_enthusiasts",
        "label": "Tech Enthusiasts",
        "emoji": "🖥️",
        "age_range": "25–45",
        "cpm_low": 28,
        "cpm_high": 50,
        "listener_pct": 42,
        "description": "CPM hit $29 in Aug 2024, trending upward 5 years straight. Brand loyalty extremely high — once they follow a show they stay. Coding/software niche peaks at $40–100. Podcast discovery: 72% via tech recommendation.",
        "content_tips": "Go deep on mechanics — they love technical accuracy. Cite real research. React to actual tech news. Early-access appeals. Use precise terminology. Reference real physics/CS.",
        "best_niches": "AI,quantum,robotics,simulation,space-tech,biotech,cyberpunk",
        "platforms": "YouTube,X/Twitter,Twitch,Podcasts"
    },
    {
        "key": "gen_z",
        "label": "Gen Z",
        "emoji": "⚡",
        "age_range": "13–27",
        "cpm_low": 25,
        "cpm_high": 45,
        "listener_pct": 59,
        "description": "FASTEST GROWING audience 2020–2024: monthly listeners jumped from 49% → 59% in 5 years (Edison Research). 82% take action on ads = highest conversion. 63% aged 13–24 listen monthly = 35M US listeners alone. Video podcast preference: 67%.",
        "content_tips": "Short cold opens (<60s). Cliffhangers every 4 min. React memes and TikTok-able moments. Authentic host voices only. No corporate tone. Social-native language.",
        "best_niches": "sci-fi,gaming,conspiracy,tech,space,paranormal,climate",
        "platforms": "YouTube Shorts,TikTok,Instagram Reels,YouTube"
    },
    {
        "key": "health_wellness",
        "label": "Health & Wellness",
        "emoji": "💊",
        "age_range": "35–65",
        "cpm_low": 24,
        "cpm_high": 40,
        "listener_pct": 55,
        "description": "5-year trend: 35–54 segment grew from 40% → 55% monthly listeners (Edison Research). Emotionally responsive, high supplement ad spend. 44% made purchase after podcast ad. Fastest ABSOLUTE growth over 5 years.",
        "content_tips": "Connect sci-fi to human health implications. Longevity science, anti-aging, consciousness, biohacking. Emotional storytelling. Personal stakes — what does this mean for YOUR body?",
        "best_niches": "consciousness,longevity,biohacking,space-medicine,simulation,paranormal",
        "platforms": "YouTube,Spotify,Apple Podcasts,Instagram"
    },
]

def _seed_audiences():
    db = get_db()
    for a in AUDIENCES:
        db.execute("""
            INSERT INTO audiences(key,label,emoji,age_range,cpm_low,cpm_high,listener_pct,description,content_tips,best_niches,platforms)
            VALUES(:key,:label,:emoji,:age_range,:cpm_low,:cpm_high,:listener_pct,:description,:content_tips,:best_niches,:platforms)
            ON CONFLICT(key) DO UPDATE SET
              label=excluded.label, cpm_low=excluded.cpm_low, cpm_high=excluded.cpm_high,
              description=excluded.description, content_tips=excluded.content_tips
        """, a)
    db.commit(); db.close()

def audience_list():
    db = get_db()
    rows = db.execute("SELECT * FROM audiences ORDER BY cpm_high DESC").fetchall()
    db.close()
    return [dict(r) for r in rows]

def audience_get(key):
    db = get_db()
    row = db.execute("SELECT * FROM audiences WHERE key=?", (key,)).fetchone()
    db.close()
    return dict(row) if row else None


# ── SKILL PROFILES ────────────────────────────────────────────────────────────

def skill_profile_get(lang, audience):
    """Return writing profile for lang+audience combo from the seeded profiles."""
    db = get_db()
    row = db.execute(
        "SELECT * FROM skill_profiles WHERE lang=? AND audience=?",
        (lang, audience)
    ).fetchone()
    db.close()
    return dict(row) if row else None


def skill_profile_list():
    """List all saved skill profiles."""
    db = get_db()
    rows = db.execute(
        "SELECT lang, audience, lang_label, audience_label, "
        "substr(tone,1,60) AS tone_preview, created_at "
        "FROM skill_profiles ORDER BY lang, audience"
    ).fetchall()
    db.close()
    return [dict(r) for r in rows]


def skill_profile_context(lang, audience):
    """Build a ready-to-use writing directive from the skill profile.
    
    Returns a formatted string that can be injected directly into
    script-writing prompts to guide tone, slang, cultural references, etc.
    """
    p = skill_profile_get(lang, audience)
    if not p:
        return f"[NO PROFILE] No writing profile found for {lang}/{audience}. Use default style."
    
    return f"""# WRITING PROFILE: {p.get('lang_label','?')} × {p.get('audience_label','?')}

## Tone & Voice
{p.get('tone', 'N/A')}

## Slang & Expressions (USE THESE naturally in dialogue)
{p.get('slang', 'N/A')}

## Vocabulary & Terminology
{p.get('vocab', 'N/A')}

## Cultural References (weave these in)
{p.get('cultural_refs', 'N/A')}

## Hook Strategies
{p.get('hooks', 'N/A')}

## AVOID (these kill engagement for this audience)
{p.get('avoid', 'N/A')}
"""




def _fts(db, type_, eid, title, content, tags=""):
    db.execute(
        "INSERT INTO memory_fts(type,entity_id,title,content,tags) VALUES(?,?,?,?,?)",
        (type_, str(eid), title, content, tags)
    )

def _to_sec(t):
    p = t.split(":")
    return int(p[0]) * 60 + int(p[1])


# ══════════════════════════════════════════════════════════════════════════════
# FEATURE 1 — EVOLVING QUALITY PROFILES
# Auto-update skill profile avoid/hooks based on episode quality scores
# ══════════════════════════════════════════════════════════════════════════════

def auto_evolve_profile(eid):
    """Read quality notes for episode, evolve the matching skill profile.
    
    - score < 7  → append failure notes to profile avoid list  
    - score >= 9 → promote success notes to hooks
    """
    db = get_db()
    ep = db.execute("SELECT * FROM episodes WHERE id=?", (eid,)).fetchone()
    if not ep:
        db.close(); return "Episode not found"
    
    lang     = ep["output_language"]
    audience = ep["target_audience"]
    
    notes = db.execute(
        "SELECT * FROM quality_notes WHERE episode_id=? ORDER BY created_at DESC",
        (eid,)
    ).fetchall()
    
    if not notes:
        db.close(); return f"No quality notes for episode {eid}"
    
    profile = db.execute(
        "SELECT * FROM skill_profiles WHERE lang=? AND audience=?",
        (lang, audience)
    ).fetchone()
    
    if not profile:
        db.close(); return f"No profile found for {lang}/{audience}"
    
    changes = []
    for n in notes:
        score = n["rating"] or 5
        
        if score < 7 and n["failed"]:
            old_avoid = profile["avoid"] or ""
            new_entry = f"\n• [Ep{eid} score={score}] {n['failed']}"
            if new_entry.strip() not in old_avoid:
                db.execute(
                    "UPDATE skill_profiles SET avoid=?, updated_at=datetime('now') WHERE lang=? AND audience=?",
                    (old_avoid + new_entry, lang, audience)
                )
                db.execute(
                    "INSERT INTO profile_evolution_log(lang,audience,episode_id,quality_score,field_changed,old_value,new_value) VALUES(?,?,?,?,?,?,?)",
                    (lang, audience, eid, score, "avoid", old_avoid[-100:], new_entry)
                )
                changes.append(f"avoid ← {n['failed'][:60]}")
        
        if score >= 9 and n["worked"]:
            old_hooks = profile["hooks"] or ""
            new_entry = f"\n• [Ep{eid} score={score}] {n['worked']}"
            if new_entry.strip() not in old_hooks:
                db.execute(
                    "UPDATE skill_profiles SET hooks=?, updated_at=datetime('now') WHERE lang=? AND audience=?",
                    (old_hooks + new_entry, lang, audience)
                )
                db.execute(
                    "INSERT INTO profile_evolution_log(lang,audience,episode_id,quality_score,field_changed,old_value,new_value) VALUES(?,?,?,?,?,?,?)",
                    (lang, audience, eid, score, "hooks", old_hooks[-100:], new_entry)
                )
                changes.append(f"hooks ← {n['worked'][:60]}")
    
    db.commit(); db.close()
    
    if changes:
        return f"Profile {lang}/{audience} evolved:\n" + "\n".join(f"  • {c}" for c in changes)
    return f"Profile {lang}/{audience} — no evolution needed (scores in range)"


# ══════════════════════════════════════════════════════════════════════════════
# FEATURE 2 — PHASE OUTPUTS TRACKING
# Record what each phase produced, with optional filesystem verification
# ══════════════════════════════════════════════════════════════════════════════

def phase_output_set(eid, phase, key, value, verify=False):
    """Record a phase output. If verify=True, check the path actually exists."""
    db = get_db()
    verified = 0
    if verify:
        import os
        verified = 1 if os.path.exists(str(value)) else 0
    
    db.execute(
        """INSERT INTO phase_outputs(episode_id, phase, output_key, output_val, verified)
           VALUES(?,?,?,?,?)
           ON CONFLICT DO UPDATE SET output_val=excluded.output_val, 
           verified=excluded.verified, created_at=datetime('now')""",
        (eid, phase, key, str(value), verified)
    )
    db.commit(); db.close()
    status = "✅ verified" if verified else ("⚠️ not found" if verify else "📝 recorded")
    print(f"[{phase}] {key} = {str(value)[:80]} {status}")


def phase_output_get(eid, phase=None):
    """Get all outputs for an episode, optionally filtered by phase."""
    db = get_db()
    if phase:
        rows = db.execute(
            "SELECT * FROM phase_outputs WHERE episode_id=? AND phase=? ORDER BY created_at",
            (eid, phase)
        ).fetchall()
    else:
        rows = db.execute(
            "SELECT * FROM phase_outputs WHERE episode_id=? ORDER BY phase, created_at",
            (eid,)
        ).fetchall()
    db.close()
    return [dict(r) for r in rows]


# ══════════════════════════════════════════════════════════════════════════════
# FEATURE 3 — SMART CONTEXT (FTS-FILTERED)
# Topic-aware context — only relevant past episodes, top-rated sources, profile
# ══════════════════════════════════════════════════════════════════════════════

def smart_context(eid):
    """Build laser-targeted context for an episode using FTS topic search.
    
    Returns focused context: characters + skill profile + similar past episodes
    + top-rated sources for this topic + avoid list from quality failures.
    """
    db = get_db()
    ep = db.execute("SELECT * FROM episodes WHERE id=?", (eid,)).fetchone()
    if not ep:
        db.close()
        return build_context(eid)  # fallback
    
    topic = ep["topic"] or ""
    lang  = ep["output_language"]
    aud   = ep["target_audience"]
    
    lines = [f"# SMART CONTEXT — Episode {eid}: {ep['title_de']}",
             f"Topic: {topic} | Lang: {lang} | Audience: {aud}", ""]
    
    # 1. Characters (always needed)
    chars = db.execute("SELECT name, role, personality, voice_notes FROM characters").fetchall()
    if chars:
        lines.append("## 🎭 Characters")
        for c in chars:
            lines.append(f"**{c['name']}** ({c['role']}): {c['personality'] or ''}")
            if c['voice_notes']: lines.append(f"  Voice: {c['voice_notes']}")
        lines.append("")
    
    # 2. Skill profile for this episode
    profile = db.execute(
        "SELECT * FROM skill_profiles WHERE lang=? AND audience=?",
        (lang, aud)
    ).fetchone()
    if profile:
        lines.append(f"## ✍️ Writing Profile: {profile.get('lang_label','?')} × {profile.get('audience_label','?')}")
        lines.append(f"Tone: {(profile['tone'] or '')[:200]}")
        lines.append(f"Slang: {(profile['slang'] or '')[:200]}")
        lines.append(f"Avoid: {(profile['avoid'] or '')[:200]}")
        lines.append("")
    
    # 3. FTS: find similar past episodes
    try:
        topic_words = " OR ".join(w for w in topic.split() if len(w) > 3)
        similar = db.execute(
            """SELECT e.id, e.title_de, e.topic, e.status
               FROM episodes e
               JOIN memory_fts m ON m.entity_id = CAST(e.id AS TEXT)
               WHERE m.content MATCH ? AND e.id != ?
               LIMIT 3""",
            (topic_words, eid)
        ).fetchall() if topic_words else []
        
        if similar:
            lines.append("## 📺 Similar Past Episodes (avoid repetition)")
            for s in similar:
                lines.append(f"  S?E? [{s['status']}] {s['title_de']} — {s['topic']}")
            lines.append("")
    except Exception:
        pass
    
    # 4. Top-rated sources for related topics
    top_sources = db.execute(
        """SELECT s.title, s.url, s.quality, s.source_type
           FROM sources s JOIN episodes e ON s.episode_id = e.id
           WHERE s.quality >= 4 AND (e.topic LIKE ? OR e.topic LIKE ?)
           ORDER BY s.quality DESC LIMIT 5""",
        (f"%{topic[:20]}%", f"%{topic.split()[0] if topic else ''}%")
    ).fetchall()
    
    if top_sources:
        lines.append("## ⭐ Top-Rated Sources (reuse these)")
        for s in top_sources:
            lines.append(f"  ★{s['quality']} [{s['source_type']}] {s['title'] or s['url'] or 'N/A'}")
        lines.append("")
    
    # 5. Recent quality failures for this profile
    fails = db.execute(
        """SELECT qn.failed, qn.rating 
           FROM quality_notes qn JOIN episodes e ON qn.episode_id = e.id
           WHERE e.output_language=? AND e.target_audience=? AND qn.rating < 7
           ORDER BY qn.created_at DESC LIMIT 3""",
        (lang, aud)
    ).fetchall()
    
    if fails:
        lines.append("## ⛔ Recent Quality Failures (AVOID these)")
        for f in fails:
            lines.append(f"  [score={f['rating']}] {f['failed']}")
        lines.append("")
    
    db.close()
    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════════════
# FEATURE 4 — SESSION HANDOFF
# Save/load pipeline state so any new session can resume exactly where left off
# ══════════════════════════════════════════════════════════════════════════════

def session_save(eid, phase, next_action, resume_instruction):
    """Save current pipeline state for session handoff."""
    import json as _json
    db = get_db()
    db.execute(
        "INSERT INTO session_state(episode_id, current_phase, next_action, resume_instruction) VALUES(?,?,?,?)",
        (eid, phase, next_action, resume_instruction)
    )
    db.commit()
    
    # Also write a human-readable JSON file to the episode folder
    ep = db.execute("SELECT ep_path FROM episodes WHERE id=?", (eid,)).fetchone()
    db.close()
    
    state = {
        "episode_id": eid,
        "current_phase": phase,
        "next_action": next_action,
        "resume_instruction": resume_instruction,
        "saved_at": __import__("datetime").datetime.now().isoformat()
    }
    
    # Write to project root as well, so it's always findable
    import os
    state_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))))), "session_state.json")
    
    with open(state_path, "w", encoding="utf-8") as f:
        _json.dump(state, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Session saved — Episode {eid}, phase '{phase}'")
    print(f"   Next: {next_action[:100]}")
    print(f"   Resume: {resume_instruction[:100]}")


def session_load():
    """Load the latest saved session state."""
    import os, json as _json
    state_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))))), "session_state.json")
    
    if not os.path.exists(state_path):
        return None
    
    with open(state_path, encoding="utf-8") as f:
        return _json.load(f)


def session_clear():
    """Clear the session state (call after episode is complete)."""
    import os
    state_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))))), "session_state.json")
    
    if os.path.exists(state_path):
        os.remove(state_path)
        print("Session state cleared.")
    else:
        print("No session state to clear.")


# ══════════════════════════════════════════════════════════════════════════════
# FEATURE 5 — WORKFLOW CONTRACT ENFORCEMENT
# Verify all preconditions before a phase starts — blocks skipping steps
# ══════════════════════════════════════════════════════════════════════════════

_CONTRACT = {
    "setup":         {"order":1, "depends_on":[],
                      "inputs":[], "outputs":["ep_path"],
                      "desc":"Create episode folder structure + register in memory"},
    "research":      {"order":2, "depends_on":["setup"],
                      "inputs":["ep_path"], "outputs":["1_research/sources"],
                      "desc":"Find YouTube sources, download subtitles, add to NotebookLM"},
    "script":        {"order":3, "depends_on":["research"],
                      "inputs":["1_research/sources","skill_profile"],
                      "outputs":["2_script/SCRIPT_DE.md","2_script/SCRIPT_EN.md"],
                      "desc":"Write script using skill profile — target lang + English"},
    "audio":         {"order":4, "depends_on":["script"],
                      "inputs":["2_script/SCRIPT_DE.md","notebook_id"],
                      "outputs":["3_audio/podcast.mp3"],
                      "desc":"Generate podcast via NotebookLM, download MP3"},
    "transcribe":    {"order":5, "depends_on":["audio"],
                      "inputs":["3_audio/podcast.mp3"],
                      "outputs":["3_audio/transcript.txt"],
                      "desc":"Transcribe with Whisper, generate timestamps"},
    "visuals":       {"order":6, "depends_on":["transcribe"],
                      "inputs":["3_audio/transcript.txt","5_deliverables/SLIDE_SOURCE.md"],
                      "outputs":["4_visuals"],
                      "desc":"Generate 16:9 cinematic images in parallel batches"},
    "deliverables":  {"order":7, "depends_on":["visuals"],
                      "inputs":["4_visuals"],
                      "outputs":["5_deliverables/walkthrough.md"],
                      "desc":"Build CapCut walkthrough + register in memory"},
    "cinematic_setup":{"order":8, "depends_on":["research"],
                       "inputs":["1_research/sources"],
                       "outputs":["cinematic_notebook_id"],
                       "desc":"Create English-only NotebookLM notebook for cinematic video"},
}

def _seed_contract():
    """Seed the workflow_contract table if empty."""
    import json
    db = get_db()
    count = db.execute("SELECT COUNT(*) FROM workflow_contract").fetchone()[0]
    if count == 0:
        for phase, c in _CONTRACT.items():
            db.execute(
                "INSERT OR REPLACE INTO workflow_contract(phase,step_order,description,required_inputs,required_outputs,depends_on) VALUES(?,?,?,?,?,?)",
                (phase, c["order"], c["desc"],
                 json.dumps(c["inputs"]), json.dumps(c["outputs"]),
                 json.dumps(c["depends_on"]))
            )
        db.commit()
    db.close()


def contract_verify(eid, phase):
    """Verify all preconditions for a phase before starting.
    
    Returns a dict: {ok: bool, issues: [...], ready: [...]}
    Prints a clear summary — use this at the start of every phase.
    """
    import json, os
    _seed_contract()
    
    if phase not in _CONTRACT:
        print(f"❌ Unknown phase: {phase}")
        return {"ok": False, "issues": [f"Unknown phase: {phase}"]}
    
    c = _CONTRACT[phase]
    db = get_db()
    ep = db.execute("SELECT * FROM episodes WHERE id=?", (eid,)).fetchone()
    
    issues = []
    ready  = []
    
    if not ep:
        db.close()
        print(f"❌ Episode {eid} not found")
        return {"ok": False, "issues": ["Episode not found"]}
    
    ep_path = ep["ep_path"] or ""
    
    # Check dependend phases are done
    pipeline = {r["phase"]: r["status"] 
                for r in db.execute("SELECT phase,status FROM pipeline_state WHERE episode_id=?", (eid,)).fetchall()}
    
    for dep in c["depends_on"]:
        dep_status = pipeline.get(dep, "pending")
        if dep_status not in ("done", "skipped"):
            issues.append(f"Phase '{dep}' not complete (status: {dep_status})")
        else:
            ready.append(f"Phase '{dep}' ✅")
    
    # Check required input files
    for inp in c["inputs"]:
        if inp in ("ep_path", "notebook_id", "skill_profile", "cinematic_notebook_id"):
            # Check DB field
            val = ep[inp] if inp in ep.keys() else None
            if not val:
                issues.append(f"DB field '{inp}' is not set")
            else:
                ready.append(f"{inp} = {str(val)[:50]} ✅")
        elif ep_path:
            full = os.path.join(ep_path, inp)
            if os.path.exists(full):
                ready.append(f"{inp} ✅")
            else:
                issues.append(f"Missing: {full}")
    
    db.close()
    ok = len(issues) == 0
    
    print(f"\n{'✅ CONTRACT OK' if ok else '❌ CONTRACT FAILED'} — Phase '{phase}' (Ep {eid})")
    if ready:
        for r in ready: print(f"  ✓ {r}")
    if issues:
        print(f"\n  BLOCKING ISSUES:")
        for i in issues: print(f"  ✗ {i}")
    print()
    
    return {"ok": ok, "issues": issues, "ready": ready}


# ══════════════════════════════════════════════════════════════════════════════
# FEATURE 6 — PARALLEL PHASE DETECTION
# Show which phases can run simultaneously right now
# ══════════════════════════════════════════════════════════════════════════════

def parallel_opportunities(eid):
    """Return phases that can run RIGHT NOW in parallel.
    
    A phase is ready if all its dependencies are done/skipped AND it's pending.
    Returns groups of phases that can fire simultaneously.
    """
    _seed_contract()
    db = get_db()
    
    pipeline = {r["phase"]: r["status"]
                for r in db.execute("SELECT phase,status FROM pipeline_state WHERE episode_id=?", (eid,)).fetchall()}
    db.close()
    
    ready_now = []
    blocked   = []
    
    for phase, c in _CONTRACT.items():
        status = pipeline.get(phase, "pending")
        if status in ("done", "skipped"):
            continue
        
        deps_done = all(pipeline.get(d, "pending") in ("done", "skipped") for d in c["depends_on"])
        
        if deps_done:
            ready_now.append({"phase": phase, "order": c["order"], "desc": c["desc"]})
        else:
            missing_deps = [d for d in c["depends_on"] if pipeline.get(d, "pending") not in ("done","skipped")]
            blocked.append({"phase": phase, "waiting_for": missing_deps})
    
    ready_now.sort(key=lambda x: x["order"])
    
    print(f"\n⚡ PARALLEL OPPORTUNITIES — Episode {eid}")
    if ready_now:
        print(f"\n  🟢 CAN START NOW ({len(ready_now)} phases):")
        for r in ready_now:
            print(f"     [{r['order']}] {r['phase']:20} — {r['desc']}")
        if len(ready_now) > 1:
            print(f"\n  💡 TIP: Fire ALL {len(ready_now)} simultaneously for maximum speed!")
    else:
        print("  No phases ready to start right now.")
    
    if blocked:
        print(f"\n  🔴 BLOCKED ({len(blocked)} phases):")
        for b in blocked:
            print(f"     {b['phase']:20} → waiting for: {', '.join(b['waiting_for'])}")
    print()
    
    return {"ready": ready_now, "blocked": blocked}




# ── EPISODES ─────────────────────────────────────────────────────────────────

def episode_add(season, ep, title_de, topic, title_en=None, notebook_id=None, output_language="de", language_name="German"):
    db = get_db()
    cur = db.execute(
        "INSERT INTO episodes(season,episode,title_de,title_en,topic,notebook_id,output_language,language_name) VALUES(?,?,?,?,?,?,?,?)",
        (season, ep, title_de, title_en, topic, notebook_id, output_language, language_name)
    )
    eid = cur.lastrowid
    _fts(db, "episode", eid, title_de, f"{topic} {title_en or ''}", f"S{season:02d}E{ep:02d}")
    db.commit(); db.close()
    print(f"Episode S{season:02d}E{ep:02d} registered (ID:{eid})")
    return eid


def episode_update(eid, **kw):
    VALID_COLS = frozenset({
        "title_de","title_en","topic","output_language","language_name",
        "target_audience","notebook_id","cinematic_notebook_id","cinematic_task_id",
        "ep_path","audio_dur","status","notes"
    })
    db = get_db()
    # Whitelist columns — never interpolate user-supplied keys directly
    fields = [(k, v) for k, v in kw.items() if k in VALID_COLS]
    if fields:
        # All column names are from a hard-coded frozenset — safe to interpolate
        sets = ", ".join(k + "=?" for k, _ in fields)  # nosec B608
        vals = [v for _, v in fields] + [eid]
        db.execute("UPDATE episodes SET " + sets + " WHERE id=?", vals)  # nosec B608
        db.commit()
    db.close()
    print("Updated.")



def episode_list(season=None):
    db = get_db()
    # Use pre-built safe query strings — no user input goes into SQL structure
    if season:
        q = "SELECT * FROM episodes WHERE season=? ORDER BY season,episode"  # nosec B608
        rows = db.execute(q, (season,)).fetchall()
    else:
        q = "SELECT * FROM episodes ORDER BY season,episode"  # nosec B608
        rows = db.execute(q).fetchall()
    db.close()
    return [dict(r) for r in rows]



def episode_get(eid):
    db = get_db()
    ep = dict(db.execute("SELECT * FROM episodes WHERE id=?", (eid,)).fetchone())
    ep["sources"]    = [dict(r) for r in db.execute("SELECT * FROM sources WHERE episode_id=?", (eid,)).fetchall()]
    ep["timestamps"] = [dict(r) for r in db.execute("SELECT * FROM timestamps WHERE episode_id=? ORDER BY slide_num", (eid,)).fetchall()]
    ep["quality"]    = [dict(r) for r in db.execute("SELECT * FROM quality_notes WHERE episode_id=?", (eid,)).fetchall()]
    ep["log"]        = [dict(r) for r in db.execute("SELECT * FROM prod_log WHERE episode_id=? ORDER BY ts", (eid,)).fetchall()]
    db.close()
    return ep


# ── SOURCES ───────────────────────────────────────────────────────────────────

def source_add(eid, stype, title, url=None, file_path=None, language="en", nlm_id=None):
    db = get_db()
    cur = db.execute(
        "INSERT INTO sources(episode_id,source_type,url,file_path,title,nlm_source_id,language) VALUES(?,?,?,?,?,?,?)",
        (eid, stype, url, file_path, title, nlm_id, language)
    )
    sid = cur.lastrowid
    _fts(db, "source", sid, title, f"{url or ''} {file_path or ''}", f"{stype} {language}")
    db.commit(); db.close()
    return sid


def source_rate(sid, rating, notes=None):
    db = get_db()
    db.execute("UPDATE sources SET quality=?,notes=? WHERE id=?", (rating, notes, sid))
    db.commit(); db.close()
    print("Rated.")


# ── CHARACTERS ────────────────────────────────────────────────────────────────

def char_set(name, role, personality, catchphrases=None, analogy_style=None, voice_notes=None):
    db = get_db()
    db.execute("""
        INSERT INTO characters(name,role,personality,catchphrases,analogy_style,voice_notes,updated_at)
        VALUES(?,?,?,?,?,?,datetime('now'))
        ON CONFLICT(name) DO UPDATE SET
            role=excluded.role, personality=excluded.personality,
            catchphrases=excluded.catchphrases, analogy_style=excluded.analogy_style,
            voice_notes=excluded.voice_notes, updated_at=datetime('now')
    """, (name, role, personality,
          json.dumps(catchphrases or [], ensure_ascii=False),
          analogy_style, voice_notes))
    _fts(db, "character", name, name, f"{personality} {analogy_style or ''}", role)
    db.commit(); db.close()
    print(f"Character '{name}' saved.")


def char_get(name):
    db = get_db()
    row = db.execute("SELECT * FROM characters WHERE name=?", (name,)).fetchone()
    db.close()
    if not row: return None
    d = dict(row)
    d["catchphrases"] = json.loads(d["catchphrases"]) if d["catchphrases"] else []
    return d


def char_list():
    db = get_db()
    rows = db.execute("SELECT * FROM characters ORDER BY name").fetchall()
    db.close()
    return [dict(r) for r in rows]


# ── QUALITY ───────────────────────────────────────────────────────────────────

def quality_add(eid, category, worked=None, failed=None, improve=None, rating=None):
    db = get_db()
    cur = db.execute(
        "INSERT INTO quality_notes(episode_id,category,worked,failed,improve,rating) VALUES(?,?,?,?,?,?)",
        (eid, category, worked, failed, improve, rating)
    )
    qid = cur.lastrowid
    _fts(db, "quality", qid, f"E{eid} {category}", f"{worked or ''} {failed or ''} {improve or ''}", category)
    db.commit(); db.close()
    return qid


# ── VISUAL STYLES ─────────────────────────────────────────────────────────────

def style_set(topic_type, prompt, palette=None, mood=None, notes=None):
    db = get_db()
    db.execute("""
        INSERT INTO visual_styles(topic_type,prompt,palette,mood,notes,updated_at)
        VALUES(?,?,?,?,?,datetime('now'))
        ON CONFLICT(topic_type) DO UPDATE SET
            prompt=excluded.prompt, palette=excluded.palette,
            mood=excluded.mood, notes=excluded.notes, updated_at=datetime('now')
    """, (topic_type, prompt, palette, mood, notes))
    db.commit(); db.close()
    print(f"Style '{topic_type}' saved.")


def style_get(topic_type):
    db = get_db()
    row = db.execute("SELECT * FROM visual_styles WHERE topic_type=?", (topic_type,)).fetchone()
    db.close()
    return dict(row) if row else None


# ── TIMESTAMPS ────────────────────────────────────────────────────────────────

def timestamp_add(eid, slide_num, start, end, label, summary, visual_file=None):
    db = get_db()
    db.execute(
        "INSERT INTO timestamps(episode_id,slide_num,start_time,end_time,start_sec,end_sec,label,summary,visual_file) VALUES(?,?,?,?,?,?,?,?,?)",
        (eid, slide_num, start, end, _to_sec(start), _to_sec(end), label, summary, visual_file)
    )
    db.commit(); db.close()


def timestamp_list(eid):
    db = get_db()
    rows = db.execute("SELECT * FROM timestamps WHERE episode_id=? ORDER BY slide_num", (eid,)).fetchall()
    db.close()
    return [dict(r) for r in rows]


# ── TOPICS ────────────────────────────────────────────────────────────────────

def topic_add(topic, category, controversy=5, appeal=5, sub_topics=None):
    db = get_db()
    db.execute("""
        INSERT INTO topics(topic,category,controversy,appeal,sub_topics)
        VALUES(?,?,?,?,?)
        ON CONFLICT(topic) DO UPDATE SET
            category=excluded.category, controversy=excluded.controversy,
            appeal=excluded.appeal, sub_topics=excluded.sub_topics
    """, (topic, category, controversy, appeal, json.dumps(sub_topics or [], ensure_ascii=False)))
    _fts(db, "topic", topic, topic, f"{category} {' '.join(sub_topics or [])}", category)
    db.commit(); db.close()
    print(f"Topic '{topic}' registered.")


def topic_check(topic):
    db = get_db()
    row = db.execute("SELECT * FROM topics WHERE topic=?", (topic,)).fetchone()
    db.close()
    return dict(row) if row else None


def topic_list():
    db = get_db()
    rows = db.execute("SELECT * FROM topics ORDER BY category, topic").fetchall()
    db.close()
    return [dict(r) for r in rows]


# ── LOG ───────────────────────────────────────────────────────────────────────

def log_action(eid, phase, action, details=None, success=True, error=None):
    db = get_db()
    db.execute(
        "INSERT INTO prod_log(episode_id,phase,action,details,success,error) VALUES(?,?,?,?,?,?)",
        (eid, phase, action, details, 1 if success else 0, error)
    )
    db.commit(); db.close()
    print("Logged.")


# ── SEARCH ────────────────────────────────────────────────────────────────────

def search(query, type_=None, limit=20):
    db = get_db()
    if type_:
        rows = db.execute(
            "SELECT type,entity_id,title,snippet(memory_fts,3,'>>>','<<<','...',32) as snip,rank "
            "FROM memory_fts WHERE memory_fts MATCH ? AND type=? ORDER BY rank LIMIT ?",
            (query, type_, limit)
        ).fetchall()
    else:
        rows = db.execute(
            "SELECT type,entity_id,title,snippet(memory_fts,3,'>>>','<<<','...',32) as snip,rank "
            "FROM memory_fts WHERE memory_fts MATCH ? ORDER BY rank LIMIT ?",
            (query, limit)
        ).fetchall()
    db.close()
    return [dict(r) for r in rows]


# ── CONTEXT BUILDER ───────────────────────────────────────────────────────────

PHASES = [
    "setup", "research", "script", "audio",
    "transcribe", "visuals", "deliverables", "cinematic_setup"
]


def build_context(eid=None):
    """Generate a focused AI context string from memory — includes quality rules."""
    db = get_db()
    out = []

    chars = db.execute("SELECT * FROM characters").fetchall()
    if chars:
        out.append("## Character Bible")
        for c in chars:
            out.append(f"**{c['name']}** ({c['role']}): {c['personality']}")
            phrases = json.loads(c['catchphrases']) if c['catchphrases'] else []
            if phrases:
                out.append(f"  Catchphrases: {', '.join(phrases)}")

    eps = db.execute("SELECT season,episode,title_de,status,topic FROM episodes ORDER BY season,episode").fetchall()
    if eps:
        out.append("\n## Episode History")
        for e in eps:
            out.append(f"- S{e['season']:02d}E{e['episode']:02d} [{e['status']}] {e['title_de']} — {e['topic']}")

    # Quality learnings injected as actionable DO/AVOID rules
    quality = db.execute("SELECT * FROM quality_notes ORDER BY created_at DESC LIMIT 20").fetchall()
    if quality:
        out.append("\n## Production Rules (Learned From Past Episodes)")
        out.append("> Apply these to every new episode:")
        for q in quality:
            if q['worked']:  out.append(f"  ✅ DO: {q['worked']}")
            if q['failed']:  out.append(f"  ❌ AVOID: {q['failed']}")
            if q['improve']: out.append(f"  💡 TRY: {q['improve']}")

    topics = db.execute("SELECT topic,category,controversy,appeal FROM topics ORDER BY category").fetchall()
    if topics:
        out.append("\n## Covered Topics (Do Not Repeat)")
        for t in topics:
            out.append(f"  [{t['category']}] {t['topic']} (c:{t['controversy']} a:{t['appeal']})")

    styles = db.execute("SELECT * FROM visual_styles").fetchall()
    if styles:
        out.append("\n## Visual Style Guide")
        for s in styles:
            out.append(f"  [{s['topic_type']}] {(s['prompt'] or '')[:80]} | mood:{s['mood']}")

    if eid:
        ep = db.execute("SELECT * FROM episodes WHERE id=?", (eid,)).fetchone()
        if ep:
            out.append(f"\n## Current Episode: S{ep['season']:02d}E{ep['episode']:02d}")
            out.append(f"Title: {ep['title_de']}")
            out.append(f"Topic: {ep['topic']}")
            if ep['notebook_id']:
                out.append(f"Notebook: {ep['notebook_id']}")
            srcs = db.execute("SELECT * FROM sources WHERE episode_id=?", (eid,)).fetchall()
            if srcs:
                out.append("Sources:")
                for s in srcs:
                    stars = '★' * s['quality'] if s['quality'] else ''
                    out.append(f"  [{s['source_type']}] {s['title']} {stars}")

    db.close()
    return "\n".join(out)


# ── PIPELINE STATE ────────────────────────────────────────────────────────────

def pipeline_init(eid):
    """Create fresh pending state for all phases of an episode."""
    db = get_db()
    for phase in PHASES:
        db.execute("""
            INSERT INTO pipeline_state(episode_id, phase, status)
            VALUES(?,?,'pending')
            ON CONFLICT(episode_id, phase) DO NOTHING
        """, (eid, phase))
    db.commit(); db.close()
    print(f"Pipeline state initialized for episode {eid}.")


def pipeline_set(eid, phase, status, error=None):
    """Update phase status: pending | running | done | failed | skipped."""
    db = get_db()
    if status == "running":
        db.execute("""
            INSERT INTO pipeline_state(episode_id, phase, status, started_at, attempts)
            VALUES(?,?,?,datetime('now'),1)
            ON CONFLICT(episode_id, phase) DO UPDATE SET
                status='running', started_at=datetime('now'),
                attempts=pipeline_state.attempts+1, error=NULL
        """, (eid, phase, "running"))
    elif status in ("done", "failed", "skipped"):
        db.execute("""
            UPDATE pipeline_state SET status=?, done_at=datetime('now'), error=?
            WHERE episode_id=? AND phase=?
        """, (status, error, eid, phase))
    db.commit(); db.close()


def pipeline_status(eid):
    """Return list of (phase, status, started_at, done_at, attempts, error)."""
    db = get_db()
    rows = db.execute(
        "SELECT phase, status, started_at, done_at, attempts, error "
        "FROM pipeline_state WHERE episode_id=? ORDER BY id",
        (eid,)
    ).fetchall()
    db.close()
    return [dict(r) for r in rows]


def pipeline_next(eid):
    """Return the next phase that is pending or failed (resume point)."""
    db = get_db()
    row = db.execute(
        "SELECT phase FROM pipeline_state WHERE episode_id=? AND status IN ('pending','failed') ORDER BY id LIMIT 1",
        (eid,)
    ).fetchone()
    db.close()
    return row["phase"] if row else None


# ── SOURCE DEDUPLICATION ──────────────────────────────────────────────────────

def source_check_dup(eid, url=None, file_path=None):
    """Return existing source if URL or filepath already added to this episode."""
    db = get_db()
    row = None
    if url:
        row = db.execute(
            "SELECT * FROM sources WHERE episode_id=? AND url=?", (eid, url)
        ).fetchone()
    elif file_path:
        row = db.execute(
            "SELECT * FROM sources WHERE episode_id=? AND file_path=?", (eid, file_path)
        ).fetchone()
    db.close()
    return dict(row) if row else None


# ── ANALYTICS ─────────────────────────────────────────────────────────────────

def analytics_record(eid, metric, value):
    """Record a numeric metric for an episode (e.g. quality_score, audio_dur, source_count)."""
    db = get_db()
    db.execute(
        "INSERT INTO analytics(episode_id, metric, value) VALUES(?,?,?)",
        (eid, metric, float(value))
    )
    db.commit(); db.close()


def analytics_summary():
    """Return aggregated analytics across all episodes."""
    db = get_db()
    rows = db.execute("""
        SELECT metric,
               ROUND(AVG(value),2) as avg,
               ROUND(MIN(value),2) as min,
               ROUND(MAX(value),2) as max,
               COUNT(*) as count
        FROM analytics GROUP BY metric ORDER BY metric
    """).fetchall()

    # Category performance from quality_notes + topics
    cat_rows = db.execute("""
        SELECT t.category,
               ROUND(AVG(q.rating),1) as avg_rating,
               COUNT(DISTINCT t.topic) as topic_count
        FROM topics t
        LEFT JOIN quality_notes q ON q.episode_id IN (
            SELECT id FROM episodes
        )
        GROUP BY t.category ORDER BY avg_rating DESC
    """).fetchall()

    db.close()
    return {
        "metrics": [dict(r) for r in rows],
        "categories": [dict(r) for r in cat_rows]
    }


def stats():
    """High-level stats snapshot of the entire project."""
    db = get_db()
    ep_count   = db.execute("SELECT COUNT(*) FROM episodes").fetchone()[0]
    done_count = db.execute("SELECT COUNT(*) FROM episodes WHERE status='complete'").fetchone()[0]
    src_count  = db.execute("SELECT COUNT(*) FROM sources").fetchone()[0]
    topic_count = db.execute("SELECT COUNT(*) FROM topics").fetchone()[0]
    qual_count  = db.execute("SELECT COUNT(*) FROM quality_notes").fetchone()[0]

    total_dur = db.execute("SELECT SUM(audio_dur) FROM episodes WHERE audio_dur IS NOT NULL").fetchone()[0] or 0
    avg_rating = db.execute("SELECT AVG(rating) FROM quality_notes WHERE rating IS NOT NULL").fetchone()[0]

    best_cat = db.execute("""
        SELECT t.category, COUNT(*) as c FROM topics t GROUP BY t.category ORDER BY c DESC LIMIT 1
    """).fetchone()

    db.close()
    return {
        "episodes_total":    ep_count,
        "episodes_complete": done_count,
        "sources_total":     src_count,
        "topics_covered":    topic_count,
        "quality_notes":     qual_count,
        "total_audio_hours": round(total_dur / 3600, 2),
        "avg_quality_score": round(avg_rating, 1) if avg_rating else None,
        "top_category":      best_cat["category"] if best_cat else None,
    }


def suggest_topic():
    """Suggest next topic categories based on coverage gaps and quality trends."""
    db = get_db()
    ALL_CATEGORIES = ["paranormal", "space", "biology", "technology", "military",
                      "consciousness", "time", "simulation", "ai", "ocean", "ancient"]

    covered = {r["category"] for r in db.execute("SELECT DISTINCT category FROM topics").fetchall()}
    uncovered = [c for c in ALL_CATEGORIES if c not in covered]

    # Best-rated categories
    top_cats = db.execute("""
        SELECT t.category, ROUND(AVG(q.rating),1) as avg_r
        FROM topics t
        JOIN quality_notes q ON q.episode_id IN (SELECT id FROM episodes)
        WHERE q.rating IS NOT NULL
        GROUP BY t.category ORDER BY avg_r DESC LIMIT 5
    """).fetchall()

    db.close()
    return {
        "uncovered_categories": uncovered,
        "top_performing":       [dict(r) for r in top_cats],
        "suggestion":           uncovered[0] if uncovered else (top_cats[0]["category"] if top_cats else "space")
    }


# ── CLI ───────────────────────────────────────────────────────────────────────

HELP = """
Podcast Memory — SQLite + FTS5

Commands:
  init
  episode add <S> <E> <title_de> <topic> [title_en]
  episode list [season]
  episode get <id>
  episode update <id> <field> <value>
  source add <ep_id> <type> <title> [url]
  source rate <id> <1-5> [notes]
  source check-dup <ep_id> <url>
  char set <name> <role> <personality>
  char get <name>
  char list
  quality add <ep_id> <category> [worked] [failed] [improve] [rating]
  style set <topic_type> <prompt> [palette] [mood]
  style get <topic_type>
  topic add <topic> <category> [controversy] [appeal]
  topic list
  topic check <topic>
  pipeline init <ep_id>
  pipeline set <ep_id> <phase> <status>
  pipeline status <ep_id>
  pipeline next <ep_id>
  log <ep_id> <phase> <action> [details]
  analytics record <ep_id> <metric> <value>
  analytics summary
  stats
  suggest
  language list
  search <query> [type]
  context [ep_id]
"""

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    if len(sys.argv) < 2:
        print(HELP); return

    cmd = sys.argv[1]
    a = sys.argv

    if cmd == "init":
        init_db()

    elif cmd == "episode":
        sub = a[2]
        if sub == "add":
            episode_add(int(a[3]), int(a[4]), a[5], a[6], a[7] if len(a)>7 else None)
        elif sub == "list":
            for e in episode_list(int(a[3]) if len(a)>3 else None):
                print(f"  S{e['season']:02d}E{e['episode']:02d} [{e['status']:>12}] {e['title_de']}")
        elif sub == "get":
            print(json.dumps(episode_get(int(a[3])), indent=2, ensure_ascii=False, default=str))
        elif sub == "update":
            episode_update(int(a[3]), **{a[4]: a[5]})

    elif cmd == "source":
        sub = a[2]
        if sub == "add":
            # Dedup check before adding
            dup = source_check_dup(int(a[3]), url=a[6] if len(a)>6 else None,
                                   file_path=a[6] if len(a)>6 and not a[6].startswith("http") else None)
            if dup:
                print(f"DUPLICATE — already added: {dup['title']} (ID:{dup['id']})")
                return
            sid = source_add(int(a[3]), a[4], a[5], a[6] if len(a)>6 else None)
            print(f"Source added (ID:{sid})")
        elif sub == "rate":
            source_rate(int(a[3]), int(a[4]), a[5] if len(a)>5 else None)
        elif sub == "check-dup":
            dup = source_check_dup(int(a[3]), url=a[4])
            print(json.dumps(dict(dup), ensure_ascii=False, default=str) if dup else "NOT DUPLICATE — safe to add.")

    elif cmd == "char":
        sub = a[2]
        if sub == "set":
            char_set(a[3], a[4], a[5])
        elif sub == "get":
            c = char_get(a[3])
            print(json.dumps(c, indent=2, ensure_ascii=False) if c else "Not found.")
        elif sub == "list":
            for c in char_list():
                print(f"  {c['name']} ({c['role']}): {c['personality'][:70]}...")

    elif cmd == "quality":
        if a[2] == "add":
            quality_add(int(a[3]), a[4],
                        a[5] if len(a)>5 else None,
                        a[6] if len(a)>6 else None,
                        a[7] if len(a)>7 else None,
                        int(a[8]) if len(a)>8 else None)

    elif cmd == "style":
        sub = a[2]
        if sub == "set":
            style_set(a[3], a[4], a[5] if len(a)>5 else None, a[6] if len(a)>6 else None)
        elif sub == "get":
            s = style_get(a[3])
            print(json.dumps(s, indent=2, ensure_ascii=False) if s else "Not found.")

    elif cmd == "topic":
        sub = a[2]
        if sub == "add":
            topic_add(a[3], a[4], int(a[5]) if len(a)>5 else 5, int(a[6]) if len(a)>6 else 5)
        elif sub == "list":
            for t in topic_list():
                print(f"  [{t['category']:>12}] {t['topic']} (c:{t['controversy']} a:{t['appeal']})")
        elif sub == "check":
            t = topic_check(a[3])
            print(f"COVERED:\n{json.dumps(t, indent=2, ensure_ascii=False, default=str)}" if t else "NOT COVERED — available.")

    elif cmd == "language":
        if len(a) > 2 and a[2] == "list":
            print(json.dumps(language_list(), ensure_ascii=False))


    elif cmd == "audience":
        if len(a) > 2 and a[2] == "list":
            print(json.dumps(audience_list(), ensure_ascii=False))
        elif len(a) > 3 and a[2] == "get":
            result = audience_get(a[3])
            print(json.dumps(result, ensure_ascii=False) if result else "Not found.")

    elif cmd == "pipeline":
        sub = a[2]
        if sub == "init":
            pipeline_init(int(a[3]))
        elif sub == "set":
            pipeline_set(int(a[3]), a[4], a[5], a[6] if len(a)>6 else None)
            print(f"Phase '{a[4]}' → {a[5]}")
        elif sub == "status":
            rows = pipeline_status(int(a[3]))
            icons = {"pending":"⏳","running":"🔄","done":"✅","failed":"❌","skipped":"⏭️"}
            for r in rows:
                icon = icons.get(r["status"], "?")
                print(f"  {icon} {r['phase']:20} {r['status']:8} "
                      f"{'('+r['error'][:40]+')' if r['error'] else ''}")
        elif sub == "next":
            nxt = pipeline_next(int(a[3]))
            print(f"Next phase: {nxt}" if nxt else "All phases complete!")

    elif cmd == "log":
        log_action(int(a[2]), a[3], a[4], a[5] if len(a)>5 else None)

    elif cmd == "analytics":
        sub = a[2]
        if sub == "record":
            analytics_record(int(a[3]), a[4], float(a[5]))
            print(f"Recorded: {a[4]} = {a[5]}")
        elif sub == "summary":
            print(json.dumps(analytics_summary(), indent=2, ensure_ascii=False))

    elif cmd == "stats":
        s = stats()
        print(f"\n  📊 Project Stats")
        print(f"  Episodes   : {s['episodes_complete']}/{s['episodes_total']} complete")
        print(f"  Sources    : {s['sources_total']}")
        print(f"  Topics     : {s['topics_covered']} covered")
        print(f"  Audio hrs  : {s['total_audio_hours']}h")
        print(f"  Avg Quality: {s['avg_quality_score'] or 'N/A'}/10")
        print(f"  Top Cat    : {s['top_category'] or 'N/A'}")
        print()

    elif cmd == "suggest":
        r = suggest_topic()
        print(f"\n  🎯 Topic Suggestion")
        print(f"  → Best next: {r['suggestion']}")
        print(f"  Uncovered  : {', '.join(r['uncovered_categories'])}")
        if r['top_performing']:
            print(f"  Top rated  : {r['top_performing'][0]['category']} ({r['top_performing'][0]['avg_r']}/10)")
        print()

    elif cmd == "search":
        results = search(a[2], a[3] if len(a)>3 else None)
        for r in results:
            print(f"  [{r['type']:>10}] {r['title']} — {r['snip']}")

    elif cmd == "context":
        print(build_context(int(a[2]) if len(a)>2 else None))

    elif cmd == "profile":
        sub = a[2]
        if sub == "get" and len(a) >= 5:
            p = skill_profile_get(a[3], a[4])
            if p:
                print(json.dumps(p, indent=2, ensure_ascii=False, default=str))
            else:
                print(f"No profile found for {a[3]}/{a[4]}")
        elif sub == "list":
            profiles = skill_profile_list()
            for p in profiles:
                print(f"  {p['lang']:3} × {p['audience']:20} | {p['lang_label']:12} × {p['audience_label']:20} | {p['tone_preview']}…")
            print(f"\n  Total: {len(profiles)} profiles")
        elif sub == "context" and len(a) >= 5:
            ctx = skill_profile_context(a[3], a[4])
            print(ctx)
        elif sub == "evolve" and len(a) >= 4:
            # Feature 1: evolve profile from quality notes
            result = auto_evolve_profile(int(a[3]))
            print(result)
        else:
            print("Usage: profile get <lang> <audience>")
            print("       profile list")
            print("       profile context <lang> <audience>")
            print("       profile evolve <episode_id>")

    # ── Feature 2: Phase outputs ───────────────────────────────────────────────
    elif cmd == "output":
        sub = a[2]
        if sub == "set" and len(a) >= 6:
            verify = "--verify" in a
            phase_output_set(int(a[3]), a[4], a[5], a[6] if len(a) > 6 and not a[6].startswith("--") else "", verify)
        elif sub == "get":
            phase = a[4] if len(a) > 4 else None
            rows = phase_output_get(int(a[3]), phase)
            if not rows:
                print("No outputs recorded.")
            for r in rows:
                v = "✅" if r["verified"] else "📝"
                print(f"  {v} [{r['phase']}] {r['output_key']} = {r['output_val']}")
        else:
            print("Usage: output set <eid> <phase> <key> <value> [--verify]")
            print("       output get <eid> [phase]")

    # ── Feature 3: Smart context ───────────────────────────────────────────────
    elif cmd == "smart-context":
        print(smart_context(int(a[2])))

    # ── Feature 4: Session handoff ─────────────────────────────────────────────
    elif cmd == "session":
        sub = a[2]
        if sub == "save" and len(a) >= 6:
            session_save(int(a[3]), a[4], a[5], a[6] if len(a) > 6 else "")
        elif sub == "load":
            state = session_load()
            if state:
                print(f"\n💾 SESSION STATE")
                print(f"  Episode     : {state['episode_id']}")
                print(f"  Phase       : {state['current_phase']}")
                print(f"  Saved at    : {state.get('saved_at','?')}")
                print(f"\n  ▶ NEXT ACTION:")
                print(f"  {state['next_action']}")
                print(f"\n  📋 RESUME INSTRUCTION:")
                print(f"  {state['resume_instruction']}")
                print()
            else:
                print("No session state found. Start fresh.")
        elif sub == "clear":
            session_clear()
        else:
            print("Usage: session save <eid> <phase> \"<next_action>\" \"<resume>\"")
            print("       session load")
            print("       session clear")

    # ── Feature 5: Contract verification ──────────────────────────────────────
    elif cmd == "contract":
        sub = a[2]
        if sub == "verify" and len(a) >= 5:
            contract_verify(int(a[3]), a[4])
        elif sub == "list":
            _seed_contract()
            db = get_db()
            rows = db.execute("SELECT * FROM workflow_contract ORDER BY step_order").fetchall()
            db.close()
            print("\n📋 WORKFLOW CONTRACT")
            for r in rows:
                print(f"  [{r['step_order']}] {r['phase']:20} — {r['description']}")
            print()
        else:
            print("Usage: contract verify <eid> <phase>")
            print("       contract list")

    # ── Feature 6: Parallel opportunities ─────────────────────────────────────
    elif cmd == "parallel":
        if len(a) >= 3:
            parallel_opportunities(int(a[2]))
        else:
            print("Usage: parallel <episode_id>")

    else:
        print(f"Unknown: {cmd}\n{HELP}")



if __name__ == "__main__":
    main()
