"""生成「观澜 · agent/skills 对投研流程的提升」详细 PDF（中文，reportlab 内置 CJK 字体，无外部依赖）。

    python scripts/make_impact_pdf.py            # -> docs/投研流程提升报告.pdf
    python scripts/make_impact_pdf.py -o x.pdf

围绕**投研流程六环节**做手工(前) vs agent+skills(后)的详细对比 + 端到端走查 + 逐 skill 详解。
所有量化数字与 docs/before-after.md 同源（实测，不编）。纯 reportlab，CJK 用 STSong-Light（随库自带）。
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
from reportlab.platypus import (HRFlowable, PageBreak, Paragraph, SimpleDocTemplate, Spacer,
                                Table, TableStyle)

CJK = "STSong-Light"
pdfmetrics.registerFont(UnicodeCIDFont(CJK))

INK = colors.HexColor("#1d2733")
MUTED = colors.HexColor("#5b6673")
BRAND = colors.HexColor("#2f6df6")
NAVY = colors.HexColor("#14233b")
GOOD = colors.HexColor("#1aa861")
LINE = colors.HexColor("#d9e1ec")
SOFT = colors.HexColor("#eef3fb")
BANDB = colors.HexColor("#fbe9e7")
BANDG = colors.HexColor("#e9f7ef")


def _styles() -> dict:
    base = getSampleStyleSheet()

    def mk(**k):
        k.setdefault("fontName", CJK)
        return ParagraphStyle(**k)

    return {
        "title": mk(name="t", parent=base["Title"], fontSize=22, leading=28, textColor=INK,
                    alignment=TA_CENTER, spaceAfter=2),
        "sub": mk(name="s", fontSize=10.5, leading=15, textColor=MUTED, alignment=TA_CENTER, spaceAfter=3),
        "h2": mk(name="h2", fontSize=14.5, leading=19, textColor=BRAND, spaceBefore=14, spaceAfter=5),
        "h3": mk(name="h3", fontSize=11.5, leading=16, textColor=INK, spaceBefore=8, spaceAfter=3),
        "body": mk(name="b", fontSize=10, leading=15.8, textColor=INK, alignment=TA_LEFT, spaceAfter=5),
        "bullet": mk(name="bu", fontSize=10, leading=15.5, textColor=INK, leftIndent=12,
                     firstLineIndent=-9, spaceAfter=3),
        "small": mk(name="sm", fontSize=8.6, leading=12.5, textColor=MUTED),
        "cell": mk(name="c", fontSize=8.8, leading=12.4, textColor=INK),
        "cellb": mk(name="cb", fontSize=8.8, leading=12.4, textColor=INK),
        "kpi": mk(name="k", fontSize=9.6, leading=14, textColor=INK, leftIndent=12,
                  firstLineIndent=-9, spaceAfter=3),
        "mono": mk(name="m", fontName="Courier", fontSize=8, leading=12,
                   textColor=colors.HexColor("#33414f")),
    }


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFont(CJK, 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(16 * mm, 10 * mm, "观澜 · 大势研判 + 因子研究 ｜ 仅供量化研究参考，不构成投资建议")
    canvas.drawRightString(A4[0] - 16 * mm, 10 * mm, f"第 {doc.page} 页")
    canvas.restoreState()


def _table(data, col_w, header_bg=BRAND, head_fs=9):
    t = Table(data, colWidths=col_w, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), header_bg),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, -1), CJK), ("FONTSIZE", (0, 0), (-1, 0), head_fs),
        ("VALIGN", (0, 0), (-1, -1), "TOP"), ("GRID", (0, 0), (-1, -1), 0.5, LINE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, SOFT]),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def _band(text, S, bg, border):
    tb = Table([[Paragraph(text, S["cell"])]], colWidths=[None])
    tb.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg), ("BOX", (0, 0), (-1, -1), 0.5, border),
        ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 9)]))
    return tb


def build(path: str) -> None:
    S = _styles()
    doc = SimpleDocTemplate(path, pagesize=A4, topMargin=16 * mm, bottomMargin=16 * mm,
                            leftMargin=16 * mm, rightMargin=16 * mm,
                            title="观澜 · agent/skills 对投研流程的提升", author="观澜")
    W = doc.width
    e = []
    P = lambda t, s="body": Paragraph(t, S[s])

    # ===== 封面区 =====
    e.append(P("观澜 · agent / skills 对投研流程的提升", "title"))
    e.append(P("课程作业交付物 · 前后效果对比报告", "sub"))
    e.append(P("1 个 agent（guanlan-analyst）+ 5 个自定义 skill ｜ 真实 A 股 ETF/指数数据 ｜ "
               "交付研判读数（非组合 / 非回测）", "sub"))
    e.append(HRFlowable(width="100%", thickness=1.2, color=BRAND, spaceBefore=5, spaceAfter=9))

    # ===== 执行摘要 =====
    e.append(P("执行摘要", "h2"))
    e.append(P("• <b>一句话</b>：把「研报检索 → 风险 regime → 大势研判（HMM×效率比×基本面）→ 因子研究」"
               "这条原本靠人工、易出错、难复现的投研链路，固化成<b>一句话触发、一行命令复跑、带溯源、可单测"
               "验证</b>的流水线。", "bullet"))
    e.append(P("• <b>最大提升</b>：研究<b>时效</b>（半天→秒级）、<b>可信度</b>（每个数字可溯源、绝不编造）、"
               "<b>可复现</b>（同输入字节级一致）、<b>防前视</b>（写死在代码 + 单测护栏）。", "bullet"))
    e.append(P("• <b>诚实边界</b>：本项目交付研判读数，<b>不构建组合、不回测</b>，因此提升体现在<b>投研流程</b>"
               "本身，而非收益/夏普这类 PnL（那属于已移除的 FOF 模块）。", "bullet"))

    # ===== 一、投研流程与痛点 =====
    e.append(P("一、投研流程的六个环节，手工卡在哪", "h2"))
    e.append(P("一个量化投研问题（如「今天该进攻还是防御、配哪些风格」）通常要走六个环节。手工做法在每一环"
               "都有摩擦，且摩擦会向下游传导、放大：", "body"))
    pains = [
        ("① 信息搜集", "翻几十篇券商/社区研报，靠记忆引用，结论无法回溯到出处；不同人找到的依据不一样。"),
        ("② 数据获取", "手动从 Tushare/Wind 拉数据，缓存零散、口径不一，常忘记更新到最新交易日。"),
        ("③ 指标 / 模型计算", "在 notebook 里各算各的 RSRS / ERP / HMM / 因子；改一个参数就要全表重跑；"
                          "最危险的是<b>无意中用了未来数据（前视偏差）</b>，回测虚高而不自知。"),
        ("④ 综合研判", "技术面、基本面、情绪面三套分析口径与 asof 对不齐，最后靠经验「拍」一个方向。"),
        ("⑤ 形成结论", "结论散落在聊天记录/截图里，无法直接落成「该进攻还是防御、配哪些风格」的可执行判断。"),
        ("⑥ 复盘 / 复现", "一周后想复现当时的判断，凭手稿很难重跑；他人更无法独立验证数字真伪。"),
    ]
    for k, v in pains:
        e.append(P(f"<b>{k}</b>：{v}", "bullet"))

    # ===== 二、系统如何重构这条流程 =====
    e.append(P("二、agent + 5 skill 如何重构这条流程", "h2"))
    e.append(P("把六环节映射成「<b>纪律编排者（agent）+ 单一职责的能力（skill）+ 确定性数据契约"
               "（outputs/*.json）</b>」三层结构：", "body"))
    e.append(P("<b>计算层 fof/</b>：HMM / 效率比 / 因子 / 指标的真实算法，防前视写死于此。<br/>"
               "<b>Skill 层</b>：每个 skill 一件事，薄脚本调 fof/ → 写一个 JSON（可单独命令行跑）。<br/>"
               "<b>Agent 层</b>：guanlan-analyst 按固定 6 步串起来，强制研究纪律。", "body"))
    e.append(P("agent 的固定工作流：", "h3"))
    for step in [
        "<b>① GROUND 取证</b> — 先用 quant-research-retriever 检索内置研报库，每个机制 ≥2 条 vault/ 路径引用。",
        "<b>② COMPUTE 计算</b> — 一行 run_pipeline.py 在<b>同一 walk-forward</b> 下产 regime/master/factors 三 JSON。",
        "<b>③ READ 解读</b> — 按各 skill 的 references 读法解读三份 JSON。",
        "<b>④ BRIEF 简报</b> — 大势 verdict + 置信 + 风险 band + 因子读数 + 一句姿态，全部来自 JSON。",
        "<b>⑤ ADVISE 建议（可选）</b> — factor-allocation 给超配/低配 + 姿态。",
        "<b>⑥ OFFER 收尾</b> — 主动问是否打开仪表板，确认后才启动。",
    ]:
        e.append(P(step, "bullet"))

    e.append(PageBreak())

    # ===== 三、六环节前后对比表 =====
    e.append(P("三、六环节 · 前后对比（核心）", "h2"))
    rows = [
        ["① 信息搜集", "翻数十篇研报、凭记忆、无引用链",
         "秒级检索内置库，<b>每机制 ≥2 条 vault/ 路径引用</b>", "quant-research-retriever"],
        ["② 数据获取", "手动下载、缓存零散、易过期",
         "增量 tail 拉取 + parquet 缓存，<b>asof 自动对齐</b>", "fof/data.py"],
        ["③ 指标/模型", "各写各、改参全重跑、<b>易前视</b>",
         "12 风险指标+HMM 4 态+12 因子，<b>loc[:asof]/shift(-1) 写死</b>",
         "regime-radar / regime-verdict / factor-research"],
        ["④ 综合研判", "三套口径不一、拍脑袋",
         "同 walk-forward 一次产 3 JSON，三轴融合<b>走强/震荡/走弱</b>", "run_pipeline → master.json"],
        ["⑤ 形成结论", "结论散落、无法落地",
         "姿态(进攻/中性/防御)+超配/低配，<b>纯解读带 caveat</b>", "factor-allocation"],
        ["⑥ 复盘复现", "凭手稿、难重跑/审阅",
         "<b>5 份确定性 JSON + 45 单测 + 两页仪表板</b>", "outputs · tests · web"],
    ]
    data = [[P("投研环节", "cellb"), P("手工（前）", "cellb"), P("agent + skills（后）", "cellb"),
             P("对应组件", "cellb")]]
    for r in rows:
        data.append([P(r[0], "cellb"), P(r[1], "cell"), P(r[2], "cell"), P(r[3], "small")])
    e.append(_table(data, [W * 0.12, W * 0.29, W * 0.36, W * 0.23]))

    # ===== 四、量化提升 =====
    e.append(P("四、量化提升（八维，均为实测）", "h2"))
    qrows = [
        ["端到端耗时", "半天 ~ 一天", "离线简报 0.17–1.0 秒；全量重算 ~15–30 秒"],
        ["研报可溯源", "0 引用链", "每机制 ≥2 条路径；语料库 34 篇研报（wiki 共 236）"],
        ["防前视", "人工极易踩坑", "loc[:asof]+shift(-1) 写死，单测 test_rsrs_lookahead_safe 断言"],
        ["口径一致", "asof 漂移（曾 06-09 vs 06-12）", "run_all 同一 asof 一次产出三 JSON"],
        ["可复现", "凭手稿、难重跑", "5 份确定性 JSON；同输入两次跑 SHA256 完全一致"],
        ["可验证", "无测试", "9 文件 / 45 测试；无网络子集 19 passed in 1.0s"],
        ["可视化/审阅", "散落的图", "两页仪表板 + 内嵌 AI 顾问可质询；刷新 5 阶段进度条"],
        ["工具/模型绑定", "绑死本机环境", "任意 LLM（⚙配置）；AGENTS.md 跨工具；零-LLM CLI 兜底"],
    ]
    qdata = [[P("维度", "cellb"), P("手工（前）", "cellb"), P("agent + skills（后）", "cellb")]]
    qdata += [[P(a, "cellb"), P(b, "cell"), P(c, "cell")] for a, b, c in qrows]
    e.append(_table(qdata, [W * 0.18, W * 0.32, W * 0.50], header_bg=NAVY))

    # ===== 五、端到端走查 =====
    e.append(P("五、一个真实问题的端到端走查", "h2"))
    e.append(P("问题：<b>「今天 A 股该进攻还是防御？该超配/低配哪些风格？依据是什么？」</b>", "body"))
    e.append(P("手工（前）：翻研报找择时/因子依据（~2 小时）→ notebook 拉数据算 RSRS/ERP/HMM/因子"
               "（~3 小时，且易前视）→ 人工对齐口径凑结论（~1 小时）→ 结论无引用、难复现。合计大半天。", "body"))
    e.append(P("agent（后）：一句「跑一遍大势研判，该进攻还是防御」即触发六步，<b>秒级</b>得到带溯源简报。"
               "当前真实输出（取自 outputs/*.json，绝不另编）：", "body"))
    e.append(_band(
        "<b>大势研判</b> = 震荡（大势分 49.5，置信 55%）｜ HMM 状态 履冰 ｜ Kaufman 效率比 ER 0.245<br/>"
        "<b>因子轮动</b> = IC 均值 0.042 ｜ ICIR 0.088 ｜ 胜率 54.5%（→ 因子动量很弱，仅弱信号）<br/>"
        "<b>配置建议</b> = 中性（半仓）｜ 超配 反转 / 低波 / 红利 ｜ 低配 质量 / 微盘 / 小市值<br/>"
        "<b>溯源</b> = 每个机制附 ≥2 条 vault/wiki/sources/*.md 路径引用", S, BANDG, colors.HexColor("#bfe6cf")))

    e.append(PageBreak())

    # ===== 六、五个 skill 详解 =====
    e.append(P("六、五个 skill 逐个详解", "h2"))
    sk = [
        ["regime-radar", "12 市场指标 → 0-100 风险分 + 顶/底评分", "outputs/regime.json",
         "解决风险口径不统一：RSRS/MA/宽度/波动 + 金铜比/期限利差/ERP + 融资/成交/Shibor + 期货/期权"],
        ["regime-verdict", "HMM 4 态 × 效率比 × 基本面 → 走强/震荡/走弱", "outputs/master.json",
         "解决大势判断主观：walk-forward 重拟合 4 态高斯 HMM + 三轴融合 + 转移矩阵，可复现"],
        ["factor-research", "12 风格因子：排行 + 月度 IC/ICIR + 滚动 Sharpe", "outputs/factors.json",
         "解决因子轮动靠感觉：用真实风格指数算 IC，诚实暴露「动量很弱」这一负结果"],
        ["factor-allocation", "读 master+factors → 姿态 + 超配/低配", "outputs/factor_allocation.json",
         "把研判落成可执行建议（纯解读、不建组合、带 caveat）"],
        ["quant-research-retriever", "检索内置 34 篇研报库（可选 WebSearch）", "引用 JSON（带路径）",
         "解决无引用链：每个机制 ≥2 条 vault/ 路径，论据可回溯"],
    ]
    skd = [[P("Skill", "cellb"), P("职责", "cellb"), P("产出", "cellb"), P("消除的痛点", "cellb")]]
    for r in sk:
        skd.append([P(f"<b>{r[0]}</b>", "small"), P(r[1], "cell"), P(r[2], "small"), P(r[3], "cell")])
    e.append(_table(skd, [W * 0.20, W * 0.26, W * 0.18, W * 0.36], head_fs=8.6))

    # ===== 七、研究纪律 =====
    e.append(P("七、agent 强制的研究纪律（为什么结果可信）", "h2"))
    e.append(P("• <b>绝不编造数字（never invent numbers）</b>：简报每个数字都来自 outputs/*.json，"
               "模型不得自行生成读数。", "bullet"))
    e.append(P("• <b>每个机制 ≥2 条研报引用</b>：先取证再下结论，论据可回溯到 vault/ 路径。", "bullet"))
    e.append(P("• <b>防前视写死在 fof/</b>：指标只用 series.loc[:asof]，回测收益 nav.pct_change().shift(-1)"
               "（收盘决策、次日兑现），HMM 每月只用 [:m] 重拟合；单测断言「追加未来 bar 不改变历史结论」。", "bullet"))
    e.append(P("• <b>诚实标注弱信号/局限</b>：因子动量弱、ER 涨跌停虚高、研判非交易信号——都在输出里写明。", "bullet"))
    e.append(P("• <b>无密钥也能跑</b>：整条 pipeline + 仪表板不需要任何 LLM key；agent 本身不调 LLM API。", "bullet"))

    # ===== 八、实测证据 =====
    e.append(P("八、实测证据（可复现）", "h2"))
    e.append(P("• <b>确定性</b>：两次离线简报 SHA256 完全相同（5270A5F4…），run1 1.00s / run2 0.17s。", "kpi"))
    e.append(P("• <b>溯源</b>：query_vault &quot;HMM regime&quot; --top 5 返回 5 条带路径引用"
               "（含 S 级研报 + 2 个 topic 枢纽）。", "kpi"))
    e.append(P("• <b>可验证</b>：pytest 无网络核心子集 19 passed in 1.00s（全套 9 文件 / 45 测试）。", "kpi"))
    e.append(P("• <b>产物规模</b>：5 份确定性 JSON（dashboard 470KB / factors 192KB / regime 151KB / "
               "master 74KB / factor_allocation 2.8KB）。", "kpi"))

    # ===== 九、诚实局限 =====
    e.append(P("九、诚实局限（不夸大）", "h2"))
    e.append(_band(
        "• 本文衡量的是<b>投研流程的效率与可信度</b>，不是 PnL 提升——本项目交付研判读数、不构建组合、未回测。<br/>"
        "• 因子动量很弱（IC≈0.04 / ICIR≈0.09 / 胜率≈55%）→ 风格 tilt 仅<b>弱倾斜</b>，别据此重仓押注。<br/>"
        "• 大势是<b>研究读数、非交易信号</b>；ER 在涨跌停日虚高；历史状态色带为 walk-forward 样本外判定，非全样本平滑。<br/>"
        "• 仅供量化研究参考，不构成投资建议。", S, BANDB, colors.HexColor("#f0c8c0")))

    # ===== 十、复现 =====
    e.append(P("十、如何复现这份对比", "h2"))
    e.append(P("python scripts/guanlan_brief.py            # 离线研判简报（跑两次比 SHA256 一致）<br/>"
               "python -m pytest tests -q                  # 单测（含防前视断言）<br/>"
               "python .claude/skills/quant-research-retriever/scripts/query_vault.py &quot;HMM regime&quot; --top 5<br/>"
               "python scripts/run_pipeline.py --asof YYYY-MM-DD --start 2020-01-01   # 全量重算<br/>"
               "python scripts/make_impact_pdf.py          # 重新生成本 PDF", "mono"))
    e.append(Spacer(1, 4))
    e.append(P("详见仓库 docs/before-after.md（八维对比明细）、docs/architecture.md（分层逻辑）、"
               "docs/portable-agent.md（跨工具用法）。", "small"))

    doc.build(e, onFirstPage=_footer, onLaterPages=_footer)


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
