status: done
priority: 2
assignee: zcode
created: 2026-11-07 14:24

# 0197 任务：极小极大后悔值准则 (Minimax Regret) 下的第 2 发策略优选

## 任务背景
量化第 1 发反馈后面对不同网络环境时各候选策略的后悔值（Regret Matrix），利用 Savage 准则选取最稳健候选。

## 目标
给出顺风、基准、逆风三态下的极小极大后悔值最优决策下界。

## 交付物与路径
- `zcode/reports/0197-analysis.md`
- `docs/analysis/0197-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写后悔矩阵推导与计算脚本
2. 形成分析成果写入 `docs/analysis/0197-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0197-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
