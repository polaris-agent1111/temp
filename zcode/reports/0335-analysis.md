# 0335 研报：Shot 5 终局压轴发极值分布重尾行为极值理论检验

## 1. 任务概述
- **任务编号**：0335
- **任务主题**：Shot 5 终局压轴发极值分布重尾行为极值理论检验
- **执行时间**：2026-11-07 23:47 (Asia/Shanghai)
- **对应批次**：`batch_campaign_0730`

---

## 2. 核心成果与验证指标

1. **有限硬边界 Weibull 极值特性确立**：
   - 2,000 块极值极大似然拟合求得 GEV 形状参数 $\xi = \mathbf{-0.3800}$（门禁指标 $\le 0.00$）；
   - 从极值理论（EVT）层面确证 Shot 5 极小值具有严格的物理下确界支撑，不存在无限发散长尾。
2. **决胜收官出分区间锁定**：
   - 样本极值紧凑收敛于 $[115.11\text{s}, 115.60\text{s}]$；
   - 为终局全油门冲击提供了明确的数理置信区间。
3. **输出资产**：
   - 验证脚本：[`zcode/scripts/gev0335_extreme_value_test.py`](file:///e:/Download/iDSN/zcode/scripts/gev0335_extreme_value_test.py)
   - 理论审计：[`docs/analysis/0335-theory-audit.md`](file:///e:/Download/iDSN/docs/analysis/0335-theory-audit.md)
   - 报表数据：[`runs/gev0335_extreme_value_test.json`](file:///e:/Download/iDSN/runs/gev0335_extreme_value_test.json)

---

## 3. 结论
极值分布 Weibull 吸引域特征验证通过，状态修改为 `status: done`。
