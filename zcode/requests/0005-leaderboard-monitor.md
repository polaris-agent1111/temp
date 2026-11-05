status: done
priority: 3
assignee: zcode
created: 2026-11-05 10:40

# 0005 — 榜单监控与变化分析

## 背景

官方榜单每 30 分钟刷新，比赛 2026-11-16 23:59:59 冻结。需要有人盯着对手的分数变化（尤其是 Catnet，当前 126.9647 s），及时发现反超/被反超。这是纯"杂活"，适合 zcode 定时做。

## 目标

维护 `runs/leaderboard/monitor.md`：一张「时间 / 排名 / 团队 / 最好成绩 / 相对上次变化」的表，外加一段「本次变化解读」。每次被唤醒做一轮（一轮 = 抓一次榜单 + 更新文件）。

## 允许写的路径

- `runs/leaderboard/monitor.md`（主产出，追加或整体刷新均可）
- `zcode/reports/0005-leaderboard-monitor.md`（交付摘要，可只写一次并更新）
- 允许执行：`python client/api.py board --save`（公开接口，无需密码；会向 `runs/leaderboard/ledger.csv` 追加记录）

## 具体动作

1. 运行 `python client/api.py board --save`（工作目录 `E:\Download\iDSN`），拿到当前排名与各队最好成绩。
2. 与 `runs/leaderboard/ledger.csv` 里上一次快照对比，标出变化（谁变快了、快了多少、名次是否变化）。
3. 更新 `runs/leaderboard/monitor.md`：
   - 「当前榜单」表（名次/团队/题目一最好成绩/提交数）
   - 「最近变化」列表（时间 + 团队 + 旧→新 + 变化量）
   - 「我方状态」：团队「赛博coder」当前是否已在榜（未提交则显示"未上榜"）
   - 「风险提示」：与第 1 名的差距、我方需要达到的目标线（一句话）
4. 如果发现异常（例如某队成绩突然比历史最好还快很多），单独记一条。

## 禁止

- 不要登录（不需要）、不要提交、不要碰 `client/secrets.json`、`runs/.session.pkl`、`runs/trit_token.json`。
- 不要操作云主机、不要跑评测。
- 不要删除 `ledger.csv` 已有内容。

## 交付

`runs/leaderboard/monitor.md` 更新完毕 + 报告摘要。完成后把本文件头改成 `status: done`（后续 Lead 会重新 open 让你继续盯）。
