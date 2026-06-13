---
type: entity
entity_type: mechanism
created: 2026-05-16
sources:
  - [[2026-05-16-worldquant-brain-api-zh-ready-顾问培训]]
---

# neutralization鲁棒性检测

## 定义

BRAIN 评估 alpha 鲁棒性的标准流程：用 rank（抹除数值仅保留排序）、sign/binary（仅保留正负）三种压力测试，表现仍稳定则鲁棒性强。

## 核心要点

- 三种抹除测试：
  - rank → 保留排序丢弃数值
  - sign → 保留方向丢弃幅度
  - binary → 二值化 (>0 / ≤0)
- 通过测试 = 信号不依赖数值精确度
- **可借鉴到 V25**：作为 OOS 验证的额外鲁棒性测试
- 相关：[[group算子]] [[alpha筛选去冗余]]

## 出处

- [[2026-05-16-worldquant-brain-api-zh-ready-顾问培训]]
