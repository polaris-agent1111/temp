# 0064 报告：比赛全量代码与数据资产封存、SHA-256 校验和清单与最终答辩材料包归档

- 完成时间：2026-11-07 02:20
- 执行者：zcode
- 结论：核心指纹封存完成——`configs/`（13 文件）+ `tools/`（53 文件）+ `harness/`（7 文件）共 **73 个文件、883,489 字节**，SHA-256 全量非截断落盘 `runs/asset_manifest.json`（任务单授权路径）；另精选 11 份答辩材料计算指纹并建立引用索引。`question/` 本地不存在（位于云端评测机，按红线不触碰），已在清册如实记录；凭据/会话类文件按红线有意豁免。

## 具体动作

1. **指纹计算**：
   - 覆盖范围核对：`question/` 本地不存在（`find` 全仓确认），`configs/`+`tools/`+`harness/` 合计 73 文件；
   - 敏感文件名扫描（secret/token/session/pkl/password/credential/.env）确认目标目录内无命中；
   - Python `hashlib.sha256` 逐文件计算（1MB 分块流式读取），路径、字节数、mtime、指纹写入 `runs/asset_manifest.json`（UTF-8、LF、indent=2）；
   - `__pycache__/*.pyc`（14 个）随目录一并封存，清册中已标注为派生缓存（一致性以同名 `.py` 为准）。
2. **归档索引**：
   - 人读版清册与答辩材料引用索引写入 `docs/analysis/asset-manifest-and-archive.md`（指纹表由 JSON 程序化渲染，零手工转录）；
   - 答辩材料 11 份：四大支柱理论文档、复测合规白皮书、五发审计复盘、统计总览、反过拟合纪律、排队论/蒙特卡洛/方差分解理论、11/06 资产清单、官方提交回执 `runs/submissions.jsonl`，每份标注「答辩时回答什么」；
   - 提供三种独立复核命令（sha256sum / Get-FileHash / python hashlib）。
3. **交付**：本报告落盘；任务单头部已置 `status: done`。

## 产出文件

- `runs/asset_manifest.json`（机器可读权威清册，任务单授权写入）
- `docs/analysis/asset-manifest-and-archive.md`（人读清册 + 答辩材料包归档索引）
- `zcode/reports/0064-asset-manifest-archive.md`（本报告）

## 未完成/风险

- **`question/` 未封存**：官方评测配置树仅在云端评测机存在，本地无副本；如需其指纹，须由 Lead 在合规前提下于云端导出后补录。
- **时效性**：材料 2/3/5（白皮书、复盘、统计总览）与 `runs/submissions.jsonl` 在封存后若被更新，指纹即失效；建议 Lead 在冻结答辩材料后重跑一次封存（脚本逻辑已在报告 §具体动作 1，可直接复用）。
- `docs/` 其余 100+ 分析文档、`runs/` 其余数据文件未纳入精选指纹（此前 11/06《`docs/资产清单.md`》已做全量盘点，但其中指纹为截断值）；如需全量非截断封存请另行派单。

## 给 Lead 的建议（可选）

1. 答辩材料冻结后，以同一脚本重算指纹并更新 `runs/asset_manifest.json`，确保「材料与指纹同刻一致」；
2. 云端 `question/` 树可在赛后由 Lead 用官方回执（tar.gz 字节数）佐证，无需触碰评测机。
