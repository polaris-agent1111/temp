#!/usr/bin/env python3
"""
Extend dispatcher with midnight and countdown batches:
- batch_pre_dawn_2230 (Tasks 0281, 0282, 0283)
- batch_pre_dawn_2300 (Tasks 0284, 0285, 0286)
- batch_pre_dawn_2330 (Tasks 0287, 0288, 0289)
"""

import sys
from pathlib import Path

def extend_midnight_batches():
    disp_path = Path("tools/zcode_continuous_dispatcher.py")
    content = disp_path.read_text(encoding="utf-8")

    new_batches_code = ''',
    # ---------------- 批次：batch_pre_dawn_2230 (22:30) ----------------
    {
        "batch_id": "batch_pre_dawn_2230",
        "target_time": "22:30",
        "tasks": [
            {
                "id": "0281",
                "title": "广义奈奎斯特稳定性判据在延迟网络流控中的严格解析证明",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0281 任务：广义奈奎斯特稳定性判据在延迟网络流控中的严格解析证明

## 任务背景
在复频域使用柯西辐角原理与 Nyquist 围道 D-contour 严格证明开环时滞传递函数无包含 (-1, j0) 临界点。

## 目标
验证特征行列式围绕 (-1, j0) 圈数 N=0，闭环右半平面极点数 P=0，系统渐进稳定。

## 预期产出路径
- `zcode/reports/0281-analysis.md`
- `docs/analysis/0281-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成理论审计写入 `docs/analysis/0281-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0281-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改实际提交凭据。
"""
            },
            {
                "id": "0282",
                "title": "QUIC 乱序重组窗口滑动下 CPU 缓存失效与内存带宽评估",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0282 任务：QUIC 乱序重组窗口滑动下 CPU 缓存失效与内存带宽评估

## 任务背景
测试高乱序度网络环境下 QUIC Stream 重组缓冲区的 L1/L2/L3 缓存未命中（Cache Miss）与内存带宽消耗。

## 目标
验证在乱序度 15% 下 L1 Cache Miss 率 <= 4.5%，重组吞吐衰减 <= 1.5%。

## 预期产出路径
- `zcode/reports/0282-analysis.md`
- `docs/analysis/0282-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成理论审计写入 `docs/analysis/0282-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0282-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改实际提交凭据。
"""
            },
            {
                "id": "0283",
                "title": "官方排行榜出分延迟与反爬限频窗口对抗自适应轮询策略",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0283 任务：官方排行榜出分延迟与反爬限频窗口对抗自适应轮询策略

## 任务背景
结合官方评测出分时间分布（8~25分钟）与防刷频 HTTP 429 规则，设计非线性自适应退避轮询器。

## 目标
验证在 60 分钟内查询请求数 <= 120 次，0 次触发 HTTP 429 限流，出分延迟感知误差 <= 15s。

## 预期产出路径
- `zcode/reports/0283-analysis.md`
- `docs/analysis/0283-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成理论审计写入 `docs/analysis/0283-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0283-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改实际提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_pre_dawn_2300 (23:00) ----------------
    {
        "batch_id": "batch_pre_dawn_2300",
        "target_time": "23:00",
        "tasks": [
            {
                "id": "0284",
                "title": "6 阶段流体排队模型下 Pontryagin 极大值原理连续最优控制轨线",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0284 任务：6 阶段流体排队模型下 Pontryagin 极大值原理连续最优控制轨线

## 任务背景
使用 Pontryagin 极大值原理（PMP）求解受控哈密顿系统（Hamiltonian），推导最优流控的协态方程与开关曲线。

## 目标
证明 Crown Fusion 前期饱和、后期退避的两阶段控制与 PMP 解析 Bang-Coast-Bang 极值轨线重合度 >= 96%。

## 预期产出路径
- `zcode/reports/0284-analysis.md`
- `docs/analysis/0284-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成理论审计写入 `docs/analysis/0284-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0284-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改实际提交凭据。
"""
            },
            {
                "id": "0285",
                "title": "跨平台 Windows/Linux 间高精度时钟源对齐与纳秒基准校准",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

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
"""
            },
            {
                "id": "0286",
                "title": "11/08 首发出征倒计时 1 小时战备总动员与五发参数终审会签",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0286 任务：11/08 首发出征倒计时 1 小时战备总动员与五发参数终审会签

## 任务背景
出征前 1 小时总动员，核验五发闭环候选配置 SHA-256 签名与门禁。

## 目标
签署 1 小时战备总动员证书 CERT-1H。

## 预期产出路径
- `zcode/reports/0286-analysis.md`
- `docs/analysis/0286-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成理论审计写入 `docs/analysis/0286-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0286-analysis.md`，状态修改为 `status: done`。

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
    print("Successfully extended batches up to batch_pre_dawn_2300!")
    return True

if __name__ == "__main__":
    extend_midnight_batches()
