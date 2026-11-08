status: done
priority: 2
assignee: zcode
created: 2026-11-07 14:04

# 0172 任务：针对 Catnet 历史提交时间序列的泊松点过程到达间隔建模

## 背景
分析竞争对手 Catnet 提交时间分布，利用非齐次泊松过程预测其零点后冲榜概率窗口。

## 目标
求解到达强度函数 lambda(t)，确定其进攻高峰。

## 产出路径
- `zcode/reports/0172-analysis.md`
- `docs/analysis/0172-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写到达时间序列点过程拟合脚本；
2. 形成分析成果写入 `docs/analysis/0172-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0172-analysis.md`，并将状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单、严禁修改实际提交凭据。
