// LLM 配置弹窗：让用户在浏览器里改 .env 中的 LLM_* 字段，无需手编辑文件。
// key 不显示当前值（password 框只写不读）；保存后 POST /api/llm_config 写入 .env + os.environ。
"use strict";

(function () {
  const btn = document.getElementById("llm-settings-btn");
  const dlg = document.getElementById("llm-dialog");
  if (!btn || !dlg) return;

  const providerSel = document.getElementById("llm-provider");
  const keyInput = document.getElementById("llm-key");
  const baseInput = document.getElementById("llm-base");
  const modelInput = document.getElementById("llm-model");
  const statusEl = document.getElementById("llm-status");
  const cancelBtn = document.getElementById("llm-cancel");
  const clearBtn = document.getElementById("llm-clear");
  const saveBtn = document.getElementById("llm-save");
  const healthPill = document.getElementById("health-pill");

  function applyPreset(p) {
    providerSel.value = p.dataset.provider;
    baseInput.value = p.dataset.base || "";
    modelInput.value = p.dataset.model || "";
    keyInput.focus();
  }

  async function loadCurrent() {
    try {
      const r = await fetch("/api/health");
      const d = await r.json();
      providerSel.value = d.llm_provider === "anthropic" ? "anthropic" : "openai";
      baseInput.value = d.llm_base_url || "";
      modelInput.value = d.llm_model || "";
      statusEl.textContent = d.key_available ? `当前已连接：${d.llm_provider} / ${d.llm_model || "?"}`
                                             : "当前未配置 API key（AI 顾问降级为基线建议）";
    } catch (e) {
      statusEl.textContent = "无法读取当前配置：" + e.message;
    }
  }

  async function save() {
    const provider = providerSel.value;
    const payload = {
      LLM_PROVIDER: provider,
      LLM_BASE_URL: baseInput.value.trim(),
      LLM_MODEL: modelInput.value.trim(),
    };
    // 留空 = 保留当前值（不发空 key 把现有 key 清空）；点「清空配置」走另一路径
    const key = keyInput.value.trim();
    if (key) {
      payload.LLM_API_KEY = key;
      // 写到对应专属字段也填一份，保证 auto-detect 不会优先挑到旧的另一家 key
      if (provider === "anthropic") payload.ANTHROPIC_API_KEY = key;
      else payload.OPENAI_API_KEY = key;
    }
    saveBtn.disabled = true; statusEl.textContent = "保存中…";
    try {
      const r = await fetch("/api/llm_config", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const d = await r.json();
      keyInput.value = "";              // never keep the key in the DOM
      if (d.ok) {
        statusEl.textContent = `✓ 已启用：${d.provider} / ${d.model || "?"} `
                              + (d.base_url ? `· ${d.base_url}` : "")
                              + (d.key_available ? "" : " · ⚠ 无 key，AI 仍为基线建议");
        if (healthPill) {
          healthPill.textContent = d.key_available ? `● 实时 AI 已连接 · ${d.provider}` : "○ AI 离线（基线建议）";
          healthPill.className = "pill " + (d.key_available ? "pill-on" : "pill-off");
        }
        setTimeout(() => dlg.close(), 800);
      } else {
        statusEl.textContent = "✗ 失败：" + (d.error || "未知错误");
      }
    } catch (e) {
      statusEl.textContent = "✗ 请求失败：" + e.message;
    } finally {
      saveBtn.disabled = false;
    }
  }

  async function clearAll() {
    if (!confirm("清空 .env 中的所有 LLM_* / *_API_KEY 字段？AI 顾问将降级为基线建议。")) return;
    const empties = {
      LLM_PROVIDER: "", LLM_API_KEY: "", LLM_BASE_URL: "", LLM_MODEL: "",
      ANTHROPIC_API_KEY: "", OPENAI_API_KEY: "",
    };
    try {
      const r = await fetch("/api/llm_config", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(empties),
      });
      const d = await r.json();
      statusEl.textContent = d.ok ? "✓ 已清空" : "✗ " + (d.error || "失败");
      if (d.ok && healthPill) {
        healthPill.textContent = "○ AI 离线（基线建议）";
        healthPill.className = "pill pill-off";
      }
    } catch (e) {
      statusEl.textContent = "✗ " + e.message;
    }
  }

  btn.addEventListener("click", async () => { await loadCurrent(); dlg.showModal(); });
  cancelBtn.addEventListener("click", () => dlg.close());
  saveBtn.addEventListener("click", save);
  clearBtn.addEventListener("click", clearAll);
  document.querySelectorAll(".llm-dialog .preset").forEach((p) =>
    p.addEventListener("click", () => applyPreset(p)));
})();
