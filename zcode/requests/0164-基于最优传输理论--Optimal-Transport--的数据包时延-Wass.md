status: done
priority: 2
assignee: zcode
created: 2026-11-07 13:57

# 0164 任务：基于最优传输理论 (Optimal Transport) 的数据包时延 Wasserstein 距离计算

## 背景
使用 Wasserstein-1 距离量化我方输出流量分布与理想均匀平滑分布的几何流形距离。

## 目标
计算 W1 距离，证明我方方案比基准接近理想平滑度 68%。

## 产出路径
- `zcode/reports/0164-analysis.md`
- `docs/analysis/0164-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写最优传输 W1 求解脚本；
2. 形成分析成果写入 `docs/analysis/0164-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0164-analysis.md`，并将状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单、严禁修改实际提交凭据。
