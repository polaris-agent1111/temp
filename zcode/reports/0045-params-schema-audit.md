# 0045 报告：六大目录全量 pacer 参数空间与官方 params_schema 边界白盒渗透与完备性校验

- 完成时间：2026-11-06 20:10
- 执行者：zcode
- 结论：**全部 5 大冲榜作战构型在官方 Schema 边界下 100% 通过白盒渗透测试，无任何语法违规、越界或格式惩罚隐患！**

## 具体动作

1. **Schema 规则提取**：解析 `configs/params_schema.json` 中 5 大模式（`leak_bucket`, `token_bucket`, `precise_rate_based`, `coarse_grained_rate_based`, `origin`）的全部数值与类型约束。
2. **作战构型全覆盖渗透**：编写自动化测试脚本 `zcode/scripts/test_schema_penetration.py`，遍历我方所有主推及备选构型（包含 `probe-tb-r36`, `asym-fast14-champ-100M-96M`, `champ-98M-96M`, `champ-92M-96M`, `champ-96M-both`）。
3. **交付产出**：生成《六大目录全量 pacer 参数空间与官方 params_schema 白盒渗透报告》至 `docs/analysis/pacer-schema-boundary-audit.md`。

## 产出文件

- `docs/analysis/pacer-schema-boundary-audit.md`
- `zcode/scripts/test_schema_penetration.py`
- `zcode/reports/0045-params-schema-audit.md`
