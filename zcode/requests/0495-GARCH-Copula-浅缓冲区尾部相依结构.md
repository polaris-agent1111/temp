status: done
priority: 1
assignee: zcode
created: 2026-11-08 05:26

# 0495 GARCH-Copula 浅缓冲区尾部相依结构

## 任务背景
结合 GARCH 异方差波动与 Clayton-Gumbel Copula，建模网络突发微抖动与排队突发的极值尾部相依性。

## 目标指标
Kendall秩相关误差 < 0.02，尾部相依参数辨识准确率 >= 98.0%。

## 预期产出路径
- `zcode/reports/0495-analysis.md`
- `docs/analysis/0495-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0495-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0495-analysis.md`，将状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改实验提交凭证。
