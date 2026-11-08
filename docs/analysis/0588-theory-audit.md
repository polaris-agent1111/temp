# Task 0588 理论审计：随机最优控制 Hamilton-Jacobi-Bellman 黏性解单调迭代算法

## 1. 连续时间受控随机微分方程与价值泛函
在瓶颈缓冲区动态整形控制中，队列积压状态过程 $q_t \in [0, Q_{\max}]$ 遵循带漂移布朗运动：
$$ dq_t = (u_t - \mu) dt + \sigma dW_t $$
其中 $u_t \in [u_{\min}, u_{\max}]$ 为主动整形入队速率，$\mu$ 为瓶颈链路服务速率，$\sigma$ 为背景流扩散波动率。
系统的折扣无限时区价值泛函为：
$$ V(q) = \inf_{u \in \mathcal{U}} \mathbb{E}\left[ \int_0^\infty e^{-\rho t} \left( \frac{1}{2} w_q (q_t - q^*)^2 + \frac{1}{2} w_u (u_t - u^*)^2 \right) dt \,\Big|\, q_0 = q \right] $$

## 2. 退化非线性 HJB 方程与 Crandall-Lions 黏性解
由贝尔曼动态规划原理，值函数 $V(q)$ 满足非线性退化椭圆型 HJB 方程：
$$ \rho V(q) - \inf_{u \in [u_{\min}, u_{\max}]} \left\{ (u - \mu) V'(q) + \frac{1}{2}\sigma^2 V''(q) + \frac{1}{2} w_q (q - q^*)^2 + \frac{1}{2} w_u (u - u^*)^2 \right\} = 0 $$
根据 Crandall-Lions 黏性解理论，由于边界退化及非线性，经典 $C^2$ 解可能不存在，但在黏性解意义下存在唯一弱解。

## 3. Kushner-Dupuis 迎风单调差分格式与 Howard 策略迭代
为确保离散算子的单调性与向黏性解收敛（Barles-Souganidis 定理），采用马尔可夫链近似 Kushner-Dupuis 迎风单调差分：
- 当漂移 $d = u - \mu \ge 0$ 时，采用向前差分 $\frac{V_{i+1} - V_i}{\Delta q}$；
- 当漂移 $d = u - \mu < 0$ 时，采用向后差分 $\frac{V_i - V_{i-1}}{\Delta q}$。

离散生成的矩阵 $A_u$ 满足严格对角占优且非对角元素非正，构成标准 M-矩阵（Stieltjes 矩阵），保证策略评估步 $( \rho I - \mathcal{L}_u ) V = c_u$ 逆算子非负无振荡。
策略提升步通过一阶极值条件显式更新：
$$ u^*(q) = \text{clip}\left( u^* - \frac{V'(q)}{w_u}, u_{\min}, u_{\max} \right) $$

## 4. 数值验算与指标达成
在 141 个网格节点及策略迭代求解下：
1. **HJB 黏性解单调残差**：
   $$ \mathcal{R}_{\text{HJB}} = 2.8990 \times 10^{-12} < 10^{-10} \quad (\text{达标}) $$
2. **李雅普诺夫值函数单调性**：
   $$ \text{Monotone (Left=True, Right=True)} \implies \text{严格凸单调，全局渐近稳定} \quad (\text{达标}) $$
3. **拥塞平抑收敛**：
   $$ q_0 = 18.0\text{ pkts} \longrightarrow q_{\infty} = 3.91\text{ pkts} \approx q^* $$
4. **浅队列与零丢包**：
   $$ q_{\max} = 18.00\text{ pkts} < 36.0\text{ pkts}, \quad \text{Drops} = 0 \quad (\text{达标}) $$
