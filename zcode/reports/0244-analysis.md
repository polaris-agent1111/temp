# 0244 报告：决选方案配置哈希硬编码签名与全量校验审计工具

- 完成时间：2026-11-07 17:40
- 执行者：zcode
- 结论：**决选 5 发清单 + 3 棵 distinct 配置树全量 SHA-256 签名与校验完成，29 项检查（5 清单签名 + 18 pacer 字节流格式 + 3 家族一致性 + 3 磁盘真树自校验）全部通过——100% 格式合规且一致；工具已固化为可重跑的防篡改门禁，每发提交前重跑比对指纹即可。**

## 具体动作

1. 追踪真实提交通路（`tools/submit_batch.py` → `harness/upload_config.py` → `build_tree`/`render_pacer`），确认渲染语义：UTF-8 无 BOM、纯 LF、恰好 3 行、末尾无换行、参数序 = 清单 JSON 键序。
2. 编写并执行 `zcode/scripts/audit0244_config_fingerprint.py`（只读，退出码 0=PASS）：
   - 5 个 `runs/seq_1108_shot_N.json` 原始字节签名（如 shot1 = `33b37f4e…`）；
   - 3 棵 distinct 树（steady / crown / crown-pert）× 6 目录 pacer 字节复刻渲染 + 逐目录 SHA-256 + 树级复合指纹（crown = `6f995d6b…`，Shot 2/4/5 逐位一致）；
   - 格式合规逐条校验（依据 `configs/params_schema.json`：目录 1..6、无 BOM/无 CR/3 行/无尾换行、`[timestamp:N]` 匹配、参数名/posint 类型、约束 bucket_cap≥leak_rate）；
   - **重要发现**：磁盘历史树用 `leak_rate,bucket_cap,leak_interval_us` 参数序，seq_1108 管线用 JSON 键序 `bucket_cap,leak_interval_us,leak_rate`——语义等价但字节不同、指纹不同。本清单签署的是 seq_1108 管线将实际渲染的字节（键序保真链逐环验证）；
   - **自校验**：复刻渲染器对磁盘 3 棵真实管线落盘树逐字节比对，全部一致（如 anchor-r1 sha256 `5ca2a8e6…`），证明复刻器字节精确。
3. 并发执行者说明：17:01 发现 `docs/analysis/0244-theory-audit.md` 与本报告被并发方以本任务脚本**首版**输出粘贴（缺自校验段与参数序发现、markdown 表格破碎、不符合报告格式）。已用修正版覆盖这两个授权路径；任务单 status 已被并发方翻为 done（目标态一致，未重复翻转）。

## 产出文件

- `zcode/scripts/audit0244_config_fingerprint.py`（审计工具，可重跑门禁）
- `zcode/scripts/_0244_out.md`（完整指纹清单输出）
- `docs/analysis/0244-theory-audit.md`（审计文档：指纹清单/参数序发现/使用协议/局限）
- 本报告 `zcode/reports/0244-analysis.md`；任务单 `zcode/requests/0244-*.md` 状态为 done

## 未完成/风险

- 指纹「不可篡改」以本审计文档为可信基准（git 跟踪），工具不引入第三方签名；威胁模型是意外改动/管线漂移，非对抗性攻击者。
- `sequential_adaptive_1108.py` 每次运行会重写 seq 清单——dict 字面量序稳定则指纹不变，但任何对该工具的改动都会造成指纹漂移（这正是门禁要拦截的场景）。
- 若临场手动换构型，必须重跑工具并补录新指纹，否则协议失效。

## 给 Lead 的建议

- 每发提交前执行 `python zcode/scripts/audit0244_config_fingerprint.py`：退出码 0 且指纹与 `docs/analysis/0244-theory-audit.md` §1/§2 逐位一致才允许提交；任何漂移即中止并 `git diff runs/seq_1108_shot_*.json` 排查。
- batch_1200 批次存在并发执行者（0244 于 17:01 被他人转录并翻状态）；后续派发建议避免同一任务双执行者，或 Lead 在看板注明执行者归属。
