# CLAUDE.md — 观澜 · 大势研判 + 因子研究助手（项目级）

## 这是什么
自包含的量化研究作业：agent + 3 skills，仪表板两页——**大势研判**（HMM 4 态 × Kaufman 效率比 × 基本面 + 风险研判 + AI 顾问）与**因子看板**（真实风格指数代理因子），真实 A 股 ETF / 指数数据驱动。FOF 组合模块已从仪表板移除，代码保留在 `fof/` 作研究证据链（见 [README.md](README.md)）。

## 常用命令
```powershell
python scripts\run_pipeline.py --asof 2026-06-05 --start 2020-01-01   # 全链路 -> outputs/*.json + docs/
python -m uvicorn server.app:app --port 8000                          # 仪表盘 http://localhost:8000
python -m pytest tests -q                                             # 单测
python scripts\grid_search.py                                         # 网格证据 -> outputs/grid_search.csv
```
> 控制台中文乱码时设 `$env:PYTHONIOENCODING="utf-8"`（仅显示问题，文件均为 UTF-8）。

## 硬约束（改代码必须遵守）
- **防前视**：任何指标/选择只用 `series.loc[:asof]`；回测收益 `nav.pct_change().shift(-1)`（收盘决策、次日兑现）。新增 sleeve 的 `rule_fn` 也必须只看 `panels[...].loc[:d]`。
- **密钥**：`TUSHARE_TOKEN`/`ANTHROPIC_API_KEY` 只从 `.env`（gitignored）读，绝不写进任何提交文件或日志。
- **JSON 安全**：所有 `outputs/*.json` 经 `report._finite` 清洗 NaN/Inf → null（Starlette JSONResponse 拒绝 NaN）。
- **诚实**：FOF 以 raw 收益换低回撤，前后对比与 STRATEGY 文档须如实标注，不得暗示"免费午餐"。

## 模块边界（coding-style：单文件 200-400 行）
- `fof/selection.py` 4 铁律选择 · `fof/weights.py` 风险平价+上限+门控 · `fof/engine.py` 每日回测主循环
- `fof/regime.py` 指标+综合分 · `fof/report.py` 汇总 outputs/*.json + 前后对比
- 数据源切换在 `fof/data.py`（Tushare 主、efinance 备）；新参数加到 `fof/config.py:FOFConfig`
- 改了 4 铁律参数 → 跑 `scripts/grid_search.py` 留证据，冠军写回 `FOFConfig` 默认值
