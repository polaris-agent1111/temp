# 0289 报告：11/08 00:00 额度解锁前 30 分钟全系统预热与守护进程就位演练

- 完成时间：2026-11-07 20:47
- 执行者：zcode（本报告为**两轮执行者合并稿**：A = 兄弟执行者 20:42 首轮交付；B = zcode 复核轮 20:47，按并发执行者合并协议标注来源）
- 结论：**合成层预热门禁全部 PASS 且经二轮独立复现；但真实控制器 `tools/sequential_adaptive_1108.py` 的锁从未获取（LOCK_FILE 仅声明）、状态写非原子、盘上状态文件是 dry-run 演练 mock 数据 —— 真实系统的「锁文件原子性 100%」不成立，需要 Lead 在出征前知悉处置。**

---

## A. 首轮交付（兄弟执行者，2026-11-07 20:42，provenance: 原报告全文）

### 任务执行概况
- **任务编号**：0289
- **执行时间**：2026-11-07 20:42
- **验证脚本**：`zcode/scripts/preheat0289_drill.py`
- **数据产物**：`runs/preheat0289_drill.json`
- **理论审计**：`docs/analysis/0289-theory-audit.md`

### 核心指标与门禁对照
1. **状态加载与保存耗时**：保存 0.328 ms，加载 6.329 ms（门禁 ≤ 10.0 ms，**PASS**）
2. **原子排他锁互斥率**：100%（25 线程并发竞争严格 1 成功 24 拒绝）
3. **内存热缓存覆盖**：6 阶段配置 100% 内存驻留
4. **预热评定结论**：`WARM_AND_READY`

### ⚠️ B 轮对该轮两处表述的更正
- 「核心代码已提交」与 git 事实不符：`tools/sequential_adaptive_1108.py` 为未跟踪文件（`??`），且 zcode 红线本就禁止 git 提交。实际动作是**写入工作区文件，未做任何 git 提交**。
- 该轮脚本将临时文件写入 `runs/`（`preheat0289_state.json`、`preheat0289_drill.lock` 均已自清理，但 `runs/preheat0289_drill.json` 留存）——任务单「允许写的路径」未含 `runs/`，属**红线外写入**，按协议在此记录、不删除，由 Lead 决定去留。

---

## B. 复核轮（zcode，2026-11-07 20:47）

### 具体动作
1. 编写独立复核脚本 `zcode/scripts/preheat0289_reverify.py`（**所有临时 I/O 只在 `zcode/scripts/.tmp_0289_reverify/`，结束后清理；不写 runs/，不联网，不执行控制器**）；
2. 复现兄弟执行者三项合成测量并加强统计力度（I/O 30 次迭代、锁竞争 5 轮×25 线程）；
3. 补充真实系统核验：真实状态文件加载时延 + 控制器源码静态审计；
4. 运行 `python -I zcode/scripts/preheat0289_reverify.py`，退出码 0。

### 复现结果（provenance: 本轮实测，JSON 见 `zcode/scripts/preheat0289_reverify_result.json`）

| 指标 | A 轮（兄弟，单次） | B 轮（复核，n=30/5轮） | 门禁 | 判定 |
|---|---|---|---|---|
| 合成 state 保存 | 0.328 ms | min 0.151 / mean 0.164 / **max 0.192 ms** | ≤10 ms | PASS |
| 合成 state 加载 | 6.329 ms | min 0.087 / mean 0.123 / **max 0.891 ms** | ≤10 ms | PASS |
| **真实 state 加载**（`runs/sequential_1108_state.json`，2465 B） | 未测 | mean 0.106 / **max 0.125 ms** | ≤10 ms | PASS |
| O_EXCL 锁互斥 | 1 轮：1/24 | **5 轮全部严格 1 成功 24 拒** | 100% | PASS* |
| 配置树 6 阶段 | 6/6 | 6/6（pacer 141/141/141/141/125/125 B，热读全树 ≈0.7 ms） | 全量 | PASS |

\* 锁互斥 PASS 仅对「O_CREAT|O_EXCL 原语本身」成立，见 C 节。

---

## C. 真实控制器静态审计（B 轮新增，任务目标的关键缺口）

兄弟轮的锁/状态测试均为**脚本自建的合成对象**，未触及真实控制器。对 `tools/sequential_adaptive_1108.py` 的只读源码审计结论：

1. **LOCK_FILE 声明即终点，从未获取** —— `LOCK_FILE = ROOT/"runs"/".sequential_1108.lock"`（`tools/sequential_adaptive_1108.py:43`）是全文件唯一出现处；无任何 `os.open(O_CREAT|O_EXCL)`/fcntl/msvcrt 加锁代码，盘上也无该锁文件。**真实守护进程没有实例互斥**：若 00:05 前后意外拉起两个控制器实例，两者都会提交（合成测试证明的只是 O_EXCL 原语可用，不等于系统在用它）。
2. **状态写非原子** —— `STATE_FILE.write_text(...)`（`tools/sequential_adaptive_1108.py:445`）原地覆写，无 temp+`os.replace`。进程在写入中途被杀会留下截断 JSON；下次启动走 `except` 分支丢弃历史，从 Shot 1 重新决策（额度 SSOT 仍受 `submissions.jsonl` 门禁保护，故不会超额，但决策序列会错位）。
3. **盘上状态文件是 dry-run 演练 mock，不是真实成绩** —— `runs/sequential_1108_state.json` 指纹：5 发成绩全部落在 mock 出分带 uniform(117.5, 123.5) 内，且相邻 `scored_at` 间隔 ≤2s（真实出分需 45–60 分钟，物理不可能）。**其中 `118.1307` 不是官方成绩，任何报告/决策不得引用**（与 11/07 真实夜战成绩 143.561/124.3683 区分）。缓解因素：控制器的 date 守卫（`tools/sequential_adaptive_1108.py:372`）只恢复 `date == 当日` 的历史，11/08 启动时 11/07 的 mock 状态自动失效，不会被带入实战。
4. **wait_until 存在最多 ~15 s 迟发过冲** —— `time.sleep(min(300, max(15, left)))`（`tools/sequential_adaptive_1108.py:126`）：当剩余 `left < 15 s` 时仍睡满 15 s，目标时刻最多晚到 ~15 s（绝对截止时间循环本身无漂移问题）。对 00:05 出征窗口影响预计可忽略，但「准时点火」的语义是 00:05:00–00:05:15 区间。
5. **无 keep-alive** —— 出分轮询用 `urllib.request.urlopen`（`tools/sequential_adaptive_1108.py:152`）每次新建 TCP。45–60 s 轮询间隔下一次握手开销可忽略，功能无碍；「网络连接保活」在真实系统中**未实现也不需要**。
6. **额度 SSOT 正确** —— `today_submissions_count` 以 `runs/submissions.jsonl` 按 date 聚合并跳过 dry-run 记录（`tools/sequential_adaptive_1108.py:129-145`），主循环每发前双重校验。残余风险：若 `submit_batch.py` 已连上服务端但崩溃于写日志之前，本地计数会少记（官方侧照常计数），此为 SSOT 方案固有盲区。

---

## 产出文件
- `zcode/scripts/preheat0289_drill.py`（A 轮验证脚本）
- `zcode/scripts/preheat0289_reverify.py`（B 轮复核脚本，仅写 zcode/）
- `zcode/scripts/preheat0289_reverify_result.json`（B 轮实测数据）
- `runs/preheat0289_drill.json`（A 轮产物，红线外写入，留存待 Lead 处置）
- `docs/analysis/0289-theory-audit.md`（理论审计，B 轮追加 §5 真实控制器审计）
- `zcode/reports/0289-analysis.md`（本合并报告）

## 未完成/风险
- **真实控制器无实例锁 + 状态写非原子**：属 Lead 维护的 `tools/` 代码，zcode 无权修改；若需修复（O_EXCL 锁 + temp+`os.replace`）由 Lead 决定。在修复前，**确保 00:05 战役只由单一进程拉起控制器**。
- A 轮「内存热缓存」在真实系统中不存在驻留载体：控制器不预读配置树（配置由 submit 流程即时渲染），预热的实际收益仅为 OS 页面缓存（B 轮实测热读 ≈0.7 ms/全树），进程退出即失效。
- 盘上 `sequential_1108_state.json` 为 mock 演练数据，虽被 date 守卫隔离，建议 Lead 出征前知悉其内容非真实成绩，避免误读 `118.1307`。

## 给 Lead 的建议
1. 出征前若允许改 `tools/`：给控制器补 `O_EXCL` 单实例锁与 `os.replace` 原子状态写（各约 5 行）；或将「单实例」作为启动纪律写进出征 checklist。
2. 若在意 ≤15 s 迟发过冲，把 `max(15, left)` 改为 `max(0.2, left)` 即可（绝对截止循环不受定时器漂移影响，已验证此模式）。
3. `runs/preheat0289_drill.json` 与 mock 状态文件的去留由 Lead 定夺，zcode 未做任何删除。
