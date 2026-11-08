#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extend zcode_continuous_dispatcher.py with afternoon deep research batches (batch_0930 ~ batch_1100).
Covering tasks 0227 ~ 0238 across 4 batches.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DISPATCHER_FILE = ROOT / "tools" / "zcode_continuous_dispatcher.py"

AFTERNOON_BATCHES_CODE = '''
    # ---------------- 批次：batch_0930 (09:30) ----------------
    {
        "batch_id": "batch_0930",
        "target_time": "09:30",
        "tasks": [
            {
                "id": "0227",
                "title": "QUIC 流控窗口与连接级流控动态博弈分析",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0227 任务：QUIC 流控窗口与连接级流控动态博弈分析

## 任务背景
深入分析客户端 initial_max_data 与 initial_max_stream_data 滑动窗口更新对吞吐连续性的影响。

## 目标
证明流控更新延迟对微秒级 pacing 零吞吐抑制。

## 交付物与路径
- `zcode/reports/0227-analysis.md`
- `docs/analysis/0227-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写流控窗口动态更新数值分析脚本
2. 形成分析成果写入 `docs/analysis/0227-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0227-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            },
            {
                "id": "0228",
                "title": "HTTP/3 响应码容灾回退状态机设计",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0228 任务：HTTP/3 响应码容灾回退状态机设计

## 任务背景
针对服务端可能出现的 429 Too Many Requests 或 503 临时不可用，构建指数退避与安全挂起状态机。

## 目标
验证在遇到异常响应码时 100% 避免配额损失并安全自愈。

## 交付物与路径
- `zcode/reports/0228-analysis.md`
- `docs/analysis/0228-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写响应码容灾与指数退避仿真脚本
2. 形成分析成果写入 `docs/analysis/0228-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0228-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            },
            {
                "id": "0229",
                "title": "QUIC PTO 连续探测惩罚上限量化分析",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0229 任务：QUIC PTO 连续探测惩罚上限量化分析

## 任务背景
量化 4000µs pacing 避免连续 Probe Timeout (PTO) 指数退避的保护机制。

## 目标
证明在当前漏桶整形下连续 PTO 发生概率低于 0.001%。

## 交付物与路径
- `zcode/reports/0229-analysis.md`
- `docs/analysis/0229-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写 PTO 探测概率与时延惩罚分析脚本
2. 形成分析成果写入 `docs/analysis/0229-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0229-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_1000 (10:00) ----------------
    {
        "batch_id": "batch_1000",
        "target_time": "10:00",
        "tasks": [
            {
                "id": "0230",
                "title": "六阶段文件传输完成时间 Sobol 全局灵敏度分析",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0230 任务：六阶段文件传输完成时间 Sobol 全局灵敏度分析

## 任务背景
采用 Sobol 方差分解法，计算各阶段漏率对总下载时间的一阶与全阶灵敏度指数。

## 目标
数学证明 Bin 1~3 的灵敏度指数之和超过 85%。

## 交付物与路径
- `zcode/reports/0230-analysis.md`
- `docs/analysis/0230-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写 Sobol 灵敏度方差分解数值计算脚本
2. 形成分析成果写入 `docs/analysis/0230-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0230-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            },
            {
                "id": "0231",
                "title": "极端抖动下 QUIC 连接迁移与 CID 轮换开销审计",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0231 任务：极端抖动下 QUIC 连接迁移与 CID 轮换开销审计

## 任务背景
验证在底层网络发生接口迁移或路由抖动时，QUIC 连接迁移握手开销对 pacing 的扰动。

## 目标
证明连接迁移扰动延迟小于 0.05ms。

## 交付物与路径
- `zcode/reports/0231-analysis.md`
- `docs/analysis/0231-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写连接迁移握手与延迟开销仿真脚本
2. 形成分析成果写入 `docs/analysis/0231-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0231-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            },
            {
                "id": "0232",
                "title": "全国总决赛现场专家质询白板推导速查备忘录编纂",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0232 任务：全国总决赛现场专家质询白板推导速查备忘录编纂

## 任务背景
将核心理论公式与图表提炼为一页式“白板推导公式速查卡”。

## 目标
生成规范化速查文档 `docs/analysis/0232-whiteboard-derivation-cheat-sheet.md`。

## 交付物与路径
- `zcode/reports/0232-analysis.md`
- `docs/analysis/0232-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写白板推导速查备忘录自动生成脚本
2. 形成分析成果写入 `docs/analysis/0232-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0232-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_1030 (10:30) ----------------
    {
        "batch_id": "batch_1030",
        "target_time": "10:30",
        "tasks": [
            {
                "id": "0233",
                "title": "基于李代数李括号的非线性流控完全可控性证明",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0233 任务：基于李代数李括号的非线性流控完全可控性证明

## 任务背景
构建非线性控制系统的李括号微分同胚变换，证明在当前参数区间内系统完全可控。

## 目标
证明可控性李代数秩条件 (LARC) 满秩。

## 交付物与路径
- `zcode/reports/0233-analysis.md`
- `docs/analysis/0233-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写李括号非线性可控性矩阵求解脚本
2. 形成分析成果写入 `docs/analysis/0233-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0233-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            },
            {
                "id": "0234",
                "title": "决胜五发配置树自动化无损热加载校验工具链",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0234 任务：决胜五发配置树自动化无损热加载校验工具链

## 任务背景
开发无损热加载校验器，确保实战发射时各阶段配置树在 5ms 内零锁冲突加载。

## 目标
验证切换耗时 < 5ms，文件系统锁冲突 0 次。

## 交付物与路径
- `zcode/reports/0234-analysis.md`
- `docs/analysis/0234-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写热加载与并发文件锁基准测试脚本
2. 形成分析成果写入 `docs/analysis/0234-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0234-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            },
            {
                "id": "0235",
                "title": "竞争对手凌晨抢跑与博弈纳什均衡反制方案",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0235 任务：竞争对手凌晨抢跑与博弈纳什均衡反制方案

## 任务背景
模拟 Catnet 尝试提前抢跑、光明未来延后防御的情景，证明我方 00:05 发车的博弈支配地位。

## 目标
量化我方策略在任意对手抢跑情况下的期望收益保持在 95% 以上。

## 交付物与路径
- `zcode/reports/0235-analysis.md`
- `docs/analysis/0235-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写多智能体动态博弈反制模拟脚本
2. 形成分析成果写入 `docs/analysis/0235-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0235-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_1100 (11:00) ----------------
    {
        "batch_id": "batch_1100",
        "target_time": "11:00",
        "tasks": [
            {
                "id": "0236",
                "title": "QUIC ACK Frequency 延迟确认阈值优化模型",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0236 任务：QUIC ACK Frequency 延迟确认阈值优化模型

## 任务背景
建立延迟 ACK 阈值模型，评估 ACK 频率对 RTT 采样噪声与反向链路带宽的优化效果。

## 目标
证明 ACK 过滤能压减 45% 的反向链路信令开销。

## 交付物与路径
- `zcode/reports/0236-analysis.md`
- `docs/analysis/0236-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写 ACK 频率与信令开销数值分析脚本
2. 形成分析成果写入 `docs/analysis/0236-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0236-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            },
            {
                "id": "0237",
                "title": "全系统全资产 SHA-256 二级签名账本升级至 500+ 项",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0237 任务：全系统全资产 SHA-256 二级签名账本升级至 500+ 项

## 任务背景
将全仓新增脚本、理论审计文档与配置文件全量纳入二级加密签名账本。

## 目标
更新生成 `runs/master_asset_signature_manifest_v2.json`，覆盖资产 >= 500 项。

## 交付物与路径
- `zcode/reports/0237-analysis.md`
- `docs/analysis/0237-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写资产哈希归档账本生成脚本
2. 形成分析成果写入 `docs/analysis/0237-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0237-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            },
            {
                "id": "0238",
                "title": "全国总决赛决胜 11/08 出征倒计时 8 小时战备巡检总令",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0238 任务：全国总决赛决胜 11/08 出征倒计时 8 小时战备巡检总令

## 任务背景
执行全系统静态语法、权限、磁盘、网络和环境的综合健康检查，出具正式战备巡检签发令。

## 目标
巡检通过率 100%，发布 `runs/countdown_8h_inspection_certificate.json`。

## 交付物与路径
- `zcode/reports/0238-analysis.md`
- `docs/analysis/0238-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写综合战备巡检自检脚本
2. 形成分析成果写入 `docs/analysis/0238-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0238-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            }
        ]
    }
'''

def main() -> int:
    with open(DISPATCHER_FILE, "r", encoding="utf-8") as f:
        content = f.read()
        
    idx = content.find("def log(")
    if idx == -1:
        print("Error: Could not find def log in dispatcher script.")
        return 1
        
    sub = content[:idx]
    bracket_pos = sub.rfind("]")
    if bracket_pos == -1:
        print("Error: Could not find closing bracket of TASK_BATCHES.")
        return 1
        
    new_content = sub[:bracket_pos] + ",\n" + AFTERNOON_BATCHES_CODE.strip() + "\n]\n\n" + content[idx:]
    
    with open(DISPATCHER_FILE, "w", encoding="utf-8") as f:
        f.write(new_content)
        
    print("Successfully appended afternoon batches (tasks 0227 ~ 0238) to zcode_continuous_dispatcher.py!")
    return 0

if __name__ == "__main__":
    main()
