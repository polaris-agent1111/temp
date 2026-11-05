status: done
priority: 2
assignee: zcode
created: 2026-11-05 15:15

# 0007 — 技术报告数据填充与图表

## 背景

`report/技术报告-初稿.md` 是你之前写的骨架（占位符 `{{...}}`）。现在已有 56 次有效本地评测数据，需要把真实数据填进去并生成图表，产出可提交/可答辩的报告版本。

## 数据来源（只读）

- `runs/results.jsonl`：每次评测的配置、6 个文件耗时、总时间、valid
- `report/实验结果-数据表.md`：Lead 自动生成的汇总表（可直接引用）
- `docs/extracted/*.md`：赛题与参数规范
- `docs/knowledge/flow-shaping-analysis.md`：你自己写的机制分析

## 目标产出

1. `report/技术报告-v1.md`：把骨架填成完整报告，必须包含：
   - 问题建模（决策变量/目标/约束）
   - 方法：黑箱参数搜索（单因子 → 随机/网格 → 精调）、**方差惩罚的稳健选择**、配置格式工程坑（CRLF 导致服务端解析失败、假成功 80.18s 的识别方法）
   - 结果表：Top 配置的均值/标准差/分文件耗时（引用数据表）
   - 辅助指标章节：稳定性（多次运行标准差）、鲁棒性、创新性、可解释性、可复现性——用真实数据支撑，没有数据的地方写「待补充」而不是编造
   - 结论与后续工作
2. `report/figures/`：至少 3 张图（matplotlib，中文标签；用英文文件名）
   - `fig1_config_compare.png`：Top 8 配置的总耗时箱线图或误差棒图（均值±标准差）
   - `fig2_per_file.png`：最佳配置 vs 基线 的分文件耗时对比柱状图
   - `fig3_rate_sweep.png`：漏桶 leak_rate 与总耗时的关系（含散点与均值线）
3. `zcode/reports/0007-report-data.md`：交付摘要（做了什么、图怎么看、哪些数字待补）

## 技术约束

- 用 Python3 + matplotlib（已安装）；中文字体若缺失，可用英文标签并在图注说明，不要为装字体折腾。
- 所有数字必须能在 `runs/results.jsonl` 或 `report/实验结果-数据表.md` 里对上。
- 不得写入任何真实凭据（GUID/密码）。

## 禁止

- 不操作云主机、不跑评测、不改 `runs/results.jsonl`。
- 不覆盖 `report/技术报告-初稿.md`（保留原稿，新写 v1）。

## 交付

完成后把本文件头改成 `status: done`，并在 `zcode/reports/0007-report-data.md` 里列出所有产出路径。
