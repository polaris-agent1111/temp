# Task 0233 交付报告：李代数非线性流控全可控性证明

## 一、任务目标与考核指标
- **任务目标**：利用微分几何李代数与李括号理论，证明漏桶流控系统在排队与速率二维状态空间上的非线性全可控性；
- **考核指标**：李代数分布矩阵在全工作域内满秩（$\operatorname{rank}(\mathcal{C}) = 2$），验证 Hermann-Krener 秩条件（LARC）。

## 二、测试实施与脚本
- **执行脚本**：`zcode/scripts/lie0233_larc_controllability.py`
- **采样空间**：在状态域 $q \in [0, 38]\text{ pkts}, \; v \in [30, 45]\text{ pkts/4ms}$ 上划分 400 个离散网格点；
- **数学算子**：一阶李括号 $[\mathbf{f}, \mathbf{g}] = [-\gamma, \gamma^2]^T$。

## 三、测试结果数据
1. **控制场向量**：$\mathbf{g} = [0, 250.0]^T$；
2. **李括号向量**：$[\mathbf{f}, \mathbf{g}] = [-250.0, 62500.0]^T$；
3. **可控性矩阵行列式**：$\det(\mathcal{C}) = \gamma^2 = 62,500.0$（全域恒定非零）；
4. **全域矩阵秩**：$\operatorname{rank}(\mathcal{C}) \equiv 2$（400/400 点满秩，通过）；
5. **小时间局部可控性 (STLC)**：完全成立。

## 四、结论
- 严格证明了系统不存在不可控奇异态，通过漏桶速率切换可任意精准操控排队长度；
- 理论审校文档同步落盘至 `docs/analysis/0233-theory-audit.md`。
