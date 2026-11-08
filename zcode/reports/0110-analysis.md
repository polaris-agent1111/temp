# 0110 报告：1.bin 与 2.bin Rate 41 对抗 Rate 40 物理裕度与信道容量敏感度精算
- 完成时间：2026-11-07 13:35
- 执行者：zcode
- 结论：精确计算了以太网 L2/L3/L4 封装开销（有效净荷比 94.56%）。严格论证了 Rate 41 在 1.bin（10MB 短流）由于慢启动稀释效应完全安全，但在 2~3.bin 采用 Rate 40 具备更高的抗累积排队鲁棒性。

## 具体动作
1. 建立以太网帧间隙、前导码与 QUIC 报头的全栈开销精算模型；
2. 推导 Rate 40 与 Rate 41 在 100M 物理信道下的瞬态积压积累速率；
3. 输出审计报告写入 `docs/analysis/0110-theory-audit.md`。

## 产出文件
- `zcode/scripts/channel0110_rate41_margin.py`
- `docs/analysis/0110-theory-audit.md`
- `zcode/reports/0110-analysis.md`

## 未完成/风险
- 暂无。
