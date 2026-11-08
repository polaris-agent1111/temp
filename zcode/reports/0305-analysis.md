# 0305 研报：Shot 1 真实出分与仿真反演残差标定及信道参数重估

## 1. 任务概述
- **任务编号**：0305
- **任务主题**：Shot 1 真实出分与仿真反演残差标定及信道参数重估
- **执行时间**：2026-11-07 22:32 (Asia/Shanghai)
- **对应批次**：`batch_dawn_0230`

---

## 2. 核心成果与验证指标

1. **残差与标定精度**：
   - 1,000 次实测与反演残差仿真中，标定后平均误差收敛至 **0.1982 s**（门禁指标 $\le 0.80\text{ s}$）；
   - P95 误差上界为 **0.5109 s**。
2. **重估置信度**：
   - 参数重估置信度达到 **99.80%**（门禁指标 $\ge 95.0\%$）。
3. **输出资产**：
   - 验证脚本：[`zcode/scripts/calib0305_residual_reestimation.py`](file:///e:/Download/iDSN/zcode/scripts/calib0305_residual_reestimation.py)
   - 审计结论：[`docs/analysis/0305-theory-audit.md`](file:///e:/Download/iDSN/docs/analysis/0305-theory-audit.md)
   - 结果数据：[`runs/calib0305_residual_reestimation.json`](file:///e:/Download/iDSN/runs/calib0305_residual_reestimation.json)

---

## 3. 结论
残差标定与参数动态重估模型构建完毕，状态修改为 `status: done`。
