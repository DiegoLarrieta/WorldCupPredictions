// WC Betting Desk — pure presentation. Reads data.json (built by scripts/build_dashboard.py).
// No API keys, no LLM. The engine runs in the Claude Code session and writes the data.

const fmt = (n) => (n < 0 ? "-" : "") + "$" + Math.abs(n).toLocaleString("es-MX");
const sign = (n) => (n > 0 ? "+" : "") + fmt(n);

async function load() {
  let d;
  try {
    d = await (await fetch("data.json", { cache: "no-store" })).json();
  } catch (e) {
    document.getElementById("fixtures").innerHTML =
      `<p class="no-rec">No pude leer data.json. Corre <code>python scripts/build_dashboard.py</code> y sirve la carpeta con <code>make dashboard</code>.</p>`;
    return;
  }
  renderMetrics(d.metrics);
  renderFixtures(d.fixtures || []);
  document.getElementById("updated").textContent =
    "actualizado " + new Date().toLocaleString("es-MX", { dateStyle: "medium", timeStyle: "short" });
}

function renderMetrics(m) {
  const bank = fmt(m.bank);
  document.getElementById("bank-badge").textContent = bank + " " + m.currency;
  const pnlCls = m.pnl > 0 ? "green" : m.pnl < 0 ? "red" : "blue";
  const cards = [
    { cls: "blue", k: "Banca", v: bank, sub: `inicio ${fmt(m.bankroll_start)} ${m.currency}` },
    { cls: "blue", k: "Apuestas", v: m.n_bets, sub: `${m.n_open} abiertas · ${m.n_settled} cerradas` },
    { cls: pnlCls, k: "Ganancias", v: sign(m.pnl), sub: m.hit_rate != null ? `acierto ${m.hit_rate}%` : "sin apuestas cerradas" },
    { cls: "amber", k: "En juego", v: fmt(m.in_play), sub: `${m.n_open} ${m.n_open === 1 ? "activa" : "activas"}` },
  ];
  document.getElementById("metrics").innerHTML = cards.map((c) => `
    <div class="card ${c.cls}">
      <div class="k">${c.k}</div>
      <div class="v">${c.v}</div>
      <div class="sub">${c.sub}</div>
    </div>`).join("");
}

function chk(hit) {
  if (hit === true) return `<span class="chk-y">✓</span>`;
  if (hit === false) return `<span class="chk-n">✗</span>`;
  return `<span class="chk-w">·</span>`;
}

function marketsTable(markets) {
  if (!markets.length) return "";
  const rows = markets.map((mk) => `
    <tr>
      <td class="mk-name">${mk.label}</td>
      <td class="prob">${mk.model}%<span class="bar" style="width:${Math.round(mk.model * 0.45)}px"></span></td>
      <td class="odds">${mk.odds && mk.odds.includes("fetch") ? "—" : mk.odds}</td>
      <td>${chk(mk.hit)}</td>
    </tr>`).join("");
  return `<div><h4>Mercados — prob. del modelo vs lo que paga</h4>
    <table><thead><tr><th>Mercado</th><th>Modelo</th><th>Paga</th><th></th></tr></thead>
    <tbody>${rows}</tbody></table></div>`;
}

function recsBlock(recs) {
  if (!recs.length)
    return `<div class="recs"><h4>Props recomendados</h4><p class="no-rec">Ninguno con valor + datos para este partido.</p></div>`;
  const total = recs.reduce((s, r) => s + r.stake, 0);
  const rows = recs.map((r) => `
    <div class="rec">
      <span class="who">${r.player} <small>o${r.line} ${r.market}</small></span>
      <span class="num"><span>${r.odds}</span><span class="prob">modelo ${r.model}%</span><span class="stake">$${r.stake.toLocaleString("es-MX")}</span></span>
    </div>`).join("");
  return `<div class="recs"><h4>Props recomendados · total $${total.toLocaleString("es-MX")} MXN</h4>${rows}</div>`;
}

const STAGE_LABEL = { knockout: "16avos de final", group: "Fase de grupos" };

function renderFixtures(fx) {
  // group by stage (knockout first), then by date within — already sorted by build_dashboard.
  const stages = {};
  fx.forEach((f) => { (stages[f.stage || "group"] ||= []).push(f); });
  const order = ["knockout", "group"].filter((s) => stages[s]);
  const html = order.map((stage) => {
    const byDate = {};
    stages[stage].forEach((f) => { (byDate[f.date || "Sin fecha"] ||= []).push(f); });
    const dates = Object.entries(byDate).map(([date, items], di) => {
      const cards = items.map((f, i) => fixtureCard(f, `${stage}-${date}-${i}`)).join("");
      return `<div class="date-group"><div class="date-label">${date}</div>${cards}</div>`;
    }).join("");
    return `<div class="stage"><h3 class="stage-head">${STAGE_LABEL[stage] || stage}
      <span class="stage-count">${stages[stage].length}</span></h3>${dates}</div>`;
  }).join("");
  document.getElementById("fixtures").innerHTML = html;

  document.querySelectorAll(".fx-row").forEach((row) => {
    row.addEventListener("click", () => {
      const fixture = row.closest(".fixture");
      fixture.classList.toggle("open");
      const btn = fixture.querySelector(".expand-btn");
      const open = fixture.classList.contains("open");
      btn.classList.toggle("open", open);
      btn.textContent = open ? "Cerrar" : (fixture.dataset.played === "true" ? "Ver predicción" : "Predecir partido");
    });
  });
}

function fixtureCard(f, id) {
  const status = f.played
    ? `<span class="status played"><span class="score">${f.score}</span> <span class="checks">· checks ${f.checks || "—"}</span></span>`
    : `<span class="status upcoming">Por jugarse</span>`;
  const btnLabel = f.played ? "Ver predicción" : "Predecir partido";
  return `
  <div class="fixture" data-played="${f.played}">
    <div class="fx-row">
      <div class="fx-teams">
        <span class="flag">${f.home_flag}</span>
        <span class="tnames">${f.home}<span class="vs">vs</span>${f.away}</span>
        <span class="flag">${f.away_flag}</span>
      </div>
      <div class="fx-meta">
        ${f.kickoff ? `<span class="ko">${f.kickoff.slice(11) || ""}</span>` : ""}
        ${status}
        <button class="expand-btn">${btnLabel}</button>
      </div>
    </div>
    <div class="detail">
      ${marketsTable(f.markets)}
      ${recsBlock(f.prop_recs)}
      ${f.caveat ? `<p class="caveat">⚠️ ${f.caveat.replace(/\*\*/g, "")}</p>` : ""}
      ${f.sug ? `<p class="sug">1X2/goles sugerido: ${f.sug}</p>` : ""}
    </div>
  </div>`;
}

load();
