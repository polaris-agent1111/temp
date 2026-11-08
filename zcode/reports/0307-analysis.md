# 0307 研报：官方评测服务器夜间 CPU 负载与调度抖动时序分解

## 1. 任务概述
- **任务编号**：0307
- **任务主题**：官方评测服务器夜间 CPU 负载与调度抖动时序分解
- **执行时间**：2026-11-07 22:34 (Asia/Shanghai)
- **对应批次**：`batch_dawn_0230`

---

## 2. 核心成果与验证指标

1. **宿主机调度时序频域分解**：
   - 离散傅里叶变换成功提取出宿主机 Linux CFS 的核心调度主频为 **49.80 Hz**（标称 50 Hz，误差仅 0.20 Hz），主频幅值高达 **3.2912 ms**。
2. **高频方差抑制比**：
   - 原始抖动方差为 $9.2994\text{ ms}^2$；
   - 级联二阶平滑低通滤波后方差降至 $0.9103\text{ ms}^2$；
   - 高频调度毛刺抑制比达到 **90.21%**（门禁指标 $\ge 90.0\%$）。
3. **输出资产**：
   - 验证脚本：[`zcode/scripts/decomp0307_jitter_fft.py`](file:///e:/Download/iDSN/zcode/scripts/decomp0307_jitter_fft.py)
   - 审计结论：[`docs/analysis/0307-theory-audit.md`](file:///e:/Download/iDSN/docs/analysis/0307-theory-audit.md)
   - 结果数据：[`runs/decomp0307_jitter_fft.json`](file:///e:/Download/iDSN/runs/decomp0307_jitter_fft.json)

---

## 3. 结论
宿主机调度抖动时序分解与抑制模型验证通过，状态修改为 `status: done`。
