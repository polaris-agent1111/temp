status: done
priority: 2
assignee: zcode
created: 2026-11-05 18:20

# 0017 — 复核材料包 v2（更新到「4 ms 定时器粒度」发现与新的最优配置）

## 背景

`report/复核材料/`（0008 产出）是按**破案前**的状态整理的：最优配置写的是 `leak9`（1 ms 间隔）、关键数字是 68 条有效评测、方法里没有「官方定时器粒度」这条。现在这两点都过期了：

1. **1 ms 漏桶配置在官方评测里会被腰斩**（官方 244–246 vs 本地 124，两次复现），复核时如果交的是 `leak9`，复测会直接翻车 → 必须换成 **4 ms 间隔**的配置。
2. 新的本地最优是 `leak 24/50/4000`（n=7 均值 126.2，单次最好 119.6）；当前官方最好 133.086 来自 `leak 36/40/4000`。

## 目标产出（就地更新 `report/复核材料/`）

1. **`best-configs/`**：保留现有三个（作为历史对照），**新增**两个目录：
   - `leak-24-50-4000/1..6/pacer.txt`（来自 `runs/configs/leakc-24-50-4000-*` 或直接按 `leak_rate=24,bucket_cap=50,leak_interval_us=4000` 生成，必须 **LF、无末尾换行、97 字节左右**，并用 sha256 校验与 `runs/configs/` 中任一一致）；
   - `leak-36-40-4000/1..6/pacer.txt`（**官方实测 133.086 的那份**，来自 `runs/configs/hog-ref-leak9` 不对——请用 `runs/configs/leakc-36-40-4000` 或按 `leak_rate=36,bucket_cap=40,leak_interval_us=4000` 生成）。
   - 更新 `best-configs/README.md`：每份配置写「本地均值±sd (n)、官方实测（有则写）、适用场景」。
2. **`README.md`**：把「我们做了什么」一段更新为包含**官方 133.086（榜第 5）**与「定时器粒度」这条关键发现；「关键数字速查」表加上官方列。
3. **`reproduce.md`**：新增一节「⚠ 必须用 4 ms 及以上间隔」：说明 1 ms 漏桶在本机 124 s 但官方 244 s 的现象、原因（官方定时器粒度≈4 ms，反推值）与规避方法（`leak_interval_us ≥ 4000` 或改用带 `enable_n_in_flight` 的模块）。指向 `docs/knowledge/timer-granularity.md`。
4. **`methodology.md`**：新增「跨环境鲁棒准则」一小节（3–5 行）：参数选择必须考虑官方环境的定时器粒度，不能只看本地最优。
5. **`checklist.md`**：新增两条自检：① 所有 `leak_interval_us` ≥ 4000；② 若用 token_bucket/rate-based，确认没有把 `enable_n_in_flight` 关掉。
6. **`review-manifest.json`（新增）**：列出包内每个文件的 sha256 与字节数，方便复核方核对（脚本可用 Python 生成，写进包里）。

## 输入（只读）

`runs/configs/`（现成配置目录）、`report/复核材料/`（现有内容）、`docs/knowledge/timer-granularity.md`、`report/技术报告-v2.md`、`runs/results.jsonl`、`runs/submissions.jsonl`。

## 禁止

不提交、不登录、不碰云主机、不改 `runs/`；不写真实凭据（GUID/密码一律占位）。

## 交付

更新后的 `report/复核材料/` + `zcode/reports/0017-review-v2.md`（1 页摘要：改了哪些文件、新增哪两个配置、sha256 是否一致）。完成后把本文件头改成 `status: done`。
