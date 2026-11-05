# 复核材料包（赛博coder · 六载穿柜）

> 一页说明：我们做了什么、怎么复现、目录导航。整理于 2026-11-05；凭据类信息（团队 GUID、密码）一律占位。

## 我们做了什么（一段话）

赛题要求为 6 个依次下载的文件（10→320 MB，共 630 MB）在共享 100 Mbps 链路 + 100 Mbps 网页搜索背景流量下配置 QUIC 流量整形参数，使总耗时最短。我们以链路预算分析定位瓶颈（79% 损失在 4/5/6 号大文件的稳态份额），用「对照 → 单因子 → 网格 → 复测选型」四层黑箱搜索 + 均值加方差惩罚选型，完成 68 次有效本地评测：**总耗时从基线 170.0 s（n=2）降至 123.81 s（n=7，−26.2%，CV 5.8%）**；统计上最优配置族之间差异不显著（Welch t 全部 p>0.05），收益来自模块层的结构切换。所有数字可由本包内命令一键复算。

## 怎么复现（三步）

1. **看配置**：`best-configs/` 内 3 个候选配置（字节级复制自 `runs/configs/`，sha256 已核对）。
2. **跑评测**：按 `reproduce.md` 把任一候选放入云主机 `question/1..6`，先 `./format_check_client` 再 `./competition_question1`（4 核及以上，单次 3–4 分钟）。
3. **算统计**：工作区执行 `python tools/config_stats.py` → 重新生成 `report/实验结果-统计.md` 第 1–4 节；数据源 `runs/results.jsonl`（68 条有效记录，含配置、分文件耗时、valid 标记）。

## 目录导航

| 文件/目录 | 内容 |
|---|---|
| `best-configs/README.md` | 3 个候选配置的本地成绩（均值/标准差/n/来源 tag）与官方状态 |
| `best-configs/<name>/1..6/pacer.txt` | 配置原文（UTF-8、LF、无末尾换行；sha256 与源一致） |
| `reproduce.md` | 逐步复现：目录结构、格式检查、本地评测命令、结果文件含义、统计复跑 |
| `methodology.md` | 方法摘要（链路预算 → 四层搜索 → 方差惩罚 → 跨环境鲁棒准则），详版见 `report/技术报告-v1.md` |
| `checklist.md` | 复核自检清单（格式/换行/时间戳/非法参数/结果可复现，逐条打勾） |

## 关键数字速查（全部可溯源）

| 指标 | 值 | 溯源 |
|---|---|---|
| 基线（origin 全默认） | 170.00±2.34 s（n=2） | `runs/results.jsonl` tags `baseline-manual-*` |
| 本地最优族 leak9 | 123.81±7.19 s（n=7，−26.2%） | 同上，tags `e5-leak-rate9` 等 7 条 |
| 提交口径 token_bucket 100/200/20@1000 | 136.24±7.60 s（n=2） | tags `e8-tokenbucket-burst`、`tb-100-200-20-r2` |
| 有效评测 / 配置族 | 68 次 / 48 族 | `report/实验结果-统计.md` §1–2 |
| 官方同配置实测 | 245.995 / 243.958 s（差 0.83%） | `intel/raw/leaderboard_*.json`、`runs/submissions.jsonl` |

> 注：官方环境与本地存在系统性差异，归因分析见 `docs/analysis/official-score-anomaly.md`（进行中）；本包只陈述可复核事实。
