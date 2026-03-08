'use strict';

// ── CONSTANTS ──────────────────────────────────────────────────────────────────

const PHASES = ["setup", "research", "script", "audio", "transcribe", "visuals", "deliverables", "cinematic_setup"];
const PHASE_ICONS = { setup: "📁", research: "🔍", script: "✍️", audio: "🎙️", transcribe: "🎧", visuals: "🖼️", deliverables: "📦", cinematic_setup: "🎬" };
const PHASE_DESC = {
  setup: "Create episode folder + register in memory",
  research: "Find YouTube sources, add to NotebookLM",
  script: "Write script in target language + English translation",
  audio: "Generate podcast via NotebookLM, download MP3",
  transcribe: "Transcribe audio with real timestamps",
  visuals: "Generate 16:9 cinematic images for each segment",
  deliverables: "Build CapCut walkthrough + register in memory",
  cinematic_setup: "Create English NotebookLM notebook + add sources",
};
const PALETTE = { "deep-blue": "#1e40af", "purple": "#7c3aed", "black": "#111", "gold": "#d97706", "navy": "#1e3a5f", "cyan": "#0891b2", "amber": "#f59e0b", "dark-grey": "#374151", "green": "#15803d", "teal": "#0f766e", "orange": "#c2410c", "neon-blue": "#2563eb", "white": "#e5e7eb", "red": "#b91c1c", "violet": "#6d28d9" };

// ── FLAG IMAGES ────────────────────────────────────────────────────────────────
// Map lang codes to ISO 3166-1 alpha-2 for flagcdn.com (Windows has no native flag emoji)
const LANG_TO_COUNTRY = { en: "gb", de: "de", fr: "fr", pt: "br", es: "es" };
function flagImg(langCode, size = 20) {
  const cc = LANG_TO_COUNTRY[langCode] || langCode;
  return `<img src="https://flagcdn.com/${size}x${Math.round(size * 0.75)}/${cc}.png"
    srcset="https://flagcdn.com/${size * 2}x${Math.round(size * 0.75 * 2)}/${cc}.png 2x"
    width="${size}" height="${Math.round(size * 0.75)}"
    alt="${langCode}" style="border-radius:2px;vertical-align:middle;display:inline-block;margin-right:4px">`;
}

// Global state
let _languages = [];
let _audiences = [];
let _episodes = [];
let _filters = { status: "", lang: "" };
let _filterDash = "all";

// ── API ────────────────────────────────────────────────────────────────────────

async function api(path, opts = {}) {
  try {
    const r = await fetch(path, { headers: { "Content-Type": "application/json" }, ...opts });
    if (!r.ok) { const t = await r.text(); throw new Error(t); }
    return r.json();
  } catch (e) { console.error(`API ${path}:`, e); return null; }
}

// ── TOAST ──────────────────────────────────────────────────────────────────────

function toast(msg, type = "info") {
  const t = document.createElement("div");
  t.className = `toast ${type}`;
  t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(() => t.remove(), 3000);
}

// ── ROUTER ─────────────────────────────────────────────────────────────────────

function navigate(page, data = null) {
  document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));
  document.querySelectorAll(".nav-link").forEach(l => l.classList.remove("active"));
  const el = document.getElementById(`page-${page}`);
  if (!el) return;
  el.classList.add("active");
  const link = document.querySelector(`[data-page="${page}"]`);
  if (link) link.classList.add("active");
  const loaders = { dashboard: loadDashboard, episodes: loadEpisodes, analytics: loadAnalytics, memory: loadMemory };
  if (loaders[page]) loaders[page]();
  if (page === "episode-detail" && data) loadEpisodeDetail(data);
}

// ── LANGUAGE PICKER ────────────────────────────────────────────────────────────

async function initLanguagePicker() {
  const data = await api("/api/languages");
  if (!data) return;
  _languages = data;

  const dd = document.getElementById("lang-dropdown");
  if (!dd) return;

  dd.innerHTML = `<input type="text" placeholder="Search…" id="lang-search-input" oninput="filterLangs(this.value)" />`;
  renderLangOptions();

  document.getElementById("lang-selected").addEventListener("click", () => {
    dd.classList.toggle("hidden");
    const inp = dd.querySelector("input");
    if (inp) { inp.focus(); }
  });

  // Close on outside click
  document.addEventListener("click", e => {
    if (!e.target.closest(".lang-picker-wrap")) dd.classList.add("hidden");
  });
}

function renderLangOptions(filter = "") {
  const dd = document.getElementById("lang-dropdown");
  const existing = dd.querySelector("input");
  const items = _languages
    .filter(l => !filter || l.name.toLowerCase().includes(filter.toLowerCase()) || l.code.includes(filter))
    .map(l => `<div class="lang-option" data-code="${l.code}" data-name="${l.name}" onclick="selectLang('${l.code}','${l.name}')"> ${flagImg(l.code)} ${l.name} <small style="color:var(--text-dim);margin-left:4px">${l.code}</small></div>`)
    .join("");
  dd.innerHTML = "";
  if (existing) dd.appendChild(existing);
  dd.insertAdjacentHTML("beforeend", items || '<div class="search-empty">No results</div>');
}

window.filterLangs = function (val) { renderLangOptions(val); };

window.selectLang = function (code, name) {
  document.getElementById("lang-selected").innerHTML = `${flagImg(code)} ${name}`;
  document.getElementById("lang-code-input").value = code;
  document.getElementById("lang-name-input").value = name;
  document.getElementById("lang-dropdown").classList.add("hidden");
  // Refresh skill profile badge for new language + current audience combo
  checkSkillProfile();
};


// ── AUDIENCE PICKER ───────────────────────────────────────────────────────────

async function initAudiencePicker() {
  const data = await api("/api/audiences");
  if (!data?.length) return;
  _audiences = data;
  const grid = document.getElementById("audience-card-grid");
  if (!grid) return;

  grid.innerHTML = data.map(a =>
    `<div class="audience-card${a.key === 'finance_listeners' ? ' selected' : ''}" 
        id="aud-card-${a.key}"
        onclick="selectAudience('${a.key}')">
      <div class="audience-emoji">${a.emoji}</div>
      <div class="audience-label">${a.label}</div>
    </div>`
  ).join("");

  selectAudience("finance_listeners");
}

window.selectAudience = function (key) {
  document.querySelectorAll(".audience-card").forEach(c => c.classList.remove("selected"));
  const card = document.getElementById(`aud-card-${key}`);
  if (card) card.classList.add("selected");
  document.getElementById("target-audience-input").value = key;

  // Hide tips box (no longer used)
  const tips = document.getElementById("audience-tips-box");
  if (tips) tips.classList.add("hidden");

  // Check skill profile for this audience + current language
  checkSkillProfile();
};

// ── SKILL PROFILE BADGE ────────────────────────────────────────────────────────

let _profileCheckTimer = null;

function checkSkillProfile() {
  const lang = document.getElementById("lang-code-input")?.value || "en";
  const audience = document.getElementById("target-audience-input")?.value || "gen_z";
  const badge = document.getElementById("skill-profile-status");
  const icon = document.getElementById("skill-profile-icon");
  const msg = document.getElementById("skill-profile-msg");
  const btn = document.getElementById("skill-profile-btn");
  if (!badge) return;

  badge.className = "skill-profile-status";
  badge.classList.remove("hidden");
  icon.textContent = "⏳";
  msg.textContent = "Checking writing profile…";
  btn.classList.add("hidden");

  clearTimeout(_profileCheckTimer);
  _profileCheckTimer = setTimeout(async () => {
    try {
      const res = await fetch(`/api/skill-profiles/check/${lang}/${audience}`);
      const data = await res.json();
      if (data.exists) {
        badge.classList.add("found");
        icon.textContent = "✅";
        const p = data.profile;
        const lbl = (p.lang_label && p.lang_label.length < 30) ? p.lang_label : (p.lang || "?").toUpperCase();
        msg.textContent = `Writing profile: ${lbl} × ${p.audience_label || "?"} — ${p.tone || ""}`;
        btn.textContent = "Rebuild";
        btn.classList.remove("hidden");
      } else {
        badge.classList.add("missing");
        icon.textContent = "⚡";
        msg.textContent = `No writing profile yet for this combo — will research before writing`;
        btn.textContent = "Build Now";
        btn.classList.remove("hidden");
      }
    } catch (e) {
      badge.classList.add("missing");
      icon.textContent = "⚠️";
      msg.textContent = "Could not check profile status";
    }
  }, 300);
}

window.buildSkillProfile = async function (force = false) {
  const lang = document.getElementById("lang-code-input")?.value || "en";
  const audience = document.getElementById("target-audience-input")?.value || "gen_z";
  const badge = document.getElementById("skill-profile-status");
  const icon = document.getElementById("skill-profile-icon");
  const msg = document.getElementById("skill-profile-msg");
  const btn = document.getElementById("skill-profile-btn");
  if (!badge) return;

  badge.className = "skill-profile-status building";
  icon.textContent = "🔬";
  msg.textContent = "Researching writing style, slang, cultural refs…";
  btn.classList.add("hidden");

  const evtSource = new EventSource("/api/skill-profiles/research?" +
    new URLSearchParams({ lang, audience, force: force ? "1" : "0" }));

  // Switch to POST via fetch + SSE workaround — use fetch streaming
  evtSource.close();

  const resp = await fetch("/api/skill-profiles/research", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ lang, audience, force }),
  });

  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
  let buf = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });
    const parts = buf.split("\n\n");
    buf = parts.pop();
    for (const part of parts) {
      const dataLine = part.split("\n").find(l => l.startsWith("data:"));
      if (!dataLine) continue;
      const payload = JSON.parse(dataLine.slice(5).trim());
      if (payload.log) {
        msg.textContent = payload.log.replace(/^\[(INFO|BUILD|SAVE|SKIP)\] /, "");
      } else if (payload.status === "complete" && payload.profile) {
        badge.className = "skill-profile-status found";
        icon.textContent = "✅";
        const p = payload.profile;
        msg.textContent = `Profile built — ${p.lang_label} × ${p.audience_label} · ready`;
        btn.textContent = "Rebuild";
        btn.classList.remove("hidden");
      } else if (payload.status === "done") {
        // Refresh from DB
        checkSkillProfile();
      }
    }
  }
};

// ── DASHBOARD ──────────────────────────────────────────────────────────────────

async function loadDashboard() {
  const [statsData, eps] = await Promise.all([api("/api/stats"), api("/api/episodes")]);
  _episodes = eps || [];

  if (statsData?.stats) {
    const s = statsData.stats;
    setText("sv-eps", `${s.episodes_complete ?? 0}/${s.episodes_total ?? 0}`);
    setText("sv-src", s.sources_total ?? 0);
    setText("sv-aud", s.total_audio_hours != null ? `${s.total_audio_hours}h` : "—");
    setText("sv-qual", s.avg_quality_score != null ? `${s.avg_quality_score}/10` : "—");
    // Count unique languages
    const langs = [...new Set(_episodes.map(e => e.output_language).filter(Boolean))];
    setText("sv-langs", langs.length || "—");
  }

  if (statsData?.suggest) {
    const sg = statsData.suggest;
    document.getElementById("suggest-box").innerHTML = `
      <div class="suggest-topic">🎯 ${sg.suggestion ?? "paranormal"}</div>
      <div style="color:var(--text-dim);font-size:12px;margin-bottom:10px">Best next category</div>
      <div class="suggest-cats">${(sg.uncovered_categories || []).slice(0, 8).map(c => `<span class="tag">${c}</span>`).join("")}</div>`;
  }

  // Language summary pills
  const langSummary = document.getElementById("lang-summary");
  if (langSummary && _episodes.length) {
    const counts = {};
    _episodes.forEach(e => { const k = `${e.output_language || "de"}:${e.language_name || "German"}`; counts[k] = (counts[k] || 0) + 1; });
    langSummary.innerHTML = Object.entries(counts).map(([k, c]) => {
      const [code, name] = k.split(":");
      const lang = _languages.find(l => l.code === code) || {};
      return `<span class="lang-pill">${flagImg(lang.code)} ${name} <strong>${c}</strong></span>`;
    }).join("");
  }

  renderDashboardEpisodes();
}

function renderDashboardEpisodes() {
  const list = document.getElementById("recent-ep-list");
  let eps = [..._episodes].reverse();
  if (_filterDash !== "all") eps = eps.filter(e => (e.status || "planned") === _filterDash);
  eps = eps.slice(0, 8);
  list.innerHTML = eps.length
    ? eps.map(ep => epRow(ep)).join("")
    : `<div class="loading-spinner">No episodes${_filterDash !== "all" ? ` with status "${_filterDash}"` : ""}. <a href="#" onclick="navigate('new-episode')">Create one →</a></div>`;
  list.querySelectorAll(".ep-row").forEach(el => el.addEventListener("click", () => navigate("episode-detail", el.dataset.eid)));
}

function epRow(ep) {
  const code = `S${String(ep.season).padStart(2, "0")}E${String(ep.episode).padStart(2, "0")}`;
  const st = ep.status || "planned";
  const lang = _languages.find(l => l.code === (ep.output_language || "de")) || {};
  return `<div class="ep-row" data-eid="${ep.id}">
    <span class="ep-code">${code}</span>
    <span class="ep-title">${ep.title_de || "—"}</span>
    <span class="ep-lang-pill">${flagImg(lang ? lang.code : ep.output_language || 'en')}</span>
    <span class="ep-status ${st}">${st}</span>
  </div>`;
}

// Dashboard filter buttons
document.querySelectorAll(".filter-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".filter-btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    _filterDash = btn.dataset.filter;
    renderDashboardEpisodes();
  });
});

// ── EPISODES GRID ─────────────────────────────────────────────────────────────

async function loadEpisodes() {
  const eps = await api("/api/episodes");
  _episodes = eps || [];
  populateLangFilter();
  renderEpisodesGrid();

  document.getElementById("ep-filter-lang").addEventListener("change", e => { _filters.lang = e.target.value; renderEpisodesGrid(); });
  document.getElementById("ep-filter-status").addEventListener("change", e => { _filters.status = e.target.value; renderEpisodesGrid(); });
}

function populateLangFilter() {
  const sel = document.getElementById("ep-filter-lang");
  if (!sel) return;
  const langs = [...new Set(_episodes.map(e => `${e.output_language || "de"}:${e.language_name || "German"}`))];
  const opts = langs.map(k => { const [code, name] = k.split(":"); return `<option value="${code}">${name}</option>`; }).join("");
  sel.innerHTML = `<option value="">All Languages</option>${opts}`;
}

function renderEpisodesGrid() {
  const grid = document.getElementById("episodes-grid");
  let eps = [..._episodes];
  if (_filters.status) eps = eps.filter(e => (e.status || "planned") === _filters.status);
  if (_filters.lang) eps = eps.filter(e => (e.output_language || "de") === _filters.lang);
  if (!eps.length) { grid.innerHTML = `<div class="loading-spinner">No episodes match filters.</div>`; return; }
  grid.innerHTML = eps.map(ep => {
    const code = `S${String(ep.season).padStart(2, "0")}E${String(ep.episode).padStart(2, "0")}`;
    const lang = _languages.find(l => l.code === (ep.output_language || "de")) || {};
    return `<div class="ep-card" onclick="navigate('episode-detail','${ep.id}')">
      <div class="ep-card-code"><span>${code}</span><span>${lang.flag || "🌐"} ${ep.language_name || "German"}</span></div>
      <div class="ep-card-title">${ep.title_de || "—"}</div>
      <div class="ep-card-topic">${ep.topic || ""}</div>
      <div class="ep-card-footer"><span class="ep-status ${ep.status || "planned"}">${ep.status || "planned"}</span></div>
    </div>`;
  }).join("");
}

// ── NEW EPISODE (SSE) ─────────────────────────────────────────────────────────

document.getElementById("new-episode-form").addEventListener("submit", async e => {
  e.preventDefault();
  const btn = document.getElementById("create-btn");
  const terminal = document.getElementById("live-terminal");
  const termBody = document.getElementById("terminal-body");
  const termBadge = document.getElementById("terminal-status");
  const fd = new FormData(e.target);

  btn.disabled = true; btn.textContent = "⏳ Creating…";
  terminal.classList.remove("hidden");
  termBody.innerHTML = "";
  termBadge.className = "terminal-badge running"; termBadge.textContent = "Running";

  const body = {
    season: parseInt(fd.get("season")),
    episode: parseInt(fd.get("episode")),
    slug: fd.get("slug"),
    title_de: fd.get("title_de"),
    title_en: fd.get("title_en") || null,
    topic: fd.get("topic"),
    output_language: fd.get("output_language") || "de",
    language_name: fd.get("language_name") || "German",
    target_audience: fd.get("target_audience") || "scifi_curious",
  };

  const res = await api("/api/episodes", { method: "POST", body: JSON.stringify(body) });
  if (!res?.job_id) { toast("Failed to start job", "error"); btn.disabled = false; btn.textContent = "🚀 Create Episode"; return; }

  // Stream SSE
  const es = new EventSource(`/api/stream/${res.job_id}`);
  es.onmessage = ev => {
    const msg = JSON.parse(ev.data);
    if (msg.type === "line") {
      const span = document.createElement("span");
      span.className = `terminal-line${msg.text.toLowerCase().includes("error") ? " err" : msg.text.includes("✅") ? " success" : ""}`;
      span.textContent = msg.text;
      termBody.appendChild(span);
      termBody.appendChild(document.createTextNode("\n"));
      termBody.scrollTop = termBody.scrollHeight;
    } else if (msg.type === "done") {
      es.close();
      btn.disabled = false; btn.textContent = "🚀 Create Episode";
      if (msg.ok) {
        termBadge.className = "terminal-badge done"; termBadge.textContent = "Done";
        toast("Episode created! 🎉", "success");
        e.target.reset();
        // Reset to highest-CPM defaults
        document.getElementById("lang-selected").textContent = "🇬🇧 English";
        document.getElementById("lang-code-input").value = "en";
        document.getElementById("lang-name-input").value = "English";
        document.getElementById("target-audience-input").value = "finance_listeners";
        document.querySelectorAll(".audience-card").forEach(c => c.classList.remove("selected"));
        const fc = document.getElementById("aud-card-finance_listeners");
        if (fc) fc.classList.add("selected");
        document.getElementById("audience-tips-box")?.classList.add("hidden");
      } else {
        termBadge.className = "terminal-badge error"; termBadge.textContent = "Failed";
        toast("Episode creation failed", "error");
      }
    }
  };
  es.onerror = () => { es.close(); btn.disabled = false; btn.textContent = "🚀 Create Episode"; };
});

// ── EPISODE DETAIL ────────────────────────────────────────────────────────────

async function loadEpisodeDetail(eid) {
  const content = document.getElementById("episode-detail-content");
  const actions = document.getElementById("detail-actions");
  content.innerHTML = `<div class="loading-spinner">Loading episode…</div>`;
  actions.innerHTML = "";

  const data = await api(`/api/episodes/${eid}`);
  if (!data?.episode) { content.innerHTML = `<div class="loading-spinner">Episode not found.</div>`; return; }

  const ep = data.episode;
  const phases = data.phases || [];
  const srcs = data.sources || [];
  const aud = data.audience || null;
  const lang = _languages.find(l => l.code === (ep.output_language || "de")) || {};
  const code = `S${String(ep.season).padStart(2, "0")}E${String(ep.episode).padStart(2, "0")}`;

  // Header actions
  actions.innerHTML = `
    <button class="btn-icon" title="Init Pipeline" onclick="initPipeline(${ep.id})">🔄 Init</button>
    <button class="btn-icon" title="Export JSON" onclick="exportEpisode(${ep.id})">📥 Export</button>
    <button class="btn-ghost" onclick="navigate('episodes')">All Episodes</button>`;

  content.innerHTML = `
    <div class="detail-header">
      <div>
        <div class="detail-code">${code} <span class="lang-pill">${flagImg(ep.output_language || 'en')} ${ep.language_name || "German"}</span></div>
        <div class="detail-title">${ep.title_de || "—"}</div>
        <div class="detail-topic">${ep.topic || ""}</div>
      </div>
      <span class="ep-status ${ep.status || "planned"}" style="font-size:13px;padding:5px 14px">${ep.status || "planned"}</span>
    </div>

    <div class="detail-grid">
      <!-- LEFT: Pipeline + Sources -->
      <div style="display:flex;flex-direction:column;gap:14px">
        <div class="card">
          <div class="card-header"><h2>🔄 Pipeline Status</h2></div>
          <div class="pipeline-track" id="pipeline-track-${ep.id}">
            ${phases.map(p => phaseRow(ep.id, p)).join("")}
            ${phases.length && phases.every(p => p.status === "done" || p.status === "skipped") ? `
              <div class="phase-row done" style="background:linear-gradient(135deg,rgba(16,185,129,0.15),rgba(5,150,105,0.08));border:1px solid rgba(16,185,129,0.3);margin-top:6px;cursor:pointer" onclick="openDeliverables(${ep.id})">
                <span class="phase-icon" style="font-size:22px">📂</span>
                <div style="flex:1">
                  <div class="phase-name" style="color:#10b981;font-weight:600">Open Deliverables</div>
                  <div class="phase-desc">Open output folder in file explorer</div>
                </div>
                <span class="phase-badge done" style="background:#10b981;color:#fff">✓ Complete</span>
              </div>
            ` : ""}
          </div>
        </div>
        <div class="card">
          <div class="card-header"><h2>🔗 Sources</h2><span style="color:var(--text-dim);font-size:12px">${srcs.length} added</span></div>
          <div class="sources-list" id="sources-list-${ep.id}">
            ${srcs.length ? srcs.map(s => sourceRow(ep.id, s)).join("") : `<div class="loading-spinner" style="padding:8px 0">No sources yet.</div>`}
          </div>
          <div class="source-add-form">
            <select id="src-type-${ep.id}"><option value="youtube">YouTube</option><option value="article">Article</option><option value="podcast">Podcast</option><option value="doc">Document</option></select>
            <input type="text" id="src-title-${ep.id}" placeholder="Title" />
            <input type="text" id="src-url-${ep.id}" placeholder="URL or path" />
            <button class="btn-primary" onclick="addSource(${ep.id})">+ Add</button>
          </div>
        </div>
      </div>
      <!-- RIGHT: Info + Context -->
      <div style="display:flex;flex-direction:column;gap:14px">
        <div class="card">
          <div class="card-header"><h2>📋 Info</h2></div>
          <div class="meta-grid">
            <div class="meta-item"><div class="meta-key">Season</div><div class="meta-val">${ep.season}</div></div>
            <div class="meta-item"><div class="meta-key">Episode</div><div class="meta-val">${ep.episode}</div></div>
            <div class="meta-item"><div class="meta-key">Language</div><div class="meta-val">${lang.flag || "🌐"} ${ep.language_name || "German"}</div></div>
            <div class="meta-item"><div class="meta-key">Audio</div><div class="meta-val">${ep.audio_dur ? (() => { const m = Math.floor(ep.audio_dur / 60); const s = ep.audio_dur % 60; return `${m}:${String(s).padStart(2, '0')}`; })() : '—'}</div></div>
          </div>
          ${ep.notebook_id ? `<div style="font-family:var(--mono);font-size:11px;color:var(--text-dim);margin-top:4px">📓 ${ep.notebook_id.slice(0, 32)}…</div>` : ""}
          ${ep.ep_path ? `<div style="font-family:var(--mono);font-size:11px;color:var(--text-dim);margin-top:4px">📁 ${ep.ep_path}</div>` : ""}
        </div>
        ${aud ? `<div class="card">
          <div class="card-header"><h2>${aud.emoji || "🎯"} Target Audience</h2>
            <span class="audience-cpm-badge${aud.cpm_high >= 50 ? ' premium' : ''}">$${aud.cpm_low}–$${aud.cpm_high} CPM</span>
          </div>
          <div class="audience-label" style="margin-bottom:3px">${aud.label} <small style="color:var(--text-dim);font-weight:400">Age ${aud.age_range}</small></div>
          <div class="audience-desc" style="-webkit-line-clamp:3">${escHtml(aud.description || "")}</div>
          <div style="font-size:11px;color:var(--text-mid);margin-top:8px;line-height:1.6">${escHtml(aud.content_tips || "")}</div>
          <div class="audience-platforms" style="margin-top:8px">${(aud.platforms || "").split(",").map(p => {
    const name = p.trim();
    const LOGOS = {
      "YouTube": `<svg width="14" height="14" viewBox="0 0 24 24" fill="#FF0000"><path d="M23.5 6.2a3 3 0 0 0-2.1-2.1C19.5 3.5 12 3.5 12 3.5s-7.5 0-9.4.6A3 3 0 0 0 .5 6.2 31 31 0 0 0 0 12a31 31 0 0 0 .5 5.8 3 3 0 0 0 2.1 2.1c1.9.6 9.4.6 9.4.6s7.5 0 9.4-.6a3 3 0 0 0 2.1-2.1A31 31 0 0 0 24 12a31 31 0 0 0-.5-5.8zM9.75 15.5V8.5l6.5 3.5-6.5 3.5z"/></svg>`,
      "Spotify": `<svg width="14" height="14" viewBox="0 0 24 24" fill="#1DB954"><path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z"/></svg>`,
      "TikTok": `<svg width="14" height="14" viewBox="0 0 24 24" fill="#fff"><path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-2.88 2.5 2.89 2.89 0 0 1-2.89-2.89 2.89 2.89 0 0 1 2.89-2.89c.28 0 .54.04.79.1V9.01a6.33 6.33 0 0 0-.79-.05 6.34 6.34 0 0 0-6.34 6.34 6.34 6.34 0 0 0 6.34 6.34 6.34 6.34 0 0 0 6.33-6.34V8.69a8.19 8.19 0 0 0 4.79 1.52V6.76a4.85 4.85 0 0 1-1.03-.07z"/></svg>`,
      "Instagram": `<svg width="14" height="14" viewBox="0 0 24 24" fill="url(#ig)"><defs><linearGradient id="ig" x1="0%" y1="100%" x2="100%" y2="0%"><stop offset="0%" stop-color="#f09433"/><stop offset="25%" stop-color="#e6683c"/><stop offset="50%" stop-color="#dc2743"/><stop offset="75%" stop-color="#cc2366"/><stop offset="100%" stop-color="#bc1888"/></linearGradient></defs><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 1 0 0 12.324 6.162 6.162 0 0 0 0-12.324zM12 16a4 4 0 1 1 0-8 4 4 0 0 1 0 8zm6.406-11.845a1.44 1.44 0 1 0 0 2.881 1.44 1.44 0 0 0 0-2.881z"/></svg>`,
      "Instagram Reels": `<svg width="14" height="14" viewBox="0 0 24 24" fill="url(#ig2)"><defs><linearGradient id="ig2" x1="0%" y1="100%" x2="100%" y2="0%"><stop offset="0%" stop-color="#f09433"/><stop offset="100%" stop-color="#bc1888"/></linearGradient></defs><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 1 0 0 12.324 6.162 6.162 0 0 0 0-12.324zM12 16a4 4 0 1 1 0-8 4 4 0 0 1 0 8z"/></svg>`,
      "Apple Podcasts": `<svg width="14" height="14" viewBox="0 0 24 24" fill="#9b59b6"><path d="M5.34 0A5.328 5.328 0 0 0 0 5.34v13.32A5.328 5.328 0 0 0 5.34 24h13.32A5.328 5.328 0 0 0 24 18.66V5.34A5.328 5.328 0 0 0 18.66 0zm6.556 3.701c3.806 0 6.907 3.1 6.907 6.907 0 3.543-2.69 6.5-6.18 6.869v.028c.302.418.481.93.481 1.47 0 1.407-1.141 2.548-2.548 2.548S8 20.382 8 18.975c0-.54.18-1.052.481-1.47v-.028C5.01 17.108 2.32 14.15 2.32 10.608c0-3.806 3.101-6.907 6.907-6.907zM11.896 6.37c-2.36 0-4.272 1.912-4.272 4.272 0 2.035 1.424 3.74 3.323 4.18v-1.293c-.975-.37-1.668-1.314-1.668-2.428C9.279 9.58 10.46 8.4 11.896 8.4s2.618 1.18 2.618 2.701c0 1.114-.693 2.059-1.668 2.428v1.293c1.899-.44 3.323-2.145 3.323-4.18 0-2.36-1.912-4.272-4.273-4.272z"/></svg>`,
      "X/Twitter": `<svg width="14" height="14" viewBox="0 0 24 24" fill="#fff"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-4.714-6.231-5.401 6.231H2.744l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>`,
      "Twitch": `<svg width="14" height="14" viewBox="0 0 24 24" fill="#9146FF"><path d="M11.571 4.714h1.715v5.143H11.57zm4.715 0H18v5.143h-1.714zM6 0L1.714 4.286v15.428h5.143V24l4.286-4.286h3.428L22.286 12V0zm14.571 11.143l-3.428 3.428h-3.429l-3 3v-3H6.857V1.714h13.714z"/></svg>`,
    };
    const logo = LOGOS[name] || `<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" stroke-width="2"/></svg>`;
    return `<span class="platform-tag">${logo}<span>${name}</span></span>`;
  }).join("")}</div>
        </div>` : ""}
        <div class="card">
          <div class="card-header"><h2>🧠 AI Context</h2></div>
          <div class="context-box">${escHtml(data.context_preview || "No context yet.")}</div>
        </div>
      </div>
    </div>`;
}

function phaseRow(eid, p) {
  const icon = PHASE_ICONS[p.phase] || "⚙️";
  return `<div class="phase-row ${p.status}">
    <span class="phase-icon">${icon}</span>
    <div style="flex:1">
      <div class="phase-name">${p.phase.replace(/_/g, " ")}</div>
      <div class="phase-desc">${PHASE_DESC[p.phase] || ""}</div>
    </div>
    <span class="phase-badge ${p.status}">${p.status}</span>
    <div class="phase-actions">
      <button class="phase-btn" onclick="markPhase(event,${eid},'${p.phase}','done')">✓ Done</button>
      <button class="phase-btn danger" onclick="markPhase(event,${eid},'${p.phase}','failed')">✗ Fail</button>
      <button class="phase-btn" onclick="markPhase(event,${eid},'${p.phase}','skipped')">⏭ Skip</button>
    </div>
  </div>`;
}

function sourceRow(eid, s) {
  const stars = [1, 2, 3, 4, 5].map(n => `<span class="star${n <= (s.quality || 0) ? " lit" : ""}" onclick="rateSrc(${s.id},${n})">★</span>`).join("");
  return `<div class="source-row" id="src-row-${s.id}">
    <span class="source-type">${s.source_type || "url"}</span>
    <div style="flex:1;min-width:0">
      <div class="source-title">${escHtml(s.title || "—")}</div>
      ${s.url ? `<div class="source-url">${escHtml(s.url)}</div>` : ""}
    </div>
    <div class="star-rating">${stars}</div>
  </div>`;
}

async function addSource(eid) {
  const type = document.getElementById(`src-type-${eid}`)?.value;
  const title = document.getElementById(`src-title-${eid}`)?.value.trim();
  const url = document.getElementById(`src-url-${eid}`)?.value.trim();
  if (!title) { toast("Title is required", "error"); return; }
  const res = await api(`/api/episodes/${eid}/sources`, { method: "POST", body: JSON.stringify({ type, title, url }) });
  if (res?.ok) { toast("Source added ✅", "success"); loadEpisodeDetail(eid); }
  else if (res?.error === "duplicate") toast("Already added: duplicate URL", "error");
  else toast("Error adding source", "error");
}

async function rateSrc(srcId, rating) {
  await api(`/api/sources/${srcId}/rate`, { method: "POST", body: JSON.stringify({ rating }) });
  toast(`Rated ${rating}/5 ⭐`);
}

async function markPhase(evt, eid, phase, status) {
  evt.stopPropagation();
  await api(`/api/episodes/${eid}/phase`, { method: "POST", body: JSON.stringify({ phase, status }) });
  toast(`${phase.replace(/_/g, " ")} → ${status}`);
  loadEpisodeDetail(eid);
}

async function openDeliverables(eid) {
  const r = await api(`/api/episodes/${eid}/open-folder`, { method: "POST" });
  if (r?.ok) {
    toast("📂 Opened deliverables folder", "success");
  } else {
    toast(r?.error || "Could not open folder", "error");
  }
}

async function initPipeline(eid) {
  await api(`/api/episodes/${eid}/pipeline/init`, { method: "POST" });
  toast("Pipeline initialized 🔄");
  loadEpisodeDetail(eid);
}

function exportEpisode(eid) {
  window.open(`/api/episodes/${eid}/export`, "_blank");
}

// ── ANALYTICS ─────────────────────────────────────────────────────────────────

async function loadAnalytics() {
  const data = await api("/api/stats");
  const statsEl = document.getElementById("analytics-stats");
  const suggestEl = document.getElementById("analytics-suggest");

  if (data?.stats) {
    const s = data.stats;
    statsEl.innerHTML = [
      ["Episodes", `${s.episodes_complete}/${s.episodes_total} complete`],
      ["Sources", s.sources_total],
      ["Topics covered", s.topics_covered],
      ["Audio produced", s.total_audio_hours != null ? (s.total_audio_hours < 1 ? `${Math.round(s.total_audio_hours * 60)}min` : `${s.total_audio_hours}h`) : "—"],
      ["Avg quality", s.avg_quality_score != null ? `${s.avg_quality_score}/10` : "N/A"],
      ["Top category", s.top_category || "N/A"],
    ].map(([k, v]) => `<div class="stat-row"><span class="stat-row-label">${k}</span><span class="stat-row-value">${v}</span></div>`).join("");
  }

  if (data?.suggest) {
    const sg = data.suggest;
    suggestEl.innerHTML = `
      <div class="suggest-topic">🎯 ${sg.suggestion}</div>
      <div style="color:var(--text-dim);font-size:12px;margin-bottom:10px">Recommended next category</div>
      <div class="suggest-cats">${(sg.uncovered_categories || []).map(c => `<span class="tag">${c}</span>`).join("")}</div>
      ${sg.top_performing?.length ? `<div style="margin-top:14px;font-size:12px;color:var(--text-mid);margin-bottom:6px">Top rated:</div>
        ${sg.top_performing.map(t => `<div class="stat-row" style="border-bottom:none;padding:3px 0"><span class="stat-row-label" style="text-transform:capitalize">${t.category}</span><span class="stat-row-value" style="color:var(--green)">${t.avg_r}/10</span></div>`).join("")}` : ""}`;
  }
}

document.getElementById("quality-form").addEventListener("submit", async e => {
  e.preventDefault();
  const fd = new FormData(e.target);
  const res = await api("/api/quality", {
    method: "POST", body: JSON.stringify({
      episode_id: fd.get("episode_id"), category: fd.get("category"),
      worked: fd.get("worked"), failed: fd.get("failed"),
      improve: fd.get("improve"), rating: fd.get("rating"),
    })
  });
  if (res?.ok) { toast("Quality note saved ✅", "success"); e.target.reset(); }
  else toast("Error saving", "error");
});

// ── MEMORY ────────────────────────────────────────────────────────────────────

async function loadMemory() {
  const [chars, styles, topics] = await Promise.all([api("/api/characters"), api("/api/styles"), api("/api/topics")]);

  const charEl = document.getElementById("characters-list");
  if (chars?.characters?.length) {
    charEl.innerHTML = chars.characters.map(line => {
      const m = line.match(/^\s*([\w]+)\s*\(([^)]+)\):\s*(.*)$/);
      if (!m) return `<div class="char-item"><div class="char-desc">${escHtml(line)}</div></div>`;
      return `<div class="char-item"><div class="char-name">${m[1]}</div><div class="char-role">${m[2]}</div><div class="char-desc">${escHtml(m[3])}</div></div>`;
    }).join("");
  } else charEl.innerHTML = `<div class="loading-spinner">No characters seeded.</div>`;

  const styleEl = document.getElementById("styles-list");
  if (styles?.styles?.length) {
    styleEl.innerHTML = styles.styles.map(s => {
      const dots = (s.palette || "").split(",").map(c => `<div class="palette-dot" style="background:${PALETTE[c.trim()] || "#444"}" title="${c.trim()}"></div>`).join("");
      return `<div class="style-item">
        <div style="display:flex;justify-content:space-between"><div class="style-type">${s.topic_type}</div><div style="font-size:11px;color:var(--text-dim)">🌙 ${s.mood || ""}</div></div>
        <div class="style-prompt">${escHtml(s.prompt || "")}</div>
        <div class="style-palette">${dots}</div>
      </div>`;
    }).join("");
  } else styleEl.innerHTML = `<div class="loading-spinner">No styles set.</div>`;

  const topicEl = document.getElementById("topics-list");
  topicEl.innerHTML = topics?.topics?.length
    ? topics.topics.map(t => `<span class="topic-tag">${escHtml(t)}</span>`).join("")
    : `<div class="loading-spinner">No topics covered yet.</div>`;
}

// ── GLOBAL SEARCH ─────────────────────────────────────────────────────────────

let _searchTimer = null;

function openSearch() {
  document.getElementById("search-overlay").classList.remove("hidden");
  document.getElementById("search-input").focus();
}

function closeSearch() {
  document.getElementById("search-overlay").classList.add("hidden");
  document.getElementById("search-input").value = "";
  document.getElementById("search-results").innerHTML = "";
}

document.getElementById("search-input").addEventListener("input", e => {
  clearTimeout(_searchTimer);
  const q = e.target.value.trim();
  if (q.length < 2) { document.getElementById("search-results").innerHTML = ""; return; }
  _searchTimer = setTimeout(() => doSearch(q), 260);
});

async function doSearch(q) {
  const data = await api(`/api/search?q=${encodeURIComponent(q)}`);
  const rs = document.getElementById("search-results");
  if (!data?.results?.length) { rs.innerHTML = `<div class="search-empty">No results for "${escHtml(q)}"</div>`; return; }
  rs.innerHTML = data.results.map(r => `
    <div class="search-result-item" onclick="handleSearchClick('${r.type}','${r.title}')">
      <span class="sr-type">${r.type}</span>
      <div><div class="sr-title">${escHtml(r.title)}</div><div class="sr-snip">${escHtml(r.snip || "")}</div></div>
    </div>`).join("");
}

window.handleSearchClick = function (type, title) { closeSearch(); toast(`Found: ${title}`); };

document.querySelector(".search-backdrop")?.addEventListener("click", closeSearch);

// ── KEYBOARD SHORTCUTS ────────────────────────────────────────────────────────

window.toggleShortcuts = function () {
  document.getElementById("shortcuts-panel").classList.toggle("hidden");
};

document.addEventListener("keydown", e => {
  const tag = document.activeElement?.tagName;
  const inInput = ["INPUT", "TEXTAREA", "SELECT"].includes(tag);

  if (e.key === "Escape") {
    if (!document.getElementById("search-overlay").classList.contains("hidden")) { closeSearch(); return; }
    document.getElementById("shortcuts-panel").classList.add("hidden");
    return;
  }
  if (e.key === "/" && !inInput) { e.preventDefault(); openSearch(); return; }
  if (inInput) return;

  const map = { n: "new-episode", d: "dashboard", e: "episodes", a: "analytics", m: "memory", "?": "shortcuts" };
  const target = map[e.key.toLowerCase()];
  if (target === "shortcuts") { toggleShortcuts(); return; }
  if (target) navigate(target);
});

// ── NAV WIRING ────────────────────────────────────────────────────────────────

document.querySelectorAll(".nav-link").forEach(link => {
  link.addEventListener("click", ev => { ev.preventDefault(); navigate(link.dataset.page); });
});

// ── UTILS ─────────────────────────────────────────────────────────────────────

function setText(id, val) { const el = document.getElementById(id); if (el) el.textContent = val; }
function escHtml(s) { return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); }

// ── BOOT ──────────────────────────────────────────────────────────────────────

(async () => {
  await initLanguagePicker();
  await initAudiencePicker();
  navigate("dashboard");
})();
