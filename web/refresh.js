// On-demand refresh: streams progress via SSE (one progress bar per stage).
"use strict";

(function () {
  const btn = document.getElementById("refresh-btn");
  const input = document.getElementById("token-input");
  const toast = document.getElementById("toast");
  const progBox = document.getElementById("refresh-progress");
  const progBar = document.getElementById("refresh-bar-fill");
  const progLab = document.getElementById("refresh-progress-label");

  function showToast(msg, kind, ms) {
    toast.textContent = msg;
    toast.className = "toast show" + (kind ? " " + kind : "");
    clearTimeout(toast._t);
    if (ms) toast._t = setTimeout(() => (toast.className = "toast"), ms);
  }

  function setProgress(pct, label, kind) {
    progBox.hidden = false;
    progBar.style.width = Math.max(0, Math.min(100, pct)) + "%";
    if (kind) progBar.dataset.kind = kind; else delete progBar.dataset.kind;
    if (label) progLab.textContent = label;
  }

  function hideProgress() { progBox.hidden = true; progBar.style.width = "0%"; }

  function renderToast(d) {
    const verdict = d.verdict || d.regime_label || "—";
    const ow = (d.overweight && d.overweight.length) ? "·超配 " + d.overweight.join("/") : "";
    const newRows = (d.n_etf_updated || 0) + (d.n_idx_updated || 0);
    const fresh = newRows > 0
      ? `· ${d.n_etf_updated || 0} ETF + ${d.n_idx_updated || 0} 指数 新增数据`
      : "· 已是最新（无新增）";
    return `✓ 数据已更新到 ${d.asof} ${fresh} · 风险分 ${d.composite_score}(${d.band}) · `
      + `大势 ${verdict}${ow} · 即将刷新页面…`;
  }

  async function refresh() {
    if (!input.value.trim()) {
      showToast("✗ 请先填 Tushare token（每次必填，不存盘）", "err", 5000);
      input.focus();
      return;
    }
    btn.disabled = true;
    const label = btn.textContent;
    btn.textContent = "刷新中…";
    setProgress(2, "启动…");

    try {
      const r = await fetch("/api/refresh", {
        method: "POST",
        headers: { "Content-Type": "application/json", "Accept": "text/event-stream" },
        body: JSON.stringify({ token: input.value }),
      });
      input.value = "";

      const reader = r.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buf = "", finalResult = null, errMsg = null;
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buf += decoder.decode(value, { stream: true });
        let idx;
        while ((idx = buf.indexOf("\n\n")) !== -1) {        // SSE event terminator
          const raw = buf.slice(0, idx).trim();
          buf = buf.slice(idx + 2);
          if (!raw.startsWith("data:")) continue;
          let evt;
          try { evt = JSON.parse(raw.slice(5).trim()); }
          catch { continue; }
          if (evt.type === "step") {
            setProgress(evt.pct ?? 0, evt.label || "处理中…");
          } else if (evt.type === "done") {
            setProgress(100, "完成");
            finalResult = evt.result || {};
          } else if (evt.type === "error") {
            errMsg = evt.error || "未知错误";
            setProgress(0, "✗ " + errMsg, "err");
          }
        }
      }
      if (finalResult) {
        showToast(renderToast(finalResult), "ok", 0);
        setTimeout(() => location.reload(), 1500);
      } else {
        showToast("✗ 刷新失败：" + (errMsg || "无响应"), "err", 9000);
        btn.disabled = false; btn.textContent = label;
        setTimeout(hideProgress, 1500);
      }
    } catch (e) {
      showToast("✗ 请求失败，后端是否在运行？" + (e.message || ""), "err", 9000);
      btn.disabled = false; btn.textContent = label;
      setTimeout(hideProgress, 1500);
    }
  }

  btn.addEventListener("click", refresh);
  input.addEventListener("keydown", (e) => { if (e.key === "Enter") refresh(); });
})();
