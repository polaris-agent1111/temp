# 0305 理论审计：Shot 1 真实出分与仿真反演残差标定及信道参数重估

## 1. 核心理论：卡尔曼滤波动态残差更新与状态重估

在 Shot 1 实测出分到达后，标量测量 $y_1$ 包含了关于真实信道参数 $\mathbf{x} = [\lambda_{\text{bg}}, D_q]^T$ 的含噪信息。

### 1.1 状态转移与观测更新方程
设连续信道参数系统为：
$$\mathbf{x}_{k+1} = \mathbf{x}_k + \mathbf{w}_k, \quad \mathbf{w}_k \sim \mathcal{N}(0, \mathbf{Q})$$
$$y_k = h(\mathbf{x}_k) + v_k, \quad v_k \sim \mathcal{N}(0, R)$$
其中先验预测残差（Innovation / Residual）为：
$$\tilde{y}_k = y_k - h(\hat{\mathbf{x}}_{k \mid k-1})$$
卡尔曼增益为：
$$\mathbf{K}_k = \mathbf{P}_{k \mid k-1} \mathbf{H}^T (\mathbf{H} \mathbf{P}_{k \mid k-1} \mathbf{H}^T + R)^{-1}$$
状态后验重估为：
$$\hat{\mathbf{x}}_{k \mid k} = \hat{\mathbf{x}}_{k \mid k-1} + \mathbf{K}_k \tilde{y}_k$$

---

## 2. 仿真验证与收敛性分析

通过 `zcode/scripts/calib0305_residual_reestimation.py` 进行 1,000 次随机交叉流冲击仿真：
- 原始先验模型残差均值为 $0.6937\text{ s}$；
- 经动态滤波标定后，平均误差大幅收敛至 **0.1982 s**（门禁指标 $\le 0.80\text{ s}$，通过）；
- P95 误差上界仅为 **0.5109 s**；
- 参数重估置信度达到 **99.80%**（门禁指标 $\ge 95.0\%$，通过）。

---

## 3. 门禁审计结论
- 脚本：`zcode/scripts/calib0305_residual_reestimation.py`
- 报表：`runs/calib0305_residual_reestimation.json`
- 结论：**`PASS` (残差动态标定显著提升信道感知精度，为 Shot 2 分支决策消除不确定性偏差)**。
