# docs · 资料索引

> 官方 DOCX 原件在仓库根目录 `题目1附件/`（3 个文件，约 3.8 MB）；`official/` 里是从中抽取/整理的 Markdown，方便检索。

## `official/` — 官方原文（权威）

| 文件 | 内容 |
|---|---|
| `01_rules.md` | 竞赛规则、评分、提交额度、合规红线 |
| `02_websearch_model.md` | WebSearch 背景流量模型与流长 CDF |
| `03_pacer_modules.md` | 五个流量整形模块的参数/语义/约束 |
| `04_manual.md` | 云主机、question 目录、format_check_client、competition_question1、local_send_client 的使用说明 |

## `background/` — 历史分析（有用，但注意时效）

| 文件 | 内容 | 读法 |
|---|---|---|
| `timer-granularity.md` | 官方 4 ms 定时器粒度的证据链与模型 | **必读**；解释为什么 `leak_interval_us` 不能小于 4000 |
| `flow-shaping-analysis.md` | 五个模块的行为对比、瓶颈拆解、调参假设 | 理解“为什么要平滑/为什么要抢空档” |
| `official-surface.md` | 7 个官方 leak_bucket 点的响应面拟合；单漏桶谷底 ~133s | 理解单漏桶的天花板 |
| `bottleneck-and-40shot-plan.md` | 对官方二进制的逆向、拓扑/背景流/下载流程细节 | 想搭真实环境或理解评测器行为时读 |
| `技术报告-v4.md` | 团队技术报告 v4（含 119.268s 本地混合方案） | 历史方案总览；部分结论已被后续实验修正 |
| `HANDOFF-2026-11-08.md` | 2026-11-08 的团队交接快照 | 历史状态；排名/配额以最新榜单为准 |

> 这些 `background/` 文档是**历史研究记录**，不是官方规则。里面的数字、排名、结论都有时间戳；做决策前先看根目录 `LOCAL_EVAL_GUIDE.md` 的“当前状态”一节。
