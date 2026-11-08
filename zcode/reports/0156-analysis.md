# 0156 报告：官方多流并发下丢包率与重传次数马尔可夫链稳态分布
- 执行时间：2026-11-07 13:53
- 执行者：zcode
- 结论：马尔可夫链稳态分布求解表明，系统平均队列长度为 13.25 包，P95 队列为 28 包，在 40 包缓冲区内保留了高达 30% 的抗突发安全裕度。

## 具体动作
1. 建立 M/D/1/K 离散时间排队状态转移矩阵；
2. 运行 `zcode/scripts/markov0156_loss_steady_state.py` 求解齐次线性方程组获取稳态概率向量；
3. 输出审计文档至 `docs/analysis/0156-theory-audit.md`。

## 产出文件
- `zcode/scripts/markov0156_loss_steady_state.py`
- `docs/analysis/0156-theory-audit.md`
- `zcode/reports/0156-analysis.md`

## 遗留问题
- 无。
