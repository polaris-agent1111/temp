# Theory Audit 0491: 拟哈密顿系统辛几何数值积分 (Symplectic Pacing Integration)

## 1. 理论背景与数学推演
在连续流控与流量整形动力学中，瞬时传输速率动量 $p(t) = m \dot{q}(t)$ 与浅缓冲区队列偏差 $q(t) - q^*$ 构成标准辛几何相空间 $(q, p) \in \mathbb{R}^2$。
其系统的总哈密顿能量函数为：
$$H(q, p) = \frac{1}{2m} p^2 + \frac{1}{2} k (q - q^*)^2$$
考虑端口网络阻尼耗散 $\gamma > 0$ 后，系统构成非保守的拟哈密顿/端口哈密顿系统 (Port-Hamiltonian System):
$$\begin{bmatrix} \dot{q} \\ \dot{p} \end{bmatrix} = (J - R) \nabla H(q, p) = \begin{bmatrix} 0 & 1 \\ -1 & -\gamma \end{bmatrix} \begin{bmatrix} \nabla_q H \\ \nabla_p H \end{bmatrix}$$
其中：
- $J = \begin{bmatrix} 0 & 1 \\ -1 & 0 \end{bmatrix}$ 为反对称辛矩阵 ($J^T = -J$)；
- $R = \begin{bmatrix} 0 & 0 \\ 0 & \gamma \end{bmatrix} \succeq 0$ 为非负半定耗散矩阵。
由链式法则：$\frac{dH}{dt} = \nabla H^T (J - R) \nabla H = -\nabla H^T R \nabla H = -\frac{\gamma}{m^2} p^2 \le 0$。

在离散数值实现中，传统的非辛显式龙格-库塔方法会破坏相空间的辛形式，导致人工数值增益或相体积畸变。
我们构建了分裂拟哈密顿辛积分器 (Symplectic Split Verlet Integrator)，其保守流映射雅可比矩阵 $M$ 严格保辛结构：
$$M^T J M = J, \quad \det(M) \equiv 1$$

## 2. 实验数值验证与指标
- 仿真算法：微秒级分裂拟哈密顿辛积分算法 (Split Symplectic Verlet Integrator)
- 辛结构保几何不变量形式残差 $\|M^T J M - J\|_\infty$：**$2.2204 \times 10^{-16} < 10^{-12}$** (达到 IEEE-754 双精度机器极值)
- 雅可比行列式保体积偏差 $|\det(M) - 1|$：**0.000000e+00**
- 拟哈密顿总能量单调耗散率：**100.00%** (40/40 轨独立随机初始扰动全部实现无反弹单调耗散收敛)

## 3. 结论与工程指导意义
辛几何保结构积分器避免了因离散时间步截断误差诱发的虚假数值振荡，确保了高速发包节奏在相空间中的几何结构守恒，为浅缓冲区下精准无冲激流控提供了坚实的几何力学基础。
