"""生成「观澜 · agent/skills 对投研流程的提升」PDF（中文，reportlab 内置 CJK 字体，无外部依赖）。

    python scripts/make_impact_pdf.py            # -> docs/投研流程提升报告.pdf
    python scripts/make_impact_pdf.py -o x.pdf

重点：围绕**投研流程六环节**做手工(前) vs agent+skills(后)的对比，所有量化数字与
docs/before-after.md 同源（实测，不编）。纯 reportlab，CJK 用 STSong-Light（随库自带）。
"""

from __future__ import annotations

import argparse
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import (Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
                                HRFlowable)

CJK = "STSong-Light"
pdfmetrics.registerFont(UnicodeCIDFont(CJK))

INK = colors.HexColor("#1d2733")
MUTED = colors.HexColor("#5b6673")
BRAND = colors.HexColor("#2f6df6")
GOOD = colors.HexColor("#1aa861")
LINE = colors.HexColor("#d9e1ec")
SOFT = colors.HexColor("#eef3fb")
BANDB = colors.HexColor("#fbe9e7")


def _styles() -> dict:
    base = getSampleStyleSheet()
    def mk(**k):
        k.setdefault("fontName", CJK)
        return ParagraphStyle(**k)
    return {
        "title": mk(name="t", parent=base["Title"], fontSize=21, leading=27,
                    textColor=INK, alignment=TA_CENTER, spaceAfter=2),
        "sub": mk(name="s", fontSize=10.5, leading=15, textColor=MUTED, alignment=TA_CENTER,
                  spaceAfter=4),
        "h2": mk(name="h2", fontSize=14, leading=19, textColor=BRAND, spaceBefore=13,
                 spaceAfter=5),
        "body": mk(name="b", fontSize=10, leading=15.5, textColor=INK, alignment=TA_LEFT,
                   spaceAfter=5),
        "small": mk(name="sm", fontSize=8.6, leading=12.5, textColor=MUTED),
        "cell": mk(name="c", fontSize=8.8, leading=12.2, textColor=INK),
        "cellb": mk(name="cb", fontSize=8.8, leading=12.2, textColor=INK),
        "kpi": mk(name="k", fontSize=9.4, leading=13.5, textColor=INK),
        "mono": mk(name="m", fontName="Courier", fontSize=8, leading=11, textColor=colors.HexColor("#33414f")),
    }


def build(path: str) -> None:
    S = _styles()
    doc = SimpleDocTemplate(path, pagesize=A4, topMargin=16 * mm, bottomMargin=15 * mm,
                            leftMargin=16 * mm, rightMargin=16 * mm,
                            title="观澜 · agent/skills 对投研流程的提升", author="观澜")
    W = doc.width
    e = []
    P = lambda t, s="body": Paragraph(t, S[s])

    # ---- title block
    e.append(P("观澜 · agent / skills 对投研流程的提升", "title"))
    e.append(P("1 个 agent（guanlan-analyst）+ 5 个自定义 skill ｜ 真实 A 股 ETF/指数数据 ｜ 研判读数（非组合/非回测）", "sub"))
    e.append(HRFlowable(width="100%", thickness=1, color=LINE, spaceBefore=4, spaceAfter=8))

    e.append(P("一、投研流程是什么、卡在哪", "h2"))
    e.append(P("典型量化投研流程有六个环节：<b>① 信息搜集 → ② 数据获取 → ③ 指标/模型计算 → "
               "④ 综合研判 → ⑤ 形成结论 → ⑥ 复盘复现</b>。手工做法在每一环都有摩擦：翻几十篇研报无引用链、"
               "notebook 改一个参数就重写、三个分析口径不一致、结论凭记忆难复现。本项目用 agent 把这六环"
               "<b>固化成一条可一键复跑、带溯源、可单测验证的流水线</b>——这正是对投研流程的核心提升。", "body"))

    # ---- six-stage before/after table
    e.append(P("二、六环节 · 前后对比（重点）", "h2"))
    head = [P("投研环节", "cellb"), P("手工（前）", "cellb"),
            P("agent + skills（后）", "cellb"), P("对应组件", "cellb")]
    rows = [
        ["① 信息搜集", "翻数十篇研报、凭记忆、无引用链",
         "秒级检索内置研报库，<b>每个机制 ≥2 条 vault/ 路径引用</b>", "quant-research-retriever"],
        ["② 数据获取", "手动下载、缓存零散、易过期",
         "Tushare 增量 tail 拉取 + parquet 缓存，<b>asof 自动对齐</b>", "fof/data.py"],
        ["③ 指标/模型", "notebook 各写各、改参全重跑、<b>易引入前视</b>",
         "12 风险指标 + HMM 4 态 + 12 因子，<b>loc[:asof]/shift(-1) 写死</b>",
         "regime-radar / regime-verdict / factor-research"],
        ["④ 综合研判", "三套分析口径不一、主观拍脑袋",
         "同一 walk-forward 一次产 3 JSON，三轴融合出<b>走强/震荡/走弱</b>", "run_pipeline → master.json"],
        ["⑤ 形成结论", "结论散落、无法落地",
         "姿态（进攻/中性/防御）+ 超配/低配风格，<b>纯解读带 caveat</b>", "factor-allocation"],
        ["⑥ 复盘复现", "凭手稿、难重跑、难审阅",
         "<b>5 份确定性 JSON + 45 单测 + 两页仪表板</b>可质询", "outputs/*.json · tests · web"],
    ]
    data = [head]
    for r in rows:
        data.append([P(r[0], "cellb"), P(r[1], "cell"), P(r[2], "cell"), P(r[3], "small")])
    t = Table(data, colWidths=[W * 0.13, W * 0.30, W * 0.34, W * 0.23], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BRAND),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, -1), CJK), ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, LINE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, SOFT]),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    e.append(t)

    # ---- quantified gains
    e.append(P("三、量化提升（均为实测，可复现）", "h2"))
    qhead = [P("维度", "cellb"), P("手工（前）", "cellb"), P("agent+skills（后）", "cellb")]
    qrows = [
        ["端到端耗时", "半天 ~ 一天", "离线简报 0.17–1.0 秒；全量重算 ~15–30 秒"],
        ["研报可溯源", "0 引用链", "每机制 ≥2 条路径；语料库 34 篇研报"],
        ["防前视", "人工极易踩坑", "loc[:asof]+shift(-1) 写死，单测断言"],
        ["口径一致", "asof 漂移（曾 06-09 vs 06-12）", "run_all 同一 asof 一次产出"],
        ["可复现", "凭手稿", "5 份确定性 JSON；两次跑 SHA256 完全一致"],
        ["可验证", "无测试", "9 文件 / 45 测试；无网络子集 19 passed/1.0s"],
        ["工具/模型绑定", "绑死本机环境", "任意 LLM（⚙配置）；AGENTS.md 跨工具；零-LLM CLI 兜底"],
    ]
    qdata = [qhead] + [[P(a, "cellb"), P(b, "cell"), P(c, "cell")] for a, b, c in qrows]
    qt = Table(qdata, colWidths=[W * 0.20, W * 0.34, W * 0.46], repeatRows=1)
    qt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#14233b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, -1), CJK), ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("VALIGN", (0, 0), (-1, -1), "TOP"), ("GRID", (0, 0), (-1, -1), 0.5, LINE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, SOFT]),
        ("TOPPADDING", (0, 0), (-1, -1), 4.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 4.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    e.append(qt)

    # ---- measured evidence
    e.append(P("四、实测证据片段", "h2"))
    e.append(P("• <b>确定性</b>：两次离线简报 SHA256 完全相同（5270A5F4…），run1 1.00s / run2 0.17s。", "kpi"))
    e.append(P("• <b>溯源</b>：query_vault &quot;HMM regime&quot; 返回 5 条带路径引用（含 S 级研报 + 2 个 topic 枢纽）。", "kpi"))
    e.append(P("• <b>可验证</b>：pytest 无网络核心子集 19 passed in 1.00s（全套 45 测试）。", "kpi"))
    e.append(P("• <b>当前真实读数</b>（取自 outputs/*.json，agent 绝不另编）：", "kpi"))
    e.append(P("大势研判 = 震荡（大势分 49.5，置信 55%）｜ HMM 履冰 ｜ ER 0.245；"
               "因子轮动 IC 0.042 / ICIR 0.088 / 胜率 54.5%；"
               "配置建议 = 中性（半仓），超配 反转/低波/红利，低配 质量/微盘/小市值。", "small"))

    # ---- honest limits
    e.append(P("五、诚实局限（不夸大）", "h2"))
    lim = Table([[P(
        "• 本文衡量的是<b>投研流程的效率与可信度</b>，不是 PnL 提升——本项目交付研判读数、不构建组合、未回测。<br/>"
        "• 因子动量很弱（IC≈0.04 / ICIR≈0.09 / 胜率≈55%）→ 风格 tilt 仅<b>弱倾斜</b>，别据此重仓。<br/>"
        "• 大势是<b>研究读数、非交易信号</b>；ER 在涨跌停日虚高；历史状态色带为 walk-forward 样本外判定。<br/>"
        "• 仅供量化研究参考，不构成投资建议。", "cell")]],
        colWidths=[W])
    lim.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BANDB), ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#f0c8c0")),
        ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 9)]))
    e.append(lim)

    e.append(Spacer(1, 8))
    e.append(P("如何复现：python scripts/guanlan_brief.py（两次比哈希）· python -m pytest tests -q · "
               "query_vault.py &quot;HMM regime&quot; --top 5 · 详见 docs/before-after.md", "mono"))

    doc.build(e)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--output", default=str(Path(__file__).resolve().parent.parent
                                                  / "docs" / "投研流程提升报告.pdf"))
    args = ap.parse_args()
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    build(args.output)
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
