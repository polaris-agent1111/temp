# 0167 理论审计：跨周期长时记忆对自适应打靶决策精度的增益量化

## 1. 香农信息论模型
设真实信道拥塞状态为离散随机变量 $\Theta \in \{\text{Clean}, \text{Normal}, \text{Congested}\}$，先验概率分布为 $p(\Theta) = [0.30, 0.50, 0.20]$。
首发 Shot 1 真实出分结果提供观测特征 $S_1$。
定义信道互信息增益（Mutual Information）：
$$I(\Theta; S_1) = H(\Theta) - H(\Theta | S_1)$$
其中 $H(\Theta) = -\sum p(\theta) \log_2 p(\theta)$，条件熵 $H(\Theta | S_1) = \sum_j P(s_j) H(\Theta | S_1 = s_j)$。

## 2. 增益测算与不确定性消除
运行 `zcode/scripts/memory0167_information_gain.py`：
- **先验信道信息熵**：$H(\Theta) = 1.4855\text{ bits}$；
- **后验条件信息熵**：$H(\Theta | S_1) = 0.8104\text{ bits}$；
- **自适应互信息增益**：$I(\Theta; S_1) = \mathbf{0.6751\text{ bits}}$；
- **信道不确定性压缩比**：**45.44%**。

## 3. 结论
闭环 1-by-1 打靶策略通过单发实时反馈直接消除近一半的信道不确定性，较盲目连发的开环策略实现了质的信息论收益跃升。
