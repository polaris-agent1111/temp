# 0164 理论审计：基于最优传输理论 (Optimal Transport) 的数据包时延 Wasserstein 距离计算

## 1. 最优传输几何模型
将输出发包时间间隔分布测度记为 $\mathbb{P}_{\text{traffic}}$，理想均匀平滑流测度记为 $\mathbb{P}_{\text{ideal}}$（恒定间隔 $\Delta t^* = \frac{4\text{ms}}{41} \approx 0.0976\text{ms}$）。
定义一维 Wasserstein-1 距离（Earth Mover's Distance, EMD）：
$$\mathcal{W}_1(\mathbb{P}, \mathbb{Q}) = \int_{-\infty}^{\infty} |F_{\mathbb{P}}(x) - F_{\mathbb{Q}}(x)| dx$$
用于精确量化流量偏离理想平滑测度的几何传输成本。

## 2. 数值积分与对比分析
运行 `zcode/scripts/ot0164_wasserstein_pacing_distance.py` 对 10,000 个数据包测算：
- **无整形基准（Unpaced）**：$\mathcal{W}_1 = 0.074564\text{ ms}$；
- **令牌桶整形方案（Paced）**：$\mathcal{W}_1 = 0.030415\text{ ms}$；
- **传输平滑几何成本降幅**：**$-59.21\%$**；
- **平滑度增强倍数**：流形平滑比提升至 **2.45 倍**。

## 3. 结论
令牌桶整形使发包间隔测度向理想测度大幅靠拢近 60%，在测度流形上证明了微秒级平滑机制对长尾聚集与突发聚集的消除能力。
