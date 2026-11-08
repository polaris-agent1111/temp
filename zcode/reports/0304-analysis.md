# 0304 报告：全 5 发端到端闭环自适应实验归档与复盘模型构建

- 完成时间：2026-11-07 22:22
- 执行者：zcode
- 结论：**战前归档 + 可复跑复盘模型交付**。11/08 无任何真实出分，DRY-RUN 演练数据
  （118.1307 等）已三重指纹隔离、不入成绩档案。11/07 真实基线完整归档（出分锚与日志
  5/5 一致）；按 audit_plan 口径对 11/07 官方样本过门禁：全部 LOW_N（asym-fast14 另触发
  HIGH_CV 5.1%）→ 官方样本仅作分析、不作选型依据，反过拟合纪律在数据上验证成立。
  战后复跑脚本自动纳入 11/08 真实出分并补全决策链与门禁表。

## 具体动作

- 只读盘点 8 个数据源（submissions.jsonl / 两套控制器日志与 state /
  official_results.jsonl / 榜单快照类），逐个记录 mtime 与 staleness。
- 校验 11/07 硬编码出分锚与 `sequential_adaptive_log.jsonl` 的 `shot_k_scored`
  事件完全一致（5/5，零告警）。
- 编写并运行 `python -I zcode/scripts/archive0304_full_battle.py`：
  - 配额台账 SSOT 按日聚合（11/05:5, 11/06:5, 11/07:5，无超限）；
  - mock 隔离判定（DRY-RUN 指纹 + 当日佐证 0 条 → state 定性为演练档案）；
  - 按配置官方样本 + 忠实复刻 audit_plan.py 四门禁（min_n=3 / max_cv=5% /
    min<0.9·mean / NO_LOCAL_SAMPLE）；
  - 11/07 闭环决策链逐发复盘 + 11/08 控制器对 11/07 型输入的决策重放。
- 形成审计写入 `docs/analysis/0304-theory-audit.md`。

## 产出文件

- `zcode/scripts/archive0304_full_battle.py`（战后复跑即得完整战役档案）
- `zcode/scripts/archive0304_snapshot.json`（结构化归档快照，战前版）
- `docs/analysis/0304-theory-audit.md`
- 本报告 `zcode/reports/0304-analysis.md`

## 未完成/风险

- 「全 5 发端到端」复盘需 11/08 真实出分落盘后复跑脚本才能闭环（占位符已内置）；
- 11/07 官方样本全部门禁未过（LOW_N 普遍 + asym-fast14 HIGH_CV 5.1%），只能作分析数据；
- 榜单类数据源已过期（11/05–11/06），战后排名跃迁复盘需 Lead 端实时榜单，
  zcode 侧不拉网络（合规）；
- 11/07 型环境下控制器 4/5 发落防守/冲冠交替，绝杀窗口不触发——绝杀叙事成立
  以 Shot 1 锚点 ≤122.5s 为前提（与 0302 §4 一致）。

## 给 Lead 的建议

- 战后每发出分后复跑 `archive0304_full_battle.py` 即可自动归档，无需手工整理；
- 若 Shot 1 官方 ≥130s，按 0302 §4 提前把 Shot 4/5 预期转入防守口径；
- 复盘时对照本快照的 11/07 决策链教训：验证有效的构型应给第二次机会，
  未获官方校准点前不投极限外推构型。
