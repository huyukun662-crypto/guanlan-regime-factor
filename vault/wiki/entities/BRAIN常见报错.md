---
type: entity
entity_type: knowledge
created: 2026-05-16
sources:
  - [[2026-05-16-worldquant-brain-api-zh-ready-顾问培训]]
---

# BRAIN常见报错

## 定义

BRAIN Python API 实操中高频出现的 4 类错误及触发条件。

## 核心要点

| 报错类型 | 触发原因 |
|---------|----------|
| location_key 错误 | 参数大小写写错 |
| 并发超限 | 提交速度超过角色槽位上限 |
| not_complete | session 认证失效（4 小时过期） |
| 跨 region 算子类型不匹配 | 同算子在不同 region 数据类型不一致 |
| multi simulation 整组失败 | 任一子任务表达式错误连带 |

- 调试建议：multi simulation 整组失败时，**逐个子任务**排查
- 相关：[[BRAIN Python API]] [[multi simulation]]

## 出处

- [[2026-05-16-worldquant-brain-api-zh-ready-顾问培训]]
