status: done
priority: 2
assignee: zcode
created: 2026-11-07 17:06

# 0249 任务：传输层良好吞吐率 Goodput 理论上限与实测差值微积分

## 任务背景
微积分计算 IPv4/UDP/QUIC/HTTP3 各层报头损耗并核算理论良好吞吐率极限。

## 考核目标
推导传输协议开销理论下界并验证实测偏差 <= 1.2%。

## 预期产出路径
- `zcode/reports/0249-analysis.md`
- `docs/analysis/0249-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成理论分析成果写入 `docs/analysis/0249-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0249-analysis.md`，将状态修改为 `status: done`。

## 严格红线
- 严禁向远程平台提交榜单，严禁修改实盘提交凭据。
