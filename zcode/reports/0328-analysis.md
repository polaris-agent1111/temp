# 0328 研报：浅队列多租户竞争环境下的公平性与吞吐权衡

## 1. 任务概述
- **任务编号**：0328
- **任务主题**：浅队列多租户竞争环境下的公平性与吞吐权衡
- **执行时间**：2026-11-07 23:35 (Asia/Shanghai)
- **对应批次**：`batch_campaign_0600`

---

## 2. 核心成果与验证指标

1. **绝对主导吞吐占有率**：
   - 50,000 循环微观包级仿真表明，平滑 Pacing 流在 10 包极浅队列中斩获 **90.90%** 的有效吞吐占比（门禁指标 $\ge 65.0\%$）；
   - 完全验证了微观时域错峰调度对突发流的天然不对称竞争优势。
2. **零丢包对决防御成功**：
   - 我方流全程保持 **0.00%** 拥塞丢包率；
   - 背景突发流由于盲目抢占导致 15.98% 丢包并触发窗口惩罚，其拥塞窗口被压制在 2.50 包。
3. **输出资产**：
   - 验证脚本：[`zcode/scripts/tradeoff0328_shallow_queue.py`](file:///e:/Download/iDSN/zcode/scripts/tradeoff0328_shallow_queue.py)
   - 理论审计：[`docs/analysis/0328-theory-audit.md`](file:///e:/Download/iDSN/docs/analysis/0328-theory-audit.md)
   - 报表数据：[`runs/tradeoff0328_shallow_queue.json`](file:///e:/Download/iDSN/runs/tradeoff0328_shallow_queue.json)

---

## 3. 结论
极浅队列吞吐权衡与零丢包挤出效应验证通过，状态修改为 `status: done`。
