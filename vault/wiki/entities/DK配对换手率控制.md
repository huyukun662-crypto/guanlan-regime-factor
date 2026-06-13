---
type: entity
entity_type: mechanism
created: 2026-05-16
sources:
  - [[2026-05-16-worldquant-brain-api-zh-ready-顾问培训]]
---

# DK配对换手率控制

## 定义

BRAIN 回测前的工程步骤：表达式与 DK（衰减/平滑参数）配对，控制 alpha 换手率从而控制交易成本。

## 核心要点

- 与 [[trade_when算子]] 都影响换手频率，但 DK 是平滑层、trade_when 是触发层
- 高换手 alpha 必须做 DK 配对再回测

## 出处

- [[2026-05-16-worldquant-brain-api-zh-ready-顾问培训]]
