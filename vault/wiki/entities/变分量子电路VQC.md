---
tags: [量子机器学习, VQC, NISQ, 量子神经网络]
created: 2026-05-06
updated: 2026-05-06
type: entity
entity_type: algorithm
sources:
  - wiki/sources/2026-05-06-datou-q-a3c2-paper-reading.md
---

# 变分量子电路（VQC）

> Variational Quantum Circuit — 量子机器学习的核心构件，把经典数据编码到量子态后做参数化变换

## 一句话定义

VQC 是一类**带参数的量子电路**：经典数据 x 经"量子特征映射"嵌入量子态 → 应用一系列参数化量子门 U(θ) → 测量得到经典输出 → 经典优化器更新 θ。**类似经典神经网络的层**，但运算在希尔伯特空间。

## 三段式结构

```
经典数据 x
    ↓
[特征映射 F(x)] → |ψ(x)⟩ （量子态）
    ↓
[参数化量子门 U(θ)] → U(θ)|ψ(x)⟩
    ↓
[测量] → 经典输出
    ↓
[经典优化器] → 更新 θ
```

## 关键要素

### 1. 特征映射（Feature Map）
- 把经典向量 x ∈ ℝⁿ 嵌入希尔伯特空间 |ψ(x)⟩
- 常用：振幅编码 / 角度编码 / 基态编码
- **类似 SVM 的核函数**（但表达能力可能更强）

### 2. 参数化量子门（Ansatz）
- 由可训练参数 θ 控制的量子门序列
- 常用：Hardware-Efficient Ansatz / QAOA-style / Pauli-Rotation
- 类似 NN 的"层"

### 3. 测量（Measurement）
- 通常测 Pauli-Z 期望值 ⟨ψ|Z_i|ψ⟩
- 输出经典实数
- 可作为 logits / 概率使用

## 训练范式

```python
# 伪代码
for epoch in range(N):
    for batch in data:
        loss = sum(loss_fn(VQC(x_i, θ), y_i) for x_i, y_i in batch)
        # 梯度通过 parameter-shift rule 计算
        grad = parameter_shift_rule(VQC, θ)
        θ = θ - lr · grad
```

**关键工具**：parameter-shift rule（量子计算梯度的标准方法）

## NISQ 时代的实用性

- **NISQ** = Noisy Intermediate-Scale Quantum
- 当前量子硬件：
  - 量子比特数：50-1000+
  - 噪声水平：~10⁻³ ~ 10⁻²
  - 相干时间：μs 级别
- VQC 因为**电路深度浅 + 容错性较好**，是 NISQ 时代主流的量子算法范式
- 即使在嘈杂硬件上也能工作（论文中常用 IBM Quantum / Google Sycamore 等真实硬件）

## 在量化金融的应用

### 已知应用
1. **量子强化学习**：[[Q-A3C²]] 把 VQC 作为策略网络瓶颈
2. **投资组合优化**：QAOA 用于优化二次问题（Markowitz）
3. **期权定价**：量子 Monte Carlo
4. **金融时序预测**：VQC + LSTM 混合架构

### 优势（理论）
- **指数级表达空间**：n 个量子比特能表示 2ⁿ 维向量
- **量子并行**：多状态同时处理
- **新型核函数**：可能捕捉经典核学不到的模式

### 现实质疑
- **量子优势未经实证证明**（many studies show 经典 SVM/NN 同样有效）
- **训练成本高**：量子模拟器 + 真实硬件都慢
- **样本效率不显著优于经典**

## 主流量子机器学习库

| 库 | 来源 | 特点 |
|---|---|---|
| **PennyLane** | Xanadu | 与 PyTorch / TF 集成最好 |
| Qiskit | IBM | 官方 IBM Quantum 入口 |
| Cirq | Google | TF-Quantum 集成 |
| TensorFlow Quantum | Google | TF + Cirq 包装 |

## 在素材中的出现

- [[2026-05-06-datou-q-a3c2-paper-reading]]：作为 [[Q-A3C²]] 策略网络的非线性瓶颈

## V25 项目相关性

- **不优先**（量子机器学习的工程门槛高 + 优势未实证）
- 但作为知识库**首个量子计算实体**，是个标记 — 未来 NISQ 硬件成熟时可重新评估

## 相关页面

- 主题：[[量子强化学习QRL]]（待创建）、[[机器学习选股]]
- 应用：[[Q-A3C²]]
- 来源：[[2026-05-06-datou-q-a3c2-paper-reading]]
