status: done
priority: 3
assignee: zcode
created: 2026-11-05 21:05

# 0021 — 每日运营手册（10 天冲刺的可执行 runbook）

## 背景

从 11/06 到 11/16 还有 11 天、每天 5 发额度。现在的流程散在多个文件里（`report/探测计划.md` 管策略、`tools/submit_batch.py` 管投递、`tools/official_log.py` 管记账、`tools/official_analysis.py` 管分析、`hourly/` 管日报）。需要一份**单页 runbook**，任何人（包括复核方或队友）照着做就能把当天流程跑完。

## 目标产出

`report/每日运营手册.md`，要求：

1. **每天的标准流程（5 步，带具体命令）**
   - ① 看前一天官方结果：`python tools/official_log.py`（榜站 502 时自动用快照）
   - ② 生成候选：`python tools/official_analysis.py --plan`（生成 `runs/submit_plan_<MMDD>_auto.json`，**不覆盖**手写版）
   - ③ 人工确认后提交：`python tools/submit_batch.py --plan runs/submit_plan_<MMDD>.json --yes`
   - ④ 记账与更新：`tools/official_log.py` → `report/官方探测分析.md` 重跑 → `hourly/INDEX.md` 更新
   - ⑤ 写当小时 `hourly/YYYY-MM-DD_HH00.md`（五节结构）
2. **每日检查清单（勾选式）**：额度已用/剩余、当天 5 发是否全部出分、是否有新对手纪录、榜单站是否可用、`runs/submissions.jsonl` 与 `runs/official_results.jsonl` 是否一致。
3. **异常处理表**：至少覆盖
   - 榜站 502（提交服务器仍可用，继续投，结果延后记账）
   - 提交报「已达到最大提交次数」（额度边界不在 00:00，等 10–20 min 重试）
   - 格式检查失败（立即停投，因为失败也扣额度；先本地跑 `tools/validate_pacer.py`）
   - 出分异常慢（>2 小时，检查 `submission_log` 是否有记录）
   - 官方成绩比本地差 >10%（记录为「官方异常点」，不要据此调整策略）
4. **额度台账**：一张空白表，列 `日期 | 用了几发 | 当天最好官方成绩 | 累计官方最好 | 距榜首 | 备注`，从 11/05 已发生的记录填起（5 发、133.086、距榜首 6.12 s）。
5. **最后三天的特殊规则**（11/14–11/16）：只投已知最优、11/16 必须在 17:00 前投完留出出分时间、绝不试新配置。

## 输入（只读）

`report/探测计划.md`、`report/提交台账.md`、`tools/submit_batch.py`、`tools/night_submit.py`、`tools/official_log.py`、`tools/official_analysis.py`、`hourly/INDEX.md`、`runs/submissions.jsonl`、`runs/submit_plan_1106.json`。

## 禁止

不提交、不登录、不碰云主机、不改 `runs/`。文档里的命令必须是真的能跑的（可对照脚本源码核对参数名）。

## 交付

`report/每日运营手册.md` + `zcode/reports/0021-runbook.md`（1 页摘要）。完成后把本文件头改成 `status: done`。
