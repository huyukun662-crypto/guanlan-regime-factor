"""Streaming LLM wrapper for the dashboard advisor (provider-pluggable).

Builds a cache-controlled system prompt from the current outputs/*.json so the advisor
answers from real, computed numbers (never fabricated). Degrades gracefully to the
deterministic advice line when no API key is configured.

Provider selection (env, .env-loaded):
- LLM_PROVIDER   = anthropic | openai          (default: anthropic if ANTHROPIC_API_KEY set,
                                                else openai if OPENAI_API_KEY/LLM_API_KEY set)
- LLM_API_KEY    = api key (overrides provider-specific key vars)
- LLM_BASE_URL   = custom endpoint for openai-compatible providers, e.g.
                     DeepSeek:  https://api.deepseek.com
                     Moonshot:  https://api.moonshot.cn/v1
                     Zhipu:     https://open.bigmodel.cn/api/paas/v4
                     通义千问:  https://dashscope.aliyuncs.com/compatible-mode/v1
                     Ollama:    http://localhost:11434/v1
- LLM_MODEL      = model id  (defaults: claude-opus-4-8 | gpt-4o-mini)

Both `ANTHROPIC_API_KEY` (legacy) and the new vars are supported for backward compat.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
OUTPUTS = ROOT / "outputs"
load_dotenv(ROOT / ".env")

_DEFAULT_MODEL = {"anthropic": "claude-opus-4-8", "openai": "gpt-4o-mini"}


def _resolve_provider() -> tuple[str, str, str, str]:
    """Return (provider, api_key, base_url, model). Empty api_key → no-key mode."""
    provider = (os.environ.get("LLM_PROVIDER") or "").strip().lower()
    key = (os.environ.get("LLM_API_KEY") or "").strip()
    base = (os.environ.get("LLM_BASE_URL") or "").strip()
    model = (os.environ.get("LLM_MODEL") or "").strip()

    anth_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    oai_key = os.environ.get("OPENAI_API_KEY", "").strip()
    # auto-detect: explicit LLM_PROVIDER > LLM_API_KEY+base hint > Anthropic > OpenAI
    if not provider:
        if key and base:
            provider = "openai"
        elif anth_key:
            provider = "anthropic"
        elif oai_key:
            provider = "openai"
        else:
            provider = "anthropic"
    if not key:
        key = anth_key if provider == "anthropic" else oai_key
    model = model or _DEFAULT_MODEL.get(provider, "")
    return provider, key, base, model


def key_available() -> bool:
    _, key, _, _ = _resolve_provider()
    return bool(key)


def _load(name: str) -> dict:
    path = OUTPUTS / name
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def build_system_prompt() -> str:
    reg = _load("regime.json")
    m = _load("master.json")
    hmm = m.get("hmm", {})
    er = m.get("er", {})

    return (
        "你是一个市场状态（大势研判）研究顾问，服务于一个量化研究仪表板（仅含市场研判 + 因子看板，"
        "无 FOF 组合）。只能依据下面提供的真实计算结果回答，绝不编造数字；不确定就说不确定。"
        "用简体中文，结论先行，简洁专业，不做投资建议，必要时提示仅供研究参考。\n\n"
        f"【当前 regime】{reg.get('regime_label')}｜综合风险分 {reg.get('composite_score')} "
        f"（{reg.get('band')}）\n"
        f"【确定性操作建议】{reg.get('advice_baseline', '')}\n"
        f"【大势研判】结论 {m.get('verdict')}（大势分 {m.get('master_score')}，置信 {m.get('confidence')}%）｜"
        f"HMM 状态 {hmm.get('state_name')}（已持续 {m.get('streak_days')} 交易日）｜"
        f"效率比 ER {er.get('value')}（{er.get('tag')}）｜门控标签 {m.get('gate_label')}\n"
        f"【大势研判方法】沪深300价量日频上 walk-forward 重拟合 4 态高斯隐马尔可夫(稳态/平静/履冰/危机) "
        f"× Kaufman 效率比 × 基本面，三轴融合得确定性大势结论。\n"
        f"【顶/底指标卡】" + "；".join(
            f"{c['name']}={c['value']}(顶{c.get('top')}/底{c.get('bottom')} {c.get('tag')})"
            for c in reg.get("indicators", []) if c.get("available")) + "\n"
    )


def stream_chat(messages: list[dict]):
    """Yield SSE-formatted strings. Provider-pluggable; falls back to baseline if no key."""
    provider, api_key, base_url, model = _resolve_provider()

    if not api_key:
        reg = _load("regime.json")
        yield _sse({"type": "delta", "text": reg.get(
            "advice_baseline", "请先运行 run_pipeline.py 生成数据。")})
        yield _sse({"type": "info", "text": "实时 AI 已禁用（未配置 LLM API key）。"
                                            "以上为确定性基线建议。"})
        yield _sse({"type": "done"})
        return

    system_text = build_system_prompt()
    try:
        if provider == "anthropic":
            yield from _stream_anthropic(model, api_key, system_text, messages)
        else:
            yield from _stream_openai_compatible(model, api_key, base_url, system_text, messages)
        yield _sse({"type": "done"})
    except Exception as ex:                    # surface, never 500 the stream
        yield _sse({"type": "error",
                    "text": f"调用失败({provider})：{ex.__class__.__name__}: {str(ex)[:200]}"})
        yield _sse({"type": "done"})


def _stream_anthropic(model: str, api_key: str, system_text: str, messages: list[dict]):
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    system = [{"type": "text", "text": system_text, "cache_control": {"type": "ephemeral"}}]
    with client.messages.stream(
        model=model, max_tokens=1500, system=system, messages=messages,
    ) as stream:
        for text in stream.text_stream:
            yield _sse({"type": "delta", "text": text})


def _stream_openai_compatible(model: str, api_key: str, base_url: str,
                              system_text: str, messages: list[dict]):
    """Works with OpenAI, DeepSeek, Moonshot Kimi, Zhipu, Qwen DashScope, Ollama, etc."""
    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url=base_url or None)
    chat_msgs = [{"role": "system", "content": system_text}, *messages]
    stream = client.chat.completions.create(
        model=model, messages=chat_msgs, max_tokens=1500, stream=True)
    for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta
        text = getattr(delta, "content", None)
        if text:
            yield _sse({"type": "delta", "text": text})


def _sse(obj: dict) -> str:
    return f"data: {json.dumps(obj, ensure_ascii=False)}\n\n"
