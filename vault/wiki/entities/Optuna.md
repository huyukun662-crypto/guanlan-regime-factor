---
tags: [机器学习, 工具, 超参优化]
created: 2026-05-05
updated: 2026-05-05
type: entity
entity_type: tool
sources:
  - wiki/sources/2026-05-05-openalphas-lightgbm-bayesian.md
---

# Optuna

> Python 自动超参优化库（Preferred Networks 2019 开源）

## 一句话定义

Optuna 是一个 Python 超参优化库，默认使用 TPE（Tree-structured Parzen Estimator）作为采集函数实现 [[贝叶斯超参优化]]，支持**剪枝**（提前终止表现差的试验）和**分布式搜索**。

## 标准量化用法

```python
import optuna
import lightgbm as lgb

def objective(trial):
    params = {
        'min_data_in_leaf': trial.suggest_int('min_data_in_leaf', 20, 200),
        'feature_fraction': trial.suggest_float('feature_fraction', 0.5, 1.0),
        'bagging_fraction': trial.suggest_float('bagging_fraction', 0.5, 1.0),
        'lambda_l1': trial.suggest_float('lambda_l1', 0, 10),
        'lambda_l2': trial.suggest_float('lambda_l2', 0, 10),
    }
    model = lgb.train(params, train_data, valid_sets=[val_data])
    pred = model.predict(val_X)
    ic = spearmanr(pred, val_y).correlation
    return ic

study = optuna.create_study(direction='maximize')
study.optimize(objective, n_trials=50)
print(study.best_params)
```

## 在素材中的出现

- [[2026-05-05-openalphas-lightgbm-bayesian]]：50 轮贝叶斯超参搜索，目标 = 验证集 IC

## 相关页面

- 主题：[[机器学习选股]]
- 配套：[[贝叶斯超参优化]]、[[LightGBM]]
