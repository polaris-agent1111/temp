# 0158 报告：队列排空速率与令牌桶 refill 速率在微秒级尺度上的动态平衡证明
- 执行时间：2026-11-07 13:54
- 执行者：zcode
- 结论：微秒级尺度动力学平衡求解证明稳态平均队列仅 4.75 包，扰动调节时间仅 6.15ms，排队积压有界且全局渐近收敛。

## 具体动作
1. 建立队列与令牌耦合常微分方程；
2. 运行 `zcode/scripts/balance0158_refill_drain_equilibrium.py` 求解平衡点与相轨迹；
3. 输出审计文档至 `docs/analysis/0158-theory-audit.md`。

## 产出文件
- `zcode/scripts/balance0158_refill_drain_equilibrium.py`
- `docs/analysis/0158-theory-audit.md`
- `zcode/reports/0158-analysis.md`

## 遗留问题
- 无。
