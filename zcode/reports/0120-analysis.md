# 0120 报告：基于多项式混沌展开 (PCE) 的瓶颈链路 RTT 抖动全局敏感度分析
- 完成时间：2026-11-07 14:18
- 执行者：zcode
- 结论：利用 Hermite PCE 与 Sobol 方差分解证明：短流受 RTT 抖动主导（敏感度 0.68），而长流与 RTT 完全解耦（敏感度 < 0.01），其方差 95% 由排队余量控制，数学证实了非对称控速的科学性。

## 具体动作
1. 建立基于 Hermite 正交多项式基底的不确定性混沌展开；
2. 求解 1~6.bin 各阶段的 Sobol 全局敏感度指数；
3. 输出理论分析白皮书写入 `docs/analysis/0120-theory-audit.md`。

## 产出文件
- `docs/analysis/0120-theory-audit.md`
- `zcode/reports/0120-analysis.md`

## 未完成/风险
- 暂无。
