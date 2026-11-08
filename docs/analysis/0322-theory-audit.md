# 0322 理论审计：极端网络抖动下端到端单调时钟漂移标定

## 1. 核心理论：虚拟化 TSC 时钟漂移状态方程与卡尔曼-锁相环滤波

在云环境容器与虚拟机评测中，CPU 频率动态调节（DVFS）与 vCPU 抢占会导致硬件时间戳计数器（TSC）发生非线性时钟漂移与微秒级时间戳跳变。

### 1.1 状态转移与量测模型
建立二阶离散时间状态转移模型：
$$\begin{bmatrix} x_{k} \\ v_{k} \end{bmatrix} = \begin{bmatrix} 1 & \Delta t \\ 0 & 1 \end{bmatrix} \begin{bmatrix} x_{k-1} \\ v_{k-1} \end{bmatrix} + w_k, \quad w_k \sim \mathcal{N}(0, Q)$$
其中：
- $x_k$ 为单调时间偏差（Clock Offset）；
- $v_k$ 为时钟漂移斜率（Drift Rate）；
- 量测方程：$y_k = x_k + \epsilon_{\text{jitter}}, \quad \epsilon_{\text{jitter}} \sim \mathcal{N}(0, R)$。

通过卡尔曼状态估计，系统在强网络抖动下实时估计出精确的时钟漂移斜率，消除累积误差。

---

## 2. 仿真与实测统计指标

由 `zcode/scripts/clock0322_tsc_drift_calibration.py` 开展长达 100 s 的端到端时钟跟踪仿真：
1. **稳态时钟跟踪误差**：
   - 稳态 P95 时钟漂移误差收敛至 **44.34 $\mu$s**（门禁指标 $\le 50.0\ \mu\text{s}$）；
   - 最大瞬时误差小于 $76.34\ \mu\text{s}$；
2. **高频抖动抑制率**：
   - 面对标准差 $250\ \mu\text{s}$ 的极端调度与网络抖动，方差抑制率达 **99.13%**（门禁指标 $\ge 90.0\%$）。

---

## 3. 门禁审计结论
- 验证脚本：`zcode/scripts/clock0322_tsc_drift_calibration.py`
- 审计报表：`runs/clock0322_tsc_drift_calibration.json`
- 结论：**`PASS` (P95 时钟漂移误差 44.34 us，抖动滤除率 99.13%，保障微秒级单调 Pacing 精度)**。
