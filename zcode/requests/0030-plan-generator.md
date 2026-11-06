status: open
priority: 2
assignee: zcode
created: 2026-11-05 22:50

# 0030 — 次日计划自动生成器（可复用工具）

## 为什么

现在每天的计划都靠 Lead 手写。需要一个小工具：输入「今天所有官方成绩 + 本地样本」，自动输出「明天 5 发」并附推理，以后每天一条命令。

## 任务

产出 `tools/plan_from_results.py`：

1. **输入**：`/api/leaderboard`（team=赛博coder 的全部 attempts）+ `runs/adaptive_log.jsonl` + `runs/results.jsonl` + `runs/submissions.jsonl`。
2. **输出**：`runs/submit_plan_<次日MMDD>_auto.json`（**不覆盖**手写版，已存在则加 `_auto` 后缀再编号）。
3. **决策规则**（要能说清楚）：
   - 按 δ 给每个已测配置算「官方友好度」，选出最好的 2–3 个区域
   - 明日 5 个点：2 个「复测最好点附近（±可测步长）」，2 个「最好点所在家族的新点」，1 个「结构性探针（高速翼/低速翼/换桶量级）」
   - 硬约束：不与最近 10 天已投配置重复；`bucket_cap >= leak_rate`；`leak_interval_us >= 4000`
4. **CLI**：`python tools/plan_from_results.py` 默认输出计划 + 打印推理；`--date 2026-11-07` 指定目标日。
5. **推理可读**：每个点打印一行「为什么选它」，方便 Lead 直接照抄或否决。
6. 用 11/06 的真实结果跑一遍，把输出贴进报告。

## 禁止

不提交、不登录、不碰云主机、不改 `runs/` 里的历史文件（只新增）。

## 交付

`tools/plan_from_results.py` + `zcode/reports/0030-plan-gen.md`（含一次真实运行输出）。
