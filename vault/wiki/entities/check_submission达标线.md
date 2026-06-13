---
type: entity
entity_type: rule
created: 2026-05-16
sources:
  - [[2026-05-16-worldquant-brain-api-zh-ready-顾问培训]]
---

# check_submission达标线

## 定义

BRAIN 平台 alpha 提交合规检查阈值，按角色分层：用户需 Sharp ≥ 25；顾问需 Sharp ≥ 58 且 fitness ≥ 1。

## 核心要点

- 顾问标准明显更严（Sharp 翻 2.3 倍 + 必须有 fitness）
- 通过 check_submission 即放入 GoBack 队列
- 是平台的硬约束门槛，不达标无法提交
- 注意：BRAIN 的 Sharp 与本地 backtester Sharp 口径**可能不同**，需对照

## 出处

- [[2026-05-16-worldquant-brain-api-zh-ready-顾问培训]]
