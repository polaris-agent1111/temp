status: done
priority: 1
assignee: zcode
created: 2026-11-08 04:13

# 0440 — 微突发跨流时空自协方差矩阵的张量低秩Tucker分解

## 任务背景
在空间节点 (6) x 遥测通道 (4) x 滞后时间步 (20) 的 3 阶张量上执行高阶正交迭代 (HOOI) Tucker 分解。

## 目标
核心张量能量保持率 >= 95.0%，高阶张量重构误差 < 0.05。

## 预期产出路径
- `zcode/reports/0440-analysis.md`
- `docs/analysis/0440-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0440-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0440-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
