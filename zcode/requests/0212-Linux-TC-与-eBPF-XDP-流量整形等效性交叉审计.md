status: done
priority: 2
assignee: zcode
created: 2026-11-07 14:37

# 0212 任务：Linux TC 与 eBPF XDP 流量整形等效性交叉审计

## 任务背景
比对用户态 pacing 与内核态 qdisc (fq/tbf) 的调度精度差异，评估用户态调度的开销与抖动。

## 目标
证明用户态微秒级 pacing 精度误差小于 0.8%。

## 交付物与路径
- `zcode/reports/0212-analysis.md`
- `docs/analysis/0212-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写内核态与用户态流量整形精度交叉比对脚本
2. 形成分析成果写入 `docs/analysis/0212-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0212-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
