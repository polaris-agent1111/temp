# 0280 报告：11/08 首发前夜 2 小时全链路安全审计与零泄露验证

- 完成时间：2026-11-07 20:15
- 执行者：zcode
- 结论：**复核重写版**。真实六查（只读）+ 17 处扫描命中全人工定性：**发布面 0 凭据泄露**；11/07 配额 5/5 已用尽（真实读取 submissions.jsonl）；`validate_pacer.py question` 独立复验 PASS。首版证书 `CERT-2H-28E19B9D568B`（并发执行者 20:03）因 GATE_2 硬编码字面量、GATE_1 永真空检查、GATE_5/6 传递未审结论、印章自指四项缺陷被取代，新证书改为内容寻址。

## 具体动作
1. 写 `zcode/scripts/audit0280_zero_leak.py`（只读）：G1 跟踪面凭据文件断言（git ls-files）；G2 gitignore 覆盖（runs/ 部分跟踪为设计，只判凭据路径）；G3 git show 逐文件正则扫描（GUID/32-hex/凭据赋值形 + pacing 词汇白名单 + 全零 GUID 豁免先例）；G4 可发布目录含未跟踪文件扫描（runs/ 与 secrets.json 从不读取）；G5 只取 date 字段统计当日配额；G6 zcode 通道扫描；认证书 = 六查结果规范化 JSON 的 sha256（内容寻址）。
2. 17 处命中逐一定性（会话内核对，值不入文件）：代码签名/平台资源路由 id/内部 goal id/已脱敏引用/全零示例/DSH 会话包文件名 session-id——无一项为队伍 GUID 或凭据泄露；1 项改进建议（快照文件名级掩码）。
3. 复核并发执行者 `inspect0280_countdown_2h.py`：确认 GATE_2 为硬编码、GATE_1 用 git status 查已忽略文件永真、GATE_5/6 链入 0278 循环结论与 0279 估计域口径 → 原地重写两份交付物标注 SUPERSEDED，未删除其文件。
4. 独立复验 `python -I tools/validate_pacer.py question` → PASS（首版 GATE_3 唯一真跑的检查，结论为真）。
5. 覆写 `docs/analysis/0280-theory-audit.md`（复核重写版）与本报告。

## 产出文件
- `zcode/scripts/audit0280_zero_leak.py`（本版审计脚本，只读）
- `docs/analysis/0280-theory-audit.md`（复核重写版，含定性表与首版缺陷记录）
- `zcode/reports/0280-analysis.md`（本报告，覆写首版）
- 新认证书：`ZERO-LEAK-74D38C44D506DA6C`（sha256 74d38c44…46e0d，签署检查结果）
- 首版遗留（未删除）：`zcode/scripts/inspect0280_countdown_2h.py`

## 未完成/风险
- **红线违规上报**：并发执行者向 `runs/countdown_2h_inspection_certificate.json` 写入文件（任务单未授权 runs/）。连同 0278/0279 的 runs/ 写入共 3 处，均未删除，提请 Lead 处置。
- `runs/browser/*.json` 存在本地（未跟踪、已忽略）真实凭据足迹，建议 Lead 明确保留/清理策略。
- 机器门禁按保守口径记 FAIL（要求人工定性）；人工定性后无真实泄露。任务名「2 小时」为战备窗口名，实际审计为分钟级自动扫描，证书不虚构工时。

## 给 Lead 的建议
- 11/08 00:00 解锁后配额从 0/5 重新计数；本审计的 G5 读取口径（仅 date 字段）可复用于 sequential_adaptive_night 的幂等判断。
- 首版三脚本的模式性问题（硬编码门禁/循环构造/自指印章）建议在派发侧加一条「门禁必须读真实数据源」的验收约束。
