# 0033 报告：全量配置快照格式校验

- 完成时间：2026-11-05 23:35
- 执行者：zcode
- 结论：**222 tag / 1321 个 pacer.txt 全量体检完成——格式合格率 91.4%（1207/1321），114 个不合格（主因=历史 CRLF 陷阱样本），256 个格式合格但 interval<4000（官方咬合风险⚠），6 个真实参数违法（`leakc-36-30-4000`：bucket_cap 30 < leak_rate 36）；全部 `submit-*` 投递链路 tag 零 ERROR**。未修改任何文件。

## 具体动作

1. **`tools/check_all_configs.py`**（只读、一条命令重跑、退出码恒 0）：遍历 `runs/configs/**/pacer.txt` 逐文件检查——UTF-8 无 BOM / 无 `\r` / 无末尾换行 / 三行结构 / 行首尾空白 / timestamp=目录号 / 模块白名单 / 参数解析与约束（bucket_cap≥leak_rate、burst≥tokens）/ 字节数 90–120（警告）/ **leak_interval_us≥4000（警告=陷阱风险，0013）**；tag 级：六目录齐全、无多余文件、六目录配置一致性（mix 类记 info）。
2. **`report/配置全量校验.md`**：总览 + 不合格按问题类型汇总 + 逐文件明细 + 警告清单（含 interval<4000 折叠全列）+ tag 级问题表 + 修复建议（`harness/run_experiment.py` 再生成判断，确认存在）。

## 关键发现

| 发现 | 数量 | 处置建议 |
|---|---|---|
| **格式合格** | **1207（91.4%）** | — |
| CRLF/末尾换行族 | 102 文件（`ctl-origin-norate`、`ctl-tokenbucket-default`、`s3-tokenbucket-default` 等 80 s 假成功时代样本） | 历史证据样本，**不必修复**；若重投必须重生成 |
| **参数违法：cap30 < rate36** | **6 文件（tag `leakc-36-30-4000`）** | **唯一真违法 tag**——格式检查必挂，若误投=烧额度；建议用 harness/run_experiment.py 重生成或标记废弃 |
| interval<4000（陷阱风险⚠） | 256 个格式合格文件（leak9/leak8/2ms/3ms 族等） | 已知 0013 结论：官方 ×2；**不修复**（跨环境差异证据样本，0017），只标注 |
| 六目录不一致 tag | 17（其中 mix 类为有意设计） | info |
| **`submit-*` 全系列** | **零 ERROR** | 投递链路完好 ✓ |

## 产出文件

- `tools/check_all_configs.py`
- `report/配置全量校验.md`（覆盖写，可一条命令重跑：`python tools/check_all_configs.py`）
- `zcode/reports/0033-configcheck.md`（本报告）

## 未完成/风险

- 修复建议仅为判断输出，**未实际修改/重生成任何 pacer.txt**（任务禁止）；`leakc-36-30-4000` 若确属废弃实验，建议 Lead 决定重生成或加 README 标记。
- 字节数 90–120 参考带有个别越界（tb 类 122 B、mix 类），按警告不计不合格。
- 本体检不含 `.tar.gz` 快照包内容核对（仅工作区 pacer.txt）。

## 给 Lead 的建议（可选）

- 把本脚本挂进每日 runbook §二（检查清单追加一条「`check_all_configs.py` 零新增 ERROR」），防止新配置再踩 CRLF/cap<rate 坑。
