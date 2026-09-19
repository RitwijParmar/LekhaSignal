const byId = (id) => document.getElementById(id);
const escapeHtml = (value) => String(value).replace(/[&<>'"]/g, (char) => ({ "&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;","\"":"&quot;" })[char]);

function addMessage(kind, text) {
  const item = document.createElement("article");
  item.className = `${kind}-message`;
  item.innerHTML = `<span>${kind === "user" ? "OPERATOR" : "LEKHASIGNAL"}</span><p>${escapeHtml(text)}</p>`;
  byId("dialogue").append(item);
  item.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function renderOverview(data) {
  byId("metrics").innerHTML = data.metrics.map((metric) => `<article class="metric"><p>${escapeHtml(metric.name)}</p><strong>${escapeHtml(metric.value)}</strong><span>${escapeHtml(metric.target)} · ${escapeHtml(metric.evidence)}</span></article>`).join("");
  byId("timeline").innerHTML = data.timeline.map((item) => `<article class="event"><time>${escapeHtml(item.time)}</time><p>${escapeHtml(item.event)}</p></article>`).join("");
}

function renderInvestigation(data) {
  const incident = data.incident;
  const assets = incident.affected_assets.map((asset) => `<li>${escapeHtml(asset)}</li>`).join("");
  const evidence = incident.evidence.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
  const steps = data.steps.map((step) => `<div class="agent-step"><div><strong>${escapeHtml(step.agent)}</strong><p>${escapeHtml(step.finding)}</p></div><span>${escapeHtml(step.status)}</span></div>`).join("");
  const panel = byId("incident");
  panel.classList.remove("hidden");
  panel.innerHTML = `<div class="incident-head"><div><p class="eyebrow">INVESTIGATION ${escapeHtml(incident.incident_id)}</p><h2>${escapeHtml(incident.title)}</h2></div><span class="severity ${escapeHtml(incident.severity)}">${escapeHtml(incident.severity)}</span></div><p class="lede">${escapeHtml(data.operator_summary)}</p><div class="incident-grid"><article class="incident-box"><h3>BUSINESS IMPACT</h3><p>${escapeHtml(incident.business_impact)}</p><h3>AFFECTED GOVERNED ASSETS</h3><ul>${assets}</ul></article><article class="incident-box"><h3>READ-ONLY EVIDENCE</h3><ul>${evidence}</ul><h3>SAFE PROPOSED RECOVERY</h3><p>${escapeHtml(incident.safe_action)}</p></article><article class="incident-box"><h3>BOUNDED AGENT HANDOFFS</h3><div class="agent-list">${steps}</div></article><article class="incident-box"><h3>HUMAN CONTROL</h3><p>${escapeHtml(data.approval_boundary)}</p><p><strong>Nothing has been changed.</strong> LekhaSignal has prepared an evidence-backed recovery plan only.</p></article></div>`;
  panel.scrollIntoView({ behavior: "smooth", block: "start" });
}

async function boot() { const response = await fetch("/api/overview"); renderOverview(await response.json()); }
byId("investigation-form").addEventListener("submit", async (event) => { event.preventDefault(); const input = byId("question"); const message = input.value.trim(); if (!message) return; addMessage("user", message); input.value = ""; const response = await fetch("/api/investigate", { method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({message}) }); const data = await response.json(); addMessage("assistant", data.operator_summary); renderInvestigation(data); });
boot();
