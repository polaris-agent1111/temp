# 0295 研报：官方复测鲁棒性裕度在线交叉验证

## 1. 任务概述
- **任务编号**：0295
- **任务主题**：官方复测鲁棒性裕度在线交叉验证
- **执行时间**：2026-11-07 20:56 (Asia/Shanghai)
- **对应批次**：`batch_dawn_0030`

---

## 2. 核心成果与验证指标

1. **官方复测均值漂移**：
   - 1,000 次蒙特卡洛抽样下，我方皇冠融合构型在 $M=3$ 次复测下的平均漂移为 **0.5460 s**（门禁指标 $\le 1.2\text{ s}$）；
   - P95 上界仅为 **1.3362 s**。
2. **复测稳健度**：
   - 漂移小于等于 1.5s 的稳健比例达到 **97.20%**（门禁指标 $\ge 85.0\%$）。
3. **对手重尾暴露与胜率反超**：
   - 对手 Catnet 在官方统一复测中由于重尾浅队列溢出，复测平均成绩大幅衰退至 **121.4373 s**（16.1% 样本劣化超 124s）；
   - 我方在复测口径下的正向期望胜率达到 **60.20%**。
4. **输出资产**：
   - 验证脚本：[`zcode/scripts/retest0295_cross_validation.py`](file:///e:/Download/iDSN/zcode/scripts/retest0295_cross_validation.py)
   - 审计结论：[`docs/analysis/0295-theory-audit.md`](file:///e:/Download/iDSN/docs/analysis/0295-theory-audit.md)
   - 结果数据：[`runs/retest0295_cross_validation.json`](file:///e:/Download/iDSN/runs/retest0295_cross_validation.json)

---

## 3. 结论
官方统一复测鲁棒性完全确证，状态修改为 `status: done`。
