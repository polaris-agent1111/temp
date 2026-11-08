status: done
priority: 1
assignee: zcode
created: 2026-11-08 07:10

# 0566 拓扑数据分析持续同调持续图 Betti 数网络拥塞预警特征核

## 任务背景
使用 TDA 持续同调理论构建 Vietoris-Rips 过滤复形，提取 Betti 数 beta_0 和 beta_1 拓扑不变量。

## 目标指标
瓶颈距离 < 0.05，拓扑特征稳定率 100.0%，丢包 0，峰值队列 < 36.0 pkts。

## 预期产出路径
- `zcode/reports/0566-analysis.md`
- `docs/analysis/0566-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0566-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0566-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
