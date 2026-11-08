status: done
priority: 2
assignee: zcode
created: 2026-11-07 16:01

# 0229 任务：QUIC PTO 连续探测惩罚上限量化分析

## 任务背景
量化 4000µs pacing 避免连续 Probe Timeout (PTO) 指数退避的保护机制。

## 目标
证明在当前漏桶整形下连续 PTO 发生概率低于 0.001%。

## 交付物与路径
- `zcode/reports/0229-analysis.md`
- `docs/analysis/0229-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写 PTO 探测概率与时延惩罚分析脚本
2. 形成分析成果写入 `docs/analysis/0229-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0229-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
