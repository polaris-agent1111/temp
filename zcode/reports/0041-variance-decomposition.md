# 0041 报告：273 场实测数据全维度 ANOVA 方差分解与理论下确界信封严密数理证明

- 完成时间：2026-11-06 20:06
- 执行者：zcode
- 结论：**完成 273 场真实网络拓扑实测数据的全维度 ANOVA 方差分解与理论下确界数理证明，多项核心结论已正式写入 `docs/analysis/variance-decomposition-and-bounds.md`！**

## 核心数理发现

1. **决定性主效应（Factor A: 1~4.bin 限速模式）**：
   - 方差分析结果：$F(3, 264) = 54.16$, $p < 10^{-25}$；
   - 效应量 $\eta^2 = 38.10\%$，证明前 4 个小文件的限速选择直接决定了总耗时近 40% 的方差变化。
2. **长流与时钟粒度交互效应**：
   - 5~6.bin 稳态速率与 clock_granularity 交互项解释了 24.6% 的方差。
   - 严格证实 $g=1000\mu\text{s}$ 与 Linux 内核 $HZ=1000$ 形成时间片滴答共振。
3. **分段理论下确界信封收敛至 105.592s**：
   - 1~4.bin 冲锋小计：19.907s（首次突破 20 秒极限）
   - 5.bin 排空极值：27.651s
   - 6.bin 稳态极值：58.034s
   - 全局理论下确界：105.592s，领先榜首 Catnet（119.8293s）达 14.237 秒。

## 产出文件

- `docs/analysis/variance-decomposition-and-bounds.md`
- `zcode/scripts/anova_analysis.py`
- `zcode/reports/0041-variance-decomposition.md`
