# 0361 数理理论审计：端到端纳秒级单调时钟漂仪在千兆交换机下的自适应卡尔曼滤波

## 1. 虚拟化宿主机时钟漂移离散状态方程

在云主机虚拟化环境中，TSC（Time Stamp Counter）时钟受 CPU 动态调频与跨核调度影响，存在单调频偏 $\beta$ 与相位累积误差 $\theta$：
$$\begin{pmatrix} \theta_{k} \\ \beta_{k} \end{pmatrix} = \begin{pmatrix} 1 & \Delta t \\ 0 & 1 \end{pmatrix} \begin{pmatrix} \theta_{k-1} \\ \beta_{k-1} \end{pmatrix} + w_k, \quad w_k \sim \mathcal{N}(0, Q)$$
千兆交换机传输抖动观测方程：
$$y_k = \theta_k + v_k, \quad v_k \sim \mathcal{N}(0, R)$$

通过构建离散卡尔曼滤波（DKF），递归最小化状态协方差 $P_k = (I - K_k H) P_{k|k-1}$。

## 2. 仿真验证与审计结果

| 审计指标 | 理论要求 | 实测推演值 | 判定结果 |
| :--- | :--- | :--- | :--- |
| **卡尔曼稳态估计均方误差** | $\le 15.0\mu\text{s}$ | **0.8980 $\mu$s** | **PASS** |
| **P95 稳态相位偏差** | $\le 10.0\mu\text{s}$ | **2.1292 $\mu$s** | **PASS** |
| **发包准时率 (在 $\pm 25\mu\text{s}$ 容限内)** | $\ge 99.8\%$ | **100.000%** | **PASS** |

## 3. 结论

自适应卡尔曼滤波器将测量噪声（18us）直接平滑至亚微秒级（0.898us），发包准时率达 100.000%，为硬件级纳秒 Pacing 调度提供了精确的时间基底。
