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
    .map(l => `<div class="lang-option" data-code="${l.code}" data-name="${l.name}" data-flag="${l.flag}" onclick="selectLang('${l.code}','${l.name}','${l.flag}')">${l.flag} ${l.name} <small style="color:var(--text-dim);margin-left:4px">${l.code}</small></div>`)
    .join("");
  dd.innerHTML = "";
  if (existing) dd.appendChild(existing);
  dd.insertAdjacentHTML("beforeend", items || '<div class="search-empty">No results</div>');
}

window.filterLangs = function (val) { renderLangOptions(val); };

window.selectLang = function (code, name, flag) {
  document.getElementById("lang-selected").textContent = `${flag} ${name}`;
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
      const res = await fetch(`/api/skill-profiles/${lang}/${audience}`);
      const data = await res.json();
      if (data.exists) {
        badge.classList.add("found");
        icon.textContent = "✅";
        const p = data.profile;
        msg.textContent = `Writing profile loaded — ${p.lang_label} × ${p.audience_label} (${p.tone?.slice(0, 55)}…)`;
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
      return `<span class="lang-pill">${lang.flag || "🌐"} ${name} <strong>${c}</strong></span>`;
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
    <span class="ep-lang-pill">${lang.flag || "🌐"}</span>
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
        <div class="detail-code">${code} <span class="lang-pill">${lang.flag || "🌐"} ${ep.language_name || "German"}</span></div>
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
            <div class="meta-item"><div class="meta-key">Audio</div><div class="meta-val">${ep.audio_dur ? Math.round(ep.audio_dur / 60) + "min" : "—"}</div></div>
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
          <div class="audience-platforms" style="margin-top:8px">${(aud.platforms || "").split(",").map(p => `<span class="platform-tag">${p.trim()}</span>`).join("")}</div>
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
      ["Audio produced", `${s.total_audio_hours}h`],
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
