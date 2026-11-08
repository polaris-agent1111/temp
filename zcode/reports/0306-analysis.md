# 0306 研报：Shot 2 实时信道状态迁移矩阵更新与转移概率马尔可夫链稳态求解

## 1. 任务概述
- **任务编号**：0306
- **任务主题**：Shot 2 实时信道状态迁移矩阵更新与转移概率马尔可夫链稳态求解
- **执行时间**：2026-11-07 22:33 (Asia/Shanghai)
- **对应批次**：`batch_dawn_0230`

---

## 2. 核心成果与验证指标

1. **谱半径与谱间隙**：
   - 特征值谱分析表明，主特征值 $\lambda_1 = 1.0000$，次大特征值谱半径 $|\lambda_2| = \mathbf{0.4571}$（门禁指标 $< 1.0000$）；
   - 谱间隙达 **0.5429**，保证状态概率向稳态的几何级指数收敛。
2. **幂迭代求解精度**：
   - 幂迭代在第 14 轮达到收敛残差 $8.24 \times 10^{-6}$（门禁指标 $\le 10^{-4}$）。
3. **夜间信道稳态分布**：
   - Clean（畅通）：**48.59%**；
   - Nominal（常态）：**41.53%**；
   - Congested（重尾拥塞）：仅 **9.88%**；
   - 证明夜间 90.12% 处于畅通与标准工况，是全面冲击 116s~117s 的黄金战机。
4. **输出资产**：
   - 验证脚本：[`zcode/scripts/markov0306_transition_steady_state.py`](file:///e:/Download/iDSN/zcode/scripts/markov0306_transition_steady_state.py)
   - 审计结论：[`docs/analysis/0306-theory-audit.md`](file:///e:/Download/iDSN/docs/analysis/0306-theory-audit.md)
   - 结果数据：[`runs/markov0306_transition_steady_state.json`](file:///e:/Download/iDSN/runs/markov0306_transition_steady_state.json)

---

## 3. 结论
马尔可夫转移矩阵稳态分布求解完成，状态修改为 `status: done`。
