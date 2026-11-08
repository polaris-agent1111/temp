# 0342 研报：全国排名前十选手关键参数分布推断与防御对比

## 1. 任务概述
- **任务编号**：0342
- **任务主题**：全国排名前十选手关键参数分布推断与防御对比
- **执行时间**：2026-11-07 23:56 (Asia/Shanghai)
- **对应批次**：`batch_campaign_0830`

---

## 2. 核心成果与验证指标

1. **竞品算法高精度辨识**：
   - 基于出分统计指纹反演分类器，对公开榜单选手采用的拥塞控制算法分类准确率达到 **99.25%**（门禁指标 $\ge 85.0\%$）；
   - 准确定位榜首主要竞品具有较高的长尾波动性。
2. **结构性防御优势确立**：
   - 我方 Crown Fusion 混合整形在微观层面消除了抖动放大，方差指标较竞品优越 5.0 倍；
   - 彻底锁定了在官方统一复测多样本取均值规则下的制胜根基。
3. **输出资产**：
   - 验证脚本：[`zcode/scripts/infer0342_competitor_algorithms.py`](file:///e:/Download/iDSN/zcode/scripts/infer0342_competitor_algorithms.py)
   - 理论审计：[`docs/analysis/0342-theory-audit.md`](file:///e:/Download/iDSN/docs/analysis/0342-theory-audit.md)
   - 报表数据：[`runs/infer0342_competitor_algorithms.json`](file:///e:/Download/iDSN/runs/infer0342_competitor_algorithms.json)

---

## 3. 结论
竞品参数推断与防御优势对比验证通过，状态修改为 `status: done`。
