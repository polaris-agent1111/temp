# Task 0266 理论审计报告：瓶颈网络主动丢包与被动排队时延交叉相关分析

## 1. 动力学背景与理论建模
在端到端传输控制中，浅缓冲瓶颈链路（BDP $\approx 25$ pkts，缓冲区上限 30 pkts）具有典型的非线性硬截断特性：
$$q(t+1) = \min\left( Q_{\max}, [q(t) + \lambda(t) - \mu(t)]^+ \right)$$
$$d_{\text{loss}}(t) = [q(t) + \lambda(t) - \mu(t) - Q_{\max}]^+$$
其中 $q(t)$ 为队列深度，$\lambda(t)$ 为流入速率，$\mu(t)$ 为瓶颈服务速率。

排队时延与丢包率之间的时延交叉相关函数（Cross-Correlation Function）定义为：
$$R_{\tau, d}(\tau) = \frac{\mathbb{E}[(T_{\text{queue}}(t) - \bar{T})(d_{\text{loss}}(t+\tau) - \bar{d})]}{\sigma_T \sigma_d}$$

当系统失去流控进入无节制突发状态（Unpaced / Congested）时，排队时延持续贴近缓冲区上限（$Q_{\max}$），队列达到临界点直接引发强制尾丢弃（Tail Drop），此时排队时延与丢包呈现高度正相关峰值（$R_{\tau, d} \ge 0.40$）。
相反，在 Crown Fusion Pacing 调控下，主动整形将流入速率严格锚定在服务能力邻域内，队列深度稳定在安全裕度区，丢包率被压制为 0，排队与丢包完全解耦（$R_{\tau, d} \le 0.15$）。

## 2. 实验验证与数据对比
执行 `zcode/scripts/xcorr0266_drop_delay.py` 仿真 $T=5,000$ 步离散队列演化：
1. **Paced Crown Fusion 机制**：
   - 平均排队时延：**0.024 ms**（最大时延 1.085 ms）
   - 累积丢包数：**0.0 包**
   - 互相关峰值系数：**0.0000**（门禁 $\le 0.15$，**PASS**）
2. **Unpaced 突发拥塞机制**：
   - 平均排队时延：**3.101 ms**（持续逼近 3.158 ms 缓冲上限）
   - 累积丢包数：**22,554.0 包**
   - 互相关峰值系数：**0.4182**（强相关耦合）

## 3. 结论
Crown Fusion 的流量整形机制切断了“排队膨胀 $\to$ 缓冲溢出 $\to$ 尾丢弃”的正反馈雪崩链条，实现了零丢包与超低排队时延的 Pareto 最优均衡。
