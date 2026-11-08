# 0286 报告：11/08 首发出征倒计时 1 小时战备总动员与五发参数终审会签

- 完成时间：2026-11-07 20:31
- 执行者：zcode
- 结论：**七道门禁全部实测通过，战备评定 READY_FOR_FIRST_SHOT**；五发封板配置树
  SHA-256 内容寻址会签完成，证书 `CERT-0286-1H-2AA6DDC0AC590449`（对门禁结果
  规范 JSON 做内容寻址，非时间戳哈希）。审计时点 T−208.3 min（早于字面 1 小时
  窗口，按实际派发时点如实记录）。A1/A2 两发为本地零样本新构型，已如实披露，
  本证书不豁免 Lead 投递前的自有 `audit_plan.py` 门禁。

## 具体动作

1. 从 `runs/master_battle_ready_certificate.json` 读取五发 SSOT 名单（非硬编码）。
2. G1：五棵配置树逐文件 SHA-256 → 树摘要；解析 pacer.txt 核对 `[timestamp:N]` 与
   名称↔内容一致性（leak 速率序列 / 精确速率 / cap-interval）——初跑发现 A2 误报
   系本脚本期望值逻辑缺陷（"96M-both" 应为两阶段同速率），核实真实内容正确后
   修复脚本重跑，五树全 ✓。
3. G2：`validate_pacer.py` 离线跑五棵树，rc 全 0。
4. G3：聚合 `runs/submissions.jsonl` 的 `date` 字段（不读 GUID/note）：11/07=5
   耗尽、11/08=0 未动用。
5. G4：读 0267 邻域工件：pass_gate=true、±1 单轴 max_abs_diff 0.6935s ≤ 0.8s。
6. G5：`sequential_adaptive_night.py` 存在 + ast.parse 通过。
7. G6：`git check-ignore client/secrets.json` rc=0、无 secrets 被跟踪；全程未读凭据。
8. G7：按配置名精确匹配统计本地样本：A1 n=0、A2 n=0、crown n=15 (135.48s,
   CV 6.86%)、40x3 n=3 (144.52s)、leakc-36 n=2 (129.87s)——如实写入披露表。
9. 证书 = 七门禁结果规范 JSON 的 SHA-256 内容寻址，落盘 `zcode/reports/`。

## 产出文件

- `zcode/scripts/cert0286_1h_mobilization.py`（可重跑）
- `zcode/scripts/cert0286_results.json`（门禁全量结果）
- `zcode/reports/0286-certificate.json`（正式证书）
- `docs/analysis/0286-theory-audit.md`（审计文档）

## 未完成/风险

- A1/A2 零本地样本：audit_plan.py 会以 NO_LOCAL_SAMPLE/LOW_N 拦截，投递前须 Lead
  自行决断（本证书不豁免）。
- `runs/countdown_{2h,4h,8h}_inspection_certificate.json` 为历史 v1 残留，未复核，
  不得引用；`runs/` 本会话零写入（未删除、未修改）。
- master 证书中 0.9192 胜率未经验证（与 0235 估计 11–18% 矛盾），本证书不携带
  任何胜率声明。
- 出分延迟、5 发/日、60 分钟不重投等运行时纪律无法本地验证，属 Lead 闭环职责。

## 给 Lead 的建议（可选）

- 若 11/08 现场按名单顺序出膛，建议首发窗口前 30 分钟重跑本脚本一次
  （`python -I zcode/scripts/cert0286_1h_mobilization.py`），证书哈希会随门禁
  数据自动刷新，任何漂移立即可见。
