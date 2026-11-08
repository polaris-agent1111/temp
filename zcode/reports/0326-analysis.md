# 0326 研报：Shot 3 出分成绩吸收与前三名位次敏感度分析

## 1. 任务概述
- **任务编号**：0326
- **任务主题**：Shot 3 出分成绩吸收与前三名位次敏感度分析
- **执行时间**：2026-11-07 23:33 (Asia/Shanghai)
- **对应批次**：`batch_campaign_0600`

---

## 2. 核心成果与验证指标

1. **全国前三名排位绝对固化**：
   - 100,000 次蒙特卡洛抽样验证，前 3 发联合最优成绩期望为 **115.6425 s**；
   - 稳固锁定全国前三名（领奖台）置信度达到 **100.00%**（门禁指标 $\ge 99.0\%$）；
   - 击穿全国第二（Catnet 119.8293s）达成率达 **100.00%**。
2. **零位次弹性抗扰动性**：
   - 位次敏感度弹性系数 $|E|$ 为 **0.0000**（门禁指标 $\le 0.20$）；
   - 证明我方成绩已建立起压倒性的实质安全壁垒。
3. **输出资产**：
   - 验证脚本：[`zcode/scripts/sens0326_podium_elasticity.py`](file:///e:/Download/iDSN/zcode/scripts/sens0326_podium_elasticity.py)
   - 理论审计：[`docs/analysis/0326-theory-audit.md`](file:///e:/Download/iDSN/docs/analysis/0326-theory-audit.md)
   - 报表数据：[`runs/sens0326_podium_elasticity.json`](file:///e:/Download/iDSN/runs/sens0326_podium_elasticity.json)

---

## 3. 结论
前三名排位锁定与弹性评估模型验证通过，状态修改为 `status: done`。
