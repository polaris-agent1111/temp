status: open
priority: 2
assignee: zcode
created: 2026-11-05 16:30

# 0013 — 「官方定时器粒度」发现的完整知识文档（技术报告/复核/答辩都要用）

## 背景（全部是已发生的实测事实，不要推翻，请核对文件后引用）

- 团队 `赛博coder`，赛题「六载穿柜」。我们的云主机本地评测程序与官方评测程序是同一套（`competition_question1`），本地一次约 2.5–3 分钟。
- 同一份配置 `leak_bucket leak_rate=9,bucket_cap=30,leak_interval_us=1000`：本地 7 次实测 123.81±7.19 s；官方两次提交 = **245.995 / 243.958 s**（`runs/submissions.jsonl`、`runs/official/v1.tar.gz`、`v1b.tar.gz`）。
- 同时间段其它队成绩正常：`无法导入` 13:26 = 131.2653、`大肥鱼` 13:35/13:37/13:38 = 130.9/129.6/129.0（`intel/raw/leaderboard_*.json`）。
- 本地开 4 个 CPU 满载进程（2 倍超售）后：leak9 = 137.09 s（+11%）、precise 12.5MB/s = 132.53 s → **CPU 争抢解释不了 2×**。
- 换 `token_bucket tokens=100,burst=200,token_refill_rate=20,token_refill_interval_us=1000`（本地 136–144）→ **官方 140.927 s**（≈1:1）。
- 换 `leak_bucket leak_rate=36,bucket_cap=40,leak_interval_us=4000`（本地 122.95 / 136.79）→ **官方 133.086 s**。
- 定量模型：`leak_bucket` 是五个模块中唯一没有 `enable_n_in_flight` 旁路的；假设官方运行时定时器实际粒度 ≈ 4000 µs，则 9 包/1 ms 退化为 9 包/4 ms = 2250 包/s ≈ 21.6 Mbps（按 1200 B/包）→ 630 MB ÷ 21.6 Mbps ≈ 233 s，与实测 244 s 吻合；把 `leak_interval_us` 提到 4000 后速率恢复 9000 包/s，官方回到本地水平。

## 目标产出

`docs/knowledge/timer-granularity.md`，要求：

1. **现象**：完整时间线表（提交时间、配置、本地值、官方值、官方/本地比）。
2. **证据链**：按「观测 → 排除 → 定量」三层写，每条结论标注出自哪个文件/记录。
3. **定量模型**：把上面的算式写清楚，并给出「若粒度是 2000/4000/10000 µs，各配置的理论官方值」对照表（用 Python 算，脚本放 `tools/timer_model.py`）。
4. **对配置设计的推论**：必须满足 `leak_interval_us ≥ 4000`（或改用带 `enable_n_in_flight` 的模块）；给出「等效速率表」：不同 `leak_interval_us` 下要写多少 `leak_rate` 才能达到 9000 包/s。
5. **局限**：粒度 4 ms 是反推值不是实测值；官方按文件分解不可观测；两次样本不足以排除其它共因。要明确写「待验证」。
6. **一句话结论**（给答辩用）。

## 输入

`runs/results.jsonl`、`runs/submissions.jsonl`、`runs/official/`、`intel/raw/leaderboard_*.json`、`docs/extracted/流量整形模块使用说明.md`、`zcode/STATUS.md`。

## 禁止

不提交、不登录、不碰云主机、不改 `runs/results.jsonl` `runs/submissions.jsonl` `harness/` `client/`。数值必须能对上文件，否则标「待补」。

## 交付

`docs/knowledge/timer-granularity.md` + `tools/timer_model.py` + `zcode/reports/0013-timer-granularity.md`（1 页摘要）。完成后把本文件头改成 `status: done`。
