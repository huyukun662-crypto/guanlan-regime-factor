"""Anthropic streaming wrapper for the dashboard advisor.

Builds a cache-controlled system prompt from the current outputs/*.json so the advisor
answers from real, computed numbers (never fabricated). Degrades gracefully to the
deterministic advice line when no ANTHROPIC_API_KEY is configured.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
OUTPUTS = ROOT / "outputs"
MODEL = "claude-opus-4-8"

load_dotenv(ROOT / ".env")


def key_available() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY", "").strip())


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
    """Yield SSE-formatted strings. Falls back to advice_baseline with no key."""
    if not key_available():
        reg = _load("regime.json")
        yield _sse({"type": "delta", "text": reg.get(
            "advice_baseline", "请先运行 run_pipeline.py 生成数据。")})
        yield _sse({"type": "info", "text": "实时 AI 已禁用（未配置 ANTHROPIC_API_KEY）。"
                                            "以上为确定性基线建议。"})
        yield _sse({"type": "done"})
        return

    import anthropic
    client = anthropic.Anthropic()
    system = [{"type": "text", "text": build_system_prompt(),
               "cache_control": {"type": "ephemeral"}}]
    try:
        with client.messages.stream(
            model=MODEL, max_tokens=1500,
            thinking={"type": "disabled"},
            output_config={"effort": "low"},
            system=system, messages=messages,
        ) as stream:
            for text in stream.text_stream:
                yield _sse({"type": "delta", "text": text})
        yield _sse({"type": "done"})
    except anthropic.APIError as ex:           # surface, never 500 the stream
        yield _sse({"type": "error", "text": f"调用失败：{ex.__class__.__name__}"})
        yield _sse({"type": "done"})


def _sse(obj: dict) -> str:
    return f"data: {json.dumps(obj, ensure_ascii=False)}\n\n"
