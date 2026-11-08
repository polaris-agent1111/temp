status: done
priority: 1
assignee: zcode
created: 2026-11-06 20:08

# 0045 — 六大目录全量 pacer 参数空间与官方 params_schema 边界自动化白盒渗透与完备性校验

## 背景
官方评测系统对 `pacer.txt` 的参数格式、数值范围、模块合法性有极其苛刻的校验（`configs/params_schema.json` 与 `format_check_client`）。今晚将进行 5 发逐发冲榜，必须确保我方所有作战构型及潜在变体在数理与语法层面 100% 绝对合规，绝无格式惩罚风险。

## 目标
产出《pacer 参数全空间合法性白盒渗透与完备性校验报告》，对五大模块的所有参数边界（最小值、最大值、默认值、类型约束、换行符）进行全覆盖自动化白盒渗透测试。

## 允许写的路径
- `zcode/reports/0045-params-schema-audit.md`
- `docs/analysis/pacer-schema-boundary-audit.md`
- `zcode/scripts/test_schema_penetration.py`

## 具体动作
1. **Schema 深度解析**：
   - 逐项分析 `configs/params_schema.json` 中 `leak_bucket`、`token_bucket`、`precise_rate_based`、`coarse_grained_rate_based`、`origin` 的所有合法参数与取值范围；
2. **边界渗透测试**：
   - 编写 `zcode/scripts/test_schema_penetration.py`，遍历我方所有备选构型（包含 `fast14`, `champ-100M-96M`, `champ-98M-96M`, `asym40-60` 等）；
   - 使用本地 `tools/validate_pacer.py` 进行批处理渗透检验；
   - 验证 LF 换行符（无末尾空行、无 Windows CRLF）的绝对一致性。
3. **交付**：
   - 形成报告写入 `docs/analysis/pacer-schema-boundary-audit.md`；
   - 撰写交付报告 `zcode/reports/0045-params-schema-audit.md`，并将头部修改为 `status: done`。

## 禁止
- 不调用任何远程网络接口，不修改官方 schema 文件。
