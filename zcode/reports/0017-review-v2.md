# 0017 报告：复核材料包 v2（4 ms 配置 + 定时器粒度 + manifest）

- 完成时间：2026-11-05 18:50
- 执行者：zcode
- 结论：`report/复核材料/` 已就地升级 v2——新增 `leak-24-50-4000`、`leak-36-40-4000` 两个 4 ms 配置（各 6 文件，**sha256 与 `runs/configs/` 源 12/12 全一致**、校验器 PASS、98 字节）；五份文档全部并入定时器粒度发现；新增 `review-manifest.json`（35 文件 sha256+字节数）。

## 改了哪些文件

| 文件 | 动作 | 要点 |
|---|---|---|
| `best-configs/leak-24-50-4000/{1..6}/pacer.txt` | **新增** | 源 `runs/configs/leakc-24-50-4000`（cp -p 字节级）；本地 **126.89±6.21 (n=11)**，min 119.59；官方待投 |
| `best-configs/leak-36-40-4000/{1..6}/pacer.txt` | **新增** | 源 `runs/configs/leakc-36-40-4000`；本地 132.45±6.73 (n=3)；**官方 133.086（S4，榜第 5 锚点）** |
| `best-configs/README.md` | 更新 | 5 配置表：推荐 2（4 ms，含本地/官方/场景）+ 历史 3（leak9 标 ⚠1 ms 陷阱官方复测禁用、tb 安全对照）；分文件表重算至当前 n（24/50 n=11、36/40 n=3） |
| `README.md` | 更新 | 「我们做了什么」写入官方 133.086（榜第 5）+ 定时器粒度发现；三步复现指向 4 ms 推荐；关键数字速查**加官方列**（基线/两个 4 ms/tb/陷阱/名次） |
| `reproduce.md` | 更新 | 示例配置换成 `36/40/4000`；新增 **§1.5「⚠ 必须用 4 ms 及以上间隔」**（现象×2/原因 G≈4ms 反推/三条规避规则/指向 0013 文档）；预期结果表换 4 ms 配置并标陷阱警示 |
| `methodology.md` | 更新 | §4 跨环境改「已结案」；新增**「跨环境鲁棒准则」**四条（interval≥4000 或旁路、标称 ÷4 余量、n≥3+官方探测、反转警觉+timer_model 复算）；§1 加官方最好成绩行 |
| `checklist.md` | 更新 | 新增 **F 节两条**：F1 所有 leak_interval_us≥4000；F2 rate-based/token_bucket 确认 enable_n_in_flight 未关 0 + ÷4 余量；E1 加 manifest、E2 改 v2 |
| `review-manifest.json` | **新增** | 35 文件（5 文档 + 30 个 pacer.txt）的 sha256 + 字节数；自排除；校验方法写在 note |

## sha256 校验结果

- 新增 12 个 pacer.txt：`leak-24-50-4000/1..6`、`leak-36-40-4000/1..6` 与 `runs/configs/leakc-24-50-4000`、`leakc-36-40-4000` 源**逐一比对 12/12 OK**；
- 两配置均过 `python tools/validate_pacer.py` 8 项 **[PASS]**（LF/无末尾换行/timestamp=目录号/参数约束）；
- 原有 18 个历史配置文件未动（0008 时已核对 18/18）。

## 产出文件

- `report/复核材料/`（更新 5 文档 + 新增 12 配置文件 + 新增 `review-manifest.json`，共 36 个文件变动/新增）
- `zcode/reports/0017-review-v2.md`（本报告）

## 未完成/风险

- `24/50/4000` 官方值待 11/06 探测后回填 best-configs/README 与包 README 的速查表。
- 分文件均值与总表同批（n=11/n=3），但 `技术报告-v2.md` §2.2 仍是 n=5 时点（0015 已 done 未动）；两处数字口径以本包为最新。
- manifest 生成后若再改包内任何文件，需重跑生成脚本（脚本为一次性内联，重跑方法见本报告「具体动作」第 6 步同款逻辑）。

## 给 Lead 的建议（可选）

- 11/18 复核前把本包 + `report/技术报告-v2.md` + `docs/knowledge/timer-granularity.md` 一起打包即为完整证据链。
- `24/50/4000` 官方出分后，只需更新两处 README 的一行数字 + 重生成 manifest。
