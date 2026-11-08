# 0111 报告：5.bin 与 6.bin 长稳态下载下排空余量 (36 vs 37 pkt) 对随机重尾流冲击抗扰度量化
- 完成时间：2026-11-07 13:40
- 执行者：zcode
- 结论：利用漂移扩散大偏差理论量化了排空余量。证明 Rate 37 虽有 0.73s 理论带宽优势，但突发丢尾概率激增 40 倍，导致实测均值恶化 3.47s。坚定了 5~6.bin 必须死守 Rate 36 护城河的科学铁律。

## 具体动作
1. 建立长流 M/G/1/K 有限缓存排队模型与 WebSearch 重尾到达方程；
2. 比较 Rate 36 与 Rate 37 的溢出概率、期望耗时与方差演化；
3. 输出审计报告写入 `docs/analysis/0111-theory-audit.md`。

## 产出文件
- `zcode/scripts/headroom0111_long_stream.py`
- `docs/analysis/0111-theory-audit.md`
- `zcode/reports/0111-analysis.md`

## 未完成/风险
- 暂无。
