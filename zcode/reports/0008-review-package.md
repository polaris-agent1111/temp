# 0008 报告：复核材料包

- 完成时间：2026-11-05 17:25
- 执行者：zcode
- 结论：`report/复核材料/` 五件套齐备；3 个候选配置（leak9 / leak8 / tb-100-200-20）从 `runs/configs/` 字节级复制（18 文件 sha256 全部一致）并通过校验器 8 项检查；无任何真实凭据。

## 产出文件（路径 + 字节数）

```
report/复核材料/
├── README.md                          2953 B   一页说明：做了什么/三步复现/目录导航/关键数字速查
├── best-configs/
│   ├── README.md                      2467 B   3 候选的 mean±std/n/来源 tag/官方状态 + 分文件表 + 诚实性选用说明
│   ├── leak9-rate9/{1..6}/pacer.txt   97 B×6   leak_bucket 9/30/1000（本地最优 123.81±7.19, n=7；官方口径不推荐，已注明）
│   ├── leak8-rate8/{1..6}/pacer.txt   97 B×6   leak_bucket 8/30/1000（126.09±6.96, n=3）
│   └── tb-100-200-20/{1..6}/pacer.txt 122 B×6  token_bucket 100/200/20@1000（136.24±7.60, n=2；官方提交口径 S3）
├── reproduce.md                       3886 B   逐步复现：目录结构/格式检查/评测命令/结果文件含义/统计复跑/提交（GUID 占位）/预期结果对照表（含 4 核、3–4 分钟说明）
├── methodology.md                     2921 B   方法摘要：建模→链路预算→四层搜索→方差惩罚→跨环境鲁棒准则（详版指向技术报告 v1）
└── checklist.md                       3498 B   自检清单 A 格式(8) / B 提交(4) / C 可复现(5) / D 合规(4) / E 材料(3)，CRLF·timestamp·burst≥tokens·bucket_cap≥leak_rate 等已知坑全覆盖
```

## 具体动作

1. 候选按 `report/实验结果-统计.md` 选 2–3 个：**leak9-rate9**（本地最优 n=7）、**leak8-rate8**（n=3）、**tb-100-200-20**（官方提交口径）；来源目录 `e5-leak-rate9`、`e4-leak-rate8`、`submit-s3-tokenbucket`。
2. `cp -p` 复制 18 个 pacer.txt → **sha256 逐一对照全部 OK**（字节一致，保留 LF/无末尾换行）。
3. `python tools/validate_pacer.py` 对 3 个候选目录全部 **[PASS]**（8 项检查）。
4. 文档内如实标注：leak 族官方两次 245.995/243.958 s 系统性差异（0006 分析中）→ **本地最优 ≠ 官方推荐**，best-configs/README 与 reproduce.md 双处注明。
5. 凭据检查：GUID 全部 `<团队GUID>` 占位，无密码/token。

## 未完成/风险

- `best-configs` 不含「官方已验证快于 245 的配置」——S3 出分后若成功，应把 tb 候选的官方成绩回填两处 README。
- reproduce.md 的预期结果表基于本地口径；官方复测值以平台为准（已注明跨环境差异）。
- checklist E3（队友独立复跑）需人工执行，zcode 无法代验。

## 给 Lead 的建议（可选）

- 复核期把 `report/复核材料/` 整目录连同 `report/技术报告-v1.md` 打包即交；S3 出分后回填官方成绩，再跑一遍 checklist A+B。
