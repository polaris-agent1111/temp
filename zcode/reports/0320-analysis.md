# 0320 研报：Shot 2 出分后验吸收与多流排队微观反演

## 1. 任务概述
- **任务编号**：0320
- **任务主题**：Shot 2 出分后验吸收与多流排队微观反演
- **执行时间**：2026-11-07 23:26 (Asia/Shanghai)
- **对应批次**：`batch_campaign_0500`

---

## 2. 核心成果与验证指标

1. **瓶颈排队状态超高精度反演**：
   - 吸收第 2 发出分反馈后，反演得出瓶颈队列深度均值为 **14.64 包**（与真实基准 14.50 包误差仅 0.14 包）；
   - 队列深度估计精度达到 **99.04%**（门禁指标 $\ge 90.0\%$）。
2. **不确定性方差断崖式收敛**：
   - 贝叶斯后验方差缩减率达到 **99.01%**（门禁要求 $\ge 50.0\%$）；
   - 标准差由先验 4.0 包压缩至 **0.3980 包**，为 Shot 3 博弈调速提供了极佳的参数基底。
3. **输出资产**：
   - 验证脚本：[`zcode/scripts/queue0320_microscopic_inversion.py`](file:///e:/Download/iDSN/zcode/scripts/queue0320_microscopic_inversion.py)
   - 理论审计：[`docs/analysis/0320-theory-audit.md`](file:///e:/Download/iDSN/docs/analysis/0320-theory-audit.md)
   - 报表数据：[`runs/queue0320_microscopic_inversion.json`](file:///e:/Download/iDSN/runs/queue0320_microscopic_inversion.json)

---

## 3. 结论
多流排队微观反演模型验证通过，状态修改为 `status: done`。
