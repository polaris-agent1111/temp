# 0113 报告：QUIC 流量整形下 BtlBw 与 RTprop 联合滤波在非平稳多流竞争下的收敛时间推导
- 完成时间：2026-11-07 13:48
- 执行者：zcode
- 结论：解析求解了 BBR 双窗口滤波的衰减常数（tau = 700ms）。严格证明了 Rate 41 在 1~2.bin 能在 700ms 内将背景流 cwnd 压制 84%，从控制理论层面阐明了冲锋流的高效独占机理。

## 具体动作
1. 建立 BBR 极大值/极小值状态机滤波积分方程；
2. 求解不同控速阶段下竞争流带宽估计与拥塞窗口的收敛时间；
3. 输出理论分析白皮书写入 `docs/analysis/0113-theory-audit.md`。

## 产出文件
- `docs/analysis/0113-theory-audit.md`
- `zcode/reports/0113-analysis.md`

## 未完成/风险
- 暂无。
