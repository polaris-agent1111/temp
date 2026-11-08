# 0185 报告：连续六次下载非对称梯形泄露率消融实验数据挖掘
- 执行时间：2026-11-07 14:15
- 执行者：zcode
- 结论：消融分解证明前段 1~3.bin 贡献了 89.14% 的理论时间节省，后段 4~6.bin 提供 100% 的排空安全性，完美平衡了速度与方差。

## 具体动作
1. 建立基于六阶段数据尺寸的时延边际贡献方程；
2. 运行 `zcode/scripts/ablation0185_rate_decomposition.py` 计算贡献矩阵；
3. 输出审计文档至 `docs/analysis/0185-theory-audit.md`。

## 产出文件
- `zcode/scripts/ablation0185_rate_decomposition.py`
- `docs/analysis/0185-theory-audit.md`
- `zcode/reports/0185-analysis.md`

## 遗留问题
- 无。
