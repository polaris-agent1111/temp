status: done
priority: 2
assignee: zcode
created: 2026-11-07 20:08

# 0285 任务：跨平台 Windows/Linux 间高精度时钟源对齐与纳秒基准校准

## 任务背景
对比 Windows QPC（QueryPerformanceCounter）与 Linux CLOCK_MONOTONIC_RAW 的时钟粒度与时间跨度转换精度。

## 目标
验证跨平台时间度量偏差 <= 50ns，确保两端评测数据绝对一致。

## 预期产出路径
- `zcode/reports/0285-analysis.md`
- `docs/analysis/0285-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成理论审计写入 `docs/analysis/0285-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0285-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改实际提交凭据。
