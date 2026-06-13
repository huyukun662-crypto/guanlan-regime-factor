// Live AI advisor — streams /api/chat (SSE) into the chat panel.
"use strict";

(function () {
  const log = document.getElementById("chat-log");
  const form = document.getElementById("chat-form");
  const input = document.getElementById("chat-input");
  const sendBtn = document.getElementById("chat-send");
  const history = [];           // [{role, content}]

  function bubble(cls, text) {
    const el = document.createElement("div");
    el.className = "bubble " + cls;
    el.textContent = text;
    log.appendChild(el);
    log.scrollTop = log.scrollHeight;
    return el;
  }

  async function ask(question) {
    if (!question.trim()) return;
    bubble("user", question);
    history.push({ role: "user", content: question });
    input.value = "";
    sendBtn.disabled = true;
    const ai = bubble("ai", "");
    ai.textContent = "…";
    let acc = "";

    try {
      const resp = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: history }),
      });
      const reader = resp.body.getReader();
      const dec = new TextDecoder();
      let buf = "";
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buf += dec.decode(value, { stream: true });
        const parts = buf.split("\n\n");
        buf = parts.pop();
        for (const p of parts) {
          const line = p.trim();
          if (!line.startsWith("data:")) continue;
          const evt = JSON.parse(line.slice(5).trim());
          if (evt.type === "delta") { acc += evt.text; ai.textContent = acc; }
          else if (evt.type === "info") bubble("info", evt.text);
          else if (evt.type === "error") { ai.textContent = acc || ""; bubble("info", evt.text); }
          log.scrollTop = log.scrollHeight;
        }
      }
      if (!acc) ai.textContent = ai.textContent === "…" ? "（无回复）" : ai.textContent;
      if (acc) history.push({ role: "assistant", content: acc });
    } catch (e) {
      ai.textContent = "请求失败，请确认后端正在运行。";
    } finally {
      sendBtn.disabled = false;
      input.focus();
    }
  }

  form.addEventListener("submit", (e) => { e.preventDefault(); ask(input.value); });
  document.querySelectorAll(".hint").forEach((b) =>
    b.addEventListener("click", () => ask(b.textContent)));
})();
