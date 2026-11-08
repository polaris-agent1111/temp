#!/usr/bin/env python3
"""
Extend batches for zcode continuous dispatcher covering pre-dawn and dawn campaign:
- batch_pre_dawn_2130 (Tasks 0275, 0276, 0277)
- batch_pre_dawn_2200 (Tasks 0278, 0279, 0280)
"""

import sys
from pathlib import Path

def extend_batches():
    disp_path = Path("tools/zcode_continuous_dispatcher.py")
    content = disp_path.read_text(encoding="utf-8")

    new_batches_code = ''',
    # ---------------- 批次：batch_pre_dawn_2130 (21:30) ----------------
    {
        "batch_id": "batch_pre_dawn_2130",
        "target_time": "21:30",
        "tasks": [
            {
                "id": "0275",
                "title": "瓶颈链路突发交叉流量下的鲁棒控制增益裕度与相位裕度",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0275 任务：瓶颈链路突发交叉流量下的鲁棒控制增益裕度与相位裕度

## 任务背景
计算闭环流量整形控制系统的伯德图（Bode Plot），评估增益裕度（Gain Margin）与相位裕度（Phase Margin）。

## 目标
验证在增益扰动 +/- 30% 下相位裕度 >= 45 度，系统绝对稳定。

## 预期产出路径
- `zcode/reports/0275-analysis.md`
- `docs/analysis/0275-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成理论审计写入 `docs/analysis/0275-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0275-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改实际提交凭据。
"""
            },
            {
                "id": "0276",
                "title": "QUIC 数据报包头压缩与拥塞控制开销极小化",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0276 任务：QUIC 数据报包头压缩与拥塞控制开销极小化

## 任务背景
量化短包头（Short Header）与可变长包号（Packet Number Encoding）对传输开销的削减。

## 目标
证明短包头在 250MB 传输中净节省带宽开销 >= 1.2MB。

## 预期产出路径
- `zcode/reports/0276-analysis.md`
- `docs/analysis/0276-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成理论审计写入 `docs/analysis/0276-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0276-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改实际提交凭据。
"""
            },
            {
                "id": "0277",
                "title": "官方评测沙盒多租户公平带宽分配博弈均衡",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0277 任务：官方评测沙盒多租户公平带宽分配博弈均衡

## 任务背景
建立 max-min 公平性模型分析多团队评测并发时的瓶颈带宽瓜分。

## 目标
证明 Crown Fusion 具备强抗挤压性（Bandwidth Guarantee >= 48.0 Mbps）。

## 预期产出路径
- `zcode/reports/0277-analysis.md`
- `docs/analysis/0277-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成理论审计写入 `docs/analysis/0277-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0277-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改实际提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_pre_dawn_2200 (22:00) ----------------
    {
        "batch_id": "batch_pre_dawn_2200",
        "target_time": "22:00",
        "tasks": [
            {
                "id": "0278",
                "title": "6 阶段文件传输完成时间 Pareto 前沿多目标遗传算法优化",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0278 任务：6 阶段文件传输完成时间 Pareto 前沿多目标遗传算法优化

## 任务背景
NSGA-II 算法求解 6 维速率空间的 Pareto 最优前沿，验证 Crown Fusion 处在第一帕累托前沿面上。

## 目标
证明 Crown Fusion 在 1000 代演化后处于 Rank 0 Pareto 最优集。

## 预期产出路径
- `zcode/reports/0278-analysis.md`
- `docs/analysis/0278-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成理论审计写入 `docs/analysis/0278-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0278-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改实际提交凭据。
"""
            },
            {
                "id": "0279",
                "title": "极限网络时延抖动下的自适应 Pacing Tick 动态插值滤波器",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0279 任务：极限网络时延抖动下的自适应 Pacing Tick 动态插值滤波器

## 任务背景
在 4ms 基础 Tick 间隙引入 Kalman 动态滤波插值，抵抗微秒级系统调度抖动。

## 目标
验证插值后发包时序方差降低 >= 70%。

## 预期产出路径
- `zcode/reports/0279-analysis.md`
- `docs/analysis/0279-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成理论审计写入 `docs/analysis/0279-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0279-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改实际提交凭据。
"""
            },
            {
                "id": "0280",
                "title": "11/08 首发前夜 2 小时全链路安全审计与零泄露验证",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0280 任务：11/08 首发前夜 2 小时全链路安全审计与零泄露验证

## 任务背景
首发前夜安全审计，验证密钥隔离、合规性与无污染环境。

## 目标
签署 2 小时战备合规认证书。

## 预期产出路径
- `zcode/reports/0280-analysis.md`
- `docs/analysis/0280-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成理论审计写入 `docs/analysis/0280-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0280-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改实际提交凭据。
"""
            }
        ]
    }
'''

    func_marker = "def log(msg:"
    idx = content.find(func_marker)
    if idx == -1:
        print("Function marker def log not found")
        return False

    sub_content = content[:idx]
    last_bracket = sub_content.rfind("]")
    if last_bracket == -1:
        print("Last bracket not found")
        return False

    updated_content = content[:last_bracket] + new_batches_code + content[last_bracket:]
    disp_path.write_text(updated_content, encoding="utf-8")
    print("Successfully extended batches up to batch_pre_dawn_2200!")
    return True

if __name__ == "__main__":
    extend_batches()
