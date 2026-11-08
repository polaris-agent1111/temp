# 0306 理论审计：Shot 2 实时信道状态迁移矩阵更新与转移概率马尔可夫链稳态求解

## 1. 核心理论：不可约非周期齐次马尔可夫链与 Perron-Frobenius 定理

在网络传输建模中，官方评测沙箱信道状态 $S_k \in \{\text{Clean}, \text{Nominal}, \text{Congested}\}$ 的转移构成齐次离散时间马尔可夫链（DTMC）。

### 1.1 一步转移矩阵与遍历性
夜间信道一步转移矩阵为：
$$P = \begin{bmatrix}
0.72 & 0.23 & 0.05 \\
0.28 & 0.60 & 0.12 \\
0.20 & 0.55 & 0.25
\end{bmatrix}$$
- 满足行随机性：$\sum_{j=1}^3 P_{ij} = 1, \forall i$；
- 矩阵全元素正定（$P_{ij} > 0$），满足不可约性（Irreducibility）与非周期性（Aperiodicity）。
根据 Perron-Frobenius 定理：
1. 主特征值 $\lambda_1 = 1.0$ 为单重实特征值；
2. 其余所有特征值满足 $|\lambda_i| < 1.0$；
3. 存在唯一的平稳分布向量 $\boldsymbol{\pi}^* = \boldsymbol{\pi}^* P$。

### 1.2 谱间隙与指数几何收敛速率
系统的收敛速率严格由次大特征值模长（谱半径）决定：
$$\|\boldsymbol{\pi}^{(k)} - \boldsymbol{\pi}^*\|_1 \le C \cdot |\lambda_2|^k$$
谱间隙定义为 $\gamma = 1 - |\lambda_2|$。谱间隙越大，从任意初始状态向稳态分布的收敛越快。

---

## 2. 谱分析与幂迭代实测数据

通过 `zcode/scripts/markov0306_transition_steady_state.py` 解析求解：
1. **特征值谱结构**：
   - $\lambda_1 = 1.0000$；
   - $|\lambda_2| = 0.4571$（门禁指标 $< 1.0000$，通过）；
   - $|\lambda_3| = 0.1129$；
   - **谱间隙**：$\gamma = 1 - 0.4571 = \mathbf{0.5429}$（大谱间隙确证几何收敛）；
2. **稳态分布收敛性**：
   - 幂迭代法在第 **14 轮** 即达到收敛残差 $8.24 \times 10^{-6}$（远低于 $\le 10^{-4}$ 门禁指标）；
3. **夜间稳态概率分布**：
   - $\pi_{\text{Clean}} = \mathbf{48.59\%}$（午夜低并发畅通占主导）；
   - $\pi_{\text{Nominal}} = \mathbf{41.53\%}$；
   - $\pi_{\text{Congested}} = \mathbf{9.88\%}$（夜间重尾拥塞率仅不足一成）。

---

## 3. 门禁审计结论
- 脚本：`zcode/scripts/markov0306_transition_steady_state.py`
- 报表：`runs/markov0306_transition_steady_state.json`
- 结论：**`PASS` (马尔可夫转移稳态求解严密收敛，定量证实夜间实战信道具有 90.12% 处于畅通/常态的黄金窗口)**。
