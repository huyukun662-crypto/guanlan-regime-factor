// Dashboard renderer — fetches /api/dashboard and paints the gauge, cards, FOF panels.
"use strict";

const $ = (id) => document.getElementById(id);
const pct = (v) => (v === null || v === undefined ? "—" : (v * 100).toFixed(2) + "%");
const num = (v) => (v === null || v === undefined ? "—" : v.toFixed(2));

async function boot() {
  try {
    const h = await fetch("/api/health").then((r) => r.json());
    const pill = $("health-pill");
    pill.textContent = h.key_available ? "● 实时 AI 已连接" : "● 离线建议模式";
    pill.className = "pill " + (h.key_available ? "ok" : "off");
  } catch (_) { $("health-pill").textContent = "● 后端未连接"; }

  let data;
  try {
    const r = await fetch("/api/dashboard");
    if (!r.ok) throw new Error("run pipeline first");
    data = await r.json();
  } catch (e) {
    $("error-banner").hidden = false;
    $("error-banner").textContent =
      "未能加载 outputs/dashboard.json — 请先运行 `python scripts/run_pipeline.py`。";
    return;
  }
  window.__dash = data;
  renderRegime(data.regime);
  renderMaster(data.master);
  renderCards(data.regime.indicators);
  renderTrend(data.regime.score_trend);
  renderDetails(data.regime.indicators);
}

// ---------------------------------------------------------------- regime gauge
function renderRegime(reg) {
  $("asof-pill").textContent = "最近交易日 " + reg.asof;
  $("asof-pill").title = "数据取到最近一个 A 股交易日（周末/节假日休市，故可能不是今天）";
  $("gauge-score").textContent = reg.composite_score.toFixed(0);
  $("gauge-band").textContent = reg.band + "风险";
  $("regime-label").textContent = reg.regime_label;
  $("exposure").textContent = (reg.equity_exposure * 100).toFixed(0) + "%";
  $("advice-baseline").textContent = reg.advice_baseline;
  if ($("top-score")) $("top-score").textContent = reg.top_score == null ? "—" : reg.top_score.toFixed(0);
  if ($("bot-score")) $("bot-score").textContent = reg.bottom_score == null ? "—" : reg.bottom_score.toFixed(0);
  const cs = reg.category_scores || {};
  const catBadge = (id, c) => {
    const e = $(id);
    if (e && c) e.innerHTML = `<span class="cs-top">顶${c.top == null ? "—" : c.top}</span>`
      + ` <span class="cs-bot">底${c.bottom == null ? "—" : c.bottom}</span>`;
  };
  catBadge("cat-tech-score", cs["技术面"]);
  catBadge("cat-fund-score", cs["基本面"]);
  catBadge("cat-senti-score", cs["情绪资金"]);
  const tag = $("regime-tag");
  tag.textContent = reg.regime_label;
  tag.className = "tag " + reg.regime_label;
  drawGauge(reg.composite_score);
}

// ---------------------------------------------------------------- 大势研判 (HMM×ER×基本面)
const STATE_COLORS = { "危机": "#e2503f", "平静": "#8d99ae", "履冰": "#e8a13a", "稳态": "#1aa861" };
const STATE_CODE_COLOR = ["#e2503f", "#8d99ae", "#e8a13a", "#1aa861"]; // by state_code 0..3
let _masterChart = null, _masterRadar = null;
const MCHARTS = {};                 // canvasId -> Chart，供「重置缩放」按钮
const MZOOM = {                     // 按住拖动=平移时间轴 + 滚轮缩放 + Shift拖拽=框选放大
  zoom: {
    wheel: { enabled: true },
    drag: { enabled: true, modifierKey: "shift",
            backgroundColor: "rgba(47,109,246,.12)", borderColor: "#2f6df6", borderWidth: 1 },
    mode: "x",
  },
  pan: { enabled: true, mode: "x" },
  limits: { x: { minRange: 5 } },
};
function regM(id, chart) { MCHARTS[id] = chart; return chart; }
function _ma(arr, w) {              // 简单滑动均值（忽略 null），用于平滑噪声大的 ER
  return arr.map((_, i) => {
    let s = 0, n = 0;
    for (let j = Math.max(0, i - w + 1); j <= i; j++) {
      const v = arr[j];
      if (v != null) { s += v; n += 1; }
    }
    return n ? s / n : null;
  });
}

function renderMaster(m) {
  if (!m) return;
  const vColor = m.verdict === "走强" ? "#e2503f" : m.verdict === "走弱" ? "#1aa861" : "#8d99ae";
  const vEl = $("master-verdict");
  vEl.textContent = m.verdict;
  vEl.style.color = vColor;
  $("master-score").textContent = m.master_score == null ? "—" : m.master_score;
  $("master-conf").textContent = (m.confidence == null ? "—" : m.confidence) + "%";
  const stEl = $("master-state");
  stEl.textContent = m.hmm.state_name;
  stEl.style.color = STATE_COLORS[m.hmm.state_name] || "var(--ink)";
  if ($("master-streak")) $("master-streak").textContent = (m.streak_days || 0) + " 交易日";

  const post = m.hmm.posterior || {};
  $("master-post").innerHTML = (m.hmm.states_order || []).map((n) => {
    const p = post[n] == null ? 0 : post[n];
    return `<div class="mp-row"><span class="mp-name" style="color:${STATE_COLORS[n]}">${n}</span>`
      + `<span class="mp-bar"><i style="width:${(p * 100).toFixed(0)}%;background:${STATE_COLORS[n]}"></i></span>`
      + `<b>${(p * 100).toFixed(0)}%</b></div>`;
  }).join("");

  $("master-er").textContent = `${m.er.value == null ? "—" : m.er.value} (${m.er.tag})`;
  $("master-fund").textContent = m.fundamental.score == null ? "—" : `${m.fundamental.score} (${m.fundamental.tag})`;
  $("master-gate").textContent = m.gate_label || "—";
  $("master-advice").textContent = m.advice || "";

  drawMasterGauge(m.master_score, vColor);
  renderRibbon(m.history);
  renderTransition(m.transition);
  renderStateStats(m.state_stats);
  renderSegments(m.segments);
  drawMasterRadar(m.axes);
  drawMasterChart(m.history, m.index_name || "基准指数");

  document.querySelectorAll(".zoom-reset").forEach((b) => {
    if (b._wired) return;
    b._wired = true;
    b.addEventListener("click", () => { const c = MCHARTS[b.dataset.target]; if (c) c.resetZoom(); });
  });
}

// 进攻↔防御 半圆仪表盘（复用 arc/pAng；左防御绿 → 中性灰 → 右进攻红）
function drawMasterGauge(score, vColor) {
  const el = $("master-gauge");
  if (!el || score == null) return;
  const cx = 120, cy = 128, r = 92;
  const bands = [[0, 40, "#1aa861"], [40, 60, "#8d99ae"], [60, 100, "#e2503f"]];
  let svg = "";
  for (const [a, b, c] of bands)
    svg += `<path d="${arc(cx, cy, r, a, b)}" stroke="${c}" stroke-width="15" fill="none" stroke-linecap="butt"/>`;
  const s = Math.max(0, Math.min(100, score));
  const [nx, ny] = pAng(cx, cy, r - 16, s);
  svg += `<line x1="${cx}" y1="${cy}" x2="${nx}" y2="${ny}" stroke="#1d2733" stroke-width="3" stroke-linecap="round"/>`;
  svg += `<circle cx="${cx}" cy="${cy}" r="6" fill="${vColor || "#1d2733"}"/>`;
  svg += `<text x="22" y="146" font-size="11" fill="#1aa861" font-weight="700">走弱</text>`;
  svg += `<text x="198" y="146" font-size="11" fill="#e2503f" font-weight="700">走强</text>`;
  el.innerHTML = svg;
}

// 状态色带时间轴（当日主状态着色细格）
function renderRibbon(h) {
  const el = $("master-ribbon");
  if (!el || !h || !h.state_code) return;
  el.innerHTML = h.state_code.map((c) =>
    `<span style="background:${c == null ? "#eef2f7" : STATE_CODE_COLOR[c]}"></span>`).join("");
}

// HMM 4×4 转移矩阵热力图（蓝标度，对角=持续概率）
function renderTransition(t) {
  const el = $("master-transition");
  if (!el) return;
  if (!t || !t.matrix) { el.innerHTML = '<p class="muted small">转移矩阵不可用（暖机期或拟合失败）。</p>'; return; }
  const labels = t.labels, mat = t.matrix;
  let h = '<table class="trans-table"><tr><th></th>'
    + labels.map((l) => `<th style="color:${STATE_COLORS[l]}">${l}</th>`).join("") + "</tr>";
  for (const a of labels) {
    h += `<tr><th style="color:${STATE_COLORS[a]}">${a}</th>`;
    for (const b of labels) {
      const v = mat[a][b];
      h += `<td style="background:rgba(47,109,246,${0.06 + 0.85 * v});color:${v > 0.5 ? "#fff" : "#33414f"}">`
        + `${(v * 100).toFixed(0)}</td>`;
    }
    h += "</tr>";
  }
  // 黏性摘要 + 最可能迁移路径（每行对角外最大）
  const avgDiag = labels.reduce((s, a) => s + mat[a][a], 0) / labels.length;
  const avgDur = avgDiag < 1 ? (1 / (1 - avgDiag)).toFixed(1) : "∞";
  const moves = labels.map((a) => {
    const best = labels.filter((b) => b !== a).reduce((m, b) => (mat[a][b] > mat[a][m] ? b : m),
      labels.find((b) => b !== a));
    return mat[a][best] >= 0.01
      ? `<span class="move-chip"><b style="color:${STATE_COLORS[a]}">${a}</b>→<b style="color:${STATE_COLORS[best]}">${best}</b> ${(mat[a][best] * 100).toFixed(0)}%</span>`
      : "";
  }).filter(Boolean).join("");
  el.innerHTML = h + "</table>"
    + `<p class="trans-note">状态黏性：平均<b>月度</b>自持概率 <b>${(avgDiag * 100).toFixed(0)}%</b>，对应状态平均持续约 <b>${avgDur} 个月</b>。最可能的迁移：${moves || "—"}</p>`;
}

// 状态画像：各状态覆盖段的实测年化/波动（语义证据表）
function renderStateStats(ss) {
  const el = $("master-stats");
  if (!el) return;
  if (!ss || !ss.length) { el.innerHTML = '<p class="muted small">暂无数据。</p>'; return; }
  const pc = (v) => (v == null ? "—" : (v * 100).toFixed(1) + "%");
  let h = '<table class="trans-table"><tr><th>状态</th><th>月数</th><th>实测年化</th><th>实测波动</th></tr>';
  for (const r of ss) {
    const annCol = r.ann == null ? "var(--muted)" : r.ann >= 0 ? "#e2503f" : "#1aa861";
    h += `<tr><th style="color:${STATE_COLORS[r.state]}">${r.state}</th>`
      + `<td>${r.months}</td>`
      + `<td style="color:${annCol};font-weight:700">${pc(r.ann)}</td>`
      + `<td>${pc(r.vol)}</td></tr>`;
  }
  el.innerHTML = h + "</table>";
}

// 近期状态段：连续同状态区间 + 区间涨跌
function renderSegments(segs) {
  const el = $("master-segments");
  if (!el) return;
  if (!segs || !segs.length) { el.innerHTML = '<p class="muted small">暂无数据。</p>'; return; }
  const pc = (v) => (v == null ? "—" : (v >= 0 ? "+" : "") + (v * 100).toFixed(1) + "%");
  let h = '<table class="trans-table"><tr><th>状态</th><th>起止</th><th>时长</th><th>区间涨跌</th></tr>';
  for (const s of [...segs].reverse()) {                  // 最近的排最上
    const rc = s.ret == null ? "var(--muted)" : s.ret >= 0 ? "#e2503f" : "#1aa861";
    h += `<tr><th style="color:${STATE_COLORS[s.state]}">${s.state}</th>`
      + `<td>${s.start}${s.start === s.end ? "" : " ~ " + s.end}</td>`
      + `<td>${s.months} 月</td>`
      + `<td style="color:${rc};font-weight:700">${pc(s.ret)}</td></tr>`;
  }
  el.innerHTML = h + "</table>";
}

// 三轴罗盘 radar（HMM姿态 / 效率比 / 基本面，0-100）
function drawMasterRadar(axes) {
  if (!axes || !$("master-radar")) return;
  const labels = Object.keys(axes);
  const data = labels.map((k) => (axes[k] == null ? 0 : axes[k]));
  const chips = $("master-axes");
  if (chips) chips.innerHTML = labels.map((k) => {
    const v = axes[k];
    const col = v == null ? "var(--muted)" : v >= 60 ? "#e2503f" : v <= 40 ? "#1aa861" : "var(--ink)";
    return `<span class="axis-chip">${k} <b style="color:${col}">${v == null ? "—" : v}</b></span>`;
  }).join("");
  if (_masterRadar) _masterRadar.destroy();
  _masterRadar = new Chart($("master-radar"), {
    type: "radar",
    data: { labels, datasets: [{ label: "大势三轴", data, borderColor: "#2f6df6",
      backgroundColor: "rgba(47,109,246,.18)", borderWidth: 2, pointBackgroundColor: "#2f6df6", pointRadius: 3 }] },
    options: {
      responsive: true, plugins: { legend: { display: false } },
      scales: { r: { min: 0, max: 100, ticks: { stepSize: 25, font: { size: 9 }, backdropColor: "transparent" },
        pointLabels: { font: { size: 11 } }, grid: { color: "#e6ecf4" }, angleLines: { color: "#e6ecf4" } } },
    },
  });
}

function drawMasterChart(h, idxName) {
  if (!h || !$("master-chart")) return;
  const segColor = (ctx) => {
    const c = h.state_code[ctx.p0DataIndex];
    return c == null ? "#ccced3" : STATE_CODE_COLOR[c];
  };
  const erSmooth = _ma(h.er, 7);                       // 数据为 3 日降采样，7 点 ≈ 21 个交易日
  const bvals = h.benchmark.filter((v) => v != null);
  const bmin = Math.min(...bvals), bmax = Math.max(...bvals);
  if (_masterChart) _masterChart.destroy();
  _masterChart = regM("master-chart", new Chart($("master-chart"), {
    type: "line",
    data: {
      labels: h.dates,
      datasets: [
        { label: (idxName || "基准指数") + "（按状态着色）", data: h.benchmark, yAxisID: "y", borderColor: "#8d99ae",
          borderWidth: 2.4, pointRadius: 0, tension: 0.05, segment: { borderColor: segColor } },
        { label: "效率比 ER（21日平滑）", data: erSmooth, yAxisID: "y2", borderColor: "#e8a13a",
          backgroundColor: "rgba(232,161,58,.10)", fill: true,
          borderWidth: 1.2, pointRadius: 0, tension: 0.3 },
      ],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: { legend: { position: "top", labels: { boxWidth: 12, font: { size: 10 } } }, zoom: MZOOM },
      scales: {
        x: { ticks: { maxTicksLimit: 8, font: { size: 10 } }, grid: { display: false } },
        y: { position: "left", min: Math.floor(bmin * 0.97 * 100) / 100,
             max: Math.ceil(bmax * 1.03 * 100) / 100,   // 价格轴贴合数据，不从 0 起（避免压扁）
             ticks: { font: { size: 10 } }, grid: { color: "#eef2f7" } },
        y2: { position: "right", min: 0, max: 1, grid: { display: false }, ticks: { font: { size: 10 } } },
      },
    },
  }));
}

function pAng(cx, cy, r, score) {
  const t = (Math.PI / 180) * (180 - score * 1.8);
  return [cx + r * Math.cos(t), cy - r * Math.sin(t)];
}
function arc(cx, cy, r, s1, s2) {
  const [x1, y1] = pAng(cx, cy, r, s1), [x2, y2] = pAng(cx, cy, r, s2);
  return `M ${x1} ${y1} A ${r} ${r} 0 0 1 ${x2} ${y2}`;
}
function drawGauge(score) {
  const cx = 120, cy = 128, r = 92;
  const bands = [[0, 20, "#1aa861"], [20, 40, "#6cc04a"], [40, 60, "#e8a13a"],
                 [60, 80, "#e8743a"], [80, 100, "#e2503f"]];
  let svg = "";
  for (const [a, b, c] of bands)
    svg += `<path d="${arc(cx, cy, r, a, b)}" stroke="${c}" stroke-width="15"
            fill="none" stroke-linecap="butt"/>`;
  const [nx, ny] = pAng(cx, cy, r - 16, Math.max(0, Math.min(100, score)));
  svg += `<line x1="${cx}" y1="${cy}" x2="${nx}" y2="${ny}" stroke="#1d2733"
          stroke-width="3" stroke-linecap="round"/>`;
  svg += `<circle cx="${cx}" cy="${cy}" r="6" fill="#1d2733"/>`;
  $("gauge-svg").innerHTML = svg;
}

// ---------------------------------------------------------------- GuanLan 顶/底 cards (3 panels)
function renderCards(cards) {
  const n = (v) => (v == null ? "—" : Math.round(v));
  const cardHtml = (c) => {
    const top = c.top == null ? 0 : c.top, bot = c.bottom == null ? 0 : c.bottom;
    const tagCls = c.tag === "顶" ? "top" : c.tag === "底" ? "bot" : "mid";
    const tagHtml = c.tag && c.tag !== "—"
      ? `<span class="gl-tag ${tagCls}">${c.tag}</span>` : "";
    return `<div class="gl-card ${c.available ? "" : "dim"}">
      <div class="gl-top"><span class="gl-name">${c.name}</span>
        <span class="gl-wt">${Math.round(c.weight * 100)}%</span></div>
      <div class="gl-val">${c.value}${tagHtml}</div>
      <div class="gl-bar"><span class="fill top" style="width:${top}%"></span><b>${n(c.top)}</b></div>
      <div class="gl-bar"><span class="fill bot" style="width:${bot}%"></span><b>${n(c.bottom)}</b></div>
      <div class="gl-explain">${c.explain}</div>
    </div>`;
  };
  const groups = { "技术面": "grid-tech", "基本面": "grid-fund", "情绪资金": "grid-senti" };
  for (const [cat, id] of Object.entries(groups)) {
    const el = $(id);
    if (el) el.innerHTML = cards.filter((c) => c.category === cat).map(cardHtml).join("");
  }
}

// ---------------------------------------------------------------- risk score & trend
let _trendChart = null, _trend = null, _tIndex = null, _tRange = 250;
function renderTrend(tr) {
  if (!tr) return;
  _trend = tr;
  const names = Object.keys(tr.indices || {});
  _tIndex = names[0] || null;
  $("index-tabs").innerHTML = names.map((nm, i) =>
    `<button data-index="${nm}" class="${i === 0 ? "active" : ""}">${nm}</button>`).join("");
  $("index-tabs").querySelectorAll("button").forEach((b) =>
    b.addEventListener("click", () => { setActive($("index-tabs"), b); _tIndex = b.dataset.index; drawTrend(); }));
  $("range-tabs").querySelectorAll("button").forEach((b) =>
    b.addEventListener("click", () => { setActive($("range-tabs"), b); _tRange = +b.dataset.range; drawTrend(); }));
  drawTrend();
}
function setActive(group, btn) {
  group.querySelectorAll("button").forEach((x) => x.classList.remove("active"));
  btn.classList.add("active");
}
function drawTrend() {
  const tr = _trend, total = tr.dates.length;
  const k = _tRange > 0 ? Math.max(0, total - _tRange) : 0;
  const dates = tr.dates.slice(k), top = tr.top.slice(k), bot = tr.bottom.slice(k);
  const idx = (tr.indices[_tIndex] || []).slice(k);
  if (_trendChart) _trendChart.destroy();
  _trendChart = new Chart($("trend-chart"), {
    type: "line",
    data: { labels: dates, datasets: [
      { label: "顶部分", data: top, borderColor: "#e2503f", backgroundColor: "rgba(226,80,63,.12)",
        fill: true, yAxisID: "y2", pointRadius: 0, borderWidth: 1.3, tension: 0.25 },
      { label: "底部分", data: bot, borderColor: "#1aa861", backgroundColor: "rgba(26,168,97,.12)",
        fill: true, yAxisID: "y2", pointRadius: 0, borderWidth: 1.3, tension: 0.25 },
      { label: _tIndex, data: idx, borderColor: "#e8a13a", yAxisID: "y",
        pointRadius: 0, borderWidth: 2, tension: 0.05 },
    ] },
    options: {
      responsive: true, interaction: { mode: "index", intersect: false },
      plugins: { legend: { position: "top", labels: { boxWidth: 16, font: { size: 12 } } } },
      scales: {
        x: { ticks: { maxTicksLimit: 8, font: { size: 11 } }, grid: { display: false } },
        y: { position: "left", ticks: { font: { size: 11 } }, grid: { color: "#eef2f7" } },
        y2: { position: "right", min: 0, max: 100, ticks: { font: { size: 11 } }, grid: { display: false } },
      },
    },
  });
}

// ---------------------------------------------------------------- indicator detail
function renderDetails(cards) {
  $("detail-list").innerHTML = cards.map((c) => `
    <div class="detail-card">
      <div class="detail-head"><h3>${c.name}</h3>
        <span class="gl-wt">权重 ${Math.round(c.weight * 100)}%</span></div>
      <div class="detail-rows">
        <div><span class="dk">数据来源</span><span class="dv mono">${c.source}</span></div>
        <div><span class="dk">计算公式</span><span class="dv mono">${c.formula}</span></div>
      </div>
      <p class="detail-desc">${c.explain}</p>
      <div class="detail-rule"><span class="dk">评分规则</span> ${c.rule}</div>
    </div>`).join("");
}

boot();
