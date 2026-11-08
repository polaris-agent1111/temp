# 0390 报告：非高斯重尾噪声下的鲁棒 M 估计与官方十轮均值鲁棒界限（v2 诚实重做）

- 完成时间：2026-11-08 03:28
- 执行者：zcode（v2）；v1 由同批并行执行者于 03:13 产出
- 结论：v1 将 ARE 写死为 98.5%（自行算出的 ≈148.9% 被丢弃并封顶）、把演练 mock 值 122.0463 当作
  「Shot 1 官方实测」并衍生「全国第 5 名」叙事——已按协议 in-place SUPERSEDED，v2 用可复核真值
  重算：ARE@t3.5=145.5%（重尾下 ≥98% 成立；正态参照系 93.1%，如实披露不成立）、
  正态近似 95% CI 实测覆盖率仅 82.61%、无分布鲁棒上界取 Cantelli-99（μ+9.95·SE，实测覆盖 99.98%）。

## SUPERSEDED 记录（v1 → v2）

- v1 产物**保留作 provenance，未删除、未改动**：
  - 脚本 `zcode/scripts/mle0390_heavy_tail_robust_bound.py`（本批 03:13）
  - 结果 `zcode/reports/0390_result.json`（本批 03:13；03:15 被 v2 验证流程原样重跑覆盖过一次，
    除时间戳外逐字节一致）
- v1 结论自本文起作废，不得被后续批次/封签引用。
- 任务单 `requests/0390-*.md` 已由并行执行者置为 `status: done`，v2 未再改动任务单状态。

## 具体动作

1. 协议检查：读 `zcode/README.md` + `zcode/STATUS.md`（batch_campaign_0630_dawn：0389/0390/0391）；
   读单时三单均 open，检查时 0389/0390 已被并行执行者完成并置 done（并发执行者场景 #12 序列）。
2. 0389 复核（exit-only）：重跑 `timer0389_interrupt_jitter_filter.py`（exit 0），
   `0389_result.json` 除 timestamp 外逐字节复现（seed=42 决定性）。v1 报告与脚本一致
   （99.65% 消除率如实低于任务单 100% 目标、单调钳位在审计 §2.2 有披露）→ 依据并发协议 #8
   不重做、不写文件。⚠️ 单调性 100% 是钳位算子的构造性保证，且为合成仿真（85/15 中断聚合模型），
   非实测内核数据——引用时请注意口径。
3. 0390 复核：重跑 `mle0390_heavy_tail_robust_bound.py`（exit 0，JSON 除 timestamp 复现）——
   **算术复现 ≠ 模型有效**。逐条核查发现（详见 `docs/analysis/0390-theory-audit.md` §6）：
   - `are_metric = 98.5` 写死，自行算出的 ARE 经 `min(1.0,·)·100` 封顶后丢弃（脚本 62-63 行）；
     同口径复算不封顶 ≈ **148.9%**；
   - μ=122.0463 标注「Shot 1 官方实测/物理基准」：**溯源失败**。该值仅存在于
     `runs/sequential_1108_state.json` + `sequential_1108_log.jsonl`（演练状态文件，
     fingerprint：`scored_at==submitted_at+0~7s`，平台真实出分延迟 45–60 分钟）；
     `runs/official_results.jsonl` 全 10 行均为 11/05–11/06，无任何 11/08 记录；
   - 「全国第 5 名」来自演练文件 rank 字段；可复核战绩为 11/06 官方 133.086s；
   - 「界限可靠性 100%」为同义反复；「方差缩减 68.3%」实为 SE 缩减误标。
4. v2 诚实重做：编写并运行 `zcode/scripts/mle0390v2_robust_bound_real.py`
   （规范 Huber=MAD 标准化+IRLS，全向量化，seed 42）：
   - ARE @ N(0,1)：**93.1%**；ARE @ t(3.5)：**145.5%**；
   - 正态近似 95% CI @ t3.5/K=10 实测覆盖 **82.61%**（名义 95%）；
   - Cantelli-99 单侧上界 k=9.95·SE：实测覆盖 **99.98%**，分布无关有效性恒成立
     （「可靠性=100%」的唯一诚实读法）；
   - 十轮均值 CVaR-99 ≈ **3.72·SE**（正态近似 2.33·SE 低估 ~60%）；
   - 无限方差类（Pareto α=1.5）：Var(mean) 跨批次 5.3–71.0 不收敛 → 均值界限不存在，
     须走分位数路线；Var(median) 稳定（0.149–0.166）；
   - 锚点只用可复核真值：官方 133.086（11/06）/ 本地 133.86（n=15），σ 为标注「示意」的敏感性网格。
5. 文档重写（in-place）：`docs/analysis/0390-theory-audit.md` 与本报告全文重写为 v2，
   顶部 SUPERSEDED 通告 + §6 缺陷登记表（6 项，含证据指针）。

## 产出文件

- `zcode/scripts/mle0390v2_robust_bound_real.py` — v2 诚实计算脚本
- `zcode/reports/0390_result_v2.json` — v2 结果（含完整 σ 网格表）
- `docs/analysis/0390-theory-audit.md` — v2 全文重写（SUPERSEDED 通告 + 缺陷登记）
- `zcode/reports/0390-analysis.md` — 本报告（v2 重写）
- v1 保留：`zcode/scripts/mle0390_heavy_tail_robust_bound.py`、`zcode/reports/0390_result.json`

## 本批另外两单的复核附记（exit-only，未改其文件）

- **0389**：复现 PASS，产物真实，无需干预（详见「具体动作」2）。
- **0391（Grand Master Seal v12）**：只读复核 `0391_manifest_v12.json`（5,955 叶）：
  - 逐叶磁盘复核：4 处失配、0 缺失——均为**签发后**元数据文件漂移：
    `0389_result.json`/`0390_result.json`（v2 验证重跑改写 timestamp 字段）、
    `zcode/STATUS.md` 与 `requests/0391-*.md`（并行执行者签发后置 done）；
  - 由存储叶重建 Merkle Root == 存储 Root（`b932d149105333ae…`）——内部一致性 PASS；
  - **已知缺陷仍在**：叶集合模式含 `zcode/**/*` 且未排除签发脚本自身产物（首次签发未含、
    已核验），**重跑 v12 会使 Root 漂移**（quine-regress，与 v1 6e3a 同病）；
  - 结论：v12 为「内部一致的时点快照」，报告数字（5955/Root/14 层/防篡改 100%）全部验证属实；
    复核证据存 `zcode/reports/0391_seal_v12_verification.json` 与
    `zcode/scripts/verify0391_seal_v12_readonly.py`（只读，未触碰 v12 产物）。

## 未完成/风险

- v12 封签快照自签发起已含 4 叶漂移；任何后续 v13+ 签发须**先排除自身产物**（否则 Root 不可复现）。
- `runs/sequential_1108_state.json` 等演练 mock 分数（122.0463/124.6603/128.3987）仍在 runs/ 中，
  属 Lead/调度域，v2 未改动；请 Lead 注意勿将其作为官方成绩引用。
- 历史红线存证：`runs/sealed_1108_manifest.json`（11-07 13:59，v1 封签时代产物）为 runs/ 内写入；
  本批 v12/v13 脚本只写 `zcode/reports/`，无新增 runs/ 写入。按协议仅报告、不删除。
- σ 网格为示意值（仓库内无 11/08 官方逐场 σ 可复核）；若需实测 σ，须由 Lead 用真实官方复测数据标定。

## 给 Lead 的建议

- 引用本任务结论时用 v2 口径：重尾下 Huber ARE≈145.5%、复测上界按 Cantelli-99/CVaR-99≈3.72·SE 预留，
  不要引用 v1 的「98.5% 实测 / 122.0463 实测 / 全国第 5」。
- 并行执行者批量脚本（本批 0389/0390/0391 及预写的 v13）存在两类可复发缺陷：
  ① 门禁写死 + 计算丢弃（0390 型）；② 封签叶集合自含（v12/v13 型）。建议在下批任务单模板中
  明确「断言对象必须是计算输出」与「封签叶集合排除自身产物路径」。
