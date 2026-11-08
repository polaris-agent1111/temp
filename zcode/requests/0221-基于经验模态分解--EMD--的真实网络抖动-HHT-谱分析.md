status: done
priority: 2
assignee: zcode
created: 2026-11-07 14:42

# 0221 任务：基于经验模态分解 (EMD) 的真实网络抖动 HHT 谱分析

## 任务背景
提取固有模态函数 (IMF)，在时频两域证明漏桶整形对网络微突发非平稳信号的自适应分解滤除能力。

## 目标
证明高频本征模态能量被压低 80% 以上。

## 交付物与路径
- `zcode/reports/0221-analysis.md`
- `docs/analysis/0221-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写 EMD 与希尔伯特时频谱分析脚本
2. 形成分析成果写入 `docs/analysis/0221-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0221-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
