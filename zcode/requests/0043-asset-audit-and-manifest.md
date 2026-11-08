status: done
priority: 2
assignee: zcode
created: 2026-11-06 19:20

# 0043 — 全仓库数据资产全量盘点、SHA-256 指纹库生成与合规红线零漏洞穿透核查

## 背景
iDSN 挑战赛官方明确规定了严苛的合规红线（严禁修改评测环境、严禁硬编码答案、严禁多账号、严禁泄露 GUID、每日提交不得超 5 发、提交配置严禁含 CRLF 换行等，违反将取消成绩）。随着我们科研实验深入到第 273 场，仓库内积累了大量构型、评测日志、分析文档与工具脚本。为确保最终提交材料与比赛全程无死角合规，且为决赛答辩提供严密的资产全生命周期可追溯性，需要完成全仓库级的数据资产全量盘点与穿透式合规核查。

## 目标
全面盘点工作区内所有目录资产，构建 SHA-256 数字指纹库，分类归档，并执行穿透式安全与合规审计，产出《全仓库数据资产盘点清单》与《参赛合规红线零漏洞复核报告》。

## 允许写的路径
- `zcode/reports/0043-asset-audit-and-manifest.md`
- `docs/资产清单.md`
- `docs/compliance-check-report.md`
- `zcode/scripts/audit_assets.py`（若需辅助审计脚本）

## 具体动作
1. **全仓库文件遍历与资产测绘**：
   - 遍历 `docs/`、`runs/`、`configs/`、`tools/`、`client/`、`report/`、`harness/` 下的所有文件；
   - 统计每个文件的相对路径、大小（Bytes / KB）、修改时间（ISO 8601）、SHA-256 校验哈希；
   - 按照用途严格进行四级分类：
     - A 类：每日打榜必用（results.jsonl, submissions.jsonl, official_results.jsonl, leaderboard 快照）；
     - B 类：核心构型与作战工具（configs/*.json, tools/*.py, harness/*.py）；
     - C 类：理论研究与答辩证据材料（docs/analysis/*.md, report/*.md）；
     - D 类：临时排队与演练产物。
2. **合规红线专项穿透审查**：
   - **红线 1（凭证与隐私脱敏）**：扫描所有文本文件，确保任何代码、注释、提交说明中绝无硬编码的比赛 GUID、Token、明文密码与个人敏感身份信息（仅允许从环境变量或 secrets.json 内部读取）；
   - **红线 2（配置编码与换行规范）**：检查 `configs/` 下生成的全部 `pacer.txt` 与配置模板，确保严格符合 UTF-8 编码、LF 换行（绝对严禁包含 `\r\n` CRLF 字符），恰好三行，末尾无空行；
   - **红线 3（提交配额纪律）**：审查 `runs/submissions.jsonl`，核对每日提交计数，确保历史上每日提交严格受控于 $\le 5$ 次，无任何超限提交漏洞。
3. **交付产出**：
   - 汇总生成全量 Markdown 表格资产清单至 `docs/资产清单.md`；
   - 编写穿透式合规审查结论至 `docs/compliance-check-report.md`；
   - 输出标准验收报告至 `zcode/reports/0043-asset-audit-and-manifest.md` 并标记本任务为 `status: done`。

## 禁止
- 不修改 `client/secrets.json`、`runs/.session.pkl`；
- 不删除或移动任何现有代码及实验数据；
- 不操作云主机，不登录平台。

## 交付
- `docs/资产清单.md`
- `docs/compliance-check-report.md`
- `zcode/reports/0043-asset-audit-and-manifest.md`
- 完成后把本文件头部 `status: done` 改为 `status: done`
