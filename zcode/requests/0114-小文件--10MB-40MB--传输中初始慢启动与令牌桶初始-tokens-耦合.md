status: done
priority: 2
assignee: zcode
created: 2026-11-07 13:24

# 0114 — 小文件 (10MB~40MB) 传输中初始慢启动与令牌桶初始 tokens 耦合时延积分最小化求解

## 背景
利用变分法求解小文件传输时初始 token 突发对慢启动爬坡积分时延的最优解。 本项任务服务于全国第一夺冠成果巩固、物理抗抖动建模与 11/08 闭环自适应逐发决策。

## 目标
产出具有深度学术价值与工程说服力的数理分析与审计交付件。

## 允许写的路径
- `zcode/reports/0114-analysis.md`
- `docs/analysis/0114-theory-audit.md`
- `zcode/scripts/` 目录下的辅助分析计算脚本

## 具体动作
1. 深入建模并编写 Python 验证脚本；
2. 形成分析成果写入 `docs/analysis/0114-theory-audit.md`；
3. 撰写标准交付报告写入 `zcode/reports/0114-analysis.md`，并将任务头部修改为 `status: done`。

## 禁止
- 不登录平台、不提交榜单、不修改真实提交凭据。
