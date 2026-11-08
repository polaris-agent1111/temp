status: done
priority: 4
assignee: zcode
created: 2026-11-05 22:55

# 0032 — 杂活：工作区整理与索引

## 任务（纯整理，不改变任何实验数据）

1. **`runs/README.md` 索引**：给 `runs/` 下每一类文件写一行说明：
   - `results.jsonl`（本地评测记录，字段说明）
   - `submissions.jsonl`（提交台账）
   - `official_results.jsonl`（官方成绩配对）
   - `adaptive_log.jsonl`（自适应逐发决策日志，字段说明）
   - `board_watch.jsonl`（盯榜快照）
   - `configs/`（每个 tag 的 1–6 目录）
   - `queue*.json`（历史评测队列，标明各自测了什么主题）
   - `submit_plan_*.json`（历史提交计划，标明哪些已执行、哪些作废）
2. **清理临时文件**：删除 `runs/` 下的 `*.tmp`、`*.bak`、空的临时目录（**删之前先列出来，不要动 results/submissions/official/configs 里的任何文件**）。
3. **`runs/queue*.json` 清单表**：一个表格列出每个 queue 文件 → 主题 → 配置文件数 → 对应结果条数（从 results.jsonl 按 tag 前缀匹配）。
4. **`report/figures/` 检查**：列出所有图片、尺寸、对应报告章节，指出有没有报告引用了不存在的图。
5. 输出写入 `runs/README.md` + `zcode/reports/0032-cleanup.md`。

## 禁止

不许删除或覆盖 `results.jsonl`、`submissions.jsonl`、`official_results.jsonl`、`adaptive_log.jsonl`、`board_watch.jsonl`、`configs/` 下任何内容；不许删除 `queue*.json` 与 `submit_plan_*.json`；不碰 `client/`、`harness/`。

## 交付

`runs/README.md` + `zcode/reports/0032-cleanup.md`。
