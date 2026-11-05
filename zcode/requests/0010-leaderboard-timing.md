status: open
priority: 2
assignee: zcode
created: 2026-11-05 15:12
repeat: every-run

# 0010 — 榜单时序观测（可重复执行的常驻杂活）

## 背景

团队 `赛博coder` 已提交 2 次（13:25:17 得 245.995s，14:23:59 至今未出分）。同一条 `submission_log` 里还有 13:26、13:35、13:37、13:44、13:53、14:14 共 12 次其它队提交都没出现在 `leaderboard.attempts` 里 —— 说明**官方出分有明显延迟/排队**，不是即时反馈。搞清楚这条流水线的时间特性，直接决定我们怎么花每天的 5 次提交额度。

## 每次运行都要做的事（很轻，几分钟）

1. GET 一次榜单，落到 `intel/raw/leaderboard_<YYYYMMDD-HHMM>.json`：
   ```
   python -c "import requests,json,time;d=requests.get('http://47.120.64.152:5000/api/leaderboard',timeout=30).json();json.dump(d,open('intel/raw/leaderboard_'+time.strftime('%Y%m%d-%H%M')+'.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)"
   ```
   只读 GET，**不要**带任何 cookie/token，**不要**登录，**不要** POST。
2. 用增量脚本把快照汇总成 `intel/analysis/board_timeseries.csv`，列：
   `snapshot_at, team, problem, attempt_submitted_at, download_seconds, log_submitted_at, log_status`
   （attempts 与 submission_log 按 (team, submitted_at) 关联；未出分的提交只在 log 里有）。
3. 如果 `docs/analysis/leaderboard-timing.md` 不存在就创建，已存在则追加一节 `## 观测 @ <时间>`。

## 分析要回答（写在 leaderboard-timing.md）

- 提交 → 出分的延迟分布（已知样本：我们 13:25:17 提交，约 14:1x 出分，≈45–55 min；请用快照时间精确化）
- 榜单刷新粒度和出分是否严格 FIFO（对比 submission_log 顺序 vs attempts 出现顺序）
- 各队提交时段分布（哪些时段提交少，可能排队更短）
- 结论：**给出 3 条可执行建议**，例如「提交后至少等 N 分钟再看」「同一配置不要 1 小时内重复投」「当天额度尽量早用掉，因为出分要 1h」

## 交付

- `intel/raw/leaderboard_*.json`（每次运行新增一个，勿删旧的）
- `intel/analysis/board_timeseries.csv`
- `docs/analysis/leaderboard-timing.md`
- 本次运行结束在 `zcode/reports/0010-run-<YYYYMMDD-HHMM>.md` 写 3–5 行观察（尤其：我们 14:23:59 那次出分了没有、分数多少）

## 禁止

- 不登录、不提交、不碰云主机、不改 `client/` `harness/` `runs/results.jsonl` `runs/submissions.jsonl`
- 只允许 GET 这一个公开 URL
- 不要删除或覆盖历史快照
