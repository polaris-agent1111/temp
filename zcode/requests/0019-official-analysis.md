status: done
priority: 2
assignee: zcode
created: 2026-11-05 19:05

# 0019 — 官方探测分析工具（配置 → 官方成绩，自动反推最优参数区）

## 背景

从 11/06 起每天会投 5 个不同配置（官方固定随机种子 ⇒ 同一配置成绩近似确定，重复投无收益），10 天内会积累 ~55 个「配置 → 官方成绩」观测点。这些数据是**唯一可信的优化信号**（本地噪声 sd≈6–8 s，官方才有决定性）。现在缺一个把观测点变成结论的工具。

## 数据链路（已就绪，可直接用）

1. `runs/submissions.jsonl`：每次提交一行，字段 `at`（时间）、`note`（形如 `s6-leak-24-50-4000 | S6: ...`，**竖线前是 tag**）；
2. `runs/configs/<tag>/1..6/pacer.txt`：该 tag 的实际配置（上传时生成）；
3. `runs/official_results.jsonl`：`tools/official_log.py` 生成的官方成绩表，字段 `submitted_at`、`official_seconds`、`note`（与 submissions 的 note 同源）；
4. `intel/raw/leaderboard_*.json`：榜单快照（含对手 attempts）。

## 目标产出

### 1. `tools/official_analysis.py`（纯标准库，可重复运行）

输入上面 1–3，输出：

- **配对表**：每行 = 一次提交 → `tag / 提交时刻 / 官方成绩 / 配置(mode+参数) / 本地均值(n, 若有)`；配对用「提交时刻最近匹配（±2 分钟）」。
- **参数趋势**：对 `leak_bucket` 族按 `leak_rate`、`bucket_cap` 分组算官方成绩的均值与极差；打印「官方最好 / 官方最差」的 rate 与 cap。
- **排名**：按官方成绩升序排列，标出前 3 与它们相对榜首（当前榜首成绩从快照取）的差距。
- **下一轮建议**（规则化，不要瞎猜）：按「官方最好的 rate ±1、cap ±10 邻域」生成 5 个候选，写进 `runs/submit_plan_<下一天>.json`（格式见 `runs/submit_plan_1106.json`：列表，每项 `{tag, note, all/configs}`）。
- 脚本必须能在**没有任何官方数据**时优雅退出（打印「暂无数据」），不能崩。

### 2. `report/官方探测分析.md`

- 用脚本输出生成（可手工补充解读），至少包含：配对表、参数趋势表、官方 vs 本地的偏差 δ 统计、当前最优配置、下一轮 5 个候选及其理由。
- 每次有新数据时重跑脚本更新本文（在文件头写「数据截至」时刻）。

### 3. `zcode/reports/0019-official-analysis.md`（1 页摘要）

## 参考已有数据

`runs/official_results.jsonl` 现有 5 条（v1 245.995 / v1b 243.958 / S3 140.927 / S4 133.086 / S5 141.727），可用于自测脚本。注意 v1/v1b 是 1 ms 陷阱族（官方 ×2），应当在趋势里标为异常点并排除。

## 禁止

不提交、不登录、不碰云主机、不改 `runs/results.jsonl` `runs/submissions.jsonl` `runs/official_results.jsonl`；不编造官方成绩。

## 交付

`tools/official_analysis.py` + `report/官方探测分析.md` + `zcode/reports/0019-official-analysis.md`。完成后把本文件头改成 `status: done`。
