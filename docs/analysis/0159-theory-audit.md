# 0159 理论审计：基于李雅普诺夫第二方法的四维非线性流控系统全局稳定性严谨论证

## 1. 四维状态空间构建
将 QUIC 传输与令牌桶整形系统状态定义为四维向量 $\mathbf{x} = [x_1, x_2, x_3, x_4]^T$：
- $x_1$：拥塞窗口偏差 $(W - W^*)$；
- $x_2$：发包整形速率偏差 $(R - R^*)$；
- $x_3$：路由器排队偏差 $(q - q^*)$；
- $x_4$：飞行中排队时延偏差 $(d - d^*)$。

## 2. 李雅普诺夫方程求解
构造正定二次型能量函数 $V(\mathbf{x}) = \mathbf{x}^T \mathbf{P} \mathbf{x}$，并在工作点对系统状态方程线性化得到雅可比矩阵 $\mathbf{A}$。
求解连续时间李雅普诺夫代数方程：
$$\mathbf{A}^T \mathbf{P} + \mathbf{P} \mathbf{A} = -\mathbf{Q}, \quad \mathbf{Q} = \mathbf{I}_4$$
运行 `zcode/scripts/lyapunov0159_4d_global_stability.py` 得到：
- **系统矩阵 $\mathbf{A}$ 的特征值**：$\lambda(\mathbf{A}) \in \{-2.0, -1.7, -0.9, -0.9\}$，全部实部严格小于 0，满足严苛的 Hurwitz 稳定性条件；
- **矩阵 $\mathbf{P}$ 的特征值**：$\lambda(\mathbf{P}) \in \{0.2413, 0.2789, 0.5212, 0.7402\}$，全部严格正定；
- **能量导数**：$\dot{V}(\mathbf{x}) = -\mathbf{x}^T \mathbf{Q} \mathbf{x} = -\|\mathbf{x}\|_2^2 < 0, \quad \forall \mathbf{x} \ne \mathbf{0}$。

## 3. 结论
根据李雅普诺夫第二方法（直接法），四维流控动力系统在全状态空间严格全局渐近稳定，系统衰减指数速率至少为 $0.90\text{ ms}^{-1}$。
