status: done
priority: 1
assignee: zcode
created: 2026-11-05 10:40

# 0002 — 流量整形机制分析与调参假设清单

## 背景

赛题「六载穿柜」：6 个文件（10/20/40/80/160/320 MB，共 630 MB）按顺序从 d1 下载到 d2（QUIC），单连接；同时有一段「网页搜索」背景流量（d4→d3，流长分布，平均 1.7 MB，目标速率 100 Mbps）持续占用同一 100 Mbps 汇聚链路 s1–s2；接入链路 100 Mbps、汇聚链路 100 Mbps，RTT 70 ms。每次下载前可切换服务端流量整形模块（5 选 1）及其参数。

**已有实测**：默认配置（origin，burst_tokens=10，max_pacing_rate=0 即不限速，clock_granularity=1000）本地评测总耗时 **167.663 s**，各文件耗时：2.516 / 4.611 / 16.743 / 18.503 / 43.702 / 81.588 s。官方榜单第 1 名当前 126.96 s。

参数规范见 `docs/extracted/流量整形模块使用说明.md`，赛题原文见 `docs/extracted/六载穿柜.md`（都已完成 pdf/docx→md 提取，务必先读）。

## 目标

产出一份**可直接指导下一步实验**的机制分析与假设清单：为什么慢？瓶颈在哪？哪些参数/模块最可能改进？预期方向与优先级？如何用最少实验次数验证？

## 允许写的路径

- `docs/knowledge/flow-shaping-analysis.md`（主产出，可新建目录）
- `zcode/reports/0002-flow-shaping-analysis.md`（交付摘要）

## 内容要求

1. **基线拆解**：用上面 6 个耗时反推每个文件的有效吞吐（MB/s 与 Mbps），指出哪个阶段损失最大（小文件？大文件？），并解释原因（比如 cwnd 慢启动、背景流量排队、RTT 70ms 的 BDP≈875 KB）。
2. **链路预算**：100 Mbps 链路 + 100 Mbps 背景目标速率意味着什么？在什么条件下下载能拿到带宽（背景流之间的空隙 / 背景流退避 / 队列溢出丢包）？给出定性推理。
3. **五个模块对比**：token_bucket / coarse_grained_rate_based / precise_rate_based / origin / leak_bucket 各自的发送行为差异，在「突发 vs 平滑」「是否受 cwnd 限制」「能否抢空档」上的差异，各自适合哪种文件尺寸。
4. **参数假设表**（核心）：一行一个假设，列：参数/模块、取值方向、预期对总耗时的影响、机制解释、优先级（高/中/低）、验证方式（单因子扫哪几个点）。
   - 至少覆盖：max_pacing_rate（相对 12.5 MB/s 的 0.8–2.0 倍区间）、burst_tokens、clock_granularity、token_bucket 的 tokens/burst/token_refill_rate/token_refill_interval_us、leak_bucket 的 leak_rate/bucket_cap/leak_interval_us、enable_n_in_flight 开关。
   - 特别讨论：**分文件差异化配置**（6 个目录可各写一份 pacer.txt，小文件用突发、大文件用平滑）可能带来的收益。
5. **实验设计建议**：给出一个「先做什么、后做什么」的 10 步以内的实验计划，尽量节省评测次数（单次评测约 4–5 分钟，云主机 4 核，不能并行太多）。
6. **风险提示**：哪些配置可能触发大量丢包/重传甚至下载失败（提交失败=没成绩）。

## 禁止

- 不要操作云主机、不要跑评测、不要提交榜单。
- 不要动 `client/`、`harness/`、`runs/`、`scripts/` 下的任何文件。
- **不得编造数据**：没有实测依据的推断必须标注「待验证」。

## 交付

`docs/knowledge/flow-shaping-analysis.md` + `zcode/reports/0002-flow-shaping-analysis.md`（1 页摘要：Top5 优先验证的假设 + 建议的实验顺序）。

完成后把本文件头 `status: open` 改成 `status: done`。
