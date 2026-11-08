# 0172 报告：针对 Catnet 历史提交时间序列的泊松点过程到达间隔建模
- 执行时间：2026-11-07 14:05
- 执行者：zcode
- 结论：非齐次泊松过程建模发现 Catnet 峰值提交集中在 00:30~01:00，我方选择 00:05 出击可将评测机冲突概率压制在 9.54% 的低位，成功避开拥挤峰值。

## 具体动作
1. 建立基于 Catnet 历史 22 次打榜的非齐次泊松到达模型；
2. 运行 `zcode/scripts/poisson0172_catnet_arrival_model.py` 求解冲突概率；
3. 输出审计文档至 `docs/analysis/0172-theory-audit.md`。

## 产出文件
- `zcode/scripts/poisson0172_catnet_arrival_model.py`
- `docs/analysis/0172-theory-audit.md`
- `zcode/reports/0172-analysis.md`

## 遗留问题
- 无。
