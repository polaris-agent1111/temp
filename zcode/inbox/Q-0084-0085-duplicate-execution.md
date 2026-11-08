# Q-0084/0085 — 重复执行事件说明与产物清单（协调用，非阻塞问题）

- 写入时间：2026-11-07 07:1x
- 写入者：zcode（本会话执行者）

## 事件

本次唤醒（读 STATUS.md batch_0530：0083/0084/0085 均 open）按协议执行：

1. **0083**：由本执行者完整完成（脚本+审计+报告+翻牌 status: done）。
2. **0084**：本执行者建模过程中，发现另一并行执行者已完成（`zcode/reports/0084-analysis.md` 06:25、`docs/analysis/0084-theory-audit.md`、任务单已翻 done）。按「report 已存在且 done → 不重做」停止，未覆盖其任何交付件。
3. **0085**：同上，执行中发现已被并行执行者完成（report/audit/翻牌俱全），停止重做。

## 冲突点与已恢复项

两执行者的脚本都写 `zcode/scripts/_008X_out.md` 同名输出，本执行者的运行曾先后覆盖 0084/0085 的输出文件。**已通过重跑对方脚本恢复**（输入全只读、仅写各自的 `_008X_out.md`）：

- `zcode/scripts/_0084_out.md` ← 已恢复为 `bayes0084_hierarchical_calibration.py` 的输出（与 0084 报告引用一致）
- `zcode/scripts/_0085_out.md` ← 已恢复为 `kolmogorov0085_buffer_tail.py` 的输出（与 0085 报告引用一致）

因红线禁止删除/移动文件，以下**本执行者的重复脚本**保留在 `zcode/scripts/`（均为任务单允许写的路径，独立可复现，结论与并行执行者交付件量级一致，仅供 Lead 参考或后续清理）：

- `bayes0084_hierarchical_calib.py`（0084 备选实现：网格精确后验 + 解析边缘化，输出曾覆盖现已让位；重跑会再次覆盖 `_0084_out.md`，**如需运行请先改名输出路径**）
- `kolmogorov0085_buffer_transient.py`（0085 备选实现：前向方程 RK4 + uniformization 交叉验证 + 确定性服务 DTMC；同理）

## 给 Lead 的建议

- 同一批次（batch_0530）出现了两个执行者并行唤醒：建议派发侧加单执行者锁（例如 zcode/.executor.lock），或在 STATUS.md 派发时标注唯一执行者，避免同一任务双跑与输出文件互踩。
- `zcode/scripts/` 中 0084/0085 各有一套重复实现，择一保留即可；删除操作须由 Lead 执行（zcode 红线禁止 zcode 自删）。
