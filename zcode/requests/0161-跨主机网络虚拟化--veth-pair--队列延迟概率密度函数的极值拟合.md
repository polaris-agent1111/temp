status: done
priority: 2
assignee: zcode
created: 2026-11-07 13:55

# 0161 任务：跨主机网络虚拟化 (veth pair) 队列延迟概率密度函数的极值拟合

## 背景
通过 GEV 广义极值分布拟合 veth pair 的长尾时延，评估评测平台底层的虚拟化开销波动。

## 目标
拟合形状参数 xi、尺度参数 sigma、位置参数 mu。

## 产出路径
- `zcode/reports/0161-analysis.md`
- `docs/analysis/0161-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写极值分布拟合脚本；
2. 形成分析成果写入 `docs/analysis/0161-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0161-analysis.md`，并将状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单、严禁修改实际提交凭据。
