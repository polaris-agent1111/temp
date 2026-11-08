status: done
priority: 1
assignee: zcode
created: 2026-11-08 00:09

# 0350 任务：Shot-2-出分后验高斯过程主动学习后验采样与 Shot-3 点位重构

## 任务背景
吸收 Shot 2 真机出分，利用 GPR 进行期望提升 (EI) 采样优化 Shot 3 构型。

## 目标
代理模型后验 MSE <= 0.01，局部最优发现概率 >= 95.0%。

## 预期产出路径
- `zcode/reports/0350-analysis.md`
- `docs/analysis/0350-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0350-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0350-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
