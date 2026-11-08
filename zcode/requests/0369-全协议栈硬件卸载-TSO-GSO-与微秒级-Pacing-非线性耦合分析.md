status: done
priority: 1
assignee: zcode
created: 2026-11-08 02:29

# 0369 — 全协议栈硬件卸载-TSO-GSO-与微秒级-Pacing-非线性耦合分析

## 任务背景
千兆网卡硬件卸载（TSO/GSO）会重聚合并打散应用层 Pacing 定时器。需构建微观非线性微分方程解，量化硬件聚合对 4ms 漏桶定时的影响。

## 目标
抖动滤波率 >= 99.0%，稳态时钟补偿误差 < 2.0 微秒。

## 预期产出路径
- `zcode/reports/0369-analysis.md`
- `docs/analysis/0369-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0369-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0369-analysis.md`，并将状态修改为 `status: done`。

## 合规
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
