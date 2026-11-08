status: done
priority: 1
assignee: zcode
created: 2026-11-08 00:06

# 0348 任务：自适应 QUIC ACK 压缩在线检测与滑动平滑滤波补偿

## 任务背景
针对反向信道可能发生的 ACK 堆叠与脉冲释放，构建二阶滑动平滑滤波补偿器。

## 目标
ACK 堆叠平滑滤除率 >= 90.0%，突发脉冲因子 F <= 1.05。

## 预期产出路径
- `zcode/reports/0348-analysis.md`
- `docs/analysis/0348-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0348-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0348-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
