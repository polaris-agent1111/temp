# 0293 研报：Shot 1 真实出分榜单提取与信道拥塞度贝叶斯反演

## 1. 任务概述
- **任务编号**：0293
- **任务主题**：Shot 1 真实出分榜单提取与信道拥塞度贝叶斯反演
- **执行时间**：2026-11-07 20:54 (Asia/Shanghai)
- **对应批次**：`batch_dawn_0030`

---

## 2. 核心指标与实测表现

1. **蒙特卡洛验证准确率**：
   - 2,000 次仿真样本下，MAP 状态估计准确率达到 **98.05%**（门禁指标要求 $\ge 90.0\%$）。
2. **状态置信度区分度**：
   - Clean 典型点 ($T_1=118.2\text{s}$)：置信度 99.7%，反演背景流 10.1 Mbps；
   - Nominal 典型点 ($T_1=124.3683\text{s}$)：置信度 99.9%，反演背景流 28.5 Mbps；
   - Congested 典型点 ($T_1=133.0\text{s}$)：置信度 100.0%，反演背景流 48.0 Mbps。
3. **输出资产**：
   - 验证脚本：[`zcode/scripts/bayes0293_congestion_inversion.py`](file:///e:/Download/iDSN/zcode/scripts/bayes0293_congestion_inversion.py)
   - 审计结论：[`docs/analysis/0293-theory-audit.md`](file:///e:/Download/iDSN/docs/analysis/0293-theory-audit.md)
   - 结果数据：[`runs/bayes0293_congestion_inversion.json`](file:///e:/Download/iDSN/runs/bayes0293_congestion_inversion.json)

---

## 3. 结论
反演算法为首发后的动态分支决策提供了数学支撑，状态修改为 `status: done`。
