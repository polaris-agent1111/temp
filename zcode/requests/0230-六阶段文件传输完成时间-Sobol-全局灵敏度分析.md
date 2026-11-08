status: done
priority: 2
assignee: zcode
created: 2026-11-07 16:03

# 0230 任务：六阶段文件传输完成时间 Sobol 全局灵敏度分析

## 任务背景
采用 Sobol 方差分解法，计算各阶段漏率对总下载时间的一阶与全阶灵敏度指数。

## 目标
数学证明 Bin 1~3 的灵敏度指数之和超过 85%。

## 交付物与路径
- `zcode/reports/0230-analysis.md`
- `docs/analysis/0230-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写 Sobol 灵敏度方差分解数值计算脚本
2. 形成分析成果写入 `docs/analysis/0230-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0230-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
