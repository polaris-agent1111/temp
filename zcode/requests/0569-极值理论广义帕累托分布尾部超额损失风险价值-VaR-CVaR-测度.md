status: done
priority: 1
assignee: zcode
created: 2026-11-08 07:14

# 0569 极值理论广义帕累托分布尾部超额损失风险价值 VaR/CVaR 测度

## 任务背景
采用极值统计学 EVT 与 Pickands-Balkema-de Haan 定理，精确量化六载极端重尾并发下的队列峰值 VaR 和条件期望损失 CVaR。

## 目标指标
99.99% 极值风险排队深度 < 35.0 pkts，丢包 0，KS 检验 p > 0.05。

## 预期产出路径
- `zcode/reports/0569-analysis.md`
- `docs/analysis/0569-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0569-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0569-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
