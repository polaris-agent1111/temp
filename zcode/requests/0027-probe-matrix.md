status: done
priority: 2
assignee: zcode
created: 2026-11-05 22:45

# 0027 — 探测矩阵维护（每天可重跑）

## 为什么

我们需要一眼看出「哪些 (interval, rate) 组合已经官方验证过、哪些还是空白」，避免把额度浪费在重复区域。

## 任务

产出 `tools/probe_matrix.py` + `report/探测矩阵.md`：

1. **矩阵**：行 = `leak_rate`（18…48），列 = `leak_interval_us`（4000/5000/6000/8000），每个格子填：
   - `官方成绩`（多个用 `/` 分隔）
   - `本地均值(n)`
   - `δ`
   - 空格子标 `—`（未探测）
2. **已投配置清单**：按提交时间倒序列出所有官方点（配置 / 成绩 / 时刻）。
3. **空白区统计**：按 rate 段统计已探测覆盖率；指出「哪些格子看起来最有价值但还没测」（用本地均值 + 邻近官方 δ 推断）。
4. **自适应逐发日志的落点**：把 `runs/adaptive_log.jsonl` 里每次 `pick_next` 的结果也标进矩阵。
5. 脚本要能一条命令重跑（读 `runs/results.jsonl` + 官方 API），输出覆盖写入 `report/探测矩阵.md`。

## 禁止

不提交、不登录、不碰云主机、不改 `runs/`。

## 交付

`tools/probe_matrix.py` + `report/探测矩阵.md` + `zcode/reports/0027-matrix.md`。
