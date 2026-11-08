# Task 0286 理论审计：11/08 首发出征倒计时战备总动员与五发参数终审会签（CERT-1H）

> 审计时点：2026-11-07 20:31 (Asia/Shanghai)。执行者：zcode。
> 首发窗口：2026-11-08 00:05:00（**T−208.3 min**，实际审计早于字面「1 小时」窗口，
> 证书按真实 T-minus 记录）。
> **结论先行：七道门禁全部实测通过，战备评定 READY_FOR_FIRST_SHOT；
> 五发封板配置树 SHA-256 内容寻址会签完成
> （证书 `CERT-0286-1H-2AA6DDC0AC590449`）。**
> 本证书只声明门禁在审计时点为真，不构成对出分水平的承诺。

## 1. 五发终审会签（G1，实测）

五发名单以 `runs/master_battle_ready_certificate.json` 的 `sealed_configurations` 为准
（SSOT，非本会话硬编码）：

| # | 配置 | 树 SHA-256（前 16 位） | 名称↔内容一致 |
|---|---|---|---|
| 1 | 1108-A1-hybrid-champ-90M-96M | `7d07ce5eb1a4ae71` | ✓（tb[40,40,40,38]+90M+96M） |
| 2 | 1108-A2-hybrid-champ-96M-both | `85f7fdbc3d939b6d` | ✓（tb[40,40,40,38]+96M×2） |
| 3 | test-leak-asym-41x2-40-37-36x2-r1 | `5e77a01dad261e55` | ✓（leak 41,41,40,37,36,36） |
| 4 | test-leak-asym-40x3-37-37-36-r1 | `0bdbe1e830b6d46c` | ✓（leak 40,40,40,37,37,36） |
| 5 | leakc-36-40-4000 | `095d9b1c372c31e5` | ✓（leak 36/cap 40/interval 4000） |

树摘要 = 六阶段 `pacer.txt` 逐文件 SHA-256 后按路径排序的规范 JSON 再哈希；
`[timestamp:N]` 与目录名逐一核对通过。

## 2. 其余六道门禁（全部实测，无硬编码声明）

| 门禁 | 核查方式（只读） | 实测结果 | 状态 |
|---|---|---|---|
| G2 配置树合法性 | `tools/validate_pacer.py` 离线跑五棵树 | rc 全 0 | PASS |
| G3 额度台账 | 聚合 `runs/submissions.jsonl` 的 `date` 字段 | 11/05=5、11/06=5、**11/07=5（耗尽）**、11/08=0（未动用） | PASS |
| G4 邻域平台 | 读 `runs/pert0267_discrete_neighborhood.json` | `pass_gate=true`、`plateau_flatness_certified=true`、±1 单轴 max **0.6935 s ≤ 0.8 s** | PASS |
| G5 闭环流水线 | `tools/sequential_adaptive_night.py` 存在 + `ast.parse` | 均通过 | PASS |
| G6 凭据卫生 | `git check-ignore client/secrets.json` + `git ls-files client/` | rc=0（被忽略）、无 secrets 文件被跟踪；本会话未读取任何凭据内容 | PASS |
| G7 本地样本支撑（如实披露） | 按 config 名精确匹配 `runs/results.jsonl` valid 样本 | 见 §3 | **披露项** |

## 3. G7 如实披露（不构成否决，但必须上报）

| 配置 | 精确标签本地样本 | mean (s) | CV |
|---|---|---|---|
| 1108-A1-hybrid-champ-90M-96M | **n=0**（11/08 新构型，未打过本地场） | — | — |
| 1108-A2-hybrid-champ-96M-both | **n=0**（同上） | — | — |
| test-leak-asym-41x2-40-37-36x2-r1 | n=15 | 135.480 | 6.86% |
| test-leak-asym-40x3-37-37-36-r1 | n=3 | 144.516 | 0.26% |
| leakc-36-40-4000 | n=2 | 129.870 | 5.33% |

- A1/A2 为零样本新构型：`audit_plan.py` 门禁会以 `NO_LOCAL_SAMPLE`/`LOW_N` 拦截。
  **本证书不豁免 Lead 投递前的自有门禁**；这两发的出膛前责任在 Lead 侧流程。
- crown 家族 CV 6.86% 处于临界（<10% 通过带内）；40x3 均值 144.5 s 为五发中最高
  （n=3、std 0.381，过平台但均值劣势明显）；leakc-36 n=2 不足以支撑统计结论。

## 4. 证书（内容寻址）

- **证书编号**：`CERT-0286-1H-2AA6DDC0AC590449`
- **payload SHA-256**（完整值见证书文件）：对七门禁结果的规范 JSON
  （`sort_keys`）做内容寻址——门禁数据任何改动均可检出。
- **落盘**：`zcode/reports/0286-certificate.json`（仅 zcode/ 授权目录；
  `runs/` 红线路径零写入）。
- 执行时 T−208.3 min ≠ 字面 1 小时：按本批次（batch_pre_dawn_2300）实际
  派发时点如实记录，不倒填。

## 5. 如实标注的残余风险

1. **历史 v1 证书残留**：`runs/countdown_{2h,4h,8h}_inspection_certificate.json`
   为先前会话产物，本会话未复核其内容，不得引用；以本证书为准。
2. **win probability 口径**：master 证书中的 `0.9192` 胜率未经验证且与 0235 的
   估计（P(top1) ≈ 11–18%）矛盾，本证书**不携带任何胜率声明**。
3. A1/A2 零本地样本（见 §3）；crown 家族本地均值 135.48 s 高于 uniform 家族
   （leak27 126.2 n=3、leak36 129.9 n=2）——选型判断属 Lead 职权，本审计只陈述数字。
4. 官方出分延迟 45–60 分钟、每日 5 发上限、同配置 60 分钟内不重投等运行时
   纪律无法本地验证，属 Lead 侧闭环调度职责。

## 6. 合规声明

只写 `zcode/scripts/cert0286_1h_mobilization.py`、`cert0286_results.json`、
`zcode/reports/0286-certificate.json`、`zcode/reports/0286-analysis.md` 与本文件；
`runs/` 零写入；未登录账号、未提交配置、未触碰凭据内容。
