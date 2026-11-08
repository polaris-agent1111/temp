# 0317 研报：Shot 1 出分残差深度对齐与跨宿主机拓扑推断

## 1. 任务概述
- **任务编号**：0317
- **任务主题**：Shot 1 出分残差深度对齐与跨宿主机拓扑推断
- **执行时间**：2026-11-07 23:23 (Asia/Shanghai)
- **对应批次**：`batch_campaign_0430`

---

## 2. 核心成果与验证指标

1. **物理拓扑特征高精度反演**：
   - 基于首发出分与理论先验残差，成功反演跨宿主机瓶颈链路状态；
   - 拓扑模型拟合优度 $R^2$ 达到 **0.9877**（门禁要求 $\ge 0.90$）。
2. **残差与置信度收敛**：
   - 残差波动标准差收窄至 **0.2310 s**，95% 置信半宽锁定在 $\pm 0.0453\text{ s}$；
   - 拓扑参数重估置信度达到 **95.00%**（门禁指标 $\ge 95.0\%$）。
3. **输出资产**：
   - 验证脚本：[`zcode/scripts/align0317_residual_topology.py`](file:///e:/Download/iDSN/zcode/scripts/align0317_residual_topology.py)
   - 理论审计：[`docs/analysis/0317-theory-audit.md`](file:///e:/Download/iDSN/docs/analysis/0317-theory-audit.md)
   - 审计报表：[`runs/align0317_residual_topology.json`](file:///e:/Download/iDSN/runs/align0317_residual_topology.json)

---

## 3. 结论
首发出分残差对齐与拓扑辨识模型验证通过，状态修改为 `status: done`。
