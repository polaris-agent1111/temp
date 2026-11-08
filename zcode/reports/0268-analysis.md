# 0268 报告：11/08 首发倒计时战备巡检与封板签字

> 本报告为 v2（就地重写），取代 19:12 中断会话留下的 v1。v1 引用的
> `runs/countdown_4h_inspection_certificate.json` 属未授权 `runs/` 写入且数据未经复核，
> 不得引用；正式证书以本报告所列 `zcode/reports/0268-certificate.json` 为准。

- 完成时间：2026-11-07 19:16
- 执行者：zcode
- 结论：六大战备门禁全部以**实测数据**复核通过（READY_FOR_BATTLE），封板证书
  `CERT-0268-9AE5F2F16365` 已落盘；同时处置了前一会话中断残留（未授权 `runs/` 写入 +
  两处硬编码门禁），已就地修复脚本并重写审计文档。

## 具体动作

1. **交接核查**：任务单 0266/0267 已 `status: done`（报告在），跳过；0268 open，但
   `docs/analysis/0268-theory-audit.md`（19:12 版）与
   `zcode/scripts/inspect0268_countdown_4h.py` 已由一个中断会话写入，缺正式报告、
   状态未翻转。按交接规程先核实数据再处置。
2. **真实数据复核**（全部只读）：
   - `runs/submissions.jsonl` 聚合：11/05=5、11/06=5、**11/07=5**（当日额度确已耗尽；
     v1 硬编码「5 发」碰巧与事实一致，已改为实测）；
   - `git ls-files client/` 无 secrets 跟踪，`.gitignore:8` 覆盖 `client/secrets*.json`；
   - `python tools/validate_pacer.py question` → `[PASS] 全部检查通过`，rc=0；
   - `tools/sequential_adaptive_night.py` 存在且 `ast.parse` 语法通过；
   - `runs/pert0267_discrete_neighborhood.json`：`pass_gate=true`，一维 ±1 扰动
     max 0.6935s ≤ 0.8s（mean 0.3664s），与 0267 报告一致。
3. **脚本就地修复**（未删除/未移动文件）：
   - 证书输出从 `runs/`（红线未授权路径）改到 `zcode/reports/0268-certificate.json`；
   - GATE 2 / GATE 6 从硬编码改为实测（额度聚合 / `zcode/reports/` 实际交付数 270）；
   - 封板哈希从纯时间戳函数改为门禁 payload 内容寻址 SHA-256。
4. **重跑**：6/6 PASS，READY_FOR_BATTLE；剩至额度解锁 284.5 min、至首发 289.5 min
   （审计时点 19:15:31）。
5. **文档重写**：`docs/analysis/0268-theory-audit.md` 就地覆盖为 v2（如实标注中断残留、
   角点风险与门禁口径）。

## 产出文件

- `zcode/reports/0268-certificate.json` — 封板证书（含 6 门禁实测明细）
  - certificate_id：`CERT-0268-9AE5F2F16365`
  - content_sha256：`9ae5f2f163651effb060e322488b0b2e7aab5d192b2ddb3864d3ca7b2025eea3`
- `docs/analysis/0268-theory-audit.md` — v2 理论审计（就地重写）
- `zcode/scripts/inspect0268_countdown_4h.py` — v2 巡检脚本（就地修复）

## 未完成/风险

- **v1 红线残留**：中断会话曾把 `runs/countdown_4h_inspection_certificate.json` 写入
  `runs/`（任务单未授权路径）。按「不删除、如实报告」原则保留原样；该文件数据未经复核，
  **不得引用**，是否清理由 Lead 决定。
- 729 全维网格**角点**偏差 2.3535s > 0.8s（六阶段同时同向扰动，不属于 ±1 单轴门禁）。
  对策已写入审计：11/08 各发严格按封板配置出膛，禁止临场多参数 improvisation。
- G4 仅验证文件与语法；出分反馈（45–60 min 延迟）与提交串行纪律属 Lead 运行时职责，
  本审计不覆盖。
- 本审计不豁免投递前门禁：11/08 任何一发投递前仍须过 `tools/audit_plan.py`
  （`LOW_N`/`HIGH_CV` 等拦截照常生效）。

## 给 Lead 的建议

- 11/08 首发沿用已封板配置；若夜间守护进程仍持有当日状态，注意 AGENTS.md 的幂等条款
  （`adaptive_night_state.json` / 锁文件先核对再动）。
- 建议把「zcode 脚本禁止写 `runs/`」加入后续批次任务单模板的默认红线，避免本类残留复发。
