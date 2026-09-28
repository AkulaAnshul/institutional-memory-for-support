const state = {
  mode: "memory",
  tickets: [],      // {ticket, customer}
  selected: null,
  streaming: false,
  metrics: [],      // learning-curve samples
};

const $ = (id) => document.getElementById(id);

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

async function api(path, options) {
  const res = await fetch(path, options);
  if (!res.ok) {
    let detail = res.statusText;
    try { detail = (await res.json()).detail || detail; } catch (e) { /* ignore */ }
    throw new Error(detail);
  }
  return res.json();
}

function setStatus(text, kind = "") {
  const el = $("status");
  el.textContent = text;
  el.style.color = kind === "error" ? "var(--bad)" : kind === "ok" ? "var(--good)" : "var(--muted)";
}

function renderQueue() {
  const list = $("ticket-list");
  list.innerHTML = "";
  for (const item of state.tickets) {
    const t = item.ticket;
    const li = document.createElement("li");
    li.className = t.id === state.selected ? "active" : "";
    li.innerHTML =
      `<span class="subj">${esc(t.subject)}</span>` +
      `<span class="sub ${"tk-" + t.issue_type}">${esc(t.issue_type)} · ${esc(t.module)} · v${esc(t.version)}</span>`;
    li.onclick = () => selectTicket(item);
    list.appendChild(li);
  }
}

function renderCustomer(customer) {
  $("customer-empty").hidden = true;
  $("customer").hidden = false;
  $("c-name").textContent = `${customer.name}`;
  $("c-sub").textContent = `${customer.company} · ${customer.plan} · ${customer.region}`;
  $("c-facts").innerHTML =
    `<dt>Environment</dt><dd>${esc(customer.environment)}</dd>` +
    `<dt>Owner (CSM)</dt><dd>${esc(customer.csm)}</dd>`;
}

function selectTicket(item) {
  state.selected = item.ticket.id;
  renderQueue();
  $("ticket-empty").hidden = true;
  $("ticket-view").hidden = false;
  $("draft-view").hidden = true;
  const t = item.ticket;
  $("t-subject").textContent = t.subject;
  $("t-meta").textContent = `${t.id} · ${t.status} · ${new Date(t.created_at).toLocaleDateString()}`;
  $("t-body").textContent = t.body;
  renderCustomer(item.customer);
}

function renderDraft(result) {
  $("draft-view").hidden = false;
  $("draft-mode").textContent = result.mode;
  $("draft-stats").textContent =
    `${result.elapsed_ms} ms · ${result.used_memory ? "used memory" : "no memory"} · ${result.tool_calls.length} tool calls`;

  const err = $("draft-error");
  if (result.error) {
    err.hidden = false;
    err.textContent = `Agent error: ${result.error}`;
  } else {
    err.hidden = true;
  }
  $("draft-text").textContent = result.draft || "(no draft)";

  $("cite-count").textContent = String(result.citations.length);
  const cites = $("citations");
  cites.innerHTML = "";
  for (const c of result.citations) {
    const li = document.createElement("li");
    const evidence = c.source_fact_ids && c.source_fact_ids.length
      ? ` · ${c.source_fact_ids.length} source facts` : "";
    li.innerHTML = `<span class="cite-kind">${esc(c.kind)}</span><br>${esc(c.text)}<span class="muted">${evidence}</span>`;
    cites.appendChild(li);
  }

  const calls = $("toolcalls");
  calls.innerHTML = "";
  for (const t of result.tool_calls) {
    const li = document.createElement("li");
    li.textContent = t.error ? `${t.name} — error: ${t.error}` : `${t.name}(${Object.keys(t.arguments).join(", ")})`;
    calls.appendChild(li);
  }
  recordMetric(result);
}

function recordMetric(result) {
  state.metrics.push({
    grounded: result.used_memory || result.citations.length > 0,
    citations: result.citations.length,
  });
  renderLearningChart();
}

function renderLearningChart() {
  const svg = $("learning-chart");
  const samples = state.metrics;
  if (!samples.length) {
    svg.innerHTML = '<text x="12" y="62" fill="#8b97b5" font-size="11">No drafts yet</text>';
    return;
  }
  const W = 300, H = 120, pad = 8;
  let run = 0;
  const series = samples.map((s, i) => { if (s.grounded) run += 1; return run / (i + 1); });
  const x = (i) => pad + (i / Math.max(samples.length - 1, 1)) * (W - 2 * pad);
  const y = (v) => H - pad - v * (H - 2 * pad);
  const path = series.map((v, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(" ");
  const last = series[series.length - 1];
  const avg = samples.reduce((a, b) => a + b.citations, 0) / samples.length;
  svg.innerHTML =
    `<line x1="${pad}" y1="${y(0)}" x2="${W - pad}" y2="${y(0)}" stroke="#28324f"/>` +
    `<line x1="${pad}" y1="${y(1)}" x2="${W - pad}" y2="${y(1)}" stroke="#28324f"/>` +
    `<path d="${path}" fill="none" stroke="#6ea8fe" stroke-width="2"/>`;
  $("learning-stats").textContent =
    `${(last * 100).toFixed(0)}% grounded over ${samples.length} drafts · avg ${avg.toFixed(1)} memories cited`;
}

async function loadRegressions() {
  $("btn-regressions").disabled = true;
  setStatus("Reflecting over every ticket to audit for regressions…");
  try {
    const data = await api("/api/regressions");
    const regs = data.regressions || [];
    $("reg-count").textContent = `· ${regs.length}`;
    const list = $("regressions");
    list.innerHTML = "";
    if (!regs.length) {
      list.innerHTML = "<li>No regressions detected.</li>";
    }
    for (const r of regs) {
      const li = document.createElement("li");
      li.innerHTML =
        `<strong>${esc(r.issue || "issue")}</strong><br>` +
        `<span class="muted">fixed in ${esc(r.previously_fixed_in || "?")} · back in ` +
        `${esc(r.currently_affected || "?")} · ${esc(String(r.affected_customers ?? "?"))} affected · ` +
        `${esc(r.confidence || "")}</span>`;
      list.appendChild(li);
    }
    setStatus(`Regression audit complete: ${regs.length} found.`, "ok");
  } catch (err) {
    setStatus(`Regression audit failed: ${err.message}`, "error");
  } finally {
    $("btn-regressions").disabled = false;
  }
}

async function draftSelected() {
  if (!state.selected) return;
  const item = state.tickets.find((x) => x.ticket.id === state.selected);
  if (!item) return;
  $("btn-draft").disabled = true;
  setStatus(`Drafting ${state.selected} in ${state.mode} mode…`);
  try {
    const result = await api(`/api/tickets/${state.selected}/process?mode=${state.mode}`, { method: "POST" });
    renderDraft(result);
    setStatus(`Drafted ${state.selected} (${result.mode}).`, "ok");
    await loadEmerging();
  } catch (err) {
    setStatus(`Error: ${err.message}`, "error");
  } finally {
    $("btn-draft").disabled = false;
  }
}

async function loadEmerging() {
  try {
    const model = await api("/api/emerging-issues");
    $("emerging").textContent = model.content || "—";
    $("ei-refreshed").textContent = model.last_refreshed_at
      ? `· refreshed ${new Date(model.last_refreshed_at).toLocaleTimeString()}` : "";
  } catch (err) { /* not seeded yet */ }
}

async function bootstrap() {
  $("btn-seed").disabled = true;
  setStatus("Seeding historical tickets into memory… (this waits for Hindsight to consolidate)");
  try {
    const out = await api("/api/bootstrap", { method: "POST" });
    setStatus(`Seeded ${out.seeded_tickets} tickets across ${out.customers} customers.`, "ok");
    await loadEmerging();
  } catch (err) {
    setStatus(`Seed failed: ${err.message}`, "error");
  } finally {
    $("btn-seed").disabled = false;
  }
}

function addToQueue(item) {
  state.tickets.push(item);
  renderQueue();
}

async function playStream() {
  if (state.streaming) return;
  state.streaming = true;
  state.metrics = [];
  renderLearningChart();
  setStatus("Live ticket stream running…");
  const source = new EventSource("/api/stream?delay=2.5");
  source.addEventListener("ticket", async (event) => {
    const item = JSON.parse(event.data);
    addToQueue(item);
    if ($("auto-process").checked) {
      selectTicket(item);
      await draftSelected();
    }
  });
  source.addEventListener("done", () => {
    source.close();
    state.streaming = false;
    setStatus("Stream complete.", "ok");
  });
  source.onerror = () => {
    source.close();
    state.streaming = false;
    setStatus("Stream ended.", "ok");
  };
}

function setMode(mode) {
  state.mode = mode;
  $("mode-memory").classList.toggle("active", mode === "memory");
  $("mode-amnesia").classList.toggle("active", mode === "amnesia");
  $("draft-mode").textContent = mode;
}

async function init() {
  try {
    const cfg = await api("/api/config");
    $("badge-memory").textContent = `memory: ${cfg.memory_kind || "—"}`;
    $("badge-model").textContent = `model: ${cfg.model}`;
    $("badge-bank").textContent = `bank: ${cfg.org_bank_id}`;
    if (cfg.service_error) setStatus(`Backend not ready: ${cfg.service_error}`, "error");
  } catch (err) {
    setStatus(`Config error: ${err.message}`, "error");
  }

  try {
    const stream = await api("/api/demo-stream");
    state.tickets = stream;
    renderQueue();
  } catch (err) {
    setStatus(`Could not load demo stream: ${err.message}`, "error");
  }

  await loadEmerging();

  $("mode-memory").onclick = () => setMode("memory");
  $("mode-amnesia").onclick = () => setMode("amnesia");
  $("btn-seed").onclick = bootstrap;
  $("btn-stream").onclick = playStream;
  $("btn-draft").onclick = draftSelected;
  $("btn-regressions").onclick = loadRegressions;
}

init();
