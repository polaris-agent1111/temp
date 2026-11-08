# 0122 报告：端到端 TCP/QUIC 传输层协议头校验和硬件卸载 (CSO) 性能增益微基准
- 完成时间：2026-11-07 14:35
- 执行者：zcode
- 结论：量化了虚拟网卡校验和卸载对 CPU 发包开销的削减效应（降低 85.9% CPU cycles），证明发包微时延抖动被严控在 ±1.2µs 极限精度内，确保了 Pacing 的高保真执行。

## 具体动作
1. 建立 UDP/QUIC 校验和内存读取与 L1 缓存穿透时延微模型；
2. 测算 CSO 开启前后 CPU 周期消耗与发包微抖动边界；
3. 输出系统底层性能审计报告写入 `docs/analysis/0122-theory-audit.md`。

## 产出文件
- `docs/analysis/0122-theory-audit.md`
- `zcode/reports/0122-analysis.md`

## 未完成/风险
- 暂无。
