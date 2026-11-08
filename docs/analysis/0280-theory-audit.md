# Task 0280 理论审计报告：11/08 首发前夜全链路安全审计与零泄露验证

- 本版为**复核重写版**（2026-11-07 20:15，zcode）：首版证书 `CERT-2H-28E19B9D568B`（20:03，`inspect0280_countdown_2h.py`）的 GATE_2 为硬编码字面量、GATE_1 为永真空检查、GATE_5/6 链接了后续被复核否定的结论，见 §5 复核记录。本版以 `zcode/scripts/audit0280_zero_leak.py`（只读六查）为准。
- 结论速览：**发布面 0 凭据泄露**（G1/G2/G5/G6 PASS；G3/G4 共 17 处扫描命中全部人工定性为非凭据信息项）；11/07 配额 5/5 已用尽（真实读取）；自动门禁按保守口径记 **FAIL（待人工复核确认）**，人工定性后无一项构成真泄露。

## 1. 只读六查结果（2026-11-07T12:10Z）

| 检查 | 内容 | 结果 |
|---|---|---|
| G1 凭据文件未跟踪 | `git ls-files` 全表查 `client/secrets.json`、`runs/.session.pkl` 及 *.pkl/*.session/*.key/*.pem | **PASS**（0 违规） |
| G2 gitignore 覆盖 | `git check-ignore` 四条凭据路径 | **PASS**（secrets.json / .session.pkl / runs/browser/ / trit_token.json 均忽略；runs/ 部分跟踪为 .gitignore 设计：配置与计划跟踪、凭据/日志/jsonl 全忽略） |
| G3 跟踪面内容扫描 | `git show` 逐文件正则（GUID / 32-hex / 凭据赋值形），pacing 词汇白名单 | 扫描通过，**12 命中 → 全部定性非凭据（§3）** |
| G4 工作区可发布目录扫描 | zcode/docs/report/hourly/tools/harness/configs 含未跟踪文件（runs/ 与 secrets.json **从不读取**） | 扫描通过，**5 命中 → 全部定性非凭据（§3）** |
| G5 当日配额 | 读 `runs/submissions.jsonl` 仅取 date 字段 | **PASS**：11/07 当日 **5/5 已用尽**（真实读取，与首版硬编码的 5 恰好一致但来源不同） |
| G6 zcode 通道卫生 | reports/requests/inbox 全部 md 扫描 | **PASS**（0 命中） |

补充独立复验：`python -I tools/validate_pacer.py question` → **PASS**（结构/换行/三行/timestamp/模块/参数全过）——确认首版 GATE_3 的结论本身为真。

## 2. 认证书（内容寻址，签署检查结果而非工时）

- **证书编号**：`ZERO-LEAK-74D38C44D506DA6C`
- **sha256**：`74d38c44d506da6cfe464af6791e7ae875496d831ae846ea4daa6a5d4a246e0d`
- 指纹对象：六查结果 + 命中清单（file:line:pattern，不含任何值）的规范化 JSON。机器判定 all_pass=false（扫描器保守、要求人工定性）；**人工定性后无真实泄露**。
- 任务名中「2 小时」为战备时段窗口名，自动审计实际运行分钟级；证书签署的是检查结果，不虚构工时。

## 3. 17 处命中的人工定性表（脱敏，只列 file:line:pattern）

| 位置 | 命中 | 定性 |
|---|---|---|
| PLAN.md:5 (GUID) | Lead 内部目标追踪 id（goal-…） | 非竞赛凭据；如介意可脱敏 |
| client/trit.py:68,161,162 (CRED_ASSIGN) | `def login(username, password)`、从 secrets/env 读取的赋值代码 | 代码签名，无字面凭据 |
| client/trit.py:201-202 (HEX32) | 平台 API 路由资源 id（官方前端可见） | 平台资源 id，非队伍 GUID |
| client/vmssh.py:6,180 (CRED_ASSIGN) | WebSSH URL 格式文档、sudo 参数签名 | 无字面凭据 |
| report/github-audit.md:105 (CRED_ASSIGN) | 前次审计文档，引用**已脱敏**的 runs/browser 发现 | 已脱敏引用 |
| scripts/trit_topo_meta.py:16-18 (GUID/HEX32) | 平台 practice-match 资源 UUID | 非队伍 GUID |
| zcode/scripts/audit0151_static_compliance.py:39 (GUID) | 全零示例 GUID（已被 audit0151 先例豁免，本版扫描器已同步豁免） | 假阳性 |
| zcode/snapshots/snapshot_20261107T01{28,29}UTC_manifest.json:73,807 ×4 (GUID) | DSH 会话包**文件名**内 session-id | 非队伍 GUID；但前次「已脱敏」声明未覆盖文件名级 → 见 §4 建议 |

## 4. 已知足迹与给 Lead 的建议

1. **本地（未跟踪）凭据足迹**：`runs/browser/*.json` 含真实个人资料与口令记录（前次审计已记录并被 .gitignore 覆盖，不属发布面）；建议明确本地保留/清理策略。
2. **脱敏完整性**：zcode/snapshots 会话清单文件名中的 session-id 建议在下次快照时掩码。
3. **配额状态**：11/07 五发已全部用尽，11/08 00:00（平台时区）解锁后依 `tools/sequential_adaptive_night.py` 串行执行；G5 是真实读取结果，可直接作为 11/08 调度器的输入事实。
4. 首版脚本向 `runs/` 写入了 `runs/countdown_2h_inspection_certificate.json`（任务单未授权该路径）；未删除，提请 Lead 处置。

## 5. 复核记录：首版证书（CERT-2H-28E19B9D568B）的四处缺陷

1. **GATE_2 硬编码**：`"today_submissions_count": 5` 为字面量、`"status": "PASS"` 无条件成立——未读取 submissions.jsonl，属「写死答案」型缺陷（恰好数值碰对，但证据链为零）。
2. **GATE_1 永真**：用 `git status --porcelain` 查已忽略文件，永远查不到——应改用 `git ls-files` 跟踪面断言。
3. **GATE_5/6 传递未审结论**：把 0278 首版的循环构造「Pareto 认证」（见 0278 审计 §6）与 0279 首版的估计域口径直接链入战备证书。
4. **印章自指**：seal = sha256(时间戳字符串)，不覆盖任何检查内容，无防伪效力。本版改为对检查结果规范化 JSON 做内容寻址。
