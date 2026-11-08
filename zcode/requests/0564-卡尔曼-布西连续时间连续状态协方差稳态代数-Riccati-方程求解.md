status: done
priority: 1
assignee: zcode
created: 2026-11-08 07:08

# 0564 卡尔曼-布西连续时间连续状态协方差稳态代数 Riccati 方程求解

## 任务背景
建立高斯白噪声与重尾冲击驱动下的连续时间卡尔曼-布西滤波模型，精确求解稳态误差协方差。

## 目标指标
CARE 代数李卡提残差 < 1e-14，协方差矩阵正定 lambda_min > 0，峰值队列 < 36.0 pkts，丢包 0。

## 预期产出路径
- `zcode/reports/0564-analysis.md`
- `docs/analysis/0564-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0564-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0564-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
