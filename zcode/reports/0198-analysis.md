# 0198 任务分析报告：QUIC 流量整形网络层与传输层开销 (Header Overhead) 微观精算

## 任务执行信息
- **任务编号**: 0198
- **执行人**: zcode
- **完成时间**: 2026-11-07 14:25
- **关联脚本**: `zcode/scripts/overhead0198_quic_header_ratio.py`
- **关联理论审计**: `docs/analysis/0198-theory-audit.md`

## 核心结果
1. 报文开销分解：IPv4(20B) + UDP(8B) + QUIC Short Header & Auth Tag(27B) + Stream Frame(5B) = 60 字节。
2. 载荷效率：1200 字节 MTU 下应用层净载荷为 1140 字节，净载荷率高达 95.00%。
3. 物理线速换算：Rate 36 对应 86.40 Mbps，Rate 37 对应 88.80 Mbps，Rate 41 对应 98.40 Mbps。
4. 状态更新：本任务圆满完成。
