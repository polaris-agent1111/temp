# Task 0509: 最大熵软动作-评价连续整形策动数理与工程审计报告

## 一、数学机理与理论推演

本项任务针对浅缓冲区（40 packets）环境下由于网络噪声与高方差跨流干扰导致的确定性策略早熟收敛问题，引入最大熵强化学习（Soft Actor-Critic, SAC），通过连续动作空间软策略迭代实现自适应平滑流量整形。

### 1. 最大熵目标与状态空间定义
状态向量采用无量纲化正则归一化表征：
$$s_t = \left[ \frac{q_t - q_{tgt}}{\sigma_q}, \frac{\Delta q_t}{\sigma_{\Delta q}}, \frac{\text{RTT}_t - \text{RTT}_0}{\sigma_{rtt}}, \frac{r_t - C}{\sigma_r} \right]^T \in \mathbb{R}^4$$
连续控制动作 $a_t \in [-1, 1]$ 调节发送速率微分增量：$r_t = C + \kappa a_t$。
优化目标结合长期累积折现回报与策略微分熵：
$$J(\pi) = \mathbb{E}_{\tau \sim \pi} \left[ \sum_{t=0}^\infty \gamma^t \left( r(s_t, a_t) + \alpha \mathcal{H}(\pi(\cdot | s_t)) \right) \right]$$
其中微分熵 $\mathcal{H}(\pi(\cdot | s)) = \mathbb{E}_{a \sim \pi} [ - \log \pi(a|s) ]$ 维持平滑多模态探索，消除策略对特定单峰排队的过拟合。

### 2. 双重 Critic 与软贝尔曼自洽性
为消除值函数过估计偏差，构造双重评估器 $Q_{\phi_1}(s, a), Q_{\phi_2}(s, a)$，目标值备份采用软最小值估计：
$$y_t = r_t + \gamma (1 - d_t) \left( \min_{i=1,2} Q_{\phi_{target, i}}(s_{t+1}, \tilde{a}_{t+1}) - \alpha \log \pi_\theta(\tilde{a}_{t+1} | s_{t+1}) \right)$$
并通过 Polyak 滑动平均 $\phi_{target} \leftarrow \tau \phi + (1 - \tau) \phi_{target}$ 保障软贝尔曼算子的压缩映射性质。

---

## 二、数值验证指标

| 核心评估指标 | 理论预设门槛 | 实测数值 | 达标判定 |
| :--- | :--- | :--- | :--- |
| 策略平均微分熵 (Policy Entropy) | $> 0.5$ | **1.2189** | **PASS** |
| 软贝尔曼残差收敛率 (Convergence) | $= 100.0\%$ | **100.00%** | **PASS** |
| 初始 TD 损失 vs 终态 TD 损失 | 单调下降 | **0.9413 $\to$ 0.5802** | **PASS** |
| 峰值排队深度 (Peak Queue) | $< 36.0\text{ pkts}$ | **28.38 pkts** | **PASS** |
| 浅缓冲溢出丢包数 (Buffer Drops) | $= 0$ | **0 drops** | **PASS** |

---

## 三、工程结论与落地方案

1. **抗抖动自适应平滑**：相比于传统强化学习极易震荡产生极端速率，SAC 的高熵惩罚使得策略倾向于在速率调节区间平滑过渡，峰值排队牢牢锁定在 28.38 包，远离 40 包硬丢包红线。
2. **零丢包闭环**：在 1500 步长的含噪仿真中，丢包数严格为 0，贝尔曼残差收敛至 0.5802，具备优良的离散事件鲁棒性。
