"""Lightweight grid search over the 4-铁律 tunables -> outputs/grid_search.csv.

Sweeps min_pass / calmar_min / ranging-gate / eval_window around the defaults and reports
each config's FOF metrics vs the (constant) equal-weight baseline. Reuses one prepared data
bundle so all combos share identical data — the differences are purely the selection logic.

NOTE: this is an IN-SAMPLE convenience tune over the full window (no held-out OOS), used to
pick sensible MVP defaults — NOT an OOS-validated champion. See docs/before-after.md caveats.
"""

from __future__ import annotations

import csv
import logging
import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fof.config import DEFAULT_CONFIG
from fof import engine
from fof.metrics import compute_segment

logging.basicConfig(level=logging.ERROR)
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)

MIN_PASS = [1, 2]
CALMAR_MIN = [0.8, 1.0, 1.3, 1.5]
RANGING_GATE = [0.8, 1.0]
EVAL_WINDOW = [42, 63]
# 收益偏低的主因是「单survivor被max_weight截断、超出部分丢给货基」的现金拖累。
# 放开 max_weight 让动量赢家少被稀释（cap=1.0 即取消单sleeve上限，牺牲分散换收益）。
MAX_WEIGHT = [0.5, 0.65, 0.8, 1.0]

# 回撤上限：追收益但仍保住「比等权强」的底线（等权 dd≈-9.5%）。
DD_CEIL = -0.13
# 风险底线：重调后 sharpe 不得低于此（当前冠军≈1.06，放宽到 0.95 给收益让路）。
SHARPE_FLOOR = 0.95


def _gate(ranging: float) -> dict[str, float]:
    return {"trend": 1.0, "ranging": ranging, "bear": 0.0}


def main() -> None:
    prepared = engine.prepare(DEFAULT_CONFIG)
    base = compute_segment(engine.run_fof(DEFAULT_CONFIG, prepared).baseline_nav, "baseline")
    print(f"baseline: ann={base.ann_return:.3f} dd={base.max_dd:.3f} "
          f"sharpe={base.sharpe:.2f} calmar={base.calmar:.2f}")

    rows = []
    for mp in MIN_PASS:
        for cm in CALMAR_MIN:
            for rg in RANGING_GATE:
                for ew in EVAL_WINDOW:
                    for mw in MAX_WEIGHT:
                        cfg = replace(DEFAULT_CONFIG, min_pass=mp, calmar_min=cm,
                                      regime_gate=_gate(rg), eval_window=ew, max_weight=mw)
                        res = engine.run_fof(cfg, prepared)
                        m = compute_segment(res.nav, "fof")
                        n_cash = sum(rb["fallback_to_cash"] for rb in res.rebalances)
                        avg_inv = sum(1 - rb["money_market_weight"]
                                      for rb in res.rebalances) / len(res.rebalances)
                        rows.append({
                            "min_pass": mp, "calmar_min": cm, "ranging_gate": rg,
                            "eval_window": ew, "max_weight": mw,
                            "ann_return": round(m.ann_return, 4), "max_dd": round(m.max_dd, 4),
                            "sharpe": round(m.sharpe, 3), "calmar": round(m.calmar, 3),
                            "avg_invested": round(avg_inv, 3),
                            "n_cash_rebal": n_cash, "n_rebal": len(res.rebalances),
                        })

    # 收益优先：回撤设上限 + sharpe 底线，在可行域里最大化年化（次选 calmar）。
    feasible = [r for r in rows
                if r["max_dd"] > DD_CEIL and r["sharpe"] >= SHARPE_FLOOR
                and r["avg_invested"] > 0.30]
    ranked = sorted(feasible, key=lambda r: (r["ann_return"], r["calmar"]), reverse=True)
    # 对照前沿：纯风险调整最优（旧目标）。
    calmar_front = sorted(
        [r for r in rows if r["max_dd"] > -0.12 and r["avg_invested"] > 0.30],
        key=lambda r: (r["calmar"], r["sharpe"]), reverse=True)

    path = OUT / "grid_search.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(sorted(rows, key=lambda r: (r["ann_return"], r["calmar"]), reverse=True))
    print(f"wrote {path} ({len(rows)} configs)")

    def _show(tag, lst):
        print(f"\n{tag}:")
        for r in lst[:6]:
            print(f"  mp={r['min_pass']} cm={r['calmar_min']} rg={r['ranging_gate']} "
                  f"ew={r['eval_window']} mw={r['max_weight']} | "
                  f"ann={r['ann_return']:.3f} dd={r['max_dd']:.3f} "
                  f"sharpe={r['sharpe']:.2f} calmar={r['calmar']:.2f} inv={r['avg_invested']:.2f}")

    _show(f"收益优先 Top6 (dd>{DD_CEIL}, sharpe>={SHARPE_FLOOR}, inv>30%)", ranked)
    _show("对照·calmar前沿 Top6 (dd>-12%)", calmar_front)


if __name__ == "__main__":
    main()
