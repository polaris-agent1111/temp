status: done
priority: 3
assignee: zcode
created: 2026-11-05 17:40

# 0016 — 对手情报与针对性策略（从榜单 attempts 反推）

## 背景

榜单 `/api/leaderboard` 的 `submissions[].attempts[]` 给了每个队**每次提交的官方成绩与提交时刻**（`intel/raw/leaderboard_*.json` 有 5+ 个快照，`intel/analysis/board_timeseries.csv` 已整理 162 行）。我方已知：官方评测对同一配置近似确定（同一配置两次只差 0.83%），所以**每个 attempt 基本对应一个不同配置**。据此可以反推对手的「配置搜索轨迹」。

## 目标产出

`docs/analysis/opponents.md`，包含：

1. **每队档案表**：队名、提交次数、最好成绩、成绩序列（时间 + 数值）、极差/变异系数、活跃时段。
2. **轨迹分类**：给每队打标签并给证据，例如
   - 「连续微调型」：相邻 attempts 差 1–3%（大肥鱼 130.9/129.6/129.0）
   - 「双峰型」：好坏交替（blueman 145→305→303→305；无法导入 138→186→338→301→131）
   - 「一锤定音型」：只投 1 次就上榜（YJDS 151.9、hashkimi 155.0）
   - 「早期强后期停」：Catnet 11-03 就到 126.96 之后一直没超
3. **反推结论**：
   - 哪些成绩点**不可能**是「我们已知模块/参数」能产生的（用 `docs/knowledge/timer-granularity.md` 的模型 + `runs/results.jsonl` 的本地分布判断）
   - 对手最可能的配置族（有旁路模块 / 粗粒度漏桶 / origin 调参），以及**他们的弱点**（例如成绩抖动大说明配置不稳）
   - 名次窗口：要拿一等（第 1）必须 ≤126.965，二等 ≤131.265，三等 ≤132.573（以 11-05 17:00 榜单为准，注明快照时刻）
4. **针对性策略**：
   - 我们当前最好 133.086，差距 6.12 s 的来源分解（按文件：用我们本地分文件数据估计 4/5/6.bin 各能再省多少）
   - 未来 11 天每天 5 发怎么分配（结合 `report/提交台账.md` 的排期）
   - 明确的「停止条件」：什么情况下认为 126.9 不可达、退而保二等/三等
5. **风险**：对手也可能在最后几天突然爆发；top 提交会被人工复测（防过拟合）——提醒不要用「针对固定种子的过拟合配置」。

## 输入（只读）

`intel/raw/leaderboard_*.json`、`intel/analysis/board_timeseries.csv`、`runs/results.jsonl`、`runs/submissions.jsonl`、`report/提交台账.md`、`docs/knowledge/timer-granularity.md`、`report/实验结果-统计.md`。

## 禁止

不提交、不登录、不碰云主机、不编造数据；所有数字标快照时刻。推断必须写「推断」并给反例条件。

## 交付

`docs/analysis/opponents.md` + `zcode/reports/0016-opponents.md`（1 页摘要，给出「要拿第 1 还差什么」的一句话答案）。完成后把本文件头改成 `status: done`。
