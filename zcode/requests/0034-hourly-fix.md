status: open
priority: 4
assignee: zcode
created: 2026-11-05 23:00

# 0034 — 杂活：hourly 报告索引一致性修复 + 数据回填

## 任务

1. **索引一致性**：`hourly/INDEX.md` 里的链接与 `hourly/` 目录实际文件比对，列出：链接指向不存在文件、存在文件但没进索引、文件名与标题区间不一致。
2. **修复**：把 INDEX 整理成干净的一览表（时间区间 / 文件 / 一句话要点），保留五节结构约定不变；不要删除任何已有报告文件。
3. **进度快照回填**：把 INDEX 顶部的「当前进度快照」更新为**截至最新**的事实（榜单名次/成绩、今日额度、当前最优配置、待办），数据源用 `/api/leaderboard` + `runs/submissions.jsonl` + `runs/adaptive_log.jsonl`。
4. **README 校对**：`hourly/README.md` 里写的约定与实际报告格式是否一致，不一致就修。
5. 输出 `zcode/reports/0034-hourly-fix.md`（列改了什么）。

## 禁止

不删除报告；不修改报告正文里的实验数字（只修索引与快照）。

## 交付

更新后的 `hourly/INDEX.md` + `hourly/README.md` + `zcode/reports/0034-hourly-fix.md`。
