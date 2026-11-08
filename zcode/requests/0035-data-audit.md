status: done
priority: 4
assignee: zcode
created: 2026-11-05 23:00

# 0035 — 杂活：本地评测历史数据质量审计

## 任务

产出 `report/数据质量审计.md`：

1. **完整性**：`runs/results.jsonl` 每条记录是否都有 `tag / valid / total_seconds / downloads / config`；缺字段的列出来。
2. **重复检测**：同一 tag 出现多次（`repeat` 造成）是否都保留了；有没有意外重复写入（同一 tag + 同一时间戳）。
3. **异常值**：`total_seconds` 明显异常（<80 或 >200）的记录，逐条给原因猜测（1ms 陷阱 / 评测失败 / 真慢）。
4. **valid 判定复核**：对 `valid=false` 的记录，用物理下限 `size/12.5MB/s*0.9` 重算一遍，列出「判定可能错误」的条目（如果有）。
5. **配置文件一致性**：`results.jsonl` 里记录的 config 与 `runs/configs/<tag>/*/pacer.txt` 实际内容是否一致（抽查 30 条）。
6. **统计汇总**：有效样本总数、按配置族的样本数分布、有多少配置只有 n=1（不可用）、有多少 n>=5（可用）。
7. **一句话结论**：这份数据现在能不能支撑「配置排序」的结论，哪些配置还缺样本。

## 禁止

不修改 `results.jsonl`、不改 `configs/`；只读。

## 交付

`report/数据质量审计.md` + `zcode/reports/0035-data-audit.md`。
