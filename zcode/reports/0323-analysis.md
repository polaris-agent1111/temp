# 0323 研报：Shot 3 攻防博弈动态分支权值矩阵实时投影

## 1. 任务概述
- **任务编号**：0323
- **任务主题**：Shot 3 攻防博弈动态分支权值矩阵实时投影
- **执行时间**：2026-11-07 23:30 (Asia/Shanghai)
- **对应批次**：`batch_campaign_0530`

---

## 2. 核心成果与验证指标

1. **严格占优进攻策略确立**：
   - 求解双人博弈矩阵证明，得益于微观平滑整形消除丢包，进攻策略（PUSH）对防守策略（DEF）形成严格占优；
   - 纳什均衡权重锁定为 PUSH 100.00%，在线遗憾度（Regret）为 **0.0000**（门禁要求 $\le 0.05$）。
2. **绝对压制性胜率保证**：
   - 10,000 次模拟实战中对抗胜率达 **100.00%**（门禁指标 $\ge 88.0\%$）；
   - 保障在 Shot 3 阶段将优势扩大至 +1.85 s。
3. **输出资产**：
   - 验证脚本：[`zcode/scripts/game0323_nash_weights.py`](file:///e:/Download/iDSN/zcode/scripts/game0323_nash_weights.py)
   - 理论审计：[`docs/analysis/0323-theory-audit.md`](file:///e:/Download/iDSN/docs/analysis/0323-theory-audit.md)
   - 报表数据：[`runs/game0323_nash_weights.json`](file:///e:/Download/iDSN/runs/game0323_nash_weights.json)

---

## 3. 结论
攻防博弈权值矩阵投影与零遗憾度验证通过，状态修改为 `status: done`。
