/* Institutional Memory — console */
const $ = (id) => document.getElementById(id);

const state = {
  mode: "memory",
  tickets: [],
  selected: null,
  streaming: false,
  metrics: [],
};

/* ------------------------------ helpers ------------------------------ */
function esc(v) {
  return String(v ?? "").replace(/[&<>"']/g, (c) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
  ));
}
function initials(name) {
  return (name || "?").split(/\s+/).map((w) => w[0]).slice(0, 2).join("").toUpperCase();
}
function fmtDate(iso) {
  const d = new Date(iso);
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}
function prettyIssue(t) {
  return String(t || "").replace(/_/g, " ");
}
async function api(path, options) {
  const res = await fetch(path, options);
  if (!res.ok) {
    let detail = res.statusText;
    try { detail = (await res.json()).detail || detail; } catch (e) { /* noop */ }
    throw new Error(detail);
  }
  return res.json();
}
function toast(message, kind = "") {
  const el = document.createElement("div");
  el.className = `toast ${kind}`;
  el.textContent = message;
  $("toasts").appendChild(el);
  setTimeout(() => {
    el.style.transition = "opacity .3s, transform .3s";
    el.style.opacity = "0";
    el.style.transform = "translateX(24px)";
    setTimeout(() => el.remove(), 320);
  }, 4200);
}

/* markdown-lite for the mental-model report */
function mdLite(text) {
  const inline = (s) => esc(s)
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/`(.+?)`/g, "<code>$1</code>");
  let html = "";
  let inList = false;
  for (const raw of String(text || "").split("\n")) {
    const line = raw.trim();
    if (!line) { if (inList) { html += "</ul>"; inList = false; } continue; }
    if (/^#{1,4}\s+/.test(line)) {
      if (inList) { html += "</ul>"; inList = false; }
      html += `<h4>${inline(line.replace(/^#{1,4}\s+/, ""))}</h4>`;
    } else if (/^[-*]\s+/.test(line)) {
      if (!inList) { html += "<ul>"; inList = true; }
      let item = inline(line.replace(/^[-*]\s+/, ""));
      item = item.replace(/\b(Rising|Falling)\b/g, (m) => `<span class="badge ${m.toLowerCase()}">${m}</span>`);
      html += `<li>${item}</li>`;
    } else {
      if (inList) { html += "</ul>"; inList = false; }
      html += `<p>${inline(line)}</p>`;
    }
  }
  if (inList) html += "</ul>";
  return html;
}

/* ------------------------------ queue ------------------------------ */
function renderQueue() {
  const list = $("ticket-list");
  list.innerHTML = "";
  for (const item of state.tickets) {
    const t = item.ticket;
    const li = document.createElement("li");
    li.className = "ticket-item" + (t.id === state.selected ? " active" : "");
    li.dataset.issue = t.issue_type;
    li.innerHTML =
      `<span class="subject">${esc(t.subject)}</span>` +
      `<span class="row"><span class="tz">${esc(prettyIssue(t.issue_type))}</span>` +
      `<span class="sep">·</span>${esc(t.module)}<span class="sep">·</span>${esc(t.version)}` +
      `<span class="sep">·</span>${esc(fmtDate(t.created_at))}</span>`;
    li.onclick = () => selectTicket(item);
    list.appendChild(li);
  }
}

function selectTicket(item) {
  state.selected = item.ticket.id;
  renderQueue();
  const t = item.ticket;
  const c = item.customer;

  $("ticket-empty").hidden = true;
  $("ticket-view").hidden = false;
  $("draft-view").hidden = true;

  const pill = $("t-issue");
  pill.textContent = prettyIssue(t.issue_type);
  pill.dataset.issue = t.issue_type;
  $("t-id").textContent = `${t.id} · ${t.status}`;
  $("t-subject").textContent = t.subject;
  $("t-tags").innerHTML = [
    t.product, t.version, t.module, `type: ${t.issue_type}`,
  ].map((x) => `<span class="tag">${esc(x)}</span>`).join("");

  const chip = $("t-customer");
  chip.hidden = false;
  chip.innerHTML = `${initials(c.name)} · <b>${esc(c.name)}</b> — ${esc(c.company)}`;

  $("t-body").textContent = t.body;
  $("draft-mode").textContent = state.mode;

  renderCustomer(c);
}

/* ------------------------------ customer ------------------------------ */
function renderCustomer(c) {
  $("customer-empty").hidden = true;
  const box = $("customer");
  box.hidden = false;
  box.innerHTML =
    `<div class="cust-head">
       <div class="avatar">${esc(initials(c.name))}</div>
       <div>
         <div class="cust-name">${esc(c.name)}</div>
         <div class="cust-sub">${esc(c.company)}</div>
       </div>
       <span class="cust-plan" style="margin-left:auto">${esc(c.plan)}</span>
     </div>
     <div class="facts">
       <div class="fact"><dt>Region</dt><dd>${esc(c.region)}</dd></div>
       <div class="fact"><dt>Environment</dt><dd>${esc(c.environment)}</dd></div>
       <div class="fact"><dt>Account owner</dt><dd>${esc(c.csm)}</dd></div>
     </div>`;
}

/* ------------------------------ draft ------------------------------ */
async function draftSelected() {
  if (!state.selected) return;
  const item = state.tickets.find((x) => x.ticket.id === state.selected);
  if (!item) return;

  const btn = $("btn-draft");
  btn.disabled = true;
  $("draft-view").hidden = false;
  $("draft-text").textContent = "";
  $("draft-text").hidden = true;
  $("draft-error").hidden = true;
  $("draft-loading").hidden = false;
  $("citations").innerHTML = "";
  $("toolcalls").innerHTML = "";

  try {
    const result = await api(`/api/tickets/${state.selected}/process?mode=${state.mode}`, { method: "POST" });
    renderDraft(result);
  } catch (err) {
    $("draft-loading").hidden = true;
    $("draft-text").hidden = false;
    $("draft-text").textContent = "";
    const e = $("draft-error");
    e.hidden = false;
    e.textContent = `Agent error: ${err.message}`;
    toast(`Draft failed: ${err.message}`, "error");
  } finally {
    btn.disabled = false;
  }
}

function renderDraft(result) {
  $("draft-loading").hidden = true;
  $("draft-text").hidden = false;

  $("draft-mode").textContent = result.mode;
  $("draft-stats").textContent =
    `${result.elapsed_ms} ms · ${result.citations.length} memories · ${result.tool_calls.length} calls`;

  const err = $("draft-error");
  if (result.error) {
    err.hidden = false;
    err.textContent = `Agent error: ${result.error}`;
    $("draft-text").textContent = "";
  } else {
    err.hidden = true;
    $("draft-text").textContent = result.draft || "(no draft)";
  }

  $("cite-count").textContent = String(result.citations.length);
  $("call-count").textContent = String(result.tool_calls.length);

  const cites = $("citations");
  cites.innerHTML = "";
  for (const c of result.citations) {
    const li = document.createElement("li");
    li.className = "citation";
    li.dataset.kind = c.kind;
    const evidence = c.source_fact_ids && c.source_fact_ids.length
      ? ` · ${c.source_fact_ids.length} source facts` : "";
    li.innerHTML = `<span class="cite-kind">${esc(c.kind.replace(/_/g, " "))}</span>${esc(c.text)}` +
      `<div class="muted tiny">${esc(evidence)}</div>`;
    cites.appendChild(li);
  }
  if (!result.citations.length) cites.innerHTML = '<li class="muted tiny">No memories used.</li>';

  const calls = $("toolcalls");
  calls.innerHTML = "";
  for (const t of result.tool_calls) {
    const li = document.createElement("li");
    const args = Object.keys(t.arguments || {});
    li.innerHTML = t.error
      ? `<span class="fn">${esc(t.name)}</span> — error: ${esc(t.error)}`
      : `<span class="fn">${esc(t.name)}</span>(${esc(args.join(", "))})`;
    calls.appendChild(li);
  }
  if (!result.tool_calls.length) calls.innerHTML = '<li class="muted tiny">No memory calls (amnesia mode).</li>';

  recordMetric(result);
}

/* ------------------------------ learning curve ------------------------------ */
function recordMetric(result) {
  state.metrics.push({
    grounded: result.used_memory || result.citations.length > 0,
    citations: result.citations.length,
  });
  renderLearningChart();
}

function renderLearningChart() {
  const svg = $("learning-chart");
  const s = state.metrics;
  const W = 320, H = 130, padX = 10, padY = 16;
  if (!s.length) {
    svg.innerHTML = `<text x="14" y="70" fill="#6f7ba0" font-size="11">No drafts yet — replay the stream.</text>`;
    return;
  }
  let run = 0;
  const series = s.map((d, i) => { if (d.grounded) run += 1; return run / (i + 1); });
  const x = (i) => padX + (i / Math.max(s.length - 1, 1)) * (W - 2 * padX);
  const y = (v) => H - padY - v * (H - 2 * padY);
  const line = series.map((v, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(" ");
  const area = `${line} L${x(s.length - 1).toFixed(1)},${H - padY} L${x(0).toFixed(1)},${H - padY} Z`;
  const last = series[series.length - 1];
  const avg = s.reduce((a, b) => a + b.citations, 0) / s.length;

  svg.innerHTML = `
    <defs>
      <linearGradient id="area" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#34d5ee" stop-opacity="0.45"/>
        <stop offset="100%" stop-color="#8b7bff" stop-opacity="0"/>
      </linearGradient>
      <linearGradient id="stroke" x1="0" y1="0" x2="1" y2="0">
        <stop offset="0%" stop-color="#8b7bff"/><stop offset="100%" stop-color="#34d5ee"/>
      </linearGradient>
    </defs>
    <line x1="${padX}" y1="${y(0)}" x2="${W - padX}" y2="${y(0)}" stroke="rgba(255,255,255,.08)"/>
    <line x1="${padX}" y1="${y(0.5)}" x2="${W - padX}" y2="${y(0.5)}" stroke="rgba(255,255,255,.05)"/>
    <line x1="${padX}" y1="${y(1)}" x2="${W - padX}" y2="${y(1)}" stroke="rgba(255,255,255,.08)"/>
    <path d="${area}" fill="url(#area)"/>
    <path d="${line}" fill="none" stroke="url(#stroke)" stroke-width="2.5" stroke-linecap="round"/>
    <circle cx="${x(s.length - 1).toFixed(1)}" cy="${y(last).toFixed(1)}" r="4" fill="#34d5ee" stroke="#06080f" stroke-width="2"/>
    <text x="${padX}" y="12" fill="#eaeefb" font-size="13" font-weight="700">${(last * 100).toFixed(0)}% grounded</text>`;
  $("learning-stats").textContent =
    `${s.length} drafts · avg ${avg.toFixed(1)} memories cited`;
}

/* ------------------------------ side panels ------------------------------ */
async function loadEmerging() {
  try {
    const model = await api("/api/emerging-issues");
    $("emerging").innerHTML = model.content
      ? mdLite(model.content)
      : '<span class="muted tiny">Not built yet — seed history first.</span>';
    $("ei-refreshed").textContent = model.last_refreshed_at
      ? `refreshed ${new Date(model.last_refreshed_at).toLocaleTimeString()}`
      : "";
  } catch (e) {
    $("emerging").innerHTML = '<span class="muted tiny">Unavailable.</span>';
  }
}

async function loadRegressions() {
  const btn = $("btn-regressions");
  btn.disabled = true;
  btn.textContent = "Auditing…";
  toast("Reflecting over every ticket for regressions…");
  try {
    const data = await api("/api/regressions");
    const regs = data.regressions || [];
    $("reg-count").textContent = String(regs.length);
    $("stat-regressions").textContent = String(regs.length);
    const box = $("regressions");
    box.innerHTML = "";
    if (!regs.length) {
      box.innerHTML = '<div class="muted tiny">No regressions detected.</div>';
    }
    for (const r of regs) {
      const el = document.createElement("div");
      el.className = "reg-item";
      el.innerHTML =
        `<div class="reg-title">${esc(r.issue || "issue")}</div>
         <div class="reg-badges">
           <span class="reg-badge">fixed in ${esc(r.previously_fixed_in || "?")}</span>
           <span class="reg-badge">back in ${esc(r.currently_affected || "?")}</span>
           <span class="reg-badge">${esc(String(r.affected_customers ?? "?"))} affected</span>
           ${r.confidence ? `<span class="reg-badge conf">${esc(r.confidence)} confidence</span>` : ""}
         </div>`;
      box.appendChild(el);
    }
    toast(`Regression audit complete — ${regs.length} found.`, "ok");
  } catch (err) {
    toast(`Regression audit failed: ${err.message}`, "error");
  } finally {
    btn.disabled = false;
    btn.textContent = "Run audit";
  }
}

/* ------------------------------ stream / mode / seed ------------------------------ */
async function bootstrapSeed() {
  const btn = $("btn-seed");
  btn.disabled = true;
  toast("Seeding historical tickets into Hindsight… this can take a few minutes.");
  try {
    const out = await api("/api/bootstrap", { method: "POST" });
    toast(`Seeded ${out.seeded_tickets} tickets across ${out.customers} customers.`, "ok");
    await loadEmerging();
  } catch (err) {
    toast(`Seed failed: ${err.message}`, "error");
  } finally {
    btn.disabled = false;
  }
}

function playStream() {
  if (state.streaming) return;
  state.streaming = true;
  state.metrics = [];
  renderLearningChart();
  $("btn-stream").disabled = true;
  toast("Live ticket stream running…");

  const source = new EventSource("/api/stream?delay=2.6");
  source.addEventListener("ticket", async (event) => {
    const item = JSON.parse(event.data);
    state.tickets.push(item);
    renderQueue();
    if ($("auto-process").checked) {
      selectTicket(item);
      await draftSelected();
    }
  });
  source.addEventListener("done", () => {
    source.close();
    state.streaming = false;
    $("btn-stream").disabled = false;
    toast("Stream complete.", "ok");
  });
  source.onerror = () => {
    source.close();
    state.streaming = false;
    $("btn-stream").disabled = false;
  };
}

function setMode(mode) {
  state.mode = mode;
  $("mode-memory").classList.toggle("active", mode === "memory");
  $("mode-amnesia").classList.toggle("active", mode === "amnesia");
  $("mode-slider").classList.toggle("right", mode === "amnesia");
  $("draft-mode").textContent = mode;
}

/* ------------------------------ init ------------------------------ */
async function init() {
  $("mode-memory").onclick = () => setMode("memory");
  $("mode-amnesia").onclick = () => setMode("amnesia");
  $("btn-seed").onclick = bootstrapSeed;
  $("btn-stream").onclick = playStream;
  $("btn-draft").onclick = draftSelected;
  $("btn-regressions").onclick = loadRegressions;

  try {
    const health = await api("/api/health");
    const base = health.memory?.base_url || "";
    const kind = base.includes("hindsight.vectorize.io") ? "Hindsight Cloud"
      : base.includes("localhost") ? "Self-hosted"
      : (base || "offline");
    $("stat-memory").textContent = kind;
  } catch (e) {
    $("stat-memory").textContent = "unavailable";
  }

  try {
    const cfg = await api("/api/config");
    $("footer-bank").textContent = `${cfg.org_bank_id} · ${cfg.model}`;
    if (cfg.service_error) toast(`Backend not ready: ${cfg.service_error}`, "error");
  } catch (e) { /* noop */ }

  try {
    const stream = await api("/api/demo-stream");
    state.tickets = stream;
    $("stat-tickets").textContent = String(stream.length);
    renderQueue();
  } catch (err) {
    toast(`Could not load tickets: ${err.message}`, "error");
  }

  try {
    const customers = await api("/api/customers");
    $("stat-customers").textContent = String(customers.length);
  } catch (e) { /* noop */ }

  await loadEmerging();
  renderLearningChart();
}

init();
