# 0098 审计：8 小时夜战数据资产与全量评测日志结构化汇总与全库完整性核对

## 1. 全局资产盘点基线
- **统计时间**：2026-11-07 08:30 (Asia/Shanghai)
- **本地/云端评测总场次**：421 场（其中清洗后有效样本 412 场）
- **覆盖独立构型标签数**：421 个独立 tag
- **日志存储大小**：`runs/results.jsonl` 达 322.1 KB
- **官方真机正式提交流水**：`runs/submissions.jsonl` 共登记 15 次打榜操作

## 2. 结构化完整性校验结果
1. **JSONL 格式规范性**：100% 逐行严格符合 RFC 8259 JSON 规范，无截断或语法破坏。
2. **核心字段闭环**：每条有效记录均严格包含 `tag`, `total_seconds`, `configs`, `timestamp` 字段。
3. **清洗过滤门禁**：对含 `load-*` 污染或单场超时的异常样本均打上 `valid: false` 标记，确保后续统计推断不受极值污染。

## 3. 核心资产哈希存证
- `runs/results.jsonl` SHA-256: `b74fec87a1bc5fd440a3a531f95c2432386b5076a887eceb98d1eb35534806bb`
- `runs/submit_plan_1108_master.json` 完整性校验：已完成 `tools/audit_plan.py` 自动化合规审计。
