# 0019 报告：官方探测分析工具

- 完成时间：2026-11-05 19:45
- 执行者：zcode
- 结论：`tools/official_analysis.py`（纯标准库）已跑通全链路——5 条官方成绩全部配对成功（±2 min）、1 ms 陷阱族自动识别并排除、δ 统计（+96%/+94% 陷阱、+2~3.5% 正常、+14.8% 异常）、按官方排名（距榜首 +6.121 s）、次日 5 候选按「官方最好 rate±1 × cap±10」规则生成且**非破坏写入**（`submit_plan_1106_auto.json`，未覆盖 Lead 手动版）。

## 具体动作

1. **`tools/official_analysis.py`**（可重复运行，无官方数据时打印「暂无数据」优雅退出）：
   - 配对：`official_results.submitted_at` ↔ `submissions.at` ±2 min 最近匹配；tag 取 note 竖线前（旧记录无竖线→显示「—」）；
   - 配置解析：note 正则（`rate9/cap30/int1000`、`36/40/4000`、`tokens=...,refill=20/1000us` 三种形态）+ 解析失败继承上一条（`同 v1 配置重投` 场景）；
   - 本地均值：6 目录全等于该配置的 valid 记录（默认值归一化后比对，`enable_n_in_flight=1` 等默认项剔除）；
   - 趋势：leak 族按 rate/cap 分组官方 mean/min/max/极差；**interval<4000 自动标 ⚠陷阱并排除**；
   - 排名：官方升序 + 快照榜首差距；
   - 计划：官方最好 rate±1 × cap±10、去重已投、cap≥rate 约束、确定性排序取 5 → `runs/submit_plan_<次日>.json`；**目标已存在则写 `*_auto.json` 不覆盖**。
   - 修一处 bug：submissions 带 +0800、official 无时区 → `parse_dt` 统一转 naive 后再做差。
2. **`report/官方探测分析.md`**：工具输出（配对表/趋势/排名/候选）+ 人工解读四节——δ 统计三档、当前最优与榜况、**5 候选理由及与 Lead 手动版的区域分歧**（手动 rate22–26/cap50 赌本地迁移 vs 自动 rate35–37/cap40–50 赌官方偏好高 rate；建议 11/06 用手动版、自动版顺延 11/07）、重跑说明与口径注记。
3. 自测：`--plan` 模式实测输出 `s6-leak-36-50-4000` … `s10-leak-37-50-4000` 五候选并正确检测到 1106 计划已存在。

## 产出文件

- `tools/official_analysis.py`
- `report/官方探测分析.md`（数据截至 2026-11-05 16:24:13）
- `runs/submit_plan_1106_auto.json`（任务单授权的计划输出；未动 `submit_plan_1106.json`）
- `zcode/reports/0019-official-analysis.md`（本报告）

## 未完成/风险

- **榜单 API 自 18:28 起 502（≥70 min）**：本文榜首差距基于 17:54 快照，恢复后需重跑刷新（已在使用说明注明）。
- 本地均值口径含 v1 族的 CPU 争抢对照（n=8 125.47 vs 空闲 123.81）——报告已注明；如需空闲口径可在脚本加 tag 过滤（未加，避免隐性丢样本）。
- 趋势目前只有 2 个有效 leak 官方点（36/40、27/40），rate/cap 结论均为初步；S5 的 +14.8% 究竟是种子交互还是 rate 效应，待 11/06 邻域探测裁决。

## 给 Lead 的建议（可选）

- 11/06 按手动版 5 发执行后，把新官方成绩落进 `runs/official_results.jsonl`，重跑 `python tools/official_analysis.py --plan` 即可自动出 11/07 候选。
- 若 11/06 的 rate22–26 官方读数明显差于 133.086（>5 s），说明「本地最优区≠官方最优区」，建议从 11/07 起切到自动版区域。
