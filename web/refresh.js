// On-demand refresh: optional Tushare token + rerun pipeline, then reload the dashboard.
"use strict";

(function () {
  const btn = document.getElementById("refresh-btn");
  const input = document.getElementById("token-input");
  const toast = document.getElementById("toast");

  function showToast(msg, kind, ms) {
    toast.textContent = msg;
    toast.className = "toast show" + (kind ? " " + kind : "");
    clearTimeout(toast._t);
    if (ms) toast._t = setTimeout(() => (toast.className = "toast"), ms);
  }

  async function refresh() {
    btn.disabled = true;
    const label = btn.textContent;
    btn.textContent = "刷新中…";
    showToast("正在重拉 Tushare 数据并重算（约 30–60 秒）…", "", 0);
    try {
      const r = await fetch("/api/refresh", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token: input.value }),
      });
      const d = await r.json();
      input.value = "";                     // never keep the token in the DOM
      if (d.ok) {
        const verdict = d.verdict || d.regime_label || "—";
        const ow = (d.overweight && d.overweight.length) ? "·超配 " + d.overweight.join("/") : "";
        showToast(`✓ 刷新成功 · ${d.asof} · 风险分 ${d.composite_score}(${d.band}) · `
          + `大势 ${verdict}${ow} · 即将刷新页面…`, "ok", 0);
        setTimeout(() => location.reload(), 1400);
      } else {
        showToast("✗ 刷新失败：" + (d.error || "未知错误"), "err", 9000);
        btn.disabled = false; btn.textContent = label;
      }
    } catch (e) {
      showToast("✗ 请求失败，后端是否在运行？", "err", 9000);
      btn.disabled = false; btn.textContent = label;
    }
  }

  btn.addEventListener("click", refresh);
  input.addEventListener("keydown", (e) => { if (e.key === "Enter") refresh(); });
})();
