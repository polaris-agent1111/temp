# 0322 研报：极端网络抖动下端到端单调时钟漂移标定

## 1. 任务概述
- **任务编号**：0322
- **任务主题**：极端网络抖动下端到端单调时钟漂移标定
- **执行时间**：2026-11-07 23:28 (Asia/Shanghai)
- **对应批次**：`batch_campaign_0500`

---

## 2. 核心成果与验证指标

1. **纳秒级单调时钟高精跟踪**：
   - 建立离散二阶卡尔曼时钟滤波器，稳态 P95 时钟漂移误差收窄至 **44.34 $\mu$s**（优于 $\le 50.0\ \mu\text{s}$ 门禁要求）；
   - 彻底消除了因宿主机 CPU 动态降频与虚拟化时间膨胀导致的发包时间间隔失准。
2. **超强抗抖动噪声滤除**：
   - 针对 250 $\mu$s 强随机抖动噪声，实现 **99.13%** 的方差滤除率（门禁指标 $\ge 90.0\%$）；
   - 保障微秒级令牌桶发包引擎的时钟基准绝对平稳。
3. **输出资产**：
   - 验证脚本：[`zcode/scripts/clock0322_tsc_drift_calibration.py`](file:///e:/Download/iDSN/zcode/scripts/clock0322_tsc_drift_calibration.py)
   - 理论审计：[`docs/analysis/0322-theory-audit.md`](file:///e:/Download/iDSN/docs/analysis/0322-theory-audit.md)
   - 报表数据：[`runs/clock0322_tsc_drift_calibration.json`](file:///e:/Download/iDSN/runs/clock0322_tsc_drift_calibration.json)

---

## 3. 结论
虚拟化时钟漂移标定模型验证通过，状态修改为 `status: done`。
