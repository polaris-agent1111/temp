# Task 0263 理论审计报告：基于隐马尔可夫模型 (HMM) 的信道多状态自适应推断

## 1. 建模背景与问题描述
在竞赛浅缓冲（BDP $\approx 25$ pkts，瓶颈队列上限 30 pkts）网络中，网络状态呈现强烈的非线性马尔可夫特征：
1. **状态 1 ($S_1$: IDLE)**：瓶颈队列清空，往返时延 $RTT \approx 10.15\text{ ms}$，丢包率 $P_{\text{loss}} = 0$；
2. **状态 2 ($S_2$: STABLE)**：处于平衡工作点，往返时延 $RTT \approx 11.45\text{ ms}$，丢包率极低；
3. **状态 3 ($S_3$: CONGESTED)**：队列接近上限，往返时延 $RTT \approx 14.80\text{ ms}$，突发丢包率升高。

传统滑动窗口或简单阈值法受噪声抖动影响容易产生频繁震荡，而 HMM 在线前向滤波算法（Forward Filtering）结合了状态转移先验矩阵与连续似然发射函数，能够以极低计算复杂度实现平滑且灵敏的状态跟踪。

## 2. 数学形式与推导
设离散隐状态空间 $\mathcal{S} = \{S_1, S_2, S_3\}$，转移概率矩阵为 $A = [a_{ij}]$，观测变量序列为 $O_t = (rtt_t, loss_t)$。
前向变量递归式为：
$$\alpha_t(j) = P(O_1, \dots, O_t, S_t = j) = \left( \sum_{i=1}^3 \alpha_{t-1}(i) a_{ij} \right) b_j(O_t)$$
其中发射概率密度：
$$b_j(O_t) = \mathcal{N}(rtt_t; \mu_j, \sigma_j^2) \cdot P(loss_t \mid S_t = j)$$

时刻 $t$ 的后验概率分布通过归一化求得：
$$\gamma_t(j) = \frac{\alpha_t(j)}{\sum_{k=1}^3 \alpha_t(k)}, \quad \hat{S}_t = \arg\max_{j \in \{1,2,3\}} \gamma_t(j)$$

## 3. 实验验证与门禁结果
通过 `zcode/scripts/hmm0263_channel_state_infer.py` 仿真 $T=5,000$ 步动态马尔可夫信道演化过程，门禁要求综合推断准确率 $\ge 92.0\%$。

实测输出指标：
- **总体推断准确率 (Overall Accuracy)**: **92.94%** (门禁 $\ge 92.0\%$, **PASS**)
- **拥塞状态精确率 (Precision - CONGESTED)**: **97.41%** (误报率仅 2.59%)
- **拥塞状态召回率 (Recall - CONGESTED)**: **93.97%**
- **拥塞发生检测平均时延 (Mean Detection Latency)**: **0.15 步** (即在 1 个观测周期内即可迅速锁定拥塞并触发降速流控)

混淆矩阵统计 (样本数 $N=5,000$)：
| 真实状态 \ 预测状态 | IDLE | STABLE | CONGESTED | 召回率 |
| :--- | :---: | :---: | :---: | :---: |
| **IDLE** | 1380 | 104 | 0 | 92.99% |
| **STABLE** | 143 | 2099 | 31 | 92.34% |
| **CONGESTED** | 4 | 71 | 1168 | 93.97% |

## 4. 结论与工程部署价值
1. HMM 模型几乎零误判 IDLE 为 CONGESTED（仅 4 例，占 0.3%），确保在信道畅通时不会产生不必要的过度回退；
2. 拥塞识别极度精准（精确率 97.41%），能够作为动态调节 Pacer 限速参数的高置信度感知触发源；
3. 计算复杂度为 $\mathcal{O}(|\mathcal{S}|^2) = 9$ 次浮点乘法，微秒级执行，不增加传输客户端 CPU 负担。
