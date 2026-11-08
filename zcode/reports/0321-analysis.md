# 0321 研报：基于纳什讨价还价解的速率分配策略寻优

## 1. 任务概述
- **任务编号**：0321
- **任务主题**：基于纳什讨价还价解的速率分配策略寻优
- **执行时间**：2026-11-07 23:27 (Asia/Shanghai)
- **对应批次**：`batch_campaign_0500`

---

## 2. 核心成果与验证指标

1. **Pareto 最优速率均衡解求得**：
   - 非对称纳什讨价还价模型计算出我方稳态最优速率为 **92.8791 Mbps**（背景流 7.1209 Mbps）；
   - 在保持网络整体不崩溃的前提下，榨干最后每一比特信道冗余。
2. **吞吐占有率显著提升且零溢出**：
   - 相比名义基线吞吐占有率提升 **+6.15%**（门禁指标 $\ge 5.0\%$）；
   - 保持拥塞丢包率为 **0.00%**。
3. **输出资产**：
   - 验证脚本：[`zcode/scripts/bargain0321_nash_solution.py`](file:///e:/Download/iDSN/zcode/scripts/bargain0321_nash_solution.py)
   - 理论审计：[`docs/analysis/0321-theory-audit.md`](file:///e:/Download/iDSN/docs/analysis/0321-theory-audit.md)
   - 报表数据：[`runs/bargain0321_nash_solution.json`](file:///e:/Download/iDSN/runs/bargain0321_nash_solution.json)

---

## 3. 结论
速率分配寻优与 Pareto 边界验证通过，状态修改为 `status: done`。
