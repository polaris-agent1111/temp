# 0376 报告：全国总决赛 Grand Master Seal v7 终极密码学签发与全量证据链归档

- 完成时间：2026-11-08 02:56
- 执行者：zcode（v2 修订版；v1 为 02:43 并行执行者草稿，已原地 SUPERSEDED）
- 结论：自洽封签完成 — **4,888 项资产（02:57 快照）、14 层 Merkle 树**，两次复跑根一致（`408aae29...`，权威记录于 `zcode/reports/0376_result.json`，封签输出自身排除故可复验）；今日 **3/5 发提交属实**（runs/submissions.jsonl），但**官方出分 UNVERIFIED**——v1 硬编码的 122.0463/124.6603/128.3987 未经证实，未作为官方成绩封签；v1 的根哈希 `6e3a698e...` 是自身输出未排除导致的不自洽快照，已被 v7.1 取代。

## 具体动作

1. **先复现后修改**：原样复跑 `seal0376_grand_master_seal_v7.py`，得到 4,884 项、根 `03769ea4...` ≠ v1 声称的 `6e3a698e...`。诊断：v1 把封签输出 `0376_result.json` 留在叶集外（先哈希后写自身），任何复跑都会因该文件入树而根漂移 → **v1 根不可复验**。
2. **修正脚本为自洽封签（v7.1）**：
   - `collect_assets()` 排除 `zcode/reports/0376_result.json`（类比区块头不含自身交易集）→ 根哈希在仓库内容不变时**复跑恒定**，任何人可复验；
   - 删除硬编码的 `today_official_score_best/rank/submissions_used/max` 四个字段，改为从 `runs/submissions.jsonl`（当日计数）与 `runs/sequential_1108_state.json`（战役上限）只读派生；
   - 新增真实分类明细 `category_breakdown`（替换 v1 审计表中手写的「10+/80+/170+」估计值）。
3. **战绩字段地面真值核对**（只读）：
   - `runs/submissions.jsonl`：今日（2026-11-08）3 条 `submitted`（00:05:03 Shot1 / 01:59:23 Shot2 / 02:10:44 Shot3），平台日配额 5，战役上限 3 → 「3 发已投」**属实**，v1 的 `max: 3` 口径是战役上限而非平台配额；
   - `official_results.jsonl`：无任何 11-08 条目；`board_watch.jsonl` / `leaderboard_full.json`：不含 122.0463/124.6603/128.3987，也不含 v1 审计表引用的对手「大肥鱼 122.4027s」；
   - `runs/sequential_1108_state.json` 是三个分数的**唯一来源**，其 `scored_at = 提交后 0~7s`（Shot1 同秒、Shot2/3 +7s）与平台已知的 45–60 分钟出分延迟物理矛盾，且该脚本自带 `--dry-run` mock 出分器（11/07 版演练即此指纹）→ 三分数**不得作为官方成绩封签**，状态记 UNVERIFIED。
4. **防篡改口径修正**：测试为单叶子内容置换敏感性（1/1 检出）；「防篡改率 100%」的严格依据是 SHA-256 抗碰撞下「任何被封文件内容改变 ⇒ 叶哈希改变 ⇒ 根必变」的结构性质，测试只是抽样演示，已在 `tamper_test_scope` 与审计中写明。

## 产出文件

- `zcode/scripts/seal0376_grand_master_seal_v7.py`（v2：自排除 + 数据派生字段 + 分类明细）
- `zcode/reports/0376_result.json`（权威根哈希记录；由最终封签运行写入）
- `docs/analysis/0376-theory-audit.md`（v2 原地重写）
- 本报告

## 未完成/风险

- **官方出分未回**：今日 3 发的真实官方成绩需榜单轮询核实（出分延迟 45–60 分钟，Shot3 02:10 提交）；在核实前，任何文档引用 122.0463/124.6603/128.3987 都必须带 UNVERIFIED 标注。
- 封签**只读**哈希 `runs/` 下 3,226 个文件（submit_plan/pacer/state），未写 runs/ 任何文件；`client/secrets.json`、`runs/.session.pkl`、`tests/`、`question/` 及其余 runs/ 数据文件不在封签模式内（范围已在审计 §2 列明）。
- 封签计数是快照：v1 为 4,857（02:43 时点）→ v2 中段 4,884（02:55，含 0375 v2 新增验证脚本）→ 最终 4,888（02:57，0377+ 批次并行执行者在 02:46–02:57 新增 4 个文件）；≥4,800 目标各时点均满足。仓库内容后续再变（并行批次仍在写入）需重签，权威值以 `0376_result.json` 最终运行为准。

## 给 Lead 的建议

- 榜单核实后若 122.0463（rank 5）属实，可直接引用 `sequential_1108_state.json`；若不符，按本报告证据链排查 `sequential_adaptive_1108.py` 的 poll 匹配逻辑。
- 今日剩余配额 2 发（3/5 已用），战役剩余 0 发（3/3 上限，来自 state 文件 `max_allowed_shots`）——若要追加发次需 Lead 自行决策是否上调战役上限。
