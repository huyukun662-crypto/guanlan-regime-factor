---
type: entity
entity_type: rule
created: 2026-06-05
sources:
  - [[2026-06-05-ssrn-6823998-yang-2026-hmm-factor-regimes]]
---

# Leakage控制协议

## 定义

全链条无前视协议：model selection / HMM estimation / 配置生成 / 评估都基于 t 时刻可得信息。Yang 2026 用此区分一般因子择时研究的潜在前视污染。

## 核心要点

- 实操：expanding window 月度 refit
- 防的不只是回测前视，还防 hyperparameter 长样本选优后报 OOS
- 与 V25 "IS 段只用于选参，OOS 严格只读" 的纪律同源
- 相关：[[Expanding window walk-forward]]

## 出处

- [[2026-06-05-ssrn-6823998-yang-2026-hmm-factor-regimes]]
