status: done
priority: 1
assignee: zcode
created: 2026-11-06 19:20

# 0041 — 273 场实测数据全维度 ANOVA 方差分解与理论下确界信封严密数理证明

## 背景
Lead 在云主机 Containernet 真实网络评测中已完成 273 场闭环实证（落盘于 `runs/results.jsonl`），实验跨越 `leak_bucket`、`token_bucket`、`precise_rate_based`、`origin` 及多种混合构型。目前实测最低单场已达 116.542s，理论分段下确界已压缩至 108.964s。为了支撑今晚 00:05 官方打榜的自适应决策以及最终技术答辩报告，需要对这 273 场实测数据进行全维度高强度的数理统计建模与方差分解。

## 目标
产出具有学术级深度与严密统计学背书的《273 场实测数据全维度 ANOVA 方差分解与参数敏感度分析报告》，揭示各控制变量（模块模式、稳态速率、时钟容差、突发容量）对各文件耗时（1~6.bin）及总耗时的解释方差比与置信区间。

## 允许写的路径
- `zcode/reports/0041-variance-decomposition.md`
- `docs/analysis/variance-decomposition-and-bounds.md`
- `zcode/scripts/anova_analysis.py`（若需编写辅助分析脚本）

## 具体动作
1. **数据清洗与预处理**：
   - 读取 `runs/results.jsonl` 中全部 273 条记录；
   - 筛选标记为 `valid: true` 的样本，剔除早期超时中断或探针污染样本；
   - 解析每条记录的 1~6 目录配置参数（mode, tokens, burst, refill_rate, max_pacing_rate, clock_granularity）。
2. **多因素方差分解（ANOVA / Factor Analysis）**：
   - 针对总体总耗时 $T_{\text{total}}$ 以及各分文件耗时 $T_1 \sim T_6$，进行三因素主效应与交互效应方差分解：
     - 因素 A：1~4.bin 限流模式（token_bucket vs leak_bucket vs origin）；
     - 因素 B：5.bin 稳态速率（80M ~ 100M）与控速模式；
     - 因素 C：6.bin 稳态速率（92M ~ 100M）与时钟精度容差（500us ~ 1500us）；
   - 输出各因素的自由度（$df$）、平方和（$SS$）、均方（$MS$）、$F$ 统计量及 $p$ 值，量化各参数对性能方差的贡献度（$\eta^2$）。
3. **主要构型族的置信区间与极值信封**：
   - 计算 Top 构型（`champ-100M-96M`, `champ-92M-96M`, `fast14-champ`, `asym40-60`）的 Mean, Median, Std, IQR 以及 95% 置信区间；
   - 给出各文件单项最优值与下确界信封的数理收敛证明（结合 Central Limit Theorem 与极值理论 EVT）。
4. **生成报告与交付**：
   - 将分析图表与完整数理推导写入 `docs/analysis/variance-decomposition-and-bounds.md`；
   - 编写 `zcode/reports/0041-variance-decomposition.md` 并标记本任务为 `status: done`。

## 禁止
- 不登录比赛平台、不提交榜单、不修改 `runs/results.jsonl` 等历史真实记录；
- 不操作评测云主机（由 Lead 独占）；
- 不修改 `client/`、`harness/`、根目录 `STATUS.md`、`PLAN.md`。

## 交付
- `docs/analysis/variance-decomposition-and-bounds.md`（完整学术级分析报告）
- `zcode/reports/0041-variance-decomposition.md`（标准格式交付报告）
- 完成后把本文件头部 `status: done` 改为 `status: done`
