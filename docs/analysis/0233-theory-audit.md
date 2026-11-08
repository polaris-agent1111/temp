# Task 0233 Theory Audit: 基于李代数李括号的非线性流控全可控性证明

## 1. 非线性控制仿射系统建模 (Control-Affine System)

在连续流体排队模型中，系统状态向量定义为：
$$\mathbf{x}(t) = \begin{bmatrix} q(t) \\ v(t) \end{bmatrix} \in \mathbb{R}^2$$
其中 $q(t)$ 为瓶颈队列包数，$v(t)$ 为平滑后的瞬时发送速率（pkts/4ms）。

系统的控制仿射状态方程为：
$$\dot{\mathbf{x}}(t) = \mathbf{f}(\mathbf{x}) + \mathbf{g}(\mathbf{x}) u(t)$$
- 漂移矢量场（Drift vector field）：
  $$\mathbf{f}(\mathbf{x}) = \begin{bmatrix} v(t) - \mu \\ -\gamma (v(t) - v_0) \end{bmatrix}$$
  其中 $\mu = 37.5\text{ pkts/4ms}$ 为瓶颈链路服务率，$\gamma = 250\text{ s}^{-1}$ 为 4ms 漏桶跟踪带宽，$v_0$ 为工作点速率；
- 控制输入矢量场（Control vector field）：
  $$\mathbf{g}(\mathbf{x}) = \begin{bmatrix} 0 \\ \gamma \end{bmatrix}$$
  $u(t) \in [36.0, 41.0]$ 为漏桶设定速率控制输入。

## 2. 李括号运算与李代数秩条件 (Hermann-Krener LARC 定理)

对于光滑矢量场 $\mathbf{f}$ 与 $\mathbf{g}$，其李括号定义为矢量场之间的方向导数差：
$$[\mathbf{f}, \mathbf{g}](\mathbf{x}) = \frac{\partial \mathbf{g}}{\partial \mathbf{x}} \mathbf{f}(\mathbf{x}) - \frac{\partial \mathbf{f}}{\partial \mathbf{x}} \mathbf{g}(\mathbf{x})$$

计算各阶雅可比矩阵：
$$\frac{\partial \mathbf{g}}{\partial \mathbf{x}} = \begin{bmatrix} 0 & 0 \\ 0 & 0 \end{bmatrix}, \quad \frac{\partial \mathbf{f}}{\partial \mathbf{x}} = \begin{bmatrix} 0 & 1 \\ 0 & -\gamma \end{bmatrix}$$

因此：
$$[\mathbf{f}, \mathbf{g}](\mathbf{x}) = \mathbf{0} - \begin{bmatrix} 0 & 1 \\ 0 & -\gamma \end{bmatrix} \begin{bmatrix} 0 \\ \gamma \end{bmatrix} = \begin{bmatrix} -\gamma \\ \gamma^2 \end{bmatrix}$$

构造可控性李代数分布矩阵 $\mathcal{C}(\mathbf{x})$：
$$\mathcal{C}(\mathbf{x}) = \left[ \mathbf{g}(\mathbf{x}), \; [\mathbf{f}, \mathbf{g}](\mathbf{x}) \right] = \begin{bmatrix} 0 & -\gamma \\ \gamma & \gamma^2 \end{bmatrix}$$

其行列式为：
$$\det(\mathcal{C}(\mathbf{x})) = 0 \cdot \gamma^2 - \gamma \cdot (-\gamma) = \gamma^2 = 250^2 = 62,500 > 0$$

## 3. 全局结论与小时间局部可达性 (STLC)

1. **满秩定理**：在全状态工作空间域 $q \in [0, 38], \; v \in [30, 45]$ 内，$\operatorname{rank}(\mathcal{C}(\mathbf{x})) \equiv 2$ 恒成立，处处满足 Hermann-Krener 李代数秩条件；
2. **小时间局部可达性 (STLC)**：根据 Sussmann 可达性定理，由于控制场与一阶李括号张成全空间且无奇点，系统在任意紧致工作点邻域内均具备小时间局部可控性；
3. **物理意义**：这意味着通过 4ms 漏桶参数的离散阶梯调节，不仅可以直接控制发送速率 $v(t)$，而且能够通过李括号耦合项在极短时间内精确驱动队列长度 $q(t)$ 沿任意期望轨迹收敛至平衡点，不存在不可控的残余振荡模态。
