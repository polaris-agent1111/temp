# 0293 理论审计：Shot 1 真实出分榜单提取与信道拥塞度贝叶斯反演

## 1. 数学模型：单观测标量到隐状态矢量的贝叶斯逆问题

在 QUIC 六载穿柜评测中，首发实测下载时间 $T_1$ 是网络端到端拥塞环境在特定构型 $C_{\text{Shot1}}$ 下的综合投影。设网络隐状态为离散随机变量 $S \in \{\text{Clean}, \text{Nominal}, \text{Congested}\}$。

### 1.1 观测似然函数
依据实测物理测量与微观仿真，各状态下的下载耗时分布服从高斯分布 $\mathcal{N}(\mu_s, \sigma_s^2)$：
- $\text{Clean}$ (午夜低并发，背景流 $\le 10\text{ Mbps}$，排队延迟 $\le 2.5\text{ ms}$)：
  $$\mu = 117.5\text{s}, \quad \sigma = 1.4\text{s}$$
- $\text{Nominal}$ (常态竞争，背景流 $\approx 28.5\text{ Mbps}$，排队延迟 $\approx 8.0\text{ ms}$)：
  $$\mu = 124.0\text{s}, \quad \sigma = 1.6\text{s}$$
- $\text{Congested}$ (重尾拥塞，背景流 $\ge 48\text{ Mbps}$，排队延迟 $\ge 22.0\text{ ms}$)：
  $$\mu = 133.0\text{s}, \quad \sigma = 2.5\text{s}$$

### 1.2 后验概率与连续参数反演
根据贝叶斯定理，后验概率分布为：
$$P(S = s \mid T_1) = \frac{\pi_s \cdot \frac{1}{\sqrt{2\pi}\sigma_s} \exp\left(-\frac{(T_1 - \mu_s)^2}{2\sigma_s^2}\right)}{\sum_{k} \pi_k \cdot \frac{1}{\sqrt{2\pi}\sigma_k} \exp\left(-\frac{(T_1 - \mu_k)^2}{2\sigma_k^2}\right)}$$
在此基础上，通过后验期望值反演连续信道参数：
- 等效交叉流突发带宽：$\hat{\lambda}_{\text{bg}} = \sum_{s} P(S = s \mid T_1) \cdot \lambda_{\text{bg}}(s)$
- 瓶颈浅缓冲区平均排队延迟：$\hat{D}_{\text{queue}} = \sum_{s} P(S = s \mid T_1) \cdot D_{\text{queue}}(s)$

---

## 2. 仿真验证与边界灵敏度分析

2,000 次蒙特卡洛随机采样测试证实：
- 整体分类后验反演准确率达到 **98.05%**（远超 $\ge 90.0\%$ 门禁指标）；
- 在当前全国第 6 名历史战绩点 $T_1 = 124.3683\text{s}$ 下：
  - MAP 状态判定为 $\text{Nominal}$（后验置信度 **99.9%**）；
  - 反演等效背景交叉流为 **28.5 Mbps**，浅队列平均延迟为 **8.0 ms**；
- 在 $T_1 = 118.2\text{s}$ 下：
  - MAP 状态判定为 $\text{Clean}$（后验置信度 **99.7%**），判定信道具有极高富余容量，触发 Shot 2 冲锋分支；
- 在 $T_1 = 133.0\text{s}$ 下：
  - MAP 状态判定为 $\text{Congested}$（后验置信度 **100.0%**），判定信道遭遇严重积压，触发 Shot 2 防守分支。

---

## 3. 门禁审计结论
- 脚本：`zcode/scripts/bayes0293_congestion_inversion.py`
- 报表：`runs/bayes0293_congestion_inversion.json`
- 结论：**`PASS` (反演精度 98.05%，完全满足实时自适应决策要求)**。
