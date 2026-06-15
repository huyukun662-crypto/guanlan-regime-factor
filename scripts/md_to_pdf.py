"""把 Markdown 文档转成中文 PDF（reportlab 内置 STSong-Light，无外部字体 / 无联网）。

    python scripts/md_to_pdf.py docs/usage.md                 # -> docs/usage.pdf
    python scripts/md_to_pdf.py docs/*.md                     # 批量
    python scripts/md_to_pdf.py --all                         # 转 docs/ 下所有 .md

支持的 Markdown 子集（覆盖本仓库文档）：# / ## / ### 标题、段落、- / * / 数字列表、
| 表格 |、``` 代码块、> 引用、--- 分割线、**粗体**、`行内代码`、[文字](链接)、![图说](图片路径)。
"""

from __future__ import annotations

import argparse
import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (HRFlowable, Image, Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

CJK = "STSong-Light"
pdfmetrics.registerFont(UnicodeCIDFont(CJK))

INK = colors.HexColor("#1d2733")
MUTED = colors.HexColor("#5b6673")
BRAND = colors.HexColor("#2f6df6")
LINE = colors.HexColor("#d9e1ec")
SOFT = colors.HexColor("#eef3fb")
CODEBG = colors.HexColor("#f5f7fa")
QUOTE = colors.HexColor("#fbf7e9")


def _styles() -> dict:
    def mk(**k):
        k.setdefault("fontName", CJK)
        return ParagraphStyle(**k)
    return {
        "h1": mk(name="h1", fontSize=19, leading=25, textColor=INK, spaceBefore=2, spaceAfter=8),
        "h2": mk(name="h2", fontSize=14, leading=19, textColor=BRAND, spaceBefore=12, spaceAfter=5),
        "h3": mk(name="h3", fontSize=11.5, leading=16, textColor=INK, spaceBefore=8, spaceAfter=3),
        "body": mk(name="b", fontSize=9.8, leading=15, textColor=INK, alignment=TA_LEFT, spaceAfter=5),
        "bullet": mk(name="bu", fontSize=9.8, leading=14.6, textColor=INK, leftIndent=13,
                     firstLineIndent=-9, spaceAfter=2.5),
        "quote": mk(name="q", fontSize=9.4, leading=14, textColor=MUTED),
        "cell": mk(name="c", fontSize=8.4, leading=11.8, textColor=INK),
        "cellh": mk(name="ch", fontSize=8.6, leading=12, textColor=colors.white),
        "code": mk(name="code", fontName="Courier", fontSize=8, leading=11.2,
                   textColor=colors.HexColor("#2b3440")),
    }


def _inline(text: str) -> str:
    """Markdown 行内 → reportlab 标记。先转义 HTML，再还原我们要的标签。"""
    t = html.escape(text)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"`([^`]+?)`", r'<font face="Courier">\1</font>', t)
    t = re.sub(r"\[([^\]]+?)\]\(([^)]+?)\)", r'<link href="\2" color="#2f6df6">\1</link>', t)
    t = t.replace("&lt;br/&gt;", "<br/>").replace("&lt;br&gt;", "<br/>")
    return t


def _flush_table(rows: list, S, story, W):
    if not rows:
        return
    # drop the |---|---| separator row(s)
    body = [r for r in rows if not re.match(r"^\s*\|?[\s:|-]+\|?\s*$", "|".join(r))]
    if not body:
        return
    ncol = max(len(r) for r in body)
    data = []
    for i, r in enumerate(body):
        r = (r + [""] * (ncol - len(r)))[:ncol]
        sty = "cellh" if i == 0 else "cell"
        data.append([Paragraph(_inline(c.strip()), S[sty]) for c in r])
    tb = Table(data, colWidths=[W / ncol] * ncol, repeatRows=1)
    tb.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BRAND),
        ("FONTNAME", (0, 0), (-1, -1), CJK), ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, LINE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, SOFT]),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(tb)
    story.append(Spacer(1, 6))


def _flush_code(lines: list, S, story, W):
    if not lines:
        return
    txt = "<br/>".join(html.escape(ln).replace(" ", "&nbsp;") or "&nbsp;" for ln in lines)
    p = Paragraph(txt, S["code"])
    tb = Table([[p]], colWidths=[W])
    tb.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CODEBG), ("BOX", (0, 0), (-1, -1), 0.5, LINE),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8)]))
    story.append(tb)
    story.append(Spacer(1, 6))


def _image(path: Path, alt: str, S, story, W, maxH):
    """Render ![alt](path) scaled to fit both content width and page height (Images can't split),
    with an optional centered caption."""
    if not path.exists():
        story.append(Paragraph(_inline(f"[缺图: {path.name}]"), S["quote"])); return
    iw, ih = ImageReader(str(path)).getSize()
    scale = min(W / float(iw), maxH / float(ih))   # fit-inside; tall screenshots get narrower
    w, h = float(iw) * scale, float(ih) * scale
    img = Image(str(path), width=w, height=h)
    img.hAlign = "CENTER"
    tb = Table([[img]], colWidths=[w])      # boxed frame hugs the image so it reads as a figure
    tb.hAlign = "CENTER"
    tb.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.6, LINE),
                            ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                            ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3)]))
    story.append(tb)
    if alt.strip():
        cap = ParagraphStyle(name="cap", fontName=CJK, fontSize=8.4, leading=11,
                             textColor=MUTED, alignment=1, spaceBefore=3, spaceAfter=8)
        story.append(Paragraph(_inline(f"图：{alt.strip()}"), cap))
    else:
        story.append(Spacer(1, 8))


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFont(CJK, 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(16 * mm, 10 * mm, "观澜 · 量化研究 ｜ 仅供研究参考，不构成投资建议")
    canvas.drawRightString(A4[0] - 16 * mm, 10 * mm, f"第 {doc.page} 页")
    canvas.restoreState()


def convert(md_path: Path, pdf_path: Path) -> None:
    S = _styles()
    doc = SimpleDocTemplate(str(pdf_path), pagesize=A4, topMargin=16 * mm, bottomMargin=16 * mm,
                            leftMargin=16 * mm, rightMargin=16 * mm, title=md_path.stem)
    W = doc.width
    story: list = []
    lines = md_path.read_text(encoding="utf-8").splitlines()

    in_code = False
    code_buf: list = []
    tbl_buf: list = []

    def flush_tbl():
        _flush_table(tbl_buf, S, story, W); tbl_buf.clear()

    for raw in lines:
        ln = raw.rstrip("\n")
        if ln.strip().startswith("```"):
            if in_code:
                _flush_code(code_buf, S, story, W); code_buf.clear(); in_code = False
            else:
                flush_tbl(); in_code = True
            continue
        if in_code:
            code_buf.append(ln); continue
        if ln.lstrip().startswith("|") and "|" in ln.strip()[1:]:
            tbl_buf.append([c for c in ln.strip().strip("|").split("|")]); continue
        else:
            flush_tbl()
        s = ln.strip()
        if not s:
            story.append(Spacer(1, 4)); continue
        m_img = re.match(r"^!\[([^\]]*)\]\(([^)]+?)\)\s*$", s)
        if m_img:
            alt, rel = m_img.group(1), m_img.group(2)
            img_path = Path(rel) if Path(rel).is_absolute() else (md_path.parent / rel)
            _image(img_path, alt, S, story, W, doc.height - 24); continue
        if s.startswith("### "):
            story.append(Paragraph(_inline(s[4:]), S["h3"]))
        elif s.startswith("## "):
            story.append(Paragraph(_inline(s[3:]), S["h2"]))
        elif s.startswith("# "):
            story.append(Paragraph(_inline(s[2:]), S["h1"]))
            story.append(HRFlowable(width="100%", thickness=1, color=LINE, spaceBefore=3, spaceAfter=7))
        elif s.startswith("---") and set(s) <= {"-"}:
            story.append(HRFlowable(width="100%", thickness=0.6, color=LINE, spaceBefore=4, spaceAfter=6))
        elif s.startswith(("- ", "* ", "+ ")):
            story.append(Paragraph("• " + _inline(s[2:]), S["bullet"]))
        elif re.match(r"^\d+\.\s", s):
            story.append(Paragraph(_inline(s), S["bullet"]))
        elif s.startswith(">"):
            txt = _inline(s.lstrip("> ").strip())
            tb = Table([[Paragraph(txt, S["quote"])]], colWidths=[W])
            tb.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), QUOTE),
                                    ("LINEBEFORE", (0, 0), (0, -1), 2, colors.HexColor("#e8a13a")),
                                    ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                                    ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 8)]))
            story.append(tb); story.append(Spacer(1, 4))
        else:
            story.append(Paragraph(_inline(s), S["body"]))

    flush_tbl()
    if in_code:
        _flush_code(code_buf, S, story, W)
    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*", help="markdown 文件路径")
    ap.add_argument("--all", action="store_true", help="转换 docs/ 下所有 .md")
    args = ap.parse_args()

    root = Path(__file__).resolve().parent.parent
    targets: list[Path] = []
    if args.all:
        targets = sorted((root / "docs").glob("*.md"))
    for f in args.files:
        targets.append(Path(f))
    if not targets:
        ap.error("给出 .md 文件，或用 --all")

    for md in targets:
        md = md if md.is_absolute() else (root / md)
        if not md.exists():
            print(f"skip (missing): {md}"); continue
        pdf = md.with_suffix(".pdf")
        convert(md, pdf)
        print(f"wrote {pdf.relative_to(root)}  ({pdf.stat().st_size/1024:.1f} KB)")


if __name__ == "__main__":
    main()
