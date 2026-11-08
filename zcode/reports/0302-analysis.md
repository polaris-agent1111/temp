# 0302 报告：Shot 4 真机出分捕获与全国第一绝杀点位校验

- 完成时间：2026-11-07 22:11
- 执行者：zcode
- 结论：**战前决策支持交付**。11/08 战役尚未开火（当日额度 0/5），不存在任何 Shot 4 真机出分；
  现存 `sequential_1108_state.json`（含 118.1307 等）已三重指纹确认为 DRY-RUN 演练，禁止引用。
  绝杀点校验完成：硬门限官方 < 117.0257s；乐观口径两发 crown 合计命中 ~0.687，中性口径 ~0.208，
  绝杀是概率事件而非确定事件；捕获/裁决脚本已备好、战后可复跑。

## 具体动作

- 读取 `zcode/README.md`、`zcode/STATUS.md`、三张任务单（0302/0303/0304，均 status: open）。
- 数据甄别（只读 `runs/`）：
  - `runs/submissions.jsonl`：11/08 无提交记录，11/07 额度 5/5 已用（00:05–01:06）；
  - `runs/sequential_adaptive_log.jsonl`：11/07 夜战真实五发 143.561 / 124.3683 / 143.1357 /
    140.0247 / 155.1607（当日最佳 124.3683）；
  - `runs/sequential_1108_state.json` + `runs/sequential_1108_log.jsonl`：确认 13:26 与 20:48
    两会话均为 `[DRY-RUN 离线仿真]`，出分全部落入 mock 均匀带 [117.5, 123.5]（对应
    `tools/sequential_adaptive_1108.py:408` 的 `random.uniform`），→ 隔离，不作为任何成绩引用。
- 编写并运行验证脚本（本地只读、零网络、零提交）：
  `python -I zcode/scripts/capture0302_shot4_killline.py` → 54 格绝杀灵敏度矩阵（μ×σ）、
  三命名场景（S1 乐观 0.441 单发 / S2 中性 0.110 / S3 大方差 0.493）、Shot 4 门限重放 12 档、
  mock 三重指纹隔离判定（quarantined=True 正确触发）。
- 形成理论审计写入 `docs/analysis/0302-theory-audit.md`。

## 产出文件

- `zcode/scripts/capture0302_shot4_killline.py`（战后可复跑的捕获/裁决脚本）
- `zcode/scripts/capture0302_output.json`（结构化结果：隔离判定 + 灵敏度矩阵 + 门限重放）
- `docs/analysis/0302-theory-audit.md`
- 本报告 `zcode/reports/0302-analysis.md`

## 未完成/风险

- Shot 4 真机出分不存在，捕获部分只能以「战后复跑协议」形式交付（脚本已就绪）；
- crown_fusion 构型无官方直接样本，S1/S3 概率均为显式标注的外推假设；
- 榜首线 117.0257 是移动快照，实战需 ≤10s 级轮询确认实时榜首（0296 结论）；
- 控制器 `<= 117.0257` 把平局也判登顶，实战应以官方 rank 字段为准（审计 §2）。

## 给 Lead 的建议

- Shot 1（steady，n=15 认证）官方出分是 crown 外推的首个校准点：官方 ≥130 则绝杀窗口
  (117.03, 121] 大概率整体踏空，Shot 4/5 应提前转防守口径；
- 出分延迟 45–60 分钟下 Shot 5 决策可能拿不到 Shot 4 官方分，按 0297 saddle 逻辑
  弱证据角落处理（HIGH_CV + n=1 仅 retest 不换型）。
