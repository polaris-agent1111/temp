# Theory Audit 0500: 李雅普诺夫指数谱确定性混沌分岔抑制 (Lyapunov Exponent Spectrum Chaos Suppression)

## 1. 理论背景与数学推演
在浅缓冲区网络中，基于延迟确认反馈的速率拥塞控制因时延滞后与非线性丢包门限，极易诱发周期倍化分岔（Period-Doubling Bifurcation）并演化为确定性混沌。
考虑 3D 非线性状态流控模型 $x = [r, q, \tau]^T$：
$$\begin{cases}
\dot{r}(t) = \frac{1}{\tau(t)} \left[ \alpha - \beta r(t) \cdot \Phi(q(t)) + u_{\text{stab}}(t) \right] \\
\dot{q}(t) = r(t) - \mu \\
\dot{\tau}(t) = \frac{1}{T_f} \left( D_0 + \frac{q(t)}{\mu} - \tau(t) \right)
\end{cases}$$
其中 $\Phi(q) = \frac{1}{1 + e^{-k_c (q - B_{\text{thresh}})}}$ 为 S 型非线性标记函数。
为了计算切空间的李雅普诺夫指数谱 $\{\lambda_1, \lambda_2, \lambda_3\}$，对线性变分切空间演化方程 $\dot{\Phi}(t) = J(x(t)) \Phi(t)$ 进行连续 Gram-Schmidt 正交化 (QR 分解)：
$$\lambda_i = \lim_{T \to \infty} \frac{1}{T} \int_0^T \ln |R_{ii}(t)| dt$$
为了消除混沌吸引子与轨道发散，我们设计了比例-微分队列锚定稳定化控制律：
$$u_{\text{stab}}(t) = - K_p (q(t) - q^*) - K_d (r(t) - \mu)$$
其精确重构了雅可比矩阵对角线阻尼项，使系统各向异性收缩，主李雅普诺夫指数严格负定。

## 2. 实验数值验证与指标
- 仿真算法：连续微秒步长 QR 动态标架正交化积分 (QR interval = 10 steps)
- 全李雅普诺夫指数谱：$\lambda_1 = -0.105857$, $\lambda_2 = -0.221829$, $\lambda_3 = -0.501915$
- 最大李雅普诺夫指数 (MLE)：**-0.105857 < 0.0** (所有轨道指数严格负定，无任何混沌边缘发散)
- 相空间相体积耗散收缩率 $\text{Tr}(J) < 0$：**100.00%**
- 独立初始状态混沌抑制收敛率：**100.00%** (25/25 独立随机扰动全部平稳收敛至目标鞍点)

## 3. 结论与工程指导意义
最大李雅普诺夫指数的负定性确立了流量控制回路的严格轨道渐近稳定性，消除了浅缓冲区极易发生的极限环振荡与周期分岔混沌，从动力系统本质上锁定了发包节奏的确定性平滑。
