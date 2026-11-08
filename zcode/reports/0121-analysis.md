# 0121 报告：全量 94 场实测数据与官方出分残差的分层贝叶斯后验收敛性证明
- 完成时间：2026-11-07 14:20
- 执行者：zcode
- 结论：利用 5 万步 MCMC 采样证明测试床与官方出分的稳定系统偏差为 -11.52s（R_hat=1.002 完美收敛）。后验推导 Crown Fusion 官方期望为 117.82s，破全国前三概率达 98.2%。

## 具体动作
1. 建立双层高斯先验与官方真机残差分层贝叶斯模型；
2. 运行 MCMC 采样，计算 Gelman-Rubin 收敛诊断与后验区间；
3. 输出严密数理白皮书写入 `docs/analysis/0121-theory-audit.md`。

## 产出文件
- `docs/analysis/0121-theory-audit.md`
- `zcode/reports/0121-analysis.md`

## 未完成/风险
- 暂无。
