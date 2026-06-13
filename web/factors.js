// Standalone pure-factor board — cumulative returns + ranking + full-sample tear-sheet.
"use strict";

const $ = (id) => document.getElementById(id);
const PALETTE = ["#2f6df6", "#e2503f", "#1aa861", "#e8a13a", "#9b5de5", "#00b4d8",
                 "#8d99ae", "#e07a5f", "#3d405b", "#b5179e", "#06d6a0", "#7209b7"];
const returnColor = (v) => {
  const a = Math.min(1, Math.abs(v) / 0.08);
  return v >= 0 ? `rgba(226,80,63,${0.15 + 0.8 * a})` : `rgba(26,168,97,${0.15 + 0.8 * a})`;
};

let CUM = null, CHART = null, CAT = "全部", RANGE = 0;
const CATMAP = {};
const CHARTS = {};                 // canvasId -> Chart, for zoom-reset buttons

// chartjs-plugin-zoom config: 按住拖动=平移时间轴 + 滚轮缩放 + Shift拖拽=框选放大
const ZOOM = {
  zoom: {
    wheel: { enabled: true },
    drag: { enabled: true, modifierKey: "shift",
            backgroundColor: "rgba(47,109,246,.12)", borderColor: "#2f6df6", borderWidth: 1 },
    mode: "x",
  },
  pan: { enabled: true, mode: "x" },
  limits: { x: { minRange: 5 } },
};

function regChart(id, chart) { CHARTS[id] = chart; return chart; }

async function boot() {
  let d;
  try {
    const r = await fetch("/api/factors");
    if (!r.ok) throw new Error("no data");
    d = await r.json();
  } catch (e) {
    $("error-banner").hidden = false;
    $("error-banner").textContent = "未能加载 factors.json —— 请先运行 `python scripts/run_pipeline.py`。";
    return;
  }
  $("asof-pill").textContent = "数据 " + ((d.ranking && d.ranking.asof) || "—");
  $("nf-pill").textContent = (d.n_factors || "—") + " 因子";
  (d.ranking.factors || []).forEach((f) => (CATMAP[f.key] = f.category));
  renderRanking(d.ranking);
  renderTear(d.tearsheet);
  setupCumulative(d.cumulative);
  renderFactorIC(d.rotation_ic);
  renderFactorRollingSharpe(d.rolling_sharpe);

  document.querySelectorAll(".zoom-reset").forEach((b) =>
    b.addEventListener("click", () => { const c = CHARTS[b.dataset.target]; if (c) c.resetZoom(); }));
}

// 因子轮动 月度IC + 12月滚动ICIR —— 时间窗 tab（按月）+ 缩放，交互与累积收益图一致
let ICDATA = null, IC_RANGE = 0;

function renderFactorIC(ic) {
  if (!ic || !$("factor-ic-chart")) return;
  ICDATA = ic;
  $("ic-kpi").textContent = `ICIR ${ic.icir ?? "—"} · IC均值 ${ic.ic_mean ?? "—"} · `
    + `胜率 ${ic.hit_rate == null ? "—" : Math.round(ic.hit_rate * 100) + "%"}`;
  $("ic-range-tabs").querySelectorAll("button").forEach((b) =>
    b.addEventListener("click", () => { active($("ic-range-tabs"), b); IC_RANGE = +b.dataset.range; drawIC(); }));
  drawIC();
}

function drawIC() {
  const ic = ICDATA;
  const k0 = IC_RANGE > 0 ? Math.max(0, ic.dates.length - IC_RANGE) : 0;
  const dates = ic.dates.slice(k0), bars = ic.ic.slice(k0), icir = ic.rolling_icir.slice(k0);
  if (CHARTS["factor-ic-chart"]) CHARTS["factor-ic-chart"].destroy();
  regChart("factor-ic-chart", new Chart($("factor-ic-chart"), {
    data: { labels: dates, datasets: [
      { type: "bar", label: "月度IC", data: bars, yAxisID: "y", order: 2,
        backgroundColor: bars.map((v) => (v >= 0 ? "rgba(26,168,97,.55)" : "rgba(226,80,63,.55)")) },
      { type: "line", label: "12月滚动ICIR", data: icir, yAxisID: "y2", order: 1,
        borderColor: "#2f6df6", borderWidth: 2, pointRadius: 0, tension: 0.2 },
    ] },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { labels: { boxWidth: 16, font: { size: 12 } } }, zoom: ZOOM },
      scales: {
        x: { ticks: { maxTicksLimit: 8, font: { size: 10 } }, grid: { display: false } },
        y: { position: "left", min: -1, max: 1, ticks: { font: { size: 11 } },
             grid: { color: "#eef2f7" } },           // IC 秩相关 ∈ [-1,1]，锁轴防压扁
        y2: { position: "right", suggestedMin: -1, suggestedMax: 1,
              ticks: { font: { size: 11 } }, grid: { display: false } },
      },
    },
  }));
}

// 各因子 126日滚动 Sharpe —— 类别筛选 + 时间窗 tab + 缩放，交互与累积收益图一致
let RSDATA = null, RS_CAT = "全部", RS_RANGE = 0;

function renderFactorRollingSharpe(rs) {
  if (!rs || !$("factor-rs-chart")) return;
  RSDATA = rs;
  const cats = ["全部", ...new Set(Object.keys(rs.series).map((k) => CATMAP[k]).filter(Boolean))];
  $("rs-cat-tabs").innerHTML = cats.map((c, i) =>
    `<button data-cat="${c}" class="${i === 0 ? "active" : ""}">${c}</button>`).join("");
  $("rs-cat-tabs").querySelectorAll("button").forEach((b) =>
    b.addEventListener("click", () => { active($("rs-cat-tabs"), b); RS_CAT = b.dataset.cat; drawRS(); }));
  $("rs-range-tabs").querySelectorAll("button").forEach((b) =>
    b.addEventListener("click", () => { active($("rs-range-tabs"), b); RS_RANGE = +b.dataset.range; drawRS(); }));
  drawRS();
}

function drawRS() {
  const rs = RSDATA;
  const keys = Object.keys(rs.series).filter((k) => RS_CAT === "全部" || CATMAP[k] === RS_CAT);
  const pts = RS_RANGE > 0 ? Math.ceil(RS_RANGE / 5) : 0;     // 序列为每 5 个交易日采样
  const k0 = pts > 0 ? Math.max(0, rs.dates.length - pts) : 0;
  const dates = rs.dates.slice(k0);
  const dsets = keys.map((k, i) => ({
    label: (rs.labels && rs.labels[k]) || k, data: rs.series[k].slice(k0),
    borderColor: PALETTE[i % PALETTE.length], borderWidth: 1.6, pointRadius: 0, tension: 0.15,
  }));
  if (CHARTS["factor-rs-chart"]) CHARTS["factor-rs-chart"].destroy();
  regChart("factor-rs-chart", new Chart($("factor-rs-chart"), {
    type: "line", data: { labels: dates, datasets: dsets },
    options: {
      responsive: true, maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: { legend: { position: "top", labels: { boxWidth: 14, font: { size: 10 } } }, zoom: ZOOM },
      scales: {
        x: { ticks: { maxTicksLimit: 8, font: { size: 10 } }, grid: { display: false } },
        // 早期样本的极端 Sharpe 会把纵轴撑到 ±20、压扁全图；钳到 ±5（超出部分贴边）
        y: { min: -5, max: 5, ticks: { font: { size: 11 } }, grid: { color: "#eef2f7" } },
      },
    },
  }));
}

function active(group, btn) {
  group.querySelectorAll("button").forEach((x) => x.classList.remove("active"));
  btn.classList.add("active");
}

function setupCumulative(cum) {
  if (!cum) return;
  CUM = cum;
  const cats = ["全部", ...new Set(Object.keys(cum.series).map((k) => CATMAP[k]).filter(Boolean))];
  $("cat-tabs").innerHTML = cats.map((c, i) =>
    `<button data-cat="${c}" class="${i === 0 ? "active" : ""}">${c}</button>`).join("");
  $("cat-tabs").querySelectorAll("button").forEach((b) =>
    b.addEventListener("click", () => { active($("cat-tabs"), b); CAT = b.dataset.cat; draw(); }));
  $("range-tabs").querySelectorAll("button").forEach((b) =>
    b.addEventListener("click", () => { active($("range-tabs"), b); RANGE = +b.dataset.range; draw(); }));
  draw();
}

function draw() {
  const keys = Object.keys(CUM.series).filter((k) => CAT === "全部" || CATMAP[k] === CAT);
  const pts = RANGE > 0 ? Math.ceil(RANGE / 3) : 0;   // 序列为每 3 个交易日采样：天数→点数
  const total = CUM.dates.length, k0 = pts > 0 ? Math.max(0, total - pts) : 0;
  const dates = CUM.dates.slice(k0);
  const ds = keys.map((k, i) => {
    const win = CUM.series[k].slice(k0);
    const base = win.find((v) => v != null) || 1;        // re-base each line to 1.0 at window start
    return {
      label: CUM.labels[k] || k, data: win.map((v) => (v == null ? null : v / base)),
      borderColor: PALETTE[i % PALETTE.length], borderWidth: 1.6, pointRadius: 0, tension: 0.1,
    };
  });
  if (CHART) CHART.destroy();
  CHART = regChart("cum-chart", new Chart($("cum-chart"), {
    type: "line", data: { labels: dates, datasets: ds },
    options: {
      responsive: true, interaction: { mode: "index", intersect: false },
      plugins: { legend: { position: "top", labels: { boxWidth: 12, font: { size: 10 } } }, zoom: ZOOM },
      scales: {
        x: { ticks: { maxTicksLimit: 8, font: { size: 10 } }, grid: { display: false } },
        y: { ticks: { font: { size: 11 } }, grid: { color: "#eef2f7" } },
      },
    },
  }));
}

function renderRanking(rk) {
  if (!rk) return;
  const cell = (v) => (v == null ? "<td>—</td>"
    : `<td style="background:${returnColor(v)};color:${Math.abs(v) > 0.05 ? "#fff" : "#33414f"}">`
      + `${(v * 100).toFixed(1)}%</td>`);
  let h = "<table class='factor-table'><tr><th>排名</th><th>因子</th><th>类别</th>"
    + "<th>近1月</th><th>近3月</th><th>YTD</th></tr>";
  rk.factors.forEach((f, i) => {
    h += `<tr><td>${f.rank || i + 1}</td><td class="fname">${f.display}</td>`
      + `<td class="muted">${f.category}</td>${cell(f.r_1m)}${cell(f.r_3m)}${cell(f.r_ytd)}</tr>`;
  });
  $("factor-ranking").innerHTML = h + "</table>";
}

function renderTear(t) {
  if (!t) return;
  const pct = (v) => (v == null ? "—" : (v * 100).toFixed(1) + "%");
  const num = (v) => (v == null ? "—" : v.toFixed(2));
  const shBg = (v) => (v == null ? ""
    : `background:${v >= 0 ? `rgba(26,168,97,${0.1 + 0.35 * Math.min(1, v / 2)})` : "rgba(226,80,63,.18)"}`);
  let h = "<table class='factor-table'><tr><th>因子</th><th>类别</th><th>年化</th>"
    + "<th>夏普</th><th>最大回撤</th><th>波动率</th></tr>";
  for (const f of t.factors) {
    h += `<tr><td class="fname">${f.display}</td><td class="muted">${f.category}</td>`
      + `<td style="color:${f.ann != null && f.ann < 0 ? "#1aa861" : "#e2503f"}">${pct(f.ann)}</td>`
      + `<td style="${shBg(f.sharpe)}">${num(f.sharpe)}</td>`
      + `<td style="color:#e2503f">${pct(f.maxdd)}</td><td>${pct(f.vol)}</td></tr>`;
  }
  $("factor-tear").innerHTML = h + "</table>";
}

boot();
