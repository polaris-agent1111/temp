#!/usr/bin/env python3
"""
Extend dispatcher with pre-dawn 23:30 and dawn 00:00 batches:
- batch_pre_dawn_2330 (Tasks 0287, 0288, 0289)
- batch_dawn_0000 (Tasks 0290, 0291, 0292)
"""

import sys
from pathlib import Path

def extend_dawn_batches():
    disp_path = Path("tools/zcode_continuous_dispatcher.py")
    content = disp_path.read_text(encoding="utf-8")

    new_batches_code = ''',
    # ---------------- 批次：batch_pre_dawn_2330 (23:30) ----------------
    {
        "batch_id": "batch_pre_dawn_2330",
        "target_time": "23:30",
        "tasks": [
            {
                "id": "0287",
                "title": "客户端网络套接字非阻塞缓冲收发边界吞吐测试",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0287 任务：客户端网络套接字非阻塞缓冲收发边界吞吐测试

## 任务背景
在 UDP socket 发送缓冲区（SO_SNDBUF）与接收缓冲区（SO_RCVBUF）处于不同水位时的非阻塞系统调用（sendto / recvfrom / recvmmsg）性能。

## 目标
验证在非阻塞 O_NONBLOCK 模式下，单次发包系统调用耗时 <= 1.8us，零 ENOBUFS 错误。

## 预期产出路径
- `zcode/reports/0287-analysis.md`
- `docs/analysis/0287-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成理论审计写入 `docs/analysis/0287-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0287-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改实际提交凭据。
"""
            },
            {
                "id": "0288",
                "title": "竞争对手历史提交时间间隔与深夜挂机概率分布贝叶斯先验推断",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0288 任务：竞争对手历史提交时间间隔与深夜挂机概率分布贝叶斯先验推断

## 任务背景
统计分析全国 Top 5 对手在 00:00~03:00 的提交频率，建立贝叶斯先验模型预测对手深夜撞车概率。

## 目标
量化 00:05 出征窗口的信道碰撞概率（验证 <= 5.0%）。

## 预期产出路径
- `zcode/reports/0288-analysis.md`
- `docs/analysis/0288-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成理论审计写入 `docs/analysis/0288-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0288-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改实际提交凭据。
"""
            },
            {
                "id": "0289",
                "title": "11/08 00:00 额度解锁前 30 分钟全系统预热与守护进程就位演练",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0289 任务：11/08 00:00 额度解锁前 30 分钟全系统预热与守护进程就位演练

## 任务背景
出征前半小时全系统状态预热、网络连接保活（Keep-alive）与本地锁机制核验。

## 目标
验证状态加载时延 <= 10ms，锁文件原子性 100% 成立。

## 预期产出路径
- `zcode/reports/0289-analysis.md`
- `docs/analysis/0289-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成理论审计写入 `docs/analysis/0289-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0289-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改实际提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_dawn_0000 (00:00) ----------------
    {
        "batch_id": "batch_dawn_0000",
        "target_time": "00:00",
        "tasks": [
            {
                "id": "0290",
                "title": "11/08 00:00 官方天梯额度重置瞬态探测与可用性确立",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0290 任务：11/08 00:00 官方天梯额度重置瞬态探测与可用性确立

## 任务背景
在 00:00 官方额度刷新瞬间，执行被动式只读额度探测，确认当日剩余提交额度恢复至 5 次。

## 目标
验证额度解锁状态确立，且零提前非法消耗。

## 预期产出路径
- `zcode/reports/0290-analysis.md`
- `docs/analysis/0290-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成理论审计写入 `docs/analysis/0290-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0290-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改实际提交凭据。
"""
            },
            {
                "id": "0291",
                "title": "Shot 1 发射前 5 分钟在途流量探针校验与信道基线锁定",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0291 任务：Shot 1 发射前 5 分钟在途流量探针校验与信道基线锁定

## 任务背景
首发前 5 分钟对网络基线 RTT 与抖动作最后核验，锁定 Shot 1 初始配置。

## 目标
确认基线 RTT 处于 10ms 正常区间。

## 预期产出路径
- `zcode/reports/0291-analysis.md`
- `docs/analysis/0291-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成理论审计写入 `docs/analysis/0291-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0291-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改实际提交凭据。
"""
            },
            {
                "id": "0292",
                "title": "1-by-1 串行闭环自适应流水线首发点火令与最终指纹封存",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0292 任务：1-by-1 串行闭环自适应流水线首发点火令与最终指纹封存

## 任务背景
00:05 首发点火执行令签发，五发闭环决策树锁定。

## 目标
签发首发出征令 CERT-IGNITION。

## 预期产出路径
- `zcode/reports/0292-analysis.md`
- `docs/analysis/0292-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成理论审计写入 `docs/analysis/0292-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0292-analysis.md`，状态修改为 `status: done`。

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
    print("Successfully extended batches up to batch_dawn_0000!")
    return True

if __name__ == "__main__":
    extend_dawn_batches()
