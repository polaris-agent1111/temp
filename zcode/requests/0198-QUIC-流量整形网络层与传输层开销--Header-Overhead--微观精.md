status: done
priority: 2
assignee: zcode
created: 2026-11-07 14:24

# 0198 任务：QUIC 流量整形网络层与传输层开销 (Header Overhead) 微观精算

## 任务背景
深入微观网络协议栈，精算 IPv4/UDP/QUIC 包头在 MTU 1200 字节下的真实带宽开销。

## 目标
量化有效载荷比率达 95.67%，验证 36~41 pkts/4ms 对应的实际物理吞吐。

## 交付物与路径
- `zcode/reports/0198-analysis.md`
- `docs/analysis/0198-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写网络报文开销与 Goodput 理论精算脚本
2. 形成分析成果写入 `docs/analysis/0198-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0198-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
