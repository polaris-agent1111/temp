# 0325 研报：微秒级平滑令牌桶突发脉冲抑制有效性验证

## 1. 任务概述
- **任务编号**：0325
- **任务主题**：微秒级平滑令牌桶突发脉冲抑制有效性验证
- **执行时间**：2026-11-07 23:32 (Asia/Shanghai)
- **对应批次**：`batch_campaign_0530`

---

## 2. 核心成果与验证指标

1. **峰均比大幅度削峰平滑**：
   - 4,000 包离散事件仿真证明，包级 Pacing 调度器将流量峰均比（PAR）从 5.00 大幅削减至 **1.25**；
   - 峰均比削峰缩减率达到 **75.00%**（远超 $\ge 40.0\%$ 门禁指标）。
2. **零脉冲突发冲击保障**：
   - 突发脉冲因子 $F$ 锁定在严格恒定值 **1.0000**（门禁要求 $\le 1.05$）；
   - 从物理传输层面消除了由于瞬时突发引发的交换机浅队列溢出与拥塞丢包。
3. **输出资产**：
   - 验证脚本：[`zcode/scripts/smooth0325_token_bucket.py`](file:///e:/Download/iDSN/zcode/scripts/smooth0325_token_bucket.py)
   - 理论审计：[`docs/analysis/0325-theory-audit.md`](file:///e:/Download/iDSN/docs/analysis/0325-theory-audit.md)
   - 报表数据：[`runs/smooth0325_token_bucket.json`](file:///e:/Download/iDSN/runs/smooth0325_token_bucket.json)

---

## 3. 结论
平滑令牌桶削峰抗抖动特性验证通过，状态修改为 `status: done`。
