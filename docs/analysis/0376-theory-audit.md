# Task 0376: Grand Master Seal v7 理论审计（v2）

> v2 修订说明：v1（2026-11-08 02:43 并行执行者草稿）的 Merkle 构造正确但存在三处问题：(1) 根哈希不可复验（封签输出自身未排除，先哈希后写自身导致复跑根漂移）；(2) 资产表为手写估计值；(3) 「今日官方战绩锁定」把三个未经证实的分数当作事实签发。v2 原地更正。

## 1. 密码学规范（可复验构造）

- **叶子**：每个资产文件的 SHA-256 内容哈希（64KB 分块流式）。
- **排序**：叶子按十六进制哈希字符串升序排序后两两规约（与 v1 一致）。
- **规约**：`parent = SHA-256(left_hex + right_hex)`；奇数个节点时末位与自身配对（duplicate-last）。
- **自洽性（v2 新增）**：封签输出 `zcode/reports/0376_result.json` 不入叶集——否则「先哈希后写自身」使根随每次复跑漂移，任何人无法复验。此与区块头不含自身交易集同理。
- **权威根哈希**：以 `zcode/reports/0376_result.json` 中 `merkle_root` 字段为准（本文档不内嵌根值，避免文档自引用的无穷回归）。复验方法：仓库内容不变时运行 `python -I zcode/scripts/seal0376_grand_master_seal_v7.py`，输出根与 result JSON 记录一致即通过。

## 2. 封签范围与真实资产明细（4,888 项，2026-11-08 02:57 快照）

> 本仓库存在并行写入（0377+ 批次执行者），封签是**时点快照**：权威资产数与根以 `zcode/reports/0376_result.json` 的最终一次运行为准；仓库内容再变即需重签。

| 类别 | 数量 |
| :--- | ---: |
| `runs/`（submit_plan_*.json、submissions.jsonl、sequential_1108_state.json、configs/**/pacer.txt） | 3,226 |
| `zcode/`（requests/reports/scripts） | 1,117 |
| `docs/`（analysis/knowledge/extracted 等全部 .md） | 375 |
| `tools/`（.py） | 95 |
| `hourly/`（.md） | 49 |
| `configs/`（**/*） | 13 |
| `client/` + `harness/`（.py） | 10 |
| `PLAN.md` + `README.md` + `STATUS.md` | 3 |
| **合计** | **4,888** |

树深验证：4,888 → 2,444 → 1,222 → 611 → 306 → 153 → 77 → 39 → 20 → 10 → 5 → 3 → 2 → 1，共 **14 层**（与 ⌈log₂4888⌉+1 = 13+1 = 14 一致）。

**范围外（未封签）**：`tests/`、`question/`、`docs/` 非 .md 文件、其余 `runs/` 数据文件（results.jsonl、session 等），以及**刻意排除**的 `client/secrets.json` 与 `runs/.session.pkl`（凭据类文件不入任何清单）。

## 3. 防篡改性质的严格表述

- **结构性防篡改（严格）**：在 SHA-256 抗碰撞假设下，任何被封文件内容的任何改变都使其叶哈希以压倒性概率改变，并沿树传播至根 → **根必变**。这保证「根一致 ⇒ 全部 4,884 项内容未变（以压倒性概率）」。
- **敏感性测试（抽样）**：单叶子内容置换 1/1 检出（`tamper_test_scope` 字段）。这是演示性测试，不是穷举证明；穷举不可能，严格结论由上一条的抗碰撞性质给出。

## 4. 「今日战绩」的证据链审计（v2 核心修正）

| v1 声称 | 地面真值核对结果 | 结论 |
| :--- | :--- | :--- |
| Shot 1: 122.0463s（全国第 5，超越大肥鱼 122.4027s） | 唯一来源 `runs/sequential_1108_state.json`；`official_results.jsonl` 无 11-08 条目；`board_watch.jsonl`/`leaderboard_full.json` 无此分数，「大肥鱼 122.4027」无任何快照佐证 | **UNVERIFIED** |
| Shot 2: 124.6603s | 同上；且该 state 文件 11/07 版已被识别为演练 mock（记忆指纹） | **UNVERIFIED** |
| Shot 3: 128.3987s | 同上 | **UNVERIFIED** |
| 配额「严格锁定 3/3 发」 | `runs/submissions.jsonl` 今日 3 条 `submitted` 属实；但平台日配额是 5 发（AGENTS.md），v1 的 `max: 3` 是战役上限（state 文件 `max_allowed_shots`）而非平台配额 | 提交属实，口径已修正 |

**UNVERIFIED 的三条独立依据**：(1) `scored_at = 提交后 0~7s`（Shot1 同秒）与平台已知的 45–60 分钟出分延迟物理矛盾；(2) 本地所有可读榜单/出分数据源均无佐证；(3) 写入该 state 的 `tools/sequential_adaptive_1108.py` 自带 `--dry-run` mock 出分器（`random.uniform` 生成 mock_score），state 文件自身无法证明其产生模式。**v1 已删除硬编码分数字段**；封签只对「已投 3 发」这一可验证事实负责，不对出分负责。
