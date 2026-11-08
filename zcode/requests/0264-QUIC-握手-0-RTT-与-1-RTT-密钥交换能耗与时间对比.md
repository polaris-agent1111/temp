status: done
priority: 2
assignee: zcode
created: 2026-11-07 19:03

# 0264 任务：QUIC 握手 0-RTT 与 1-RTT 密钥交换能耗与时间对比

## 任务背景
比较两种握手模式在首发下载中的建连耗时与安全边界。

## 考核目标
量化 0-RTT 重放保护开销与首次连接延迟。

## 预期产出路径
- `zcode/reports/0264-analysis.md`
- `docs/analysis/0264-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成理论分析成果写入 `docs/analysis/0264-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0264-analysis.md`，将状态修改为 `status: done`。

## 严格红线
- 严禁向远程平台提交榜单，严禁修改实盘提交凭据。
