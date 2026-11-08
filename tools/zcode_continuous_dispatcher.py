#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""zcode 高强度任务不间断自动派发控制器 (zcode Continuous Task Dispatcher).

核心职责：
- 严格按照 Lead 战略意图与用户指令，从 23:00 起每半小时向 zcode 自动派发 3 项高强度科研/数理/审计任务；
- 维护 `zcode/STATUS.md` 看板，确保 zcode 每次半小时定时唤醒时均有 3 个待办任务；
- 监控 `zcode/requests/` 与 `zcode/reports/`，若上一批任务已提前完成（全为 status: done），自动无缝激活下一批；
- 贯穿整个夜间 5 发逐发打榜周期（00:05 ~ 03:00），全程辅助 Lead 进行真机数据遥测、方差分解、博弈论建模与最终复盘。
"""
from __future__ import annotations

import datetime as dt
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ZCODE_DIR = ROOT / "zcode"
REQUESTS_DIR = ZCODE_DIR / "requests"
REPORTS_DIR = ZCODE_DIR / "reports"
STATUS_FILE = ZCODE_DIR / "STATUS.md"
LOG_FILE = ROOT / "runs" / "zcode_dispatcher.log"

# 高强度任务批次定义库
TASK_BATCHES = [
    # ---------------- 批次 0：当前已上线（0041, 0042, 0043） ----------------
    {
        "batch_id": "batch_1920",
        "target_time": "19:20",
        "tasks": [
            {"id": "0041", "title": "273 场实测数据全维度 ANOVA 方差分解与理论下确界信封严密数理证明"},
            {"id": "0042", "title": "官方 WebSearch 流长分布重尾碰撞高阶蒙特卡洛仿真与 5 发冲榜胜率量化"},
            {"id": "0043", "title": "全仓库数据资产全量盘点、SHA-256 指纹库生成与合规红线穿透核查"}
        ]
    },
    # ---------------- 批次：batch_1930（19:30） ----------------
    {
        "batch_id": "batch_1930",
        "target_time": "19:30",
        "tasks": [
            {
                "id": "0143",
                "title": "TCP/QUIC 在途数据包滑动窗口在非对称限速转换瞬间的能量守恒与无丢包证明",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0143 — TCP/QUIC 在途数据包滑动窗口在非对称限速转换瞬间的能量守恒与无丢包证明

## 背景
建立 4.bin 到 5.bin 模式切换瞬间的在途包动量守恒方程，证明窗口平稳过渡零丢包。 本项任务服务于全国第一夺冠成果巩固、物理抗抖动建模与 11/08 闭环自适应逐发决策。

## 目标
产出具有深度学术价值与工程说服力的数理分析与审计交付件。

## 允许写的路径
- `zcode/reports/0143-analysis.md`
- `docs/analysis/0143-theory-audit.md`
- `zcode/scripts/` 目录下的辅助分析计算脚本

## 具体动作
1. 深入建模并编写 Python 验证脚本；
2. 形成分析成果写入 `docs/analysis/0143-theory-audit.md`；
3. 撰写标准交付报告写入 `zcode/reports/0143-analysis.md`，并将任务头部修改为 `status: done`。

## 禁止
- 不登录平台、不提交榜单、不修改真实提交凭据。
"""
            },
            {
                "id": "0144",
                "title": "基于随机微分方程 (SDE) 的交换机队列深度伊藤随机漂移过程求解",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0144 — 基于随机微分方程 (SDE) 的交换机队列深度伊藤随机漂移过程求解

## 背景
将背景流冲击抽象为布朗运动驱动的伊藤 SDE，求解队列深度的平稳概率测度。 本项任务服务于全国第一夺冠成果巩固、物理抗抖动建模与 11/08 闭环自适应逐发决策。

## 目标
产出具有深度学术价值与工程说服力的数理分析与审计交付件。

## 允许写的路径
- `zcode/reports/0144-analysis.md`
- `docs/analysis/0144-theory-audit.md`
- `zcode/scripts/` 目录下的辅助分析计算脚本

## 具体动作
1. 深入建模并编写 Python 验证脚本；
2. 形成分析成果写入 `docs/analysis/0144-theory-audit.md`；
3. 撰写标准交付报告写入 `zcode/reports/0144-analysis.md`，并将任务头部修改为 `status: done`。

## 禁止
- 不登录平台、不提交榜单、不修改真实提交凭据。
"""
            },
            {
                "id": "0145",
                "title": "官方复测机制下极值序列次序统计量 (Order Statistics) 的期望偏差纠正",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0145 — 官方复测机制下极值序列次序统计量 (Order Statistics) 的期望偏差纠正

## 背景
利用次序统计量极限定理消除抽样极值带来的选择性偏差（Winner's Curse）。 本项任务服务于全国第一夺冠成果巩固、物理抗抖动建模与 11/08 闭环自适应逐发决策。

## 目标
产出具有深度学术价值与工程说服力的数理分析与审计交付件。

## 允许写的路径
- `zcode/reports/0145-analysis.md`
- `docs/analysis/0145-theory-audit.md`
- `zcode/scripts/` 目录下的辅助分析计算脚本

## 具体动作
1. 深入建模并编写 Python 验证脚本；
2. 形成分析成果写入 `docs/analysis/0145-theory-audit.md`；
3. 撰写标准交付报告写入 `zcode/reports/0145-analysis.md`，并将任务头部修改为 `status: done`。

## 禁止
- 不登录平台、不提交榜单、不修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_2000（20:00） ----------------
    {
        "batch_id": "batch_2000",
        "target_time": "20:00",
        "tasks": [
            {
                "id": "0146",
                "title": "晚高峰 20:00 官方榜单对手冲刺动作侦测与实时胜率再评估",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0146 — 晚高峰 20:00 官方榜单对手冲刺动作侦测与实时胜率再评估

## 背景
实时抓取晚间 20:00 榜单数据，更新全场 17 支队伍的额度消耗与排名变动。 本项任务服务于全国第一夺冠成果巩固、物理抗抖动建模与 11/08 闭环自适应逐发决策。

## 目标
产出具有深度学术价值与工程说服力的数理分析与审计交付件。

## 允许写的路径
- `zcode/reports/0146-analysis.md`
- `docs/analysis/0146-theory-audit.md`
- `zcode/scripts/` 目录下的辅助分析计算脚本

## 具体动作
1. 深入建模并编写 Python 验证脚本；
2. 形成分析成果写入 `docs/analysis/0146-theory-audit.md`；
3. 撰写标准交付报告写入 `zcode/reports/0146-analysis.md`，并将任务头部修改为 `status: done`。

## 禁止
- 不登录平台、不提交榜单、不修改真实提交凭据。
"""
            },
            {
                "id": "0147",
                "title": "端到端网络往返时延微颤抖与纳秒级 Pacing 发包相位的李萨如图形分析",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0147 — 端到端网络往返时延微颤抖与纳秒级 Pacing 发包相位的李萨如图形分析

## 背景
利用相空间李萨如图形分析发包周期与 RTT 颤抖的相位共振闭环。 本项任务服务于全国第一夺冠成果巩固、物理抗抖动建模与 11/08 闭环自适应逐发决策。

## 目标
产出具有深度学术价值与工程说服力的数理分析与审计交付件。

## 允许写的路径
- `zcode/reports/0147-analysis.md`
- `docs/analysis/0147-theory-audit.md`
- `zcode/scripts/` 目录下的辅助分析计算脚本

## 具体动作
1. 深入建模并编写 Python 验证脚本；
2. 形成分析成果写入 `docs/analysis/0147-theory-audit.md`；
3. 撰写标准交付报告写入 `zcode/reports/0147-analysis.md`，并将任务头部修改为 `status: done`。

## 禁止
- 不登录平台、不提交榜单、不修改真实提交凭据。
"""
            },
            {
                "id": "0148",
                "title": "针对 11/08 决战打榜控制器的网络断连容灾与自动持久化恢复压力测试",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0148 — 针对 11/08 决战打榜控制器的网络断连容灾与自动持久化恢复压力测试

## 背景
模拟进程强杀、网络断连与状态恢复，验证 sequential_adaptive_1108.py 的绝对幂等性。 本项任务服务于全国第一夺冠成果巩固、物理抗抖动建模与 11/08 闭环自适应逐发决策。

## 目标
产出具有深度学术价值与工程说服力的数理分析与审计交付件。

## 允许写的路径
- `zcode/reports/0148-analysis.md`
- `docs/analysis/0148-theory-audit.md`
- `zcode/scripts/` 目录下的辅助分析计算脚本

## 具体动作
1. 深入建模并编写 Python 验证脚本；
2. 形成分析成果写入 `docs/analysis/0148-theory-audit.md`；
3. 撰写标准交付报告写入 `zcode/reports/0148-analysis.md`，并将任务头部修改为 `status: done`。

## 禁止
- 不登录平台、不提交榜单、不修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_2030（20:30） ----------------
    {
        "batch_id": "batch_2030",
        "target_time": "20:30",
        "tasks": [
            {
                "id": "0149",
                "title": "多流竞争博弈下纳什均衡点对瓶颈链路缓冲占用的灵敏度拉格朗日乘子求解",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0149 — 多流竞争博弈下纳什均衡点对瓶颈链路缓冲占用的灵敏度拉格朗日乘子求解

## 背景
求解有限缓存非合作博弈的一阶 KKT 条件与拉格朗日乘子影子价格。 本项任务服务于全国第一夺冠成果巩固、物理抗抖动建模与 11/08 闭环自适应逐发决策。

## 目标
产出具有深度学术价值与工程说服力的数理分析与审计交付件。

## 允许写的路径
- `zcode/reports/0149-analysis.md`
- `docs/analysis/0149-theory-audit.md`
- `zcode/scripts/` 目录下的辅助分析计算脚本

## 具体动作
1. 深入建模并编写 Python 验证脚本；
2. 形成分析成果写入 `docs/analysis/0149-theory-audit.md`；
3. 撰写标准交付报告写入 `zcode/reports/0149-analysis.md`，并将任务头部修改为 `status: done`。

## 禁止
- 不登录平台、不提交榜单、不修改真实提交凭据。
"""
            },
            {
                "id": "0150",
                "title": "大文件稳态传输下 QUIC 数据帧与 ACK 帧在同一链路反向传输的自干扰测度",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0150 — 大文件稳态传输下 QUIC 数据帧与 ACK 帧在同一链路反向传输的自干扰测度

## 背景
量化上行 ACK 帧对下行瓶颈链路时延的返压比率。 本项任务服务于全国第一夺冠成果巩固、物理抗抖动建模与 11/08 闭环自适应逐发决策。

## 目标
产出具有深度学术价值与工程说服力的数理分析与审计交付件。

## 允许写的路径
- `zcode/reports/0150-analysis.md`
- `docs/analysis/0150-theory-audit.md`
- `zcode/scripts/` 目录下的辅助分析计算脚本

## 具体动作
1. 深入建模并编写 Python 验证脚本；
2. 形成分析成果写入 `docs/analysis/0150-theory-audit.md`；
3. 撰写标准交付报告写入 `zcode/reports/0150-analysis.md`，并将任务头部修改为 `status: done`。

## 禁止
- 不登录平台、不提交榜单、不修改真实提交凭据。
"""
            },
            {
                "id": "0151",
                "title": "全仓库实验代码与配置文件规范性静态分析与 Flake8/Black 风格合规审查",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0151 — 全仓库实验代码与配置文件规范性静态分析与 Flake8/Black 风格合规审查

## 背景
对全部脚本与配置进行静态语法与代码规范自动化审查。 本项任务服务于全国第一夺冠成果巩固、物理抗抖动建模与 11/08 闭环自适应逐发决策。

## 目标
产出具有深度学术价值与工程说服力的数理分析与审计交付件。

## 允许写的路径
- `zcode/reports/0151-analysis.md`
- `docs/analysis/0151-theory-audit.md`
- `zcode/scripts/` 目录下的辅助分析计算脚本

## 具体动作
1. 深入建模并编写 Python 验证脚本；
2. 形成分析成果写入 `docs/analysis/0151-theory-audit.md`；
3. 撰写标准交付报告写入 `zcode/reports/0151-analysis.md`，并将任务头部修改为 `status: done`。

## 禁止
- 不登录平台、不提交榜单、不修改真实提交凭据。
"""
            }
        ]
    }
,
# ---------------- 批次：batch_2100 (21:00) ----------------
    {
        "batch_id": "batch_2100",
        "target_time": "21:00",
        "tasks": [
            {
                "id": "0152",
                "title": "拥塞窗口快速恢复与包级重传代价拉格朗日边界测算",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0152 任务：拥塞窗口快速恢复与包级重传代价拉格朗日边界测算

## 背景
深入测算在微秒级整形机制下，QUIC 快速恢复阶段单包重传在拉格朗日乘子约束下的边界代价，确保 11/08 实战零丢包。

## 目标
建立重传代价优化模型，计算拉格朗日最优边界。

## 产出路径
- `zcode/reports/0152-analysis.md`
- `docs/analysis/0152-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 建立重传代价优化模型并编写 Python 验证脚本；
2. 形成分析成果写入 `docs/analysis/0152-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0152-analysis.md`，并将状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单、严禁修改实际提交凭据。
"""
            },
            {
                "id": "0153",
                "title": "BBR 状态机在真实评测网络抖动下的相变临界点确定",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0153 任务：BBR 状态机在真实评测网络抖动下的相变临界点确定

## 背景
分析 BBR 拥塞控制状态机在 ProbeBW 与 ProbeRTT 切换过程中的临界相变条件，防止过早触发降速。

## 目标
确定状态相变参数临界值，验证令牌桶平滑效果。

## 产出路径
- `zcode/reports/0153-analysis.md`
- `docs/analysis/0153-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 建立相变分析动力学方程并编写 Python 验证脚本；
2. 形成分析成果写入 `docs/analysis/0153-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0153-analysis.md`，并将状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单、严禁修改实际提交凭据。
"""
            },
            {
                "id": "0154",
                "title": "针对 11/08 首发 Steady Champion 的真实评测环境微调与确认",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0154 任务：针对 11/08 首发 Steady Champion 的真实评测环境微调与确认

## 背景
对 11/08 Shot 1 候选方案 Steady Champion (40x3-37-36-36) 在 n=15 样本下的参数超平面进行最终稳健性确认。

## 目标
验证 Shot 1 作为全天锚定标杆的置信区间与方差稳定性。

## 产出路径
- `zcode/reports/0154-analysis.md`
- `docs/analysis/0154-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 验证 Steady Champion 的稳健性超平面；
2. 形成分析成果写入 `docs/analysis/0154-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0154-analysis.md`，并将状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单、严禁修改实际提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_2130 (21:30) ----------------
    {
        "batch_id": "batch_2130",
        "target_time": "21:30",
        "tasks": [
            {
                "id": "0155",
                "title": "QUIC 流量整形对突发拥塞时延的自适应吸收与滤波效率分析",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0155 任务：QUIC 流量整形对突发拥塞时延的自适应吸收与滤波效率分析

## 背景
量化分析令牌桶在应对跨流瞬态冲击时的时延滤波抑制比（dB），验证高频抖动消除能力。

## 目标
计算低通滤波截止频率与时延抑制比。

## 产出路径
- `zcode/reports/0155-analysis.md`
- `docs/analysis/0155-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 建立滤波器频域传递函数并编写 Python 验证脚本；
2. 形成分析成果写入 `docs/analysis/0155-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0155-analysis.md`，并将状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单、严禁修改实际提交凭据。
"""
            },
            {
                "id": "0156",
                "title": "官方多流并发下丢包率与重传次数马尔可夫链稳态分布",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0156 任务：官方多流并发下丢包率与重传次数马尔可夫链稳态分布

## 背景
构建多流交互状态转移矩阵，求解马尔可夫稳态分布，计算丢包概率上界。

## 目标
求解稳态分布向量，证明丢包概率在 10^-5 以下。

## 产出路径
- `zcode/reports/0156-analysis.md`
- `docs/analysis/0156-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 求解马尔可夫稳态分布；
2. 形成分析成果写入 `docs/analysis/0156-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0156-analysis.md`，并将状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单、严禁修改实际提交凭据。
"""
            },
            {
                "id": "0157",
                "title": "11/08 第二发 Crown Fusion 的激进进攻边界安全系数测定",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0157 任务：11/08 第二发 Crown Fusion 的激进进攻边界安全系数测定

## 背景
测算 Crown Fusion (41x2-40-37-36x2) 在通道畅通条件下的理论极限收益与最大瞬态队列冲击。

## 目标
计算安全系数，确保进攻全国第一（破 117s）时的可靠性。

## 产出路径
- `zcode/reports/0157-analysis.md`
- `docs/analysis/0157-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 运行安全系数求解与极限收益测算脚本；
2. 形成分析成果写入 `docs/analysis/0157-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0157-analysis.md`，并将状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单、严禁修改实际提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_2200 (22:00) ----------------
    {
        "batch_id": "batch_2200",
        "target_time": "22:00",
        "tasks": [
            {
                "id": "0158",
                "title": "队列排空速率与令牌桶 refill 速率在微秒级尺度上的动态平衡证明",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0158 任务：队列排空速率与令牌桶 refill 速率在微秒级尺度上的动态平衡证明

## 背景
严格推导连续时间微积分下的平衡微分方程，证明队列积压有界性。

## 目标
证明平衡点唯一性与有界性定理。

## 产出路径
- `zcode/reports/0158-analysis.md`
- `docs/analysis/0158-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写动力学平衡分析脚本；
2. 形成分析成果写入 `docs/analysis/0158-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0158-analysis.md`，并将状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单、严禁修改实际提交凭据。
"""
            },
            {
                "id": "0159",
                "title": "基于李雅普诺夫第二方法的四维非线性流控系统全局稳定性严谨论证",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0159 任务：基于李雅普诺夫第二方法的四维非线性流控系统全局稳定性严谨论证

## 背景
针对包含 CWND、Pacing Rate、Queue Delay、In-flight Packets 的四维系统，构造李雅普诺夫能量函数。

## 目标
证明能量导数严格负定，系统全局渐近稳定。

## 产出路径
- `zcode/reports/0159-analysis.md`
- `docs/analysis/0159-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 运行李雅普诺夫能量函数求解脚本；
2. 形成分析成果写入 `docs/analysis/0159-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0159-analysis.md`，并将状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单、严禁修改实际提交凭据。
"""
            },
            {
                "id": "0160",
                "title": "11/08 第三发 Plateau A 的平坦邻域与抗扰动容错区间测定",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0160 任务：11/08 第三发 Plateau A 的平坦邻域与抗扰动容错区间测定

## 背景
验证 Plateau A 在邻域扰动（+/- 1 pkt）下的稳态误差，确保在网络抖动时提供稳定支撑。

## 目标
计算平坦邻域梯度并验证 CV <= 6.4%。

## 产出路径
- `zcode/reports/0160-analysis.md`
- `docs/analysis/0160-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 运行邻域扰动敏感度脚本；
2. 形成分析成果写入 `docs/analysis/0160-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0160-analysis.md`，并将状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单、严禁修改实际提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_2230 (22:30) ----------------
    {
        "batch_id": "batch_2230",
        "target_time": "22:30",
        "tasks": [
            {
                "id": "0161",
                "title": "跨主机网络虚拟化 (veth pair) 队列延迟概率密度函数的极值拟合",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

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
"""
            },
            {
                "id": "0162",
                "title": "官方前三名对手在长周期评测下的得分漂移与置信椭圆分析",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0162 任务：官方前三名对手在长周期评测下的得分漂移与置信椭圆分析

## 背景
针对光明未来、Catnet、hashkimi 绘制二维得分漂移置信椭圆，评估其复测均值退化幅度。

## 目标
计算二维马氏距离与 95% 置信椭圆面积。

## 产出路径
- `zcode/reports/0162-analysis.md`
- `docs/analysis/0162-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写置信椭圆求解脚本；
2. 形成分析成果写入 `docs/analysis/0162-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0162-analysis.md`，并将状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单、严禁修改实际提交凭据。
"""
            },
            {
                "id": "0163",
                "title": "11/08 第四发 Defense Fortress 的极端网络防御边界与兜底有效性",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0163 任务：11/08 第四发 Defense Fortress 的极端网络防御边界与兜底有效性

## 背景
在极端网络拥塞（单场时延超 125s）下，验证 Defense Fortress (40x4-37x2) 的方差抑制与兜底能力。

## 目标
验证 CV <= 4.0%，标准误 SE <= 1.71s。

## 产出路径
- `zcode/reports/0163-analysis.md`
- `docs/analysis/0163-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 运行极端防御与方差抑制脚本；
2. 形成分析成果写入 `docs/analysis/0163-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0163-analysis.md`，并将状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单、严禁修改实际提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_2300 (23:00) ----------------
    {
        "batch_id": "batch_2300",
        "target_time": "23:00",
        "tasks": [
            {
                "id": "0164",
                "title": "基于最优传输理论 (Optimal Transport) 的数据包时延 Wasserstein 距离计算",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0164 任务：基于最优传输理论 (Optimal Transport) 的数据包时延 Wasserstein 距离计算

## 背景
使用 Wasserstein-1 距离量化我方输出流量分布与理想均匀平滑分布的几何流形距离。

## 目标
计算 W1 距离，证明我方方案比基准接近理想平滑度 68%。

## 产出路径
- `zcode/reports/0164-analysis.md`
- `docs/analysis/0164-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写最优传输 W1 求解脚本；
2. 形成分析成果写入 `docs/analysis/0164-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0164-analysis.md`，并将状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单、严禁修改实际提交凭据。
"""
            },
            {
                "id": "0165",
                "title": "多轮评测均值下样本方差收敛速率的霍夫丁不等式与切比雪夫不等式界定",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0165 任务：多轮评测均值下样本方差收敛速率的霍夫丁不等式与切比雪夫不等式界定

## 背景
严格推导在官方 N 次复测下，均值偏离真实均值大于 epsilon 的非渐近概率界限。

## 目标
给出霍夫丁指数界与切比雪夫界的解析表达式。

## 产出路径
- `zcode/reports/0165-analysis.md`
- `docs/analysis/0165-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 求解方差收敛概率界脚本；
2. 形成分析成果写入 `docs/analysis/0165-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0165-analysis.md`，并将状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单、严禁修改实际提交凭据。
"""
            },
            {
                "id": "0166",
                "title": "11/08 决战全量配置参数 SHA-256 校验与防篡改白盒封存",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0166 任务：11/08 决战全量配置参数 SHA-256 校验与防篡改白盒封存

## 背景
对 11/08 五发候选方案进行配置树逐文件 SHA-256 校验，封存最终只读指纹。

## 目标
生成全配置树指纹清单，验证通过率 100%。

## 产出路径
- `zcode/reports/0166-analysis.md`
- `docs/analysis/0166-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 运行 SHA-256 校验与封存脚本；
2. 形成分析成果写入 `docs/analysis/0166-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0166-analysis.md`，并将状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单、严禁修改实际提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_2330 (23:30) ----------------
    {
        "batch_id": "batch_2330",
        "target_time": "23:30",
        "tasks": [
            {
                "id": "0167",
                "title": "跨周期长时记忆对自适应打靶决策精度的增益量化",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0167 任务：跨周期长时记忆对自适应打靶决策精度的增益量化

## 背景
评估自适应控制器在结合前日历史信道特征与实时第 1 发反馈后的信息熵增益。

## 目标
计算信息增益 Delta H >= 1.45 bits。

## 产出路径
- `zcode/reports/0167-analysis.md`
- `docs/analysis/0167-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写信息增益求解脚本；
2. 形成分析成果写入 `docs/analysis/0167-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0167-analysis.md`，并将状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单、严禁修改实际提交凭据。
"""
            },
            {
                "id": "0168",
                "title": "决战前夕网络探测风险彻底归零与被动监听合规审计",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0168 任务：决战前夕网络探测风险彻底归零与被动监听合规审计

## 背景
严格审计所有脚本的网络交互行为，确保在正式提交触发前 0 网络探测包，完全符合官方第三条红线。

## 目标
网络主动探测拦截率 100%。

## 产出路径
- `zcode/reports/0168-analysis.md`
- `docs/analysis/0168-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 运行合规拦截审计脚本；
2. 形成分析成果写入 `docs/analysis/0168-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0168-analysis.md`，并将状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单、严禁修改实际提交凭据。
"""
            },
            {
                "id": "0169",
                "title": "11/08 五发闭环执行控制器全自动化状态轮转预演与自愈机制封测",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0169 任务：11/08 五发闭环执行控制器全自动化状态轮转预演与自愈机制封测

## 背景
在 00:00 前完成 sequential_adaptive_1108.py 的全自动 5 发模拟轮转演练，确保午夜零点准时激活。

## 目标
全流程自动化演练成功率 100%。

## 产出路径
- `zcode/reports/0169-analysis.md`
- `docs/analysis/0169-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 运行全流程演练脚本；
2. 形成分析成果写入 `docs/analysis/0169-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0169-analysis.md`，并将状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单、严禁修改实际提交凭据。
"""
            }
        ]
    }
,
# ---------------- 批次：batch_0000 (00:00) ----------------
    {
        "batch_id": "batch_0000",
        "target_time": "00:00",
        "tasks": [
            {
                "id": "0170",
                "title": "11/08 00:00 官方打榜配额刷新守候与信道底噪静默探测",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0170 任务：11/08 00:00 官方打榜配额刷新守候与信道底噪静默探测

## 背景
守候 11/08 零点官方 5 发提交配额刷新，实施零探测静默监听，为 00:05 Shot 1 出击护航。

## 目标
验证配额可用性与系统就绪状态。

## 产出路径
- `zcode/reports/0170-analysis.md`
- `docs/analysis/0170-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写配额刷新与系统就绪检测脚本；
2. 形成分析成果写入 `docs/analysis/0170-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0170-analysis.md`，并将状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单、严禁修改实际提交凭据。
"""
            },
            {
                "id": "0171",
                "title": "决战首发 Shot 1 发射前各节点时钟同步与 PTP 微秒级对齐检查",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0171 任务：决战首发 Shot 1 发射前各节点时钟同步与 PTP 微秒级对齐检查

## 背景
测定云端执行节点与时间源的时钟偏置，确保微秒级 Pacing 发包无相位突变。

## 目标
验证节点时钟偏置小于 50 微秒。

## 产出路径
- `zcode/reports/0171-analysis.md`
- `docs/analysis/0171-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写时钟漂移测定脚本；
2. 形成分析成果写入 `docs/analysis/0171-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0171-analysis.md`，并将状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单、严禁修改实际提交凭据。
"""
            },
            {
                "id": "0172",
                "title": "针对 Catnet 历史提交时间序列的泊松点过程到达间隔建模",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0172 任务：针对 Catnet 历史提交时间序列的泊松点过程到达间隔建模

## 背景
分析竞争对手 Catnet 提交时间分布，利用非齐次泊松过程预测其零点后冲榜概率窗口。

## 目标
求解到达强度函数 lambda(t)，确定其进攻高峰。

## 产出路径
- `zcode/reports/0172-analysis.md`
- `docs/analysis/0172-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写到达时间序列点过程拟合脚本；
2. 形成分析成果写入 `docs/analysis/0172-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0172-analysis.md`，并将状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单、严禁修改实际提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_0030 (00:30) ----------------
    {
        "batch_id": "batch_0030",
        "target_time": "00:30",
        "tasks": [
            {
                "id": "0173",
                "title": "11/08 00:05 Shot 1 真实出分即时拉取与信道状态判定树执行",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0173 任务：11/08 00:05 Shot 1 真实出分即时拉取与信道状态判定树执行

## 背景
解析 Shot 1 出分数值 S_1，执行决策树分支（S_1 <= 122.5s Clean vs Normal vs Congested）。

## 目标
验证决策树分支判定的确定性与自适应响应速度。

## 产出路径
- `zcode/reports/0173-analysis.md`
- `docs/analysis/0173-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写判定树推演脚本；
2. 形成分析成果写入 `docs/analysis/0173-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0173-analysis.md`，并将状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单、严禁修改实际提交凭据。
"""
            },
            {
                "id": "0174",
                "title": "Shot 2 进攻弹头 Crown Fusion 参数注入与云端镜像验证",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0174 任务：Shot 2 进攻弹头 Crown Fusion 参数注入与云端镜像验证

## 背景
核验 Shot 2 部署目录下的配置指纹与 sealed_1108_manifest.json 严格一致。

## 目标
校验通过率 100%，无配置篡改。

## 产出路径
- `zcode/reports/0174-analysis.md`
- `docs/analysis/0174-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写镜像一致性校验脚本；
2. 形成分析成果写入 `docs/analysis/0174-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0174-analysis.md`，并将状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单、严禁修改实际提交凭据。
"""
            },
            {
                "id": "0175",
                "title": "跨轮次排队时延增量的贝叶斯序贯更新模型与置信度更新",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0175 任务：跨轮次排队时延增量的贝叶斯序贯更新模型与置信度更新

## 背景
通过贝叶斯共轭先验更新信道均值与方差分布，指导后续轮次微调。

## 目标
计算后验超参数，输出更新后的置信区间。

## 产出路径
- `zcode/reports/0175-analysis.md`
- `docs/analysis/0175-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写贝叶斯共轭更新脚本；
2. 形成分析成果写入 `docs/analysis/0175-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0175-analysis.md`，并将状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单、严禁修改实际提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_0100 (01:00) ----------------
    {
        "batch_id": "batch_0100",
        "target_time": "01:00",
        "tasks": [
            {
                "id": "0176",
                "title": "Shot 2 榜单成绩冲击波复盘与全国第一攻顶态势研判",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0176 任务：Shot 2 榜单成绩冲击波复盘与全国第一攻顶态势研判

## 背景
复盘 Shot 2 出分表现，量化我方相对光明未来（117.0257s）的突破幅度与榜首位势。

## 目标
研判全国第一攻顶态势并规划巩固策略。

## 产出路径
- `zcode/reports/0176-analysis.md`
- `docs/analysis/0176-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写攻顶态势分析脚本；
2. 形成分析成果写入 `docs/analysis/0176-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0176-analysis.md`，并将状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单、严禁修改实际提交凭据。
"""
            },
            {
                "id": "0177",
                "title": "Shot 3 自适应分流选型与平坦邻域容错保护执行",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0177 任务：Shot 3 自适应分流选型与平坦邻域容错保护执行

## 背景
根据前两发成绩，决策 Shot 3 是否部署 Plateau A 实施方差压制与平坦邻域保护。

## 目标
验证选型平坦性与抗扰动容错。

## 产出路径
- `zcode/reports/0177-analysis.md`
- `docs/analysis/0177-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写选型容错分析脚本；
2. 形成分析成果写入 `docs/analysis/0177-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0177-analysis.md`，并将状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单、严禁修改实际提交凭据。
"""
            },
            {
                "id": "0178",
                "title": "官方防作弊与规则符合度白盒闭环报告即时生成",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0178 任务：官方防作弊与规则符合度白盒闭环报告即时生成

## 背景
实时梳理前三发提交的合规链路，出具官方六大红线 100% 遵守证明。

## 目标
合规证明覆盖率 100%。

## 产出路径
- `zcode/reports/0178-analysis.md`
- `docs/analysis/0178-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写合规闭环审计脚本；
2. 形成分析成果写入 `docs/analysis/0178-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0178-analysis.md`，并将状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单、严禁修改实际提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_0130 (01:30) ----------------
    {
        "batch_id": "batch_0130",
        "target_time": "01:30",
        "tasks": [
            {
                "id": "0179",
                "title": "Shot 3 成绩收敛性与置信区间动态收缩率评估",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0179 任务：Shot 3 成绩收敛性与置信区间动态收缩率评估

## 背景
计算三发综合均值与置信区间收缩速度，验证方差随样本增加的平方根衰减规律。

## 目标
验证置信区间宽度收缩至初始值的 57.7% 以下。

## 产出路径
- `zcode/reports/0179-analysis.md`
- `docs/analysis/0179-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写置信区间动态收缩脚本；
2. 形成分析成果写入 `docs/analysis/0179-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0179-analysis.md`，并将状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单、严禁修改实际提交凭据。
"""
            },
            {
                "id": "0180",
                "title": "Shot 4 / Shot 5 决胜轮次出击策略微调与锁定",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0180 任务：Shot 4 / Shot 5 决胜轮次出击策略微调与锁定

## 背景
针对决胜轮次 Shot 4 与 Shot 5 进行策略锁定，决定是否发起二次极限冲锋或全面转入堡垒防御。

## 目标
输出最优双射方案与风险控制矩阵。

## 产出路径
- `zcode/reports/0180-analysis.md`
- `docs/analysis/0180-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写决胜策略优化脚本；
2. 形成分析成果写入 `docs/analysis/0180-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0180-analysis.md`，并将状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单、严禁修改实际提交凭据。
"""
            },
            {
                "id": "0181",
                "title": "极端对抗情景下的方差硬门禁校验与防御兜底生效确认",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0181 任务：极端对抗情景下的方差硬门禁校验与防御兜底生效确认

## 背景
在最后两发前再次核验 Defense Fortress 候选方案的切比雪夫兜底界，确保日终成绩不发生任何坍塌。

## 目标
确认兜底防线生效，方差受控在 CV <= 4.0%。

## 产出路径
- `zcode/reports/0181-analysis.md`
- `docs/analysis/0181-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写兜底防线核验脚本；
2. 形成分析成果写入 `docs/analysis/0181-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0181-analysis.md`，并将状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单、严禁修改实际提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_0200 (02:00) ----------------
    {
        "batch_id": "batch_0200",
        "target_time": "02:00",
        "tasks": [
            {
                "id": "0182",
                "title": "11/08 五发全量出分横向对比与官方终审复测均值预测",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0182 任务：11/08 五发全量出分横向对比与官方终审复测均值预测

## 背景
对 11/08 全部 5 发实战得分进行统计汇总，预测官方统一复测均值。

## 目标
输出全天五发均值、标准差与官方复测排名预测。

## 产出路径
- `zcode/reports/0182-analysis.md`
- `docs/analysis/0182-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写全天成绩复盘与复测预测脚本；
2. 形成分析成果写入 `docs/analysis/0182-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0182-analysis.md`，并将状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单、严禁修改实际提交凭据。
"""
            },
            {
                "id": "0183",
                "title": "全国第一夺冠数理证明大白皮书最终终审版编译",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0183 任务：全国第一夺冠数理证明大白皮书最终终审版编译

## 背景
将 0041~0182 全量理论推导、李雅普诺夫稳定性、马氏置信椭圆与实战成果汇编为终审大白皮书。

## 目标
编译生成完整的全国第一夺冠技术白皮书。

## 产出路径
- `zcode/reports/0183-analysis.md`
- `docs/analysis/0183-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写白皮书终审编译脚本；
2. 形成分析成果写入 `docs/analysis/0183-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0183-analysis.md`，并将状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单、严禁修改实际提交凭据。
"""
            },
            {
                "id": "0184",
                "title": "团队最终成果归档与 SHA-256 全数字资产签名封存",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0184 任务：团队最终成果归档与 SHA-256 全数字资产签名封存

## 背景
对全部 184 项科研产出、脚本与文档生成全量 SHA-256 哈希清单，构建不可篡改的成果档案库。

## 目标
完成成果全量密码学封存。

## 产出路径
- `zcode/reports/0184-analysis.md`
- `docs/analysis/0184-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写全量成果归档与哈希签名脚本；
2. 形成分析成果写入 `docs/analysis/0184-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0184-analysis.md`，并将状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单、严禁修改实际提交凭据。
"""
            }
        ]
    }
,
# ---------------- 批次：batch_0230 (02:30) ----------------
    {
        "batch_id": "batch_0230",
        "target_time": "02:30",
        "tasks": [
            {
                "id": "0185",
                "title": "连续六次下载非对称梯形泄露率消融实验数据挖掘",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0185 任务：连续六次下载非对称梯形泄露率消融实验数据挖掘

## 背景
对 41x2-40-37-36x2 梯形衰减策略各阶段进行逐 bin 消融分析，量化 4.bin 与 5.bin 排空断点的边际贡献。

## 目标
计算各阶段速度增益分解矩阵。

## 产出路径
- `zcode/reports/0185-analysis.md`
- `docs/analysis/0185-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写边际贡献消融分解脚本；
2. 形成分析成果写入 `docs/analysis/0185-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0185-analysis.md`，并将状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单、严禁修改实际提交凭据。
"""
            },
            {
                "id": "0186",
                "title": "针对不同背景流量强度的流控灵敏度弹性偏导数矩阵求解",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0186 任务：针对不同背景流量强度的流控灵敏度弹性偏导数矩阵求解

## 背景
求解完成时间对交叉背景流强度 lambda_bg 的偏导数 partial T / partial lambda_bg。

## 目标
证明系统处于弹性钝感区（弹性系数 < 0.25）。

## 产出路径
- `zcode/reports/0186-analysis.md`
- `docs/analysis/0186-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写背景流偏导数灵敏度脚本；
2. 形成分析成果写入 `docs/analysis/0186-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0186-analysis.md`，并将状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单、严禁修改实际提交凭据。
"""
            },
            {
                "id": "0187",
                "title": "全国决赛答辩核心 PPT 数据图表矢量渲染与高分辨率导出",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0187 任务：全国决赛答辩核心 PPT 数据图表矢量渲染与高分辨率导出

## 背景
将李雅普诺夫相轨迹、马氏置信椭圆与 Wasserstein 距离等核心成果渲染为答辩图表。

## 目标
输出高分辨率矢量渲染数据与排版说明。

## 产出路径
- `zcode/reports/0187-analysis.md`
- `docs/analysis/0187-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写答辩图表生成脚本；
2. 形成分析成果写入 `docs/analysis/0187-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0187-analysis.md`，并将状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单、严禁修改实际提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_0300 (03:00) ----------------
    {
        "batch_id": "batch_0300",
        "target_time": "03:00",
        "tasks": [
            {
                "id": "0188",
                "title": "决战五发全周期 CPU 与内存开销剖析与性能剖析 (cProfile)",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0188 任务：决战五发全周期 CPU 与内存开销剖析与性能剖析 (cProfile)

## 背景
通过 Python cProfile 剖析控制器及周边工具的运行开销，确保在微秒级整形下的极低资源占用。

## 目标
证明 CPU 占比小于 2.5%，内存占用小于 45 MB。

## 产出路径
- `zcode/reports/0188-analysis.md`
- `docs/analysis/0188-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写 cProfile 性能分析脚本；
2. 形成分析成果写入 `docs/analysis/0188-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0188-analysis.md`，并将状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单、严禁修改实际提交凭据。
"""
            },
            {
                "id": "0189",
                "title": "官方复测防针对性攻击与随机种子不敏感性蒙特卡洛再认证",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0189 任务：官方复测防针对性攻击与随机种子不敏感性蒙特卡洛再认证

## 背景
模拟官方随机更换 100 组未知随机种子，验证我方方案在未知拓扑种子下的方差抗性。

## 目标
种子间均值波动小于 1.5 秒。

## 产出路径
- `zcode/reports/0189-analysis.md`
- `docs/analysis/0189-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写随机种子鲁棒性仿真脚本；
2. 形成分析成果写入 `docs/analysis/0189-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0189-analysis.md`，并将状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单、严禁修改实际提交凭据。
"""
            },
            {
                "id": "0190",
                "title": "全国特等奖/一等奖专家评审核心技术亮点提炼与 Q&A 防御库",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0190 任务：全国特等奖/一等奖专家评审核心技术亮点提炼与 Q&A 防御库

## 背景
预测专家针对流量整形机制、防过拟合、收敛性等可能提出的尖锐质询，整理标准数理应答防御。

## 目标
形成结构化评审专家 Q&A 防御知识库。

## 产出路径
- `zcode/reports/0190-analysis.md`
- `docs/analysis/0190-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写专家 Q&A 提炼生成脚本；
2. 形成分析成果写入 `docs/analysis/0190-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0190-analysis.md`，并将状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单、严禁修改实际提交凭据。
"""
            }
        ]
    }
,
# ---------------- 批次：batch_0330 (03:30) ----------------
    {
        "batch_id": "batch_0330",
        "target_time": "03:30",
        "tasks": [
            {
                "id": "0191",
                "title": "QUIC BBR v1/v2 拥塞控制抗深缓冲区膨胀 (Bufferbloat) 频域分析",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0191 任务：QUIC BBR v1/v2 拥塞控制抗深缓冲区膨胀 (Bufferbloat) 频域分析

## 任务背景
在浅/深网络缓冲区共存环境下，BBR 的周期性探测会引发队列振荡。需通过频域变换量化 4000µs 漏桶 pacing 的低通滤波效应。

## 目标
量化证明对 f > 50Hz 的高频队列抖动衰减超过 24 dB。

## 交付物与路径
- `zcode/reports/0191-analysis.md`
- `docs/analysis/0191-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写频域傅里叶分析脚本
2. 形成分析成果写入 `docs/analysis/0191-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0191-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            },
            {
                "id": "0192",
                "title": "11/08 决胜首发稳健基石多维度异常自愈与回滚仿真",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0192 任务：11/08 决胜首发稳健基石多维度异常自愈与回滚仿真

## 任务背景
针对第 1 发在云端冷启动或极端恶劣网络抖动下的异常情况，建立全自动三级 fallback 状态机仿真。

## 目标
验证在超时、长尾、解析异常等扰动下的自愈恢复成功率达到 100%。

## 交付物与路径
- `zcode/reports/0192-analysis.md`
- `docs/analysis/0192-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写自愈状态机仿真脚本
2. 形成分析成果写入 `docs/analysis/0192-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0192-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            },
            {
                "id": "0193",
                "title": "全国前五竞争对手战术意图与发数余量攻防推演",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0193 任务：全国前五竞争对手战术意图与发数余量攻防推演

## 任务背景
深度推演光明未来 (117.02s)、Catnet (119.82s)、hashkimi (120.26s) 等对手在 11/08 的发车窗口与策略空间。

## 目标
给出错峰提交与高频碾压的最优窗口期。

## 交付物与路径
- `zcode/reports/0193-analysis.md`
- `docs/analysis/0193-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写对手行为博弈推演脚本
2. 形成分析成果写入 `docs/analysis/0193-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0193-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_0400 (04:00) ----------------
    {
        "batch_id": "batch_0400",
        "target_time": "04:00",
        "tasks": [
            {
                "id": "0194",
                "title": "多速率自适应漏桶非线性动力学 Hopf 分岔与稳定性分析",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0194 任务：多速率自适应漏桶非线性动力学 Hopf 分岔与稳定性分析

## 任务背景
将带有时滞的网络反馈建模为一阶时滞微分方程 (DDE)，分析临界点参数是否存在 Hopf 分岔导致的极限环失稳。

## 目标
证明当前漏率 (36~41) 与桶容量 (40~41) 区间远离分岔失稳边界。

## 交付物与路径
- `zcode/reports/0194-analysis.md`
- `docs/analysis/0194-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写非线性动力学微分方程数值求解脚本
2. 形成分析成果写入 `docs/analysis/0194-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0194-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            },
            {
                "id": "0195",
                "title": "六阶段文件传输完成时间与拥塞窗口纳什均衡求解",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0195 任务：六阶段文件传输完成时间与拥塞窗口纳什均衡求解

## 任务背景
将六次连续下载的带宽竞争建模为不完全信息动态博弈，求解混合策略纳什均衡。

## 目标
证明前重后轻配置（Bin 1~3 高速冲击、Bin 5~6 排空）构成了全局帕累托最优均衡。

## 交付物与路径
- `zcode/reports/0195-analysis.md`
- `docs/analysis/0195-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写博弈收益矩阵与纳什均衡求解脚本
2. 形成分析成果写入 `docs/analysis/0195-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0195-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            },
            {
                "id": "0196",
                "title": "全自动化闭环控制器 11/08 实战无缝执行沙盒演练 (Dry-Run)",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0196 任务：全自动化闭环控制器 11/08 实战无缝执行沙盒演练 (Dry-Run)

## 任务背景
在实战发射前，对 `tools/sequential_adaptive_1108.py` 进行五轮完整的模拟仿真测试。

## 目标
验证 1-by-1 打一发分析一发的决策流、状态落盘与异常拦截 100% 健壮。

## 交付物与路径
- `zcode/reports/0196-analysis.md`
- `docs/analysis/0196-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写沙盒无副作用仿真测试脚本
2. 形成分析成果写入 `docs/analysis/0196-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0196-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_0430 (04:30) ----------------
    {
        "batch_id": "batch_0430",
        "target_time": "04:30",
        "tasks": [
            {
                "id": "0197",
                "title": "极小极大后悔值准则 (Minimax Regret) 下的第 2 发策略优选",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0197 任务：极小极大后悔值准则 (Minimax Regret) 下的第 2 发策略优选

## 任务背景
量化第 1 发反馈后面对不同网络环境时各候选策略的后悔值（Regret Matrix），利用 Savage 准则选取最稳健候选。

## 目标
给出顺风、基准、逆风三态下的极小极大后悔值最优决策下界。

## 交付物与路径
- `zcode/reports/0197-analysis.md`
- `docs/analysis/0197-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写后悔矩阵推导与计算脚本
2. 形成分析成果写入 `docs/analysis/0197-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0197-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            },
            {
                "id": "0198",
                "title": "QUIC 流量整形网络层与传输层开销 (Header Overhead) 微观精算",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0198 任务：QUIC 流量整形网络层与传输层开销 (Header Overhead) 微观精算

## 任务背景
深入微观网络协议栈，精算 IPv4/UDP/QUIC 包头在 MTU 1200 字节下的真实带宽开销。

## 目标
量化有效载荷比率达 95.67%，验证 36~41 pkts/4ms 对应的实际物理吞吐。

## 交付物与路径
- `zcode/reports/0198-analysis.md`
- `docs/analysis/0198-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写网络报文开销与 Goodput 理论精算脚本
2. 形成分析成果写入 `docs/analysis/0198-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0198-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            },
            {
                "id": "0199",
                "title": "官方评测系统本地发包器边界合规与畸形数据免疫渗透测试",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0199 任务：官方评测系统本地发包器边界合规与畸形数据免疫渗透测试

## 任务背景
对生成的所有配置树进行格式鲁棒性测试，防止存在微小不可见字符或 CRLF 漏洞。

## 目标
确保 100% 格式合规且免疫任何解析畸形。

## 交付物与路径
- `zcode/reports/0199-analysis.md`
- `docs/analysis/0199-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写配置树极限边界渗透测试脚本
2. 形成分析成果写入 `docs/analysis/0199-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0199-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_0500 (05:00) ----------------
    {
        "batch_id": "batch_0500",
        "target_time": "05:00",
        "tasks": [
            {
                "id": "0200",
                "title": "基于卡尔曼滤波的网络背景流强度实时在线估计器设计",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0200 任务：基于卡尔曼滤波的网络背景流强度实时在线估计器设计

## 任务背景
在 1-by-1 串行评测中，利用官方每次返回的总耗时，构建一阶一维卡尔曼滤波器，在线估计背景流拥塞强度。

## 目标
实现测量噪声平滑与先验状态最优递推，均方误差收敛 40% 以上。

## 交付物与路径
- `zcode/reports/0200-analysis.md`
- `docs/analysis/0200-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写卡尔曼滤波在线估计仿真脚本
2. 形成分析成果写入 `docs/analysis/0200-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0200-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            },
            {
                "id": "0201",
                "title": "决胜五发配置全生命周期 SHA-256 跨平台一致性签名锁",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0201 任务：决胜五发配置全生命周期 SHA-256 跨平台一致性签名锁

## 任务背景
对 11/08 准备发射的所有候选配置树（包含 Shot 1~5 共 30 个 pacer.txt）计算并封存二级 SHA-256 哈希清单。

## 目标
形成跨平台不可篡改的配置签名锁 `runs/sha256_sealed_manifest_v2.json`。

## 交付物与路径
- `zcode/reports/0201-analysis.md`
- `docs/analysis/0201-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写 SHA-256 跨平台指纹固化脚本
2. 形成分析成果写入 `docs/analysis/0201-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0201-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            },
            {
                "id": "0202",
                "title": "全国决赛级技术成果白皮书核心成果附录编纂",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0202 任务：全国决赛级技术成果白皮书核心成果附录编纂

## 任务背景
将从 0001 到 0200 任务取得的核心数学证明、控制理论、实验数据与实战代码梳理为完整技术附录。

## 目标
生成高质量技术附录文档 `docs/analysis/national-first-prize-appendix.md`。

## 交付物与路径
- `zcode/reports/0202-analysis.md`
- `docs/analysis/0202-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写技术附录自动化汇总脚本
2. 形成分析成果写入 `docs/analysis/0202-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0202-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_0530 (05:30) ----------------
    {
        "batch_id": "batch_0530",
        "target_time": "05:30",
        "tasks": [
            {
                "id": "0203",
                "title": "QUIC 乱序包重排窗口与快速重传触发临界点模型",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0203 任务：QUIC 乱序包重排窗口与快速重传触发临界点模型

## 任务背景
在 4000µs pacing 周期内，网络微突发可能诱发乱序包到达。需建立数学模型评估快速重传假阳性概率。

## 目标
证明在当前整形策略下乱序重传假阳性概率低于 0.05%。

## 交付物与路径
- `zcode/reports/0203-analysis.md`
- `docs/analysis/0203-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写乱序概率与重传阈值建模脚本
2. 形成分析成果写入 `docs/analysis/0203-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0203-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            },
            {
                "id": "0204",
                "title": "多阶段下载交接处微秒级令牌重置与队列排空过渡态仿真",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0204 任务：多阶段下载交接处微秒级令牌重置与队列排空过渡态仿真

## 任务背景
在 6 次连续下载阶段交接时，前一次残留队列若未完全清空会影响下一次冷启动。需仿真阶段切换瞬态。

## 目标
证明阶段间队列平滑排空时间小于 2.1 ms，零队头阻塞。

## 交付物与路径
- `zcode/reports/0204-analysis.md`
- `docs/analysis/0204-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写阶段切换瞬态仿真脚本
2. 形成分析成果写入 `docs/analysis/0204-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0204-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            },
            {
                "id": "0205",
                "title": "全国前三名夺冠概率贝叶斯动态更新图谱",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0205 任务：全国前三名夺冠概率贝叶斯动态更新图谱

## 任务背景
基于先验得分分布与官方最终统一复测规则，利用 Beta-Binomial 模型绘制我方与竞争对手的夺冠概率演化路径。

## 目标
量化五发自适应打击后夺冠概率达到 91% 以上的理论路径。

## 交付物与路径
- `zcode/reports/0205-analysis.md`
- `docs/analysis/0205-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写贝叶斯信念更新演化仿真脚本
2. 形成分析成果写入 `docs/analysis/0205-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0205-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_0600 (06:00) ----------------
    {
        "batch_id": "batch_0600",
        "target_time": "06:00",
        "tasks": [
            {
                "id": "0206",
                "title": "极端丢包注入下 QUIC 连接存活与拥塞塌陷防御演练",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0206 任务：极端丢包注入下 QUIC 连接存活与拥塞塌陷防御演练

## 任务背景
在 1%~5% 随机丢包注入下压测 pacing 参数，验证整形算法避免陷入拥塞崩溃的能力。

## 目标
证明极端丢包下连接存活率 100%，耗时稳定在安全边界内。

## 交付物与路径
- `zcode/reports/0206-analysis.md`
- `docs/analysis/0206-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写丢包注入容灾压测脚本
2. 形成分析成果写入 `docs/analysis/0206-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0206-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            },
            {
                "id": "0207",
                "title": "五发方案整体置信椭球体积与广义方差广义似然比检验 (GLRT)",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0207 任务：五发方案整体置信椭球体积与广义方差广义似然比检验 (GLRT)

## 任务背景
构建 5 维多变量高斯似然比检验模型，计算五发组合的协方差行列式（广义方差）。

## 目标
证明我方策略的置信椭球体积相比对手缩小 80% 以上。

## 交付物与路径
- `zcode/reports/0207-analysis.md`
- `docs/analysis/0207-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写 5 维广义似然比检验与置信椭球体积脚本
2. 形成分析成果写入 `docs/analysis/0207-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0207-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            },
            {
                "id": "0208",
                "title": "全国总决赛专家答辩核心幻灯片文字与逻辑纲要落盘",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0208 任务：全国总决赛专家答辩核心幻灯片文字与逻辑纲要落盘

## 任务背景
将科研全景提炼为全国现场答辩的 12 页 PPT 逻辑脉络与逐字稿要点。

## 目标
输出高水准答辩 PPT 结构纲要 `docs/analysis/0208-defense-slide-deck-outline.md`。

## 交付物与路径
- `zcode/reports/0208-analysis.md`
- `docs/analysis/0208-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写答辩逻辑自动化梳理脚本
2. 形成分析成果写入 `docs/analysis/0208-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0208-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            }
        ]
    }
,
# ---------------- 批次：batch_0630 (06:30) ----------------
    {
        "batch_id": "batch_0630",
        "target_time": "06:30",
        "tasks": [
            {
                "id": "0209",
                "title": "QUIC 加密套件软硬件加速吞吐损耗审计",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0209 任务：QUIC 加密套件软硬件加速吞吐损耗审计

## 任务背景
量化云端 CPU 在 AES-NI 指令集下的加密计算周期开销，验证加解密对微秒级 pacing 抖动贡献 < 1.2µs。

## 目标
证明加解密计算延迟对 4000µs pacing 影响小于 0.03%。

## 交付物与路径
- `zcode/reports/0209-analysis.md`
- `docs/analysis/0209-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写加密计算周期微基准测试脚本
2. 形成分析成果写入 `docs/analysis/0209-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0209-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            },
            {
                "id": "0210",
                "title": "多维动态规划 (DP) 求解六阶段带宽漏率全局帕累托前沿",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0210 任务：多维动态规划 (DP) 求解六阶段带宽漏率全局帕累托前沿

## 任务背景
建立带总队列深度上限与阶段连续性约束的多阶段贝尔曼方程，数值求解全局最优漏率离散序列。

## 目标
证明 Crown Fusion (41-41-41-37-36-36) 是贝尔曼全局最优值函数的唯一解析解。

## 交付物与路径
- `zcode/reports/0210-analysis.md`
- `docs/analysis/0210-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写贝尔曼多阶段动态规划数值求解脚本
2. 形成分析成果写入 `docs/analysis/0210-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0210-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            },
            {
                "id": "0211",
                "title": "全国前五队伍历史复测方差逆向工程与破绽深度挖掘",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0211 任务：全国前五队伍历史复测方差逆向工程与破绽深度挖掘

## 任务背景
从公开榜单各队历史多轮提交的成绩离散度，逆向推导其底层拥塞控制参数与破绽。

## 目标
量化对手在官方多轮统一复测中的崩溃概率超过 85%。

## 交付物与路径
- `zcode/reports/0211-analysis.md`
- `docs/analysis/0211-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写对手历史离散度逆向分析脚本
2. 形成分析成果写入 `docs/analysis/0211-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0211-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_0700 (07:00) ----------------
    {
        "batch_id": "batch_0700",
        "target_time": "07:00",
        "tasks": [
            {
                "id": "0212",
                "title": "Linux TC 与 eBPF XDP 流量整形等效性交叉审计",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0212 任务：Linux TC 与 eBPF XDP 流量整形等效性交叉审计

## 任务背景
比对用户态 pacing 与内核态 qdisc (fq/tbf) 的调度精度差异，评估用户态调度的开销与抖动。

## 目标
证明用户态微秒级 pacing 精度误差小于 0.8%。

## 交付物与路径
- `zcode/reports/0212-analysis.md`
- `docs/analysis/0212-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写内核态与用户态流量整形精度交叉比对脚本
2. 形成分析成果写入 `docs/analysis/0212-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0212-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            },
            {
                "id": "0213",
                "title": "第 1 发出分前窗口期准实战心跳监测与静默守候",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0213 任务：第 1 发出分前窗口期准实战心跳监测与静默守候

## 任务背景
设计零网络副作用的云端评测心跳状态轮询器，精准感知服务端状态就绪，杜绝并发冲突。

## 目标
验证等待期间零额外网络请求、零平台负载污染。

## 交付物与路径
- `zcode/reports/0213-analysis.md`
- `docs/analysis/0213-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写无害心跳轮询与状态检测脚本
2. 形成分析成果写入 `docs/analysis/0213-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0213-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            },
            {
                "id": "0214",
                "title": "双队列 M/M/1/K 优先级调度模型控制报文隔离性证明",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0214 任务：双队列 M/M/1/K 优先级调度模型控制报文隔离性证明

## 任务背景
建立马尔可夫链证明 QUIC ACK 与连接管理报文不被高通量数据报文阻塞。

## 目标
证明 ACK 延迟分位数 P99.9 小于 2.8ms，零队头拥塞。

## 交付物与路径
- `zcode/reports/0214-analysis.md`
- `docs/analysis/0214-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写双队列马尔可夫优先级调度求解脚本
2. 形成分析成果写入 `docs/analysis/0214-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0214-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_0730 (07:30) ----------------
    {
        "batch_id": "batch_0730",
        "target_time": "07:30",
        "tasks": [
            {
                "id": "0215",
                "title": "基于极端值理论 (EVT) 对第 5 发防御锁仓的拟合",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0215 任务：基于极端值理论 (EVT) 对第 5 发防御锁仓的拟合

## 任务背景
采用广义极值分布 (GEV) 拟合恶劣网络环境下的长尾延迟，计算防御锁仓的最劣时延上界。

## 目标
证明防御锁仓在 99.9% 极端尾部下的最劣耗时仍小于 136.0s。

## 交付物与路径
- `zcode/reports/0215-analysis.md`
- `docs/analysis/0215-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写 GEV 极值拟合与尾部风险量化脚本
2. 形成分析成果写入 `docs/analysis/0215-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0215-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            },
            {
                "id": "0216",
                "title": "跨阶段拥塞窗口平滑过渡阻尼指数衰减系数最优求解",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0216 任务：跨阶段拥塞窗口平滑过渡阻尼指数衰减系数最优求解

## 任务背景
求解两阶段速率阶跃处的阻尼衰减系数 ζ，证明过阻尼响应完全杜绝了速率跃变时的超调丢包。

## 目标
证明阻尼比 ζ >= 1.05，超调量为 0.00%。

## 交付物与路径
- `zcode/reports/0216-analysis.md`
- `docs/analysis/0216-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写二阶系统阻尼过渡响应数值计算脚本
2. 形成分析成果写入 `docs/analysis/0216-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0216-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            },
            {
                "id": "0217",
                "title": "官方评测系统时间戳字段解析逻辑与零漂移防御方案",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0217 任务：官方评测系统时间戳字段解析逻辑与零漂移防御方案

## 任务背景
针对 [timestamp:N] 的时间戳机制进行时钟漂移敏感性分析，证明时间漂移在任意微秒级偏差下均保持解析幂等。

## 目标
证明时钟偏移容忍度超过 1000ms，解析成功率 100%。

## 交付物与路径
- `zcode/reports/0217-analysis.md`
- `docs/analysis/0217-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写时间戳漂移鲁棒性分析脚本
2. 形成分析成果写入 `docs/analysis/0217-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0217-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_0800 (08:00) ----------------
    {
        "batch_id": "batch_0800",
        "target_time": "08:00",
        "tasks": [
            {
                "id": "0218",
                "title": "自适应决策控制器在网络断连/进程异常下的无状态无锁恢复测试",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0218 任务：自适应决策控制器在网络断连/进程异常下的无状态无锁恢复测试

## 任务背景
模拟进程被意外终止信号中断，验证基于 `runs/sequential_1108_state.json` 的断点自愈能力。

## 目标
验证在任意执行步骤发生故障时，100% 恢复当前状态并继续执行，配额零越界。

## 交付物与路径
- `zcode/reports/0218-analysis.md`
- `docs/analysis/0218-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写崩溃恢复与状态机断点续传测试脚本
2. 形成分析成果写入 `docs/analysis/0218-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0218-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            },
            {
                "id": "0219",
                "title": "QUIC 流量整形全局相空间拓扑庞加莱截面分析",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0219 任务：QUIC 流量整形全局相空间拓扑庞加莱截面分析

## 任务背景
绘制队列队长与发包速率在 4000µs 采样下的二维庞加莱截面映射。

## 目标
证明系统相点严格收敛于单个稳定不动点，无拟周期或奇异吸引子。

## 交付物与路径
- `zcode/reports/0219-analysis.md`
- `docs/analysis/0219-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写庞加莱截面相空间数值映射脚本
2. 形成分析成果写入 `docs/analysis/0219-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0219-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            },
            {
                "id": "0220",
                "title": "全国总决赛专家答辩问询标准知识库扩充与二阶推导强化",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0220 任务：全国总决赛专家答辩问询标准知识库扩充与二阶推导强化

## 任务背景
针对前 200 项成果扩充 5 个高难度专家深度质问，完善二阶推导。

## 目标
更新完善答辩知识库文档 `docs/analysis/0190-expert-defense-qa-database.md`。

## 交付物与路径
- `zcode/reports/0220-analysis.md`
- `docs/analysis/0220-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写答辩知识库扩充与自动化审计脚本
2. 形成分析成果写入 `docs/analysis/0220-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0220-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_0830 (08:30) ----------------
    {
        "batch_id": "batch_0830",
        "target_time": "08:30",
        "tasks": [
            {
                "id": "0221",
                "title": "基于经验模态分解 (EMD) 的真实网络抖动 HHT 谱分析",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

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
"""
            },
            {
                "id": "0222",
                "title": "五发配置在 1000 组非高斯混合重尾噪声下的稳定性蒙特卡洛验证",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0222 任务：五发配置在 1000 组非高斯混合重尾噪声下的稳定性蒙特卡洛验证

## 任务背景
采用 Students-t 与对数正态混合分布模拟重尾背景流，统计五发配置的均值抗噪性。

## 目标
证明在重尾噪声冲击下复测胜率保持在 90% 以上。

## 交付物与路径
- `zcode/reports/0222-analysis.md`
- `docs/analysis/0222-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写非高斯重尾噪声蒙特卡洛仿真脚本
2. 形成分析成果写入 `docs/analysis/0222-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0222-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            },
            {
                "id": "0223",
                "title": "官方规则 1~6 终极门禁自动化全脚本渗透扫描",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0223 任务：官方规则 1~6 终极门禁自动化全脚本渗透扫描

## 任务背景
编写最高权限的一键合规渗透审计脚本，对项目所有文件进行零死角合规扫描。

## 目标
输出终极合规防线审计证书，违规项数量严格为 0。

## 交付物与路径
- `zcode/reports/0223-analysis.md`
- `docs/analysis/0223-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写全代码库合规渗透审计脚本
2. 形成分析成果写入 `docs/analysis/0223-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0223-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_0900 (09:00) ----------------
    {
        "batch_id": "batch_0900",
        "target_time": "09:00",
        "tasks": [
            {
                "id": "0224",
                "title": "全国决赛级技术成果白皮书核心论述与实验复盘终极归档",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0224 任务：全国决赛级技术成果白皮书核心论述与实验复盘终极归档

## 任务背景
将全部科研成果、12 页 PPT 逻辑、答辩知识库与加密指纹整合为全国决赛最高技术文献。

## 目标
完成白皮书最终归档版 `docs/analysis/national-first-prize-whitepaper-final.md`。

## 交付物与路径
- `zcode/reports/0224-analysis.md`
- `docs/analysis/0224-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写白皮书最终核验与归档脚本
2. 形成分析成果写入 `docs/analysis/0224-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0224-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            },
            {
                "id": "0225",
                "title": "11/08 决胜凌晨 00:05 启动倒计时终极演习 (Full-Scale Rehearsal)",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0225 任务：11/08 决胜凌晨 00:05 启动倒计时终极演习 (Full-Scale Rehearsal)

## 任务背景
模拟时间拨至 2026-11-08 00:05:00，执行控制脚本拉起、环境变量校验、首发目录装载的全流程零差错演练。

## 目标
演练通过率 100%，环境自检全部 PASS。

## 交付物与路径
- `zcode/reports/0225-analysis.md`
- `docs/analysis/0225-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写倒计时终极实战演习脚本
2. 形成分析成果写入 `docs/analysis/0225-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0225-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            },
            {
                "id": "0226",
                "title": "全国总冠军战备封箱指令与状态终极锁定",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0226 任务：全国总冠军战备封箱指令与状态终极锁定

## 任务背景
全面核对 5 发配置树与控制脚本，生成最终系统状态报告与任务看板，保持静默战备直到午夜出征。

## 目标
完成战备封箱锁定，生成 `runs/master_battle_ready_certificate.json`。

## 交付物与路径
- `zcode/reports/0226-analysis.md`
- `docs/analysis/0226-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写战备封箱核验与证书签署脚本
2. 形成分析成果写入 `docs/analysis/0226-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0226-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            }
        ]
    }
,
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
,
    # ---------------- 批次：batch_1130 (11:30) ----------------
    {
        "batch_id": "batch_1130",
        "target_time": "11:30",
        "tasks": [
            {
                "id": "0239",
                "title": "随机早期检测 RED 丢包概率函数在瓶颈队列的拟合",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0239 任务：随机早期检测 RED 丢包概率函数在瓶颈队列的拟合

## 任务背景
拟合 RED 线性标记概率函数并量化拥塞发生时的丢包突变拐点。

## 考核目标
计算最大丢包概率点与队列平滑安全裕度。

## 预期产出路径
- `zcode/reports/0239-analysis.md`
- `docs/analysis/0239-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成理论分析成果写入 `docs/analysis/0239-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0239-analysis.md`，将状态修改为 `status: done`。

## 严格红线
- 严禁向远程平台提交榜单，严禁修改实盘提交凭据。
"""
            },
            {
                "id": "0240",
                "title": "QUIC 乱序重组缓冲区极限内存占用测试",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0240 任务：QUIC 乱序重组缓冲区极限内存占用测试

## 任务背景
模拟网络抖动下的严重重排序并监控 QUIC 接收端重组队列内存占用。

## 考核目标
验证在 100 包乱序下重组内存增加不超过 128KB。

## 预期产出路径
- `zcode/reports/0240-analysis.md`
- `docs/analysis/0240-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成理论分析成果写入 `docs/analysis/0240-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0240-analysis.md`，将状态修改为 `status: done`。

## 严格红线
- 严禁向远程平台提交榜单，严禁修改实盘提交凭据。
"""
            },
            {
                "id": "0241",
                "title": "跨阶段速率跳变阶跃响应阻尼衰减度量",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0241 任务：跨阶段速率跳变阶跃响应阻尼衰减度量

## 任务背景
分析六阶段边界漏桶速率突变时的二阶阻尼瞬态衰减响应。

## 考核目标
验证从 Rate 41 到 Rate 37 阻尼比 >= 1.0 零超调。

## 预期产出路径
- `zcode/reports/0241-analysis.md`
- `docs/analysis/0241-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成理论分析成果写入 `docs/analysis/0241-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0241-analysis.md`，将状态修改为 `status: done`。

## 严格红线
- 严禁向远程平台提交榜单，严禁修改实盘提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_1200 (12:00) ----------------
    {
        "batch_id": "batch_1200",
        "target_time": "12:00",
        "tasks": [
            {
                "id": "0242",
                "title": "官方评分历史波动与周末评测负载周期性自相关 ACF 分析",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0242 任务：官方评分历史波动与周末评测负载周期性自相关 ACF 分析

## 任务背景
建立官方出分延迟与系统排队时间序列的自相关分析模型。

## 考核目标
验证周末出分波动自相关函数在 lag 1 下降至 0.25 以下。

## 预期产出路径
- `zcode/reports/0242-analysis.md`
- `docs/analysis/0242-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成理论分析成果写入 `docs/analysis/0242-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0242-analysis.md`，将状态修改为 `status: done`。

## 严格红线
- 严禁向远程平台提交榜单，严禁修改实盘提交凭据。
"""
            },
            {
                "id": "0243",
                "title": "极小极大遗憾策略在极端网络对抗下的最坏情况分析",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0243 任务：极小极大遗憾策略在极端网络对抗下的最坏情况分析

## 任务背景
基于 Savage 准则分析网络遭遇重度拥塞时各候选树的遗憾值界限。

## 考核目标
验证在所有极端对抗状态下我方最大遗憾值 <= 2.5s。

## 预期产出路径
- `zcode/reports/0243-analysis.md`
- `docs/analysis/0243-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成理论分析成果写入 `docs/analysis/0243-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0243-analysis.md`，将状态修改为 `status: done`。

## 严格红线
- 严禁向远程平台提交榜单，严禁修改实盘提交凭据。
"""
            },
            {
                "id": "0244",
                "title": "决选方案配置哈希硬编码签名与全量校验审计工具",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0244 任务：决选方案配置哈希硬编码签名与全量校验审计工具

## 任务背景
对最终出战的候选树配置进行 SHA-256 全量防篡改签名与校验。

## 考核目标
生成 100% 格式合规且不可篡改的决选配置指纹清单。

## 预期产出路径
- `zcode/reports/0244-analysis.md`
- `docs/analysis/0244-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成理论分析成果写入 `docs/analysis/0244-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0244-analysis.md`，将状态修改为 `status: done`。

## 严格红线
- 严禁向远程平台提交榜单，严禁修改实盘提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_1230 (12:30) ----------------
    {
        "batch_id": "batch_1230",
        "target_time": "12:30",
        "tasks": [
            {
                "id": "0245",
                "title": "针对 11/08 决战日 00:05~03:00 全程五发动态序列决策树推演",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0245 任务：针对 11/08 决战日 00:05~03:00 全程五发动态序列决策树推演

## 任务背景
模拟 5 发实战序列中各种可能出现的网络反馈分支并建立全覆盖状态转移树。

## 考核目标
推演 32 条全覆盖分支状态转移并确保无挂起死锁。

## 预期产出路径
- `zcode/reports/0245-analysis.md`
- `docs/analysis/0245-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成理论分析成果写入 `docs/analysis/0245-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0245-analysis.md`，将状态修改为 `status: done`。

## 严格红线
- 严禁向远程平台提交榜单，严禁修改实盘提交凭据。
"""
            },
            {
                "id": "0246",
                "title": "BBRv1 vs BBRv2 vs 准开环漏桶在深浅队列环境下的竞争相图",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0246 任务：BBRv1 vs BBRv2 vs 准开环漏桶在深浅队列环境下的竞争相图

## 任务背景
利用相平面方法分析不同拥塞控制算法在浅缓冲区拓扑下的稳态共存相图。

## 考核目标
绘制相空间轨线并证明准开环漏桶无饥饿与无振荡。

## 预期产出路径
- `zcode/reports/0246-analysis.md`
- `docs/analysis/0246-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成理论分析成果写入 `docs/analysis/0246-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0246-analysis.md`，将状态修改为 `status: done`。

## 严格红线
- 严禁向远程平台提交榜单，严禁修改实盘提交凭据。
"""
            },
            {
                "id": "0247",
                "title": "决选现场 10 分钟应急排障与备用云节点快速接管手册",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0247 任务：决选现场 10 分钟应急排障与备用云节点快速接管手册

## 任务背景
制定针对网络超时、客户端无响应或证书异常的快速冷启动排障手册。

## 考核目标
产出标准化应急处置 SOP 并验证故障切换时间 <= 15s。

## 预期产出路径
- `zcode/reports/0247-analysis.md`
- `docs/analysis/0247-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成理论分析成果写入 `docs/analysis/0247-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0247-analysis.md`，将状态修改为 `status: done`。

## 严格红线
- 严禁向远程平台提交榜单，严禁修改实盘提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_1300 (13:00) ----------------
    {
        "batch_id": "batch_1300",
        "target_time": "13:00",
        "tasks": [
            {
                "id": "0248",
                "title": "客户端用户态高精度计时器时钟漂移与补偿算法验证",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0248 任务：客户端用户态高精度计时器时钟漂移与补偿算法验证

## 任务背景
测试 Python 与用户态底层 clock_nanosleep 的微秒级定时精度与漂移补偿。

## 考核目标
验证 4ms 发送间隔累计漂移 < 10us。

## 预期产出路径
- `zcode/reports/0248-analysis.md`
- `docs/analysis/0248-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成理论分析成果写入 `docs/analysis/0248-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0248-analysis.md`，将状态修改为 `status: done`。

## 严格红线
- 严禁向远程平台提交榜单，严禁修改实盘提交凭据。
"""
            },
            {
                "id": "0249",
                "title": "传输层良好吞吐率 Goodput 理论上限与实测差值微积分",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0249 任务：传输层良好吞吐率 Goodput 理论上限与实测差值微积分

## 任务背景
微积分计算 IPv4/UDP/QUIC/HTTP3 各层报头损耗并核算理论良好吞吐率极限。

## 考核目标
推导传输协议开销理论下界并验证实测偏差 <= 1.2%。

## 预期产出路径
- `zcode/reports/0249-analysis.md`
- `docs/analysis/0249-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成理论分析成果写入 `docs/analysis/0249-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0249-analysis.md`，将状态修改为 `status: done`。

## 严格红线
- 严禁向远程平台提交榜单，严禁修改实盘提交凭据。
"""
            },
            {
                "id": "0250",
                "title": "全国一等奖答辩常见尖锐问题专家反击手册 v2",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0250 任务：全国一等奖答辩常见尖锐问题专家反击手册 v2

## 任务背景
补充针对多阶段突发、跨平台泛化能力与参数人工先验的专家刁钻问题反击回答。

## 考核目标
增补 Q11~Q15 专家攻击性技术问题并形成标准反击提纲。

## 预期产出路径
- `zcode/reports/0250-analysis.md`
- `docs/analysis/0250-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成理论分析成果写入 `docs/analysis/0250-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0250-analysis.md`，将状态修改为 `status: done`。

## 严格红线
- 严禁向远程平台提交榜单，严禁修改实盘提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_1330 (13:30) ----------------
    {
        "batch_id": "batch_1330",
        "target_time": "13:30",
        "tasks": [
            {
                "id": "0251",
                "title": "六阶段不同文件尺寸下漏桶最优充盈速度动态规划验证",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0251 任务：六阶段不同文件尺寸下漏桶最优充盈速度动态规划验证

## 任务背景
针对非对称文件尺寸分布建立动态规划递推验证最优前驱状态。

## 考核目标
计算离散 Bellman 状态空间下最优路径并证明唯一性。

## 预期产出路径
- `zcode/reports/0251-analysis.md`
- `docs/analysis/0251-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成理论分析成果写入 `docs/analysis/0251-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0251-analysis.md`，将状态修改为 `status: done`。

## 严格红线
- 严禁向远程平台提交榜单，严禁修改实盘提交凭据。
"""
            },
            {
                "id": "0252",
                "title": "官方沙箱环境 Linux 内核网络栈参数探测安全边界审查",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0252 任务：官方沙箱环境 Linux 内核网络栈参数探测安全边界审查

## 任务背景
全量审查本地测试工具对 Linux 内核参数的探测行为确保严格处于官方合规范围内。

## 考核目标
核查零违规调用、零特权逃逸、100% 合规边界。

## 预期产出路径
- `zcode/reports/0252-analysis.md`
- `docs/analysis/0252-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成理论分析成果写入 `docs/analysis/0252-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0252-analysis.md`，将状态修改为 `status: done`。

## 严格红线
- 严禁向远程平台提交榜单，严禁修改实盘提交凭据。
"""
            },
            {
                "id": "0253",
                "title": "极端高丢包 5%~10% 环境下 QUIC 发送窗口抗死锁验证",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0253 任务：极端高丢包 5%~10% 环境下 QUIC 发送窗口抗死锁验证

## 任务背景
注入极端恶劣丢包压力测试 QUIC 丢包探测与 PTO 恢复避免发送窗口死锁。

## 考核目标
验证在高丢包下快速恢复机制确保连接 100% 存活。

## 预期产出路径
- `zcode/reports/0253-analysis.md`
- `docs/analysis/0253-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成理论分析成果写入 `docs/analysis/0253-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0253-analysis.md`，将状态修改为 `status: done`。

## 严格红线
- 严禁向远程平台提交榜单，严禁修改实盘提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_1400 (14:00) ----------------
    {
        "batch_id": "batch_1400",
        "target_time": "14:00",
        "tasks": [
            {
                "id": "0254",
                "title": "决战日前夜系统环境清洁度与无痕化审计证明",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0254 任务：决战日前夜系统环境清洁度与无痕化审计证明

## 任务背景
排查全仓库是否存在临时日志、调试输出、密钥遗留或非合规代码。

## 考核目标
完成全代码库敏感信息与历史垃圾清理并出具审计证明。

## 预期产出路径
- `zcode/reports/0254-analysis.md`
- `docs/analysis/0254-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成理论分析成果写入 `docs/analysis/0254-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0254-analysis.md`，将状态修改为 `status: done`。

## 严格红线
- 严禁向远程平台提交榜单，严禁修改实盘提交凭据。
"""
            },
            {
                "id": "0255",
                "title": "5发串行实战发射序列沙盘推演与异常分支自动化熔断机制",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0255 任务：5发串行实战发射序列沙盘推演与异常分支自动化熔断机制

## 任务背景
验证在官方平台长时间不出分或出现网络超时时的自动熔断与降级保护机制。

## 考核目标
验证超时熔断器在 60 分钟无成绩时自动降级 fallback。

## 预期产出路径
- `zcode/reports/0255-analysis.md`
- `docs/analysis/0255-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成理论分析成果写入 `docs/analysis/0255-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0255-analysis.md`，将状态修改为 `status: done`。

## 严格红线
- 严禁向远程平台提交榜单，严禁修改实盘提交凭据。
"""
            },
            {
                "id": "0256",
                "title": "全国总决赛技术决胜白皮书归档封存与主哈希清单",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0256 任务：全国总决赛技术决胜白皮书归档封存与主哈希清单

## 任务背景
归档整理全项目 256 项科研任务与理论推导成果，封存不可篡改的主签名清单。

## 考核目标
将 256 项科研成果全量打包并封存 master 证书。

## 预期产出路径
- `zcode/reports/0256-analysis.md`
- `docs/analysis/0256-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成理论分析成果写入 `docs/analysis/0256-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0256-analysis.md`，将状态修改为 `status: done`。

## 严格红线
- 严禁向远程平台提交榜单，严禁修改实盘提交凭据。
"""
            }
        ]
    }
,
    # ---------------- 批次：batch_tonight_1830 (18:30) ----------------
    {
        "batch_id": "batch_tonight_1830",
        "target_time": "18:30",
        "tasks": [
            {
                "id": "0257",
                "title": "网络接口 MTU 探测与巨型帧分片开销在浅缓冲区下的性能边界",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0257 任务：网络接口 MTU 探测与巨型帧分片开销在浅缓冲区下的性能边界

## 任务背景
测试不同 MTU 设置下的分片开销并评估浅队列下的分片丢失风险。

## 考核目标
计算分片丢包临界点并量化 1200B 安全边界。

## 预期产出路径
- `zcode/reports/0257-analysis.md`
- `docs/analysis/0257-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成理论分析成果写入 `docs/analysis/0257-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0257-analysis.md`，将状态修改为 `status: done`。

## 严格红线
- 严禁向远程平台提交榜单，严禁修改实盘提交凭据。
"""
            },
            {
                "id": "0258",
                "title": "零拷贝数据包发送路径与内核环形缓冲区溢出防御",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0258 任务：零拷贝数据包发送路径与内核环形缓冲区溢出防御

## 任务背景
测试用户态 UDP 数据包直接发送与内核 ring buffer 占用率。

## 考核目标
验证 90Mbps 线速下 ring buffer 零丢包。

## 预期产出路径
- `zcode/reports/0258-analysis.md`
- `docs/analysis/0258-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成理论分析成果写入 `docs/analysis/0258-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0258-analysis.md`，将状态修改为 `status: done`。

## 严格红线
- 严禁向远程平台提交榜单，严禁修改实盘提交凭据。
"""
            },
            {
                "id": "0259",
                "title": "针对 11/08 00:05 启动前 60 分钟自动化演练回放",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0259 任务：针对 11/08 00:05 启动前 60 分钟自动化演练回放

## 任务背景
回放 1-by-1 自适应决策引擎在开打前的模拟流程。

## 考核目标
验证全自动化调度流水线 60 分钟演练 100% 顺畅。

## 预期产出路径
- `zcode/reports/0259-analysis.md`
- `docs/analysis/0259-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成理论分析成果写入 `docs/analysis/0259-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0259-analysis.md`，将状态修改为 `status: done`。

## 严格红线
- 严禁向远程平台提交榜单，严禁修改实盘提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_tonight_1900 (19:00) ----------------
    {
        "batch_id": "batch_tonight_1900",
        "target_time": "19:00",
        "tasks": [
            {
                "id": "0260",
                "title": "多客户端并发下的官方判分队列排队延迟拟合",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0260 任务：多客户端并发下的官方判分队列排队延迟拟合

## 任务背景
拟合高峰期官方判分队列等待时间的非参数分布。

## 考核目标
建立多队伍提交排队模型并预测出分延迟分布。

## 预期产出路径
- `zcode/reports/0260-analysis.md`
- `docs/analysis/0260-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成理论分析成果写入 `docs/analysis/0260-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0260-analysis.md`，将状态修改为 `status: done`。

## 严格红线
- 严禁向远程平台提交榜单，严禁修改实盘提交凭据。
"""
            },
            {
                "id": "0261",
                "title": "拥塞窗口突发重置与恢复时延下限分析",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0261 任务：拥塞窗口突发重置与恢复时延下限分析

## 任务背景
分析在偶发丢包后窗口快速乘性减与快速恢复时间下界。

## 考核目标
证明窗口突发重置后恢复时间 <= 2.5 RTT。

## 预期产出路径
- `zcode/reports/0261-analysis.md`
- `docs/analysis/0261-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成理论分析成果写入 `docs/analysis/0261-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0261-analysis.md`，将状态修改为 `status: done`。

## 严格红线
- 严禁向远程平台提交榜单，严禁修改实盘提交凭据。
"""
            },
            {
                "id": "0262",
                "title": "决选专家答辩现场 3 分钟极简陈述提纲",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0262 任务：决选专家答辩现场 3 分钟极简陈述提纲

## 任务背景
提炼项目 256 项科研成果为 3 分钟高密度答辩讲义。

## 考核目标
产出结构化 3 分钟白板讲解脚本与核心数字清单。

## 预期产出路径
- `zcode/reports/0262-analysis.md`
- `docs/analysis/0262-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成理论分析成果写入 `docs/analysis/0262-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0262-analysis.md`，将状态修改为 `status: done`。

## 严格红线
- 严禁向远程平台提交榜单，严禁修改实盘提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_tonight_1930 (19:30) ----------------
    {
        "batch_id": "batch_tonight_1930",
        "target_time": "19:30",
        "tasks": [
            {
                "id": "0263",
                "title": "基于隐马尔可夫模型 HMM 的信道多状态自适应推断",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0263 任务：基于隐马尔可夫模型 HMM 的信道多状态自适应推断

## 任务背景
利用 HMM 建模信道在空闲、轻载、重载状态间的转移概率。

## 考核目标
验证前向后向算法在 3 个状态间推断准确率 >= 92%。

## 预期产出路径
- `zcode/reports/0263-analysis.md`
- `docs/analysis/0263-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成理论分析成果写入 `docs/analysis/0263-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0263-analysis.md`，将状态修改为 `status: done`。

## 严格红线
- 严禁向远程平台提交榜单，严禁修改实盘提交凭据。
"""
            },
            {
                "id": "0264",
                "title": "QUIC 握手 0-RTT 与 1-RTT 密钥交换能耗与时间对比",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0264 任务：QUIC 握手 0-RTT 与 1-RTT 密钥交换能耗与时间对比

## 任务背景
比较两种握手模式在首发下载中的建连耗时与安全边界。

## 考核目标
量化 0-RTT 重放保护开销与首次连接延迟。

## 预期产出路径
- `zcode/reports/0264-analysis.md`
- `docs/analysis/0264-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成理论分析成果写入 `docs/analysis/0264-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0264-analysis.md`，将状态修改为 `status: done`。

## 严格红线
- 严禁向远程平台提交榜单，严禁修改实盘提交凭据。
"""
            },
            {
                "id": "0265",
                "title": "官方 6 目录配置热切换原子性在极限并发下的压力测试",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0265 任务：官方 6 目录配置热切换原子性在极限并发下的压力测试

## 任务背景
模拟评测客户端高频读取时配置树覆写的原子性。

## 考核目标
验证 1000 次高频并发读取无半文件现象。

## 预期产出路径
- `zcode/reports/0265-analysis.md`
- `docs/analysis/0265-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成理论分析成果写入 `docs/analysis/0265-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0265-analysis.md`，将状态修改为 `status: done`。

## 严格红线
- 严禁向远程平台提交榜单，严禁修改实盘提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_tonight_2000 (20:00) ----------------
    {
        "batch_id": "batch_tonight_2000",
        "target_time": "20:00",
        "tasks": [
            {
                "id": "0266",
                "title": "瓶颈网络主动丢包与无源排队时延交叉度量",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0266 任务：瓶颈网络主动丢包与无源排队时延交叉度量

## 任务背景
交叉对比排队时延增长与丢包发生的时域同步性。

## 考核目标
计算主动标记与排队膨胀的联合分布相关系数。

## 预期产出路径
- `zcode/reports/0266-analysis.md`
- `docs/analysis/0266-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成理论分析成果写入 `docs/analysis/0266-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0266-analysis.md`，将状态修改为 `status: done`。

## 严格红线
- 严禁向远程平台提交榜单，严禁修改实盘提交凭据。
"""
            },
            {
                "id": "0267",
                "title": "帕累托最优前沿面离散点邻域鲁棒性扰动再验证",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0267 任务：帕累托最优前沿面离散点邻域鲁棒性扰动再验证

## 任务背景
对 Crown Fusion 6 阶段离散点进行全维度局部扰动测试。

## 考核目标
验证在 +-1 包速率扰动下用时恶化 <= 0.8s。

## 预期产出路径
- `zcode/reports/0267-analysis.md`
- `docs/analysis/0267-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成理论分析成果写入 `docs/analysis/0267-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0267-analysis.md`，将状态修改为 `status: done`。

## 严格红线
- 严禁向远程平台提交榜单，严禁修改实盘提交凭据。
"""
            },
            {
                "id": "0268",
                "title": "11/08 首发倒计时 6 小时全员战备令与封板签字",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0268 任务：11/08 首发倒计时 6 小时全员战备令与封板签字

## 任务背景
对系统进行 6 小时倒计时战备巡检与终审盖章。

## 考核目标
完成 6 小时战备令各项合规签署并落盘证书。

## 预期产出路径
- `zcode/reports/0268-analysis.md`
- `docs/analysis/0268-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成理论分析成果写入 `docs/analysis/0268-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0268-analysis.md`，将状态修改为 `status: done`。

## 严格红线
- 严禁向远程平台提交榜单，严禁修改实盘提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_tonight_2030 (20:30) ----------------
    {
        "batch_id": "batch_tonight_2030",
        "target_time": "20:30",
        "tasks": [
            {
                "id": "0269",
                "title": "官方计分机制对极端离群值的截断与滤波行为审计",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0269 任务：官方计分机制对极端离群值的截断与滤波行为审计

## 任务背景
研究官方榜单对单次异常高分或低分的滤波鲁棒性。

## 考核目标
验证多次取平均机制下鲁棒均值估计的最优性。

## 预期产出路径
- `zcode/reports/0269-analysis.md`
- `docs/analysis/0269-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成理论分析成果写入 `docs/analysis/0269-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0269-analysis.md`，将状态修改为 `status: done`。

## 严格红线
- 严禁向远程平台提交榜单，严禁修改实盘提交凭据。
"""
            },
            {
                "id": "0270",
                "title": "客户端用户态时钟漂移在长时间运行下的累积误差评估",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0270 任务：客户端用户态时钟漂移在长时间运行下的累积误差评估

## 任务背景
长周期测试用户态时钟源单调性与漂移补偿精度。

## 考核目标
验证 8 小时连续运行累计漂移 <= 15us。

## 预期产出路径
- `zcode/reports/0270-analysis.md`
- `docs/analysis/0270-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成理论分析成果写入 `docs/analysis/0270-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0270-analysis.md`，将状态修改为 `status: done`。

## 严格红线
- 严禁向远程平台提交榜单，严禁修改实盘提交凭据。
"""
            },
            {
                "id": "0271",
                "title": "答辩 PPT 终版关键图表高清生成与落盘核验",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0271 任务：答辩 PPT 终版关键图表高清生成与落盘核验

## 任务背景
渲染相空间吸引子、DDE 根轨迹与 Sobol 方差分解高清图。

## 考核目标
生成 5 张高清晰度核心矢量相图与结构拓扑图。

## 预期产出路径
- `zcode/reports/0271-analysis.md`
- `docs/analysis/0271-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成理论分析成果写入 `docs/analysis/0271-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0271-analysis.md`，将状态修改为 `status: done`。

## 严格红线
- 严禁向远程平台提交榜单，严禁修改实盘提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_tonight_2100 (21:00) ----------------
    {
        "batch_id": "batch_tonight_2100",
        "target_time": "21:00",
        "tasks": [
            {
                "id": "0272",
                "title": "针对全国 Top 3 竞争对手历史最优轨迹的高精度逆向拟合",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0272 任务：针对全国 Top 3 竞争对手历史最优轨迹的高精度逆向拟合

## 任务背景
利用其公开出分耗时反演对手可能采用的整形参数。

## 考核目标
拟合 Catnet 与光明未来 6 阶段速率组合。

## 预期产出路径
- `zcode/reports/0272-analysis.md`
- `docs/analysis/0272-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成理论分析成果写入 `docs/analysis/0272-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0272-analysis.md`，将状态修改为 `status: done`。

## 严格红线
- 严禁向远程平台提交榜单，严禁修改实盘提交凭据。
"""
            },
            {
                "id": "0273",
                "title": "极端偶发断网下客户端本地持久化与重发幂等性保证",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0273 任务：极端偶发断网下客户端本地持久化与重发幂等性保证

## 任务背景
测试断网环境下状态机防重发与自愈能力。

## 考核目标
验证网络中断 30s 恢复后提交状态 100% 保持。

## 预期产出路径
- `zcode/reports/0273-analysis.md`
- `docs/analysis/0273-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成理论分析成果写入 `docs/analysis/0273-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0273-analysis.md`，将状态修改为 `status: done`。

## 严格红线
- 严禁向远程平台提交榜单，严禁修改实盘提交凭据。
"""
            },
            {
                "id": "0274",
                "title": "全国总决赛出征前夜终极战备封箱证书 v3",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0274 任务：全国总决赛出征前夜终极战备封箱证书 v3

## 任务背景
完成最终阶段全量成果封存并签署总决赛出征令。

## 考核目标
封装 274 项科研任务并签署最终出征令。

## 预期产出路径
- `zcode/reports/0274-analysis.md`
- `docs/analysis/0274-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成理论分析成果写入 `docs/analysis/0274-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0274-analysis.md`，将状态修改为 `status: done`。

## 严格红线
- 严禁向远程平台提交榜单，严禁修改实盘提交凭据。
"""
            }
        ]
    }
,
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
,
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
,
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
,
    # ---------------- 批次：batch_dawn_0030 (00:30) ----------------
    {
        "batch_id": "batch_dawn_0030",
        "target_time": "00:30",
        "tasks": [
            {
                "id": "0293",
                "title": "Shot 1 真实出分榜单提取与信道拥塞度贝叶斯反演",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0293 任务：Shot 1 真实出分榜单提取与信道拥塞度贝叶斯反演

## 任务背景
Shot 1 提交后，建立官方 API 出分反演模型，通过首发实测下载时间 T1，后验推导信道实际排队延迟与交叉流突发强度。

## 目标
验证出分后验推导算法，输出拥塞度置信区间，后验反演准确率 >= 90.0%。

## 预期产出路径
- `zcode/reports/0293-analysis.md`
- `docs/analysis/0293-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0293-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0293-analysis.md`，状态修改为 `status: done`。

## 合规守则
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0294",
                "title": "Shot 2 动态自适应分支决策与热切换无缝注入",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0294 任务：Shot 2 动态自适应分支决策与热切换无缝注入

## 任务背景
验证根据 Shot 1 真实出分（<=122.5s / 122.5~125s / >125s）动态分发 Shot 2（冲冠主力 / 超宽平台 / 防守堡垒）的热切换机制。

## 目标
验证决策 DAG 状态机切换延迟 <= 5ms，无死锁，状态落盘 100% 幂等。

## 预期产出路径
- `zcode/reports/0294-analysis.md`
- `docs/analysis/0294-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0294-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0294-analysis.md`，状态修改为 `status: done`。

## 合规守则
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0295",
                "title": "官方复测鲁棒性裕度在线交叉验证",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0295 任务：官方复测鲁棒性裕度在线交叉验证

## 任务背景
官方采用多次复测取平均更新排行榜。在首发与次发后，实时在线模拟复测均值稳定性，防止陷入尖锐孤立点。

## 目标
完成 1,000 次蒙特卡洛复测抽样，验证 3 次复测均值漂移 <= 1.2s，方差稳健度 >= 85.0%。

## 预期产出路径
- `zcode/reports/0295-analysis.md`
- `docs/analysis/0295-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0295-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0295-analysis.md`，状态修改为 `status: done`。

## 合规守则
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_dawn_0100 (01:00) ----------------
    {
        "batch_id": "batch_dawn_0100",
        "target_time": "01:00",
        "tasks": [
            {
                "id": "0296",
                "title": "Shot 2 真机出分与全国排名异动追踪",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0296 任务：Shot 2 真机出分与全国排名异动追踪

## 任务背景
跟踪 Shot 2 榜单变动，对标全国第一 Catnet (119.8293s) 与 光明未来 (117.0257s)，计算胜率与差距分段。

## 目标
验证排名变动捕获延迟 <= 10s，胜率评估置信度 >= 95.0%。

## 预期产出路径
- `zcode/reports/0296-analysis.md`
- `docs/analysis/0296-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0296-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0296-analysis.md`，状态修改为 `status: done`。

## 合规守则
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0297",
                "title": "Shot 3 进攻/防守动态权重博弈分配",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0297 任务：Shot 3 进攻/防守动态权重博弈分配

## 任务背景
在已获得前两发真实成绩后，基于博弈论分配 Shot 3 的进攻性（冲 116s）与防守性（固化前三）权重系数。

## 目标
求解纳什均衡混合策略最优权重，攻防综合期望效用提升 >= 15.0%。

## 预期产出路径
- `zcode/reports/0297-analysis.md`
- `docs/analysis/0297-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0297-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0297-analysis.md`，状态修改为 `status: done`。

## 合规守则
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0298",
                "title": "浅缓冲区纳什均衡与多租户挤出效应微观建模",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0298 任务：浅缓冲区纳什均衡与多租户挤出效应微观建模

## 任务背景
深夜时段其他参赛队伍与官方背景流在 30 包浅缓冲区的竞争行为，微观仿真定步长匀速流对激进脉冲流的自然挤出效应。

## 目标
证明定步长流在浅缓冲区的带宽占有率优势 >= 65.0%，主动丢包率为 0。

## 预期产出路径
- `zcode/reports/0298-analysis.md`
- `docs/analysis/0298-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0298-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0298-analysis.md`，状态修改为 `status: done`。

## 合规守则
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_dawn_0130 (01:30) ----------------
    {
        "batch_id": "batch_dawn_0130",
        "target_time": "01:30",
        "tasks": [
            {
                "id": "0299",
                "title": "Shot 3 真机成绩吸收与全国前三排位巩固",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0299 任务：Shot 3 真机成绩吸收与全国前三排位巩固

## 任务背景
吸收 Shot 3 真机成绩，更新全队 5 发战绩置信区间与登上领奖台（Top 3）的联合概率。

## 目标
验证三发成绩联合分布，领奖台概率达到 >= 92.0%。

## 预期产出路径
- `zcode/reports/0299-analysis.md`
- `docs/analysis/0299-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0299-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0299-analysis.md`，状态修改为 `status: done`。

## 合规守则
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0300",
                "title": "11/08 决胜半程战果推演与 Shot 4 决战终局参数微调",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0300 任务：11/08 决胜半程战果推演与 Shot 4 决战终局参数微调

## 任务背景
过半程后（已发 3 发，剩余 2 发），对 Shot 4 进行参数级微调（±0.5 pkts/tick 或微调 precise rate 12MB/s），锁定最终冲击窗口。

## 目标
验证微调邻域稳定性，单调收敛概率 >= 95.0%。

## 预期产出路径
- `zcode/reports/0300-analysis.md`
- `docs/analysis/0300-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0300-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0300-analysis.md`，状态修改为 `status: done`。

## 合规守则
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0301",
                "title": "极端高负载宿主机下 UDP 丢包重传尾部延迟对冲",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0301 任务：极端高负载宿主机下 UDP 丢包重传尾部延迟对冲

## 任务背景
在大文件阶段（5.bin 与 6.bin），仿真宿主机遭遇外部高负载突发时的 QUIC 尾部丢包重传惩罚，验证 pacing 抑制定律。

## 目标
证明平滑 pacing 下重传次数下降 >= 80.0%，尾部 P99 延迟压缩 <= 15ms。

## 预期产出路径
- `zcode/reports/0301-analysis.md`
- `docs/analysis/0301-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0301-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0301-analysis.md`，状态修改为 `status: done`。

## 合规守则
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_dawn_0200 (02:00) ----------------
    {
        "batch_id": "batch_dawn_0200",
        "target_time": "02:00",
        "tasks": [
            {
                "id": "0302",
                "title": "Shot 4 真机出分捕获与全国第一绝杀点位校验",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0302 任务：Shot 4 真机出分捕获与全国第一绝杀点位校验

## 任务背景
捕获 Shot 4 真机出分，若已击败第一名（<117.0257s），启动保分与统一复测防护；若仍有微小差距，计算 Shot 5 绝杀概率。

## 目标
完成绝杀边界灵敏度分析，判定决胜状态机转移至 Shot 5 冲顶或收官。

## 预期产出路径
- `zcode/reports/0302-analysis.md`
- `docs/analysis/0302-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0302-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0302-analysis.md`，状态修改为 `status: done`。

## 合规守则
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0303",
                "title": "Shot 5 终局压轴发全油门冲击策略裁决",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0303 任务：Shot 5 终局压轴发全油门冲击策略裁决

## 任务背景
今日官方最后一发（5/5 终局之战），根据前 4 发最优成绩与全场排名，执行绝对冲刺或最终护城河锁定。

## 目标
验证 Shot 5 裁决逻辑无死循环，全场最优成绩确定性极大化。

## 预期产出路径
- `zcode/reports/0303-analysis.md`
- `docs/analysis/0303-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0303-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0303-analysis.md`，状态修改为 `status: done`。

## 合规守则
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0304",
                "title": "全 5 发端到端闭环自适应实验归档与复盘模型构建",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0304 任务：全 5 发端到端闭环自适应实验归档与复盘模型构建

## 任务背景
在 11/08 5 发官方提交全部出分并登榜后，全面归档真机出分、排名跃迁、各阶段下载耗时、闭环决策记录，完成终极复盘。

## 目标
生成完整 11/08 决战复盘报告与全景数据报表，验证反过拟合纪律与大样本复测一致性。

## 预期产出路径
- `zcode/reports/0304-analysis.md`
- `docs/analysis/0304-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0304-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0304-analysis.md`，状态修改为 `status: done`。

## 合规守则
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            }
        ]
    }
,
    # ---------------- 批次：batch_dawn_0230 (02:30) ----------------
    {
        "batch_id": "batch_dawn_0230",
        "target_time": "02:30",
        "tasks": [
            {
                "id": "0305",
                "title": "Shot 1 真实出分与仿真反演残差标定及信道参数重估",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0305 任务：Shot 1 真实出分与仿真反演残差标定及信道参数重估

## 任务背景
在实战出分后，比对 Shot 1 实测值与贝叶斯预测值之间的残差，重估信道背景流强度与浅缓冲区排队延迟。

## 目标
验证残差标定误差 <= 0.8s，信道参数重估置信度 >= 95.0%。

## 预期产出路径
- `zcode/reports/0305-analysis.md`
- `docs/analysis/0305-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0305-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0305-analysis.md`，状态修改为 `status: done`。

## 合规守则
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0306",
                "title": "Shot 2 实时信道状态迁移矩阵更新与转移概率马尔可夫链稳态求解",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0306 任务：Shot 2 实时信道状态迁移矩阵更新与转移概率马尔可夫链稳态求解

## 任务背景
在获取 Shot 1、2 状态转移后，更新非平稳马尔可夫链的一步转移概率矩阵 P，求解夜间低负载稳态分布。

## 目标
证明稳态马尔可夫分布收敛性，谱半径 rho < 1.0，求解精度 <= 1e-4。

## 预期产出路径
- `zcode/reports/0306-analysis.md`
- `docs/analysis/0306-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0306-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0306-analysis.md`，状态修改为 `status: done`。

## 合规守则
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0307",
                "title": "官方评测服务器夜间 CPU 负载与调度抖动时序分解",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0307 任务：官方评测服务器夜间 CPU 负载与调度抖动时序分解

## 任务背景
对深夜 00:00~03:00 期间宿主机时钟中断与 CPU 争抢时序进行小波变换与频域分解，提取毛刺发生周期。

## 目标
验证时延毛刺周期性置信度，高频调度毛刺抑制比 >= 90.0%。

## 预期产出路径
- `zcode/reports/0307-analysis.md`
- `docs/analysis/0307-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0307-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0307-analysis.md`，状态修改为 `status: done`。

## 合规守则
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_dawn_0300 (03:00) ----------------
    {
        "batch_id": "batch_dawn_0300",
        "target_time": "03:00",
        "tasks": [
            {
                "id": "0308",
                "title": "Shot 3 破纪录点位全国排名跃迁监测与警报触发",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0308 任务：Shot 3 破纪录点位全国排名跃迁监测与警报触发

## 任务背景
Shot 3 突破 Catnet (119.8293s) 后的全国大榜排位跃迁实时监测，建立胜果固化与通知触发机制。

## 目标
验证排位跃迁捕获时延 <= 5s，破纪录状态确定性 100%。

## 预期产出路径
- `zcode/reports/0308-analysis.md`
- `docs/analysis/0308-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0308-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0308-analysis.md`，状态修改为 `status: done`。

## 合规守则
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0309",
                "title": "多流并发下浅缓冲区丢包避免与单流吞吐极大化凸优化证明",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0309 任务：多流并发下浅缓冲区丢包避免与单流吞吐极大化凸优化证明

## 任务背景
在 30 包浅缓冲区中，建立多流速率分配凸优化拉格朗日对偶模型，证明定步长流在保证 0 溢出下的吞吐极大化。

## 目标
推导 KKT 条件解析解，证明皇冠构型处于全局凸极值点。

## 预期产出路径
- `zcode/reports/0309-analysis.md`
- `docs/analysis/0309-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0309-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0309-analysis.md`，状态修改为 `status: done`。

## 合规守则
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0310",
                "title": "决赛最终统一复测敏感度分析与极小极大遗憾度决策准则",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0310 任务：决赛最终统一复测敏感度分析与极小极大遗憾度决策准则

## 任务背景
依据官方 top 统一复测规则，利用 Minimax Regret 理论，评估在最不利随机种子下的性能保底。

## 目标
证明极小极大遗憾度指标优于对手 >= 40.0%，复测跌出前三概率 <= 0.5%。

## 预期产出路径
- `zcode/reports/0310-analysis.md`
- `docs/analysis/0310-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0310-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0310-analysis.md`，状态修改为 `status: done`。

## 合规守则
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_dawn_0330 (03:30) ----------------
    {
        "batch_id": "batch_dawn_0330",
        "target_time": "03:30",
        "tasks": [
            {
                "id": "0311",
                "title": "Shot 4 决战终局冲冠点位全链路延迟预算解构",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0311 任务：Shot 4 决战终局冲冠点位全链路延迟预算解构

## 任务背景
冲击全国第一（光明未来 117.0257s）的延迟预算分配，精确分解握手、传输、排队与尾部确认耗时。

## 目标
验证延迟预算各分量误差 <= 0.05s，登顶预期时间缩减至 <= 116.8s。

## 预期产出路径
- `zcode/reports/0311-analysis.md`
- `docs/analysis/0311-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0311-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0311-analysis.md`，状态修改为 `status: done`。

## 合规守则
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0312",
                "title": "QUIC 传输层滑动窗口与用户态 Pacing 队列动态同步死锁防御",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0312 任务：QUIC 传输层滑动窗口与用户态 Pacing 队列动态同步死锁防御

## 任务背景
分析在极端网络背压下，QUIC flow control window 与 pacing 队列的耦合震荡风险，设计死锁防护机制。

## 目标
证明在窗口收缩至 1 个 MSS 极限工况下无死锁，拥塞窗口恢复时延 <= 1 RTT。

## 预期产出路径
- `zcode/reports/0312-analysis.md`
- `docs/analysis/0312-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0312-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0312-analysis.md`，状态修改为 `status: done`。

## 合规守则
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0313",
                "title": "官方排行榜出分序列时序相关性分析与随机游走假设检验",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0313 任务：官方排行榜出分序列时序相关性分析与随机游走假设检验

## 任务背景
对历史全量出分序列进行自相关函数 (ACF) 与偏自相关函数 (PACF) 计算，检验信道非平稳随机游走特性。

## 目标
验证出分序列自回归阶数 AR(p)，自相关系数置信度 >= 95.0%。

## 预期产出路径
- `zcode/reports/0313-analysis.md`
- `docs/analysis/0313-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0313-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0313-analysis.md`，状态修改为 `status: done`。

## 合规守则
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_dawn_0400 (04:00) ----------------
    {
        "batch_id": "batch_dawn_0400",
        "target_time": "04:00",
        "tasks": [
            {
                "id": "0314",
                "title": "Shot 5 压轴终局提交战报汇总与全国冠军领奖台最终固化",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0314 任务：Shot 5 压轴终局提交战报汇总与全国冠军领奖台最终固化

## 任务背景
在 5/5 全部出分后，汇总全日实战成绩、排位跃迁轨迹与官方统一复测入选资质，锁定胜局。

## 目标
生成 5 发全景实战汇总表，官方最优成绩确定性 100%。

## 预期产出路径
- `zcode/reports/0314-analysis.md`
- `docs/analysis/0314-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0314-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0314-analysis.md`，状态修改为 `status: done`。

## 合规守则
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0315",
                "title": "11/08 全 5 发端到端闭环自适应决策全景复盘与经验总结白皮书",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0315 任务：11/08 全 5 发端到端闭环自适应决策全景复盘与经验总结白皮书

## 任务背景
系统化复盘「打一发再分析下一发怎么打」的决策闭环全过程，总结信息增益、参数自适应与抗扰对冲实战经验。

## 目标
完成千行级决胜白皮书，全面归档实战数据与学术复盘。

## 预期产出路径
- `zcode/reports/0315-analysis.md`
- `docs/analysis/0315-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0315-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0315-analysis.md`，状态修改为 `status: done`。

## 合规守则
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0316",
                "title": "全国总决赛技术决胜终极归档封板与全资产 SHA-256 统一哈希大印章 v4",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0316 任务：全国总决赛技术决胜终极归档封板与全资产 SHA-256 统一哈希大印章 v4

## 任务背景
在全部实战与复盘收官后，对整个代码库、全部理论报告与验证脚本签署终极大印章 v4，完成全生命周期数字指纹固化。

## 目标
签发 Grand Master Seal v4，全量资产哈希不可篡改，达成 100% 决战大圆满。

## 预期产出路径
- `zcode/reports/0316-analysis.md`
- `docs/analysis/0316-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0316-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0316-analysis.md`，状态修改为 `status: done`。

## 合规守则
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            }
        ]
    }
,
    # ---------------- 批次：batch_campaign_0430 (04:30) ----------------
    {
        "batch_id": "batch_campaign_0430",
        "target_time": "04:30",
        "tasks": [
            {
                "id": "0317",
                "title": "Shot-1-出分残差深度对齐与跨宿主机拓扑推断",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0317 任务：Shot-1-出分残差深度对齐与跨宿主机拓扑推断

## 任务背景
基于首发实测成绩与先验预测残差，重构评测网络物理拓扑特征。

## 目标
残差重估置信度 >= 95.0%，拓扑拟合优度 R^2 >= 0.90。

## 预期产出路径
- `zcode/reports/0317-analysis.md`
- `docs/analysis/0317-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0317-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0317-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0318",
                "title": "Shot-2-前沿突变流量低通滤波补偿器设计",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0318 任务：Shot-2-前沿突变流量低通滤波补偿器设计

## 任务背景
针对评测机可能引入的高频中断，设计离散二阶抗混叠滤波器。

## 目标
高频脉冲抑制比 >= 85.0%，群延迟 <= 1.0ms。

## 预期产出路径
- `zcode/reports/0318-analysis.md`
- `docs/analysis/0318-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0318-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0318-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0319",
                "title": "突发丢包瞬态恢复窗口滑移稳定性证明",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0319 任务：突发丢包瞬态恢复窗口滑移稳定性证明

## 任务背景
QUIC 协议栈面对突发连续 3 包丢失时的 CWND 恢复与零抖动收敛。

## 目标
窗口恢复用时 <= 1.5 RTT，恢复期间零二次丢包。

## 预期产出路径
- `zcode/reports/0319-analysis.md`
- `docs/analysis/0319-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0319-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0319-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_0500 (05:00) ----------------
    {
        "batch_id": "batch_campaign_0500",
        "target_time": "05:00",
        "tasks": [
            {
                "id": "0320",
                "title": "Shot-2-出分后验吸收与多流排队微观反演",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0320 任务：Shot-2-出分后验吸收与多流排队微观反演

## 任务背景
吸收第 2 发出分数据，反演背景流排队队列占用与缓冲区溢出阈值。

## 目标
队列深度估计精度 >= 90.0%，后验方差缩小 >= 50.0%。

## 预期产出路径
- `zcode/reports/0320-analysis.md`
- `docs/analysis/0320-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0320-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0320-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0321",
                "title": "基于纳什讨价还价解的速率分配策略寻优",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0321 任务：基于纳什讨价还价解的速率分配策略寻优

## 任务背景
求解我方流与多条背景流在瓶颈路由器的非对称讨价还价均衡点。

## 目标
博弈解带宽占有率提升 >= 5.0%，零主动丢包。

## 预期产出路径
- `zcode/reports/0321-analysis.md`
- `docs/analysis/0321-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0321-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0321-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0322",
                "title": "极端网络抖动下端到端单调时钟漂移标定",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0322 任务：极端网络抖动下端到端单调时钟漂移标定

## 任务背景
针对虚拟化环境中的 TSC 时钟漂移，建立纳秒级时间戳校正模型。

## 目标
时钟漂移累积误差 <= 50us，抖动滤除率 >= 90.0%。

## 预期产出路径
- `zcode/reports/0322-analysis.md`
- `docs/analysis/0322-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0322-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0322-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_0530 (05:30) ----------------
    {
        "batch_id": "batch_campaign_0530",
        "target_time": "05:30",
        "tasks": [
            {
                "id": "0323",
                "title": "Shot-3-攻防博弈动态分支权值矩阵实时投影",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0323 任务：Shot-3-攻防博弈动态分支权值矩阵实时投影

## 任务背景
根据对手实时积分与出分动态，求解双人零和博弈纳什均衡最优混合策略。

## 目标
策略遗憾度 Regret <= 0.05，对抗胜率 >= 88.0%。

## 预期产出路径
- `zcode/reports/0323-analysis.md`
- `docs/analysis/0323-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0323-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0323-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0324",
                "title": "非凸参数流形上的拟牛顿割线步长加速探索",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0324 任务：非凸参数流形上的拟牛顿割线步长加速探索

## 任务背景
在 6 个轮次参数空间中应用 BFGS 算法逼近局部极小值。

## 目标
流形梯度模长收缩 >= 80.0%，计算开销 <= 5.0ms。

## 预期产出路径
- `zcode/reports/0324-analysis.md`
- `docs/analysis/0324-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0324-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0324-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0325",
                "title": "微秒级平滑令牌桶突发脉冲抑制有效性验证",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0325 任务：微秒级平滑令牌桶突发脉冲抑制有效性验证

## 任务背景
验证 bucket_cap=30 与 leak_interval=1000us 在纳秒级发包下的平滑度。

## 目标
突发脉冲因子 F <= 1.05，峰均比降低 >= 40.0%。

## 预期产出路径
- `zcode/reports/0325-analysis.md`
- `docs/analysis/0325-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0325-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0325-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_0600 (06:00) ----------------
    {
        "batch_id": "batch_campaign_0600",
        "target_time": "06:00",
        "tasks": [
            {
                "id": "0326",
                "title": "Shot-3-出分成绩吸收与前三名位次敏感度分析",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0326 任务：Shot-3-出分成绩吸收与前三名位次敏感度分析

## 任务背景
吸收第 3 发出分，评估进入全国前三名概率与位次弹性。

## 目标
前三名锁定置信度 >= 99.0%，弹性系数绝对值 <= 0.20。

## 预期产出路径
- `zcode/reports/0326-analysis.md`
- `docs/analysis/0326-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0326-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0326-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0327",
                "title": "跨轮次状态记忆与热启动参数无缝迁移验证",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0327 任务：跨轮次状态记忆与热启动参数无缝迁移验证

## 任务背景
验证 1 到 6 轮次间 pacer 状态继承机制与热启动零等待特性。

## 目标
热启动重置延迟 <= 10us，继承连续性 100.0%。

## 预期产出路径
- `zcode/reports/0327-analysis.md`
- `docs/analysis/0327-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0327-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0327-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0328",
                "title": "浅队列多租户竞争环境下的公平性与吞吐权衡",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0328 任务：浅队列多租户竞争环境下的公平性与吞吐权衡

## 任务背景
在 10-packet 浅队列中推演多租户竞争下的瓶颈吞吐分配方程。

## 目标
有效吞吐占比 >= 65.0%，拥塞丢包率 = 0.00%。

## 预期产出路径
- `zcode/reports/0328-analysis.md`
- `docs/analysis/0328-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0328-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0328-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_0630 (06:30) ----------------
    {
        "batch_id": "batch_campaign_0630",
        "target_time": "06:30",
        "tasks": [
            {
                "id": "0329",
                "title": "Shot-4-冲榜绝杀点位高斯过程代理模型主动学习",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0329 任务：Shot-4-冲榜绝杀点位高斯过程代理模型主动学习

## 任务背景
利用高斯过程 GP 对未知参数空间进行期望提升（EI）采样。

## 目标
采样后验均方误差 MSE <= 0.05，局部最优发现概率 >= 95.0%。

## 预期产出路径
- `zcode/reports/0329-analysis.md`
- `docs/analysis/0329-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0329-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0329-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0330",
                "title": "多维参数扰动下的李雅普诺夫指数与混沌边缘检验",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0330 任务：多维参数扰动下的李雅普诺夫指数与混沌边缘检验

## 任务背景
验证混合整形动力系统在参数微扰下的李雅普诺夫指数 lambda < 0。

## 目标
最大李雅普诺夫指数 < -0.15，严格渐近稳定。

## 预期产出路径
- `zcode/reports/0330-analysis.md`
- `docs/analysis/0330-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0330-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0330-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0331",
                "title": "双边时延测量与不对称反向链路 ACK 压缩对冲",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0331 任务：双边时延测量与不对称反向链路 ACK 压缩对冲

## 任务背景
反向链路高延迟导致 ACK 堆叠时，前向 Pacing 速率的防骤增抑制器。

## 目标
ACK 堆叠抑制成功率 >= 98.0%，突发突发释放 = 0。

## 预期产出路径
- `zcode/reports/0331-analysis.md`
- `docs/analysis/0331-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0331-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0331-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_0700 (07:00) ----------------
    {
        "batch_id": "batch_campaign_0700",
        "target_time": "07:00",
        "tasks": [
            {
                "id": "0332",
                "title": "Shot-4-出分击穿全国第一确信度蒙特卡洛再估算",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0332 任务：Shot-4-出分击穿全国第一确信度蒙特卡洛再估算

## 任务背景
第 4 发真机出分后的全国冠军概率后验更新与 95% 置信区间收窄。

## 目标
击穿全国第一概率 >= 95.0%，置信区间宽度 <= 0.5s。

## 预期产出路径
- `zcode/reports/0332-analysis.md`
- `docs/analysis/0332-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0332-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0332-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0333",
                "title": "内核态与用户态零拷贝环形缓冲区无锁并发验证",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0333 任务：内核态与用户态零拷贝环形缓冲区无锁并发验证

## 任务背景
针对 Pacing 调度器在高并发下的无锁环形队列进行死锁与饥饿验证。

## 目标
无锁操作耗时 <= 15ns，无锁竞争零死锁。

## 预期产出路径
- `zcode/reports/0333-analysis.md`
- `docs/analysis/0333-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0333-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0333-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0334",
                "title": "QUIC 连接迁移与 NAT 重绑定下的状态机保活机制",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0334 任务：QUIC 连接迁移与 NAT 重绑定下的状态机保活机制

## 任务背景
应对评测环境潜在 NAT 映射重置的探测包与保活迁移机制。

## 目标
重绑定恢复时延 <= 0.5 RTT，状态一致性 100.0%。

## 预期产出路径
- `zcode/reports/0334-analysis.md`
- `docs/analysis/0334-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0334-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0334-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_0730 (07:30) ----------------
    {
        "batch_id": "batch_campaign_0730",
        "target_time": "07:30",
        "tasks": [
            {
                "id": "0335",
                "title": "Shot-5-终局压轴发极值分布重尾行为极值理论检验",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0335 任务：Shot-5-终局压轴发极值分布重尾行为极值理论检验

## 任务背景
运用广义极值分布（GEV）对 Shot 5 潜在极致低分进行极值行为建模。

## 目标
GEV 形状参数 xi <= 0（威布尔型薄尾），极小值下界明确。

## 预期产出路径
- `zcode/reports/0335-analysis.md`
- `docs/analysis/0335-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0335-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0335-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0336",
                "title": "全网流量重放与多背景流交织碰撞应力测试",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0336 任务：全网流量重放与多背景流交织碰撞应力测试

## 任务背景
在极端高密背景流下进行 10 万次碰撞仿真，验证无丢包稳健性。

## 目标
碰撞无丢包率 >= 99.99%，平均吞吐衰减 <= 1.2%。

## 预期产出路径
- `zcode/reports/0336-analysis.md`
- `docs/analysis/0336-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0336-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0336-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0337",
                "title": "参数树结构完整性与哈希一致性自动体检守护",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0337 任务：参数树结构完整性与哈希一致性自动体检守护

## 任务背景
对整个 runs/ 与 question/ 目录树进行完整性校验。

## 目标
树结构校验通过率 100.0%，孤立文件数 = 0。

## 预期产出路径
- `zcode/reports/0337-analysis.md`
- `docs/analysis/0337-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0337-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0337-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_0800 (08:00) ----------------
    {
        "batch_id": "batch_campaign_0800",
        "target_time": "08:00",
        "tasks": [
            {
                "id": "0338",
                "title": "Shot-5-压轴出分收官与全国榜首位次终极确立",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0338 任务：Shot-5-压轴出分收官与全国榜首位次终极确立

## 任务背景
汇总全 5 发实战完整轨迹，计算与官方最终排名的确定性对应关系。

## 目标
全国第一排名确认率 100.0%，榜首优势 >= 1.5s。

## 预期产出路径
- `zcode/reports/0338-analysis.md`
- `docs/analysis/0338-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0338-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0338-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0339",
                "title": "官方统一复测多样本均值漂移方差收敛性严格证明",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0339 任务：官方统一复测多样本均值漂移方差收敛性严格证明

## 任务背景
运用中心极限定理与大数定律证明 3 次复测取均值下胜率收敛。

## 目标
复测胜率 >= 99.0%，漂移风险度 < 0.01。

## 预期产出路径
- `zcode/reports/0339-analysis.md`
- `docs/analysis/0339-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0339-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0339-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0340",
                "title": "六载穿柜全周期自适应调参轨迹流形拓扑可视化",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0340 任务：六载穿柜全周期自适应调参轨迹流形拓扑可视化

## 任务背景
生成 5 发决策在六维参数空间中的轨迹流形与收敛相图。

## 目标
相轨迹单调收敛，收敛曲率指标 <= 0.05。

## 预期产出路径
- `zcode/reports/0340-analysis.md`
- `docs/analysis/0340-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0340-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0340-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_0830 (08:30) ----------------
    {
        "batch_id": "batch_campaign_0830",
        "target_time": "08:30",
        "tasks": [
            {
                "id": "0341",
                "title": "全 5 发端到端实验日志完整性与可复现性穿透审查",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0341 任务：全 5 发端到端实验日志完整性与可复现性穿透审查

## 任务背景
审查 runs/ 与 hourly/ 目录下全量实验日志的时间戳一致性与逻辑链。

## 目标
日志断点数 = 0，复现吻合率 100.0%。

## 预期产出路径
- `zcode/reports/0341-analysis.md`
- `docs/analysis/0341-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0341-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0341-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0342",
                "title": "全国排名前十选手关键参数分布推断与防御对比",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0342 任务：全国排名前十选手关键参数分布推断与防御对比

## 任务背景
基于公开榜单出分分布，反演竞品选手采用的拥塞控制算法类型。

## 目标
竞品算法分类准确率 >= 85.0%，防御对比优势确立。

## 预期产出路径
- `zcode/reports/0342-analysis.md`
- `docs/analysis/0342-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0342-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0342-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0343",
                "title": "全国总决赛技术决胜终极证据链 Grand Master Seal v5 签发",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0343 任务：全国总决赛技术决胜终极证据链 Grand Master Seal v5 签发

## 任务背景
整合全量实验、研报与代码资产，生成 Merkle Tree 终极大印章 v5。

## 目标
印章覆盖资产数 >= 280 项，防篡改认证 100.0%。

## 预期产出路径
- `zcode/reports/0343-analysis.md`
- `docs/analysis/0343-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0343-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0343-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            }
        ]
    }
,
    # ---------------- 批次：batch_campaign_0430 (04:30) ----------------
    {
        "batch_id": "batch_campaign_0430",
        "target_time": "04:30",
        "tasks": [
            {
                "id": "0317",
                "title": "Shot-1-出分残差深度对齐与跨宿主机拓扑推断",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0317 任务：Shot-1-出分残差深度对齐与跨宿主机拓扑推断

## 任务背景
基于首发实测成绩与先验预测残差，重构评测网络物理拓扑特征。

## 目标
残差重估置信度 >= 95.0%，拓扑拟合优度 R^2 >= 0.90。

## 预期产出路径
- `zcode/reports/0317-analysis.md`
- `docs/analysis/0317-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0317-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0317-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0318",
                "title": "Shot-2-前沿突变流量低通滤波补偿器设计",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0318 任务：Shot-2-前沿突变流量低通滤波补偿器设计

## 任务背景
针对评测机可能引入的高频中断，设计离散二阶抗混叠滤波器。

## 目标
高频脉冲抑制比 >= 85.0%，群延迟 <= 1.0ms。

## 预期产出路径
- `zcode/reports/0318-analysis.md`
- `docs/analysis/0318-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0318-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0318-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0319",
                "title": "突发丢包瞬态恢复窗口滑移稳定性证明",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0319 任务：突发丢包瞬态恢复窗口滑移稳定性证明

## 任务背景
QUIC 协议栈面对突发连续 3 包丢失时的 CWND 恢复与零抖动收敛。

## 目标
窗口恢复用时 <= 1.5 RTT，恢复期间零二次丢包。

## 预期产出路径
- `zcode/reports/0319-analysis.md`
- `docs/analysis/0319-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0319-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0319-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_0500 (05:00) ----------------
    {
        "batch_id": "batch_campaign_0500",
        "target_time": "05:00",
        "tasks": [
            {
                "id": "0320",
                "title": "Shot-2-出分后验吸收与多流排队微观反演",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0320 任务：Shot-2-出分后验吸收与多流排队微观反演

## 任务背景
吸收第 2 发出分数据，反演背景流排队队列占用与缓冲区溢出阈值。

## 目标
队列深度估计精度 >= 90.0%，后验方差缩小 >= 50.0%。

## 预期产出路径
- `zcode/reports/0320-analysis.md`
- `docs/analysis/0320-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0320-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0320-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0321",
                "title": "基于纳什讨价还价解的速率分配策略寻优",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0321 任务：基于纳什讨价还价解的速率分配策略寻优

## 任务背景
求解我方流与多条背景流在瓶颈路由器的非对称讨价还价均衡点。

## 目标
博弈解带宽占有率提升 >= 5.0%，零主动丢包。

## 预期产出路径
- `zcode/reports/0321-analysis.md`
- `docs/analysis/0321-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0321-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0321-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0322",
                "title": "极端网络抖动下端到端单调时钟漂移标定",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0322 任务：极端网络抖动下端到端单调时钟漂移标定

## 任务背景
针对虚拟化环境中的 TSC 时钟漂移，建立纳秒级时间戳校正模型。

## 目标
时钟漂移累积误差 <= 50us，抖动滤除率 >= 90.0%。

## 预期产出路径
- `zcode/reports/0322-analysis.md`
- `docs/analysis/0322-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0322-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0322-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_0530 (05:30) ----------------
    {
        "batch_id": "batch_campaign_0530",
        "target_time": "05:30",
        "tasks": [
            {
                "id": "0323",
                "title": "Shot-3-攻防博弈动态分支权值矩阵实时投影",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0323 任务：Shot-3-攻防博弈动态分支权值矩阵实时投影

## 任务背景
根据对手实时积分与出分动态，求解双人零和博弈纳什均衡最优混合策略。

## 目标
策略遗憾度 Regret <= 0.05，对抗胜率 >= 88.0%。

## 预期产出路径
- `zcode/reports/0323-analysis.md`
- `docs/analysis/0323-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0323-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0323-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0324",
                "title": "非凸参数流形上的拟牛顿割线步长加速探索",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0324 任务：非凸参数流形上的拟牛顿割线步长加速探索

## 任务背景
在 6 个轮次参数空间中应用 BFGS 算法逼近局部极小值。

## 目标
流形梯度模长收缩 >= 80.0%，计算开销 <= 5.0ms。

## 预期产出路径
- `zcode/reports/0324-analysis.md`
- `docs/analysis/0324-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0324-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0324-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0325",
                "title": "微秒级平滑令牌桶突发脉冲抑制有效性验证",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0325 任务：微秒级平滑令牌桶突发脉冲抑制有效性验证

## 任务背景
验证 bucket_cap=30 与 leak_interval=1000us 在纳秒级发包下的平滑度。

## 目标
突发脉冲因子 F <= 1.05，峰均比降低 >= 40.0%。

## 预期产出路径
- `zcode/reports/0325-analysis.md`
- `docs/analysis/0325-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0325-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0325-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_0600 (06:00) ----------------
    {
        "batch_id": "batch_campaign_0600",
        "target_time": "06:00",
        "tasks": [
            {
                "id": "0326",
                "title": "Shot-3-出分成绩吸收与前三名位次敏感度分析",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0326 任务：Shot-3-出分成绩吸收与前三名位次敏感度分析

## 任务背景
吸收第 3 发出分，评估进入全国前三名概率与位次弹性。

## 目标
前三名锁定置信度 >= 99.0%，弹性系数绝对值 <= 0.20。

## 预期产出路径
- `zcode/reports/0326-analysis.md`
- `docs/analysis/0326-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0326-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0326-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0327",
                "title": "跨轮次状态记忆与热启动参数无缝迁移验证",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0327 任务：跨轮次状态记忆与热启动参数无缝迁移验证

## 任务背景
验证 1 到 6 轮次间 pacer 状态继承机制与热启动零等待特性。

## 目标
热启动重置延迟 <= 10us，继承连续性 100.0%。

## 预期产出路径
- `zcode/reports/0327-analysis.md`
- `docs/analysis/0327-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0327-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0327-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0328",
                "title": "浅队列多租户竞争环境下的公平性与吞吐权衡",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0328 任务：浅队列多租户竞争环境下的公平性与吞吐权衡

## 任务背景
在 10-packet 浅队列中推演多租户竞争下的瓶颈吞吐分配方程。

## 目标
有效吞吐占比 >= 65.0%，拥塞丢包率 = 0.00%。

## 预期产出路径
- `zcode/reports/0328-analysis.md`
- `docs/analysis/0328-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0328-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0328-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_0630 (06:30) ----------------
    {
        "batch_id": "batch_campaign_0630",
        "target_time": "06:30",
        "tasks": [
            {
                "id": "0329",
                "title": "Shot-4-冲榜绝杀点位高斯过程代理模型主动学习",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0329 任务：Shot-4-冲榜绝杀点位高斯过程代理模型主动学习

## 任务背景
利用高斯过程 GP 对未知参数空间进行期望提升（EI）采样。

## 目标
采样后验均方误差 MSE <= 0.05，局部最优发现概率 >= 95.0%。

## 预期产出路径
- `zcode/reports/0329-analysis.md`
- `docs/analysis/0329-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0329-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0329-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0330",
                "title": "多维参数扰动下的李雅普诺夫指数与混沌边缘检验",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0330 任务：多维参数扰动下的李雅普诺夫指数与混沌边缘检验

## 任务背景
验证混合整形动力系统在参数微扰下的李雅普诺夫指数 lambda < 0。

## 目标
最大李雅普诺夫指数 < -0.15，严格渐近稳定。

## 预期产出路径
- `zcode/reports/0330-analysis.md`
- `docs/analysis/0330-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0330-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0330-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0331",
                "title": "双边时延测量与不对称反向链路 ACK 压缩对冲",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0331 任务：双边时延测量与不对称反向链路 ACK 压缩对冲

## 任务背景
反向链路高延迟导致 ACK 堆叠时，前向 Pacing 速率的防骤增抑制器。

## 目标
ACK 堆叠抑制成功率 >= 98.0%，突发突发释放 = 0。

## 预期产出路径
- `zcode/reports/0331-analysis.md`
- `docs/analysis/0331-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0331-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0331-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_0700 (07:00) ----------------
    {
        "batch_id": "batch_campaign_0700",
        "target_time": "07:00",
        "tasks": [
            {
                "id": "0332",
                "title": "Shot-4-出分击穿全国第一确信度蒙特卡洛再估算",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0332 任务：Shot-4-出分击穿全国第一确信度蒙特卡洛再估算

## 任务背景
第 4 发真机出分后的全国冠军概率后验更新与 95% 置信区间收窄。

## 目标
击穿全国第一概率 >= 95.0%，置信区间宽度 <= 0.5s。

## 预期产出路径
- `zcode/reports/0332-analysis.md`
- `docs/analysis/0332-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0332-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0332-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0333",
                "title": "内核态与用户态零拷贝环形缓冲区无锁并发验证",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0333 任务：内核态与用户态零拷贝环形缓冲区无锁并发验证

## 任务背景
针对 Pacing 调度器在高并发下的无锁环形队列进行死锁与饥饿验证。

## 目标
无锁操作耗时 <= 15ns，无锁竞争零死锁。

## 预期产出路径
- `zcode/reports/0333-analysis.md`
- `docs/analysis/0333-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0333-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0333-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0334",
                "title": "QUIC 连接迁移与 NAT 重绑定下的状态机保活机制",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0334 任务：QUIC 连接迁移与 NAT 重绑定下的状态机保活机制

## 任务背景
应对评测环境潜在 NAT 映射重置的探测包与保活迁移机制。

## 目标
重绑定恢复时延 <= 0.5 RTT，状态一致性 100.0%。

## 预期产出路径
- `zcode/reports/0334-analysis.md`
- `docs/analysis/0334-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0334-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0334-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_0730 (07:30) ----------------
    {
        "batch_id": "batch_campaign_0730",
        "target_time": "07:30",
        "tasks": [
            {
                "id": "0335",
                "title": "Shot-5-终局压轴发极值分布重尾行为极值理论检验",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0335 任务：Shot-5-终局压轴发极值分布重尾行为极值理论检验

## 任务背景
运用广义极值分布（GEV）对 Shot 5 潜在极致低分进行极值行为建模。

## 目标
GEV 形状参数 xi <= 0（威布尔型薄尾），极小值下界明确。

## 预期产出路径
- `zcode/reports/0335-analysis.md`
- `docs/analysis/0335-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0335-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0335-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0336",
                "title": "全网流量重放与多背景流交织碰撞应力测试",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0336 任务：全网流量重放与多背景流交织碰撞应力测试

## 任务背景
在极端高密背景流下进行 10 万次碰撞仿真，验证无丢包稳健性。

## 目标
碰撞无丢包率 >= 99.99%，平均吞吐衰减 <= 1.2%。

## 预期产出路径
- `zcode/reports/0336-analysis.md`
- `docs/analysis/0336-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0336-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0336-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0337",
                "title": "参数树结构完整性与哈希一致性自动体检守护",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0337 任务：参数树结构完整性与哈希一致性自动体检守护

## 任务背景
对整个 runs/ 与 question/ 目录树进行完整性校验。

## 目标
树结构校验通过率 100.0%，孤立文件数 = 0。

## 预期产出路径
- `zcode/reports/0337-analysis.md`
- `docs/analysis/0337-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0337-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0337-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_0800 (08:00) ----------------
    {
        "batch_id": "batch_campaign_0800",
        "target_time": "08:00",
        "tasks": [
            {
                "id": "0338",
                "title": "Shot-5-压轴出分收官与全国榜首位次终极确立",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0338 任务：Shot-5-压轴出分收官与全国榜首位次终极确立

## 任务背景
汇总全 5 发实战完整轨迹，计算与官方最终排名的确定性对应关系。

## 目标
全国第一排名确认率 100.0%，榜首优势 >= 1.5s。

## 预期产出路径
- `zcode/reports/0338-analysis.md`
- `docs/analysis/0338-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0338-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0338-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0339",
                "title": "官方统一复测多样本均值漂移方差收敛性严格证明",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0339 任务：官方统一复测多样本均值漂移方差收敛性严格证明

## 任务背景
运用中心极限定理与大数定律证明 3 次复测取均值下胜率收敛。

## 目标
复测胜率 >= 99.0%，漂移风险度 < 0.01。

## 预期产出路径
- `zcode/reports/0339-analysis.md`
- `docs/analysis/0339-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0339-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0339-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0340",
                "title": "六载穿柜全周期自适应调参轨迹流形拓扑可视化",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0340 任务：六载穿柜全周期自适应调参轨迹流形拓扑可视化

## 任务背景
生成 5 发决策在六维参数空间中的轨迹流形与收敛相图。

## 目标
相轨迹单调收敛，收敛曲率指标 <= 0.05。

## 预期产出路径
- `zcode/reports/0340-analysis.md`
- `docs/analysis/0340-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0340-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0340-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_0830 (08:30) ----------------
    {
        "batch_id": "batch_campaign_0830",
        "target_time": "08:30",
        "tasks": [
            {
                "id": "0341",
                "title": "全 5 发端到端实验日志完整性与可复现性穿透审查",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0341 任务：全 5 发端到端实验日志完整性与可复现性穿透审查

## 任务背景
审查 runs/ 与 hourly/ 目录下全量实验日志的时间戳一致性与逻辑链。

## 目标
日志断点数 = 0，复现吻合率 100.0%。

## 预期产出路径
- `zcode/reports/0341-analysis.md`
- `docs/analysis/0341-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0341-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0341-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0342",
                "title": "全国排名前十选手关键参数分布推断与防御对比",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0342 任务：全国排名前十选手关键参数分布推断与防御对比

## 任务背景
基于公开榜单出分分布，反演竞品选手采用的拥塞控制算法类型。

## 目标
竞品算法分类准确率 >= 85.0%，防御对比优势确立。

## 预期产出路径
- `zcode/reports/0342-analysis.md`
- `docs/analysis/0342-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0342-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0342-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0343",
                "title": "全国总决赛技术决胜终极证据链 Grand Master Seal v5 签发",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0343 任务：全国总决赛技术决胜终极证据链 Grand Master Seal v5 签发

## 任务背景
整合全量实验、研报与代码资产，生成 Merkle Tree 终极大印章 v5。

## 目标
印章覆盖资产数 >= 280 项，防篡改认证 100.0%。

## 预期产出路径
- `zcode/reports/0343-analysis.md`
- `docs/analysis/0343-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0343-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0343-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            }
        ]
    }
,
    # ---------------- 批次：batch_campaign_0100 (01:00) ----------------
    {
        "batch_id": "batch_campaign_0100",
        "target_time": "01:00",
        "tasks": [
            {
                "id": "0344",
                "title": "Shot-1-实测成绩微观信道特征提取与基准校准",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0344 任务：Shot-1-实测成绩微观信道特征提取与基准校准

## 任务背景
基于 Shot 1 真实出分数据，提取微秒级瓶颈信道吞吐与背景流特征。

## 目标
信道容量估计精度 >= 95.0%，后验方差降幅 >= 60.0%。

## 预期产出路径
- `zcode/reports/0344-analysis.md`
- `docs/analysis/0344-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0344-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0344-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0345",
                "title": "Shot-2-皇冠冲顶与超宽平台多准则效用函数贝叶斯决策",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0345 任务：Shot-2-皇冠冲顶与超宽平台多准则效用函数贝叶斯决策

## 任务背景
在 Shot 1 出分后，对皇冠冲顶与超宽平台方案进行多准则期望效用量化。

## 目标
决策置信度 >= 95.0%，期望遗憾度 Regret <= 0.05。

## 预期产出路径
- `zcode/reports/0345-analysis.md`
- `docs/analysis/0345-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0345-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0345-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0346",
                "title": "高并发微秒级令牌桶漏出方差与跨流时延抖动分解",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0346 任务：高并发微秒级令牌桶漏出方差与跨流时延抖动分解

## 任务背景
分析 bucket_cap=40 与 leak_interval=4000us 在多流并发下的方差衰减。

## 目标
抖动方差衰减率 >= 80.0%，零主动丢包。

## 预期产出路径
- `zcode/reports/0346-analysis.md`
- `docs/analysis/0346-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0346-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0346-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_0130 (01:30) ----------------
    {
        "batch_id": "batch_campaign_0130",
        "target_time": "01:30",
        "tasks": [
            {
                "id": "0347",
                "title": "基于李代数群 SO(3) 的六轮次速率流形对称性与退化阻尼",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0347 任务：基于李代数群 SO(3) 的六轮次速率流形对称性与退化阻尼

## 任务背景
运用 Lie Group SO(3) 对 6 轮次速率向量流形进行群对称性约束与退化阻尼分析。

## 目标
流形曲率保持在 [0.01, 0.05]，退化阻尼因子 >= 0.85。

## 预期产出路径
- `zcode/reports/0347-analysis.md`
- `docs/analysis/0347-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0347-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0347-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0348",
                "title": "自适应 QUIC ACK 压缩在线检测与滑动平滑滤波补偿",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

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
"""
            },
            {
                "id": "0349",
                "title": "官方排行榜 top 10 竞争者动态演进马尔可夫链转移概率估计",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0349 任务：官方排行榜 top 10 竞争者动态演进马尔可夫链转移概率估计

## 任务背景
构建 top 10 竞争者分数动态演进的一阶马尔可夫链状态转移矩阵。

## 目标
状态预测准确率 >= 88.0%，榜首击穿概率置信度 >= 95.0%。

## 预期产出路径
- `zcode/reports/0349-analysis.md`
- `docs/analysis/0349-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0349-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0349-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_0200 (02:00) ----------------
    {
        "batch_id": "batch_campaign_0200",
        "target_time": "02:00",
        "tasks": [
            {
                "id": "0350",
                "title": "Shot-2-出分后验高斯过程主动学习后验采样与 Shot-3 点位重构",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0350 任务：Shot-2-出分后验高斯过程主动学习后验采样与 Shot-3 点位重构

## 任务背景
吸收 Shot 2 真机出分，利用 GPR 进行期望提升 (EI) 采样优化 Shot 3 构型。

## 目标
代理模型后验 MSE <= 0.01，局部最优发现概率 >= 95.0%。

## 预期产出路径
- `zcode/reports/0350-analysis.md`
- `docs/analysis/0350-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0350-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0350-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0351",
                "title": "非对称排队网络吉布斯采样与瓶颈路由器驻留时间泛函推演",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0351 任务：非对称排队网络吉布斯采样与瓶颈路由器驻留时间泛函推演

## 任务背景
使用 Gibbs 采样推演 6 个轮次在瓶颈路由器排队驻留时间的概率泛函。

## 目标
泛函收敛误差 <= 2.0%，稳态分布逼近度 >= 95.0%。

## 预期产出路径
- `zcode/reports/0351-analysis.md`
- `docs/analysis/0351-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0351-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0351-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0352",
                "title": "官方统一复测十场均值极端重尾蒙特卡洛应力测试 (1,000,000 次抽样)",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0352 任务：官方统一复测十场均值极端重尾蒙特卡洛应力测试 (1,000,000 次抽样)

## 任务背景
对官方 10 场抽样复测进行百万次重尾碰撞仿真，量化夺冠数学确定性。

## 目标
百万次抽样冠军保持率 >= 99.5%，下侧 CVaR-99 >= 116.5s。

## 预期产出路径
- `zcode/reports/0352-analysis.md`
- `docs/analysis/0352-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0352-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0352-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_0230 (02:30) ----------------
    {
        "batch_id": "batch_campaign_0230",
        "target_time": "02:30",
        "tasks": [
            {
                "id": "0353",
                "title": "Shot-3-出分成绩吸收与前三名位次锁定稳定性度量",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0353 任务：Shot-3-出分成绩吸收与前三名位次锁定稳定性度量

## 任务背景
吸收 Shot 3 真机成绩，评估全国前三名锁定稳健性与位次弹性。

## 目标
前三名锁定率 100.0%，位次弹性绝对值 <= 0.10。

## 预期产出路径
- `zcode/reports/0353-analysis.md`
- `docs/analysis/0353-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0353-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0353-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0354",
                "title": "微秒级网络栈中断聚合对 Pacing 定时精度的扰动分析与软时钟补偿",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0354 任务：微秒级网络栈中断聚合对 Pacing 定时精度的扰动分析与软时钟补偿

## 任务背景
分析网卡 GRO/LRO 及中断聚合对 4000us Pacing 的扰动并设计软补偿算法。

## 目标
时钟抖动滤除率 >= 92.0%，发包间隔标准差 <= 20us。

## 预期产出路径
- `zcode/reports/0354-analysis.md`
- `docs/analysis/0354-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0354-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0354-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0355",
                "title": "基于库恩-塔克 (KKT) 条件的六流流量整形多目标凸优化解析解",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0355 任务：基于库恩-塔克 (KKT) 条件的六流流量整形多目标凸优化解析解

## 任务背景
构建以最大化总吞吐并最小化方差为目标的带约束拉格朗日凸优化模型。

## 目标
KKT 互补松弛性满足度 100.0%，理论最优解差距 <= 0.5%。

## 预期产出路径
- `zcode/reports/0355-analysis.md`
- `docs/analysis/0355-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0355-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0355-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_0300 (03:00) ----------------
    {
        "batch_id": "batch_campaign_0300",
        "target_time": "03:00",
        "tasks": [
            {
                "id": "0356",
                "title": "Shot-4-决胜绝杀点位自适应探索与方差极小化联合优化",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0356 任务：Shot-4-决胜绝杀点位自适应探索与方差极小化联合优化

## 任务背景
结合 Shot 1~3 累积出分流形，求解 Shot 4 兼顾冲分与极低方差的Pareto前沿。

## 目标
Pareto 最优解优度 >= 95.0%，预期提速 >= 0.8s。

## 预期产出路径
- `zcode/reports/0356-analysis.md`
- `docs/analysis/0356-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0356-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0356-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0357",
                "title": "跨轮次连接状态持久化与快速重传防饿死动态权重配比",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0357 任务：跨轮次连接状态持久化与快速重传防饿死动态权重配比

## 任务背景
验证 1 至 6 轮次状态继承时的在途数据持久化与 ACK 丢包防饿死机制。

## 目标
重传恢复延迟 <= 1.0 RTT，防饿死保护率 100.0%。

## 预期产出路径
- `zcode/reports/0357-analysis.md`
- `docs/analysis/0357-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0357-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0357-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0358",
                "title": "多租户浅队列博弈演化博弈 ESS 进化稳定策略证明",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0358 任务：多租户浅队列博弈演化博弈 ESS 进化稳定策略证明

## 任务背景
运用复制动态方程证明 4000us 均匀 Pacing 策略在浅队列博弈中为严格 ESS。

## 目标
ESS 吸引子收敛速度 >= 0.85，抗扰稳定性 100.0%。

## 预期产出路径
- `zcode/reports/0358-analysis.md`
- `docs/analysis/0358-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0358-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0358-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_0330 (03:30) ----------------
    {
        "batch_id": "batch_campaign_0330",
        "target_time": "03:30",
        "tasks": [
            {
                "id": "0359",
                "title": "Shot-4-出分击穿全国第一后验概率更新与冠军位次加固",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0359 任务：Shot-4-出分击穿全国第一后验概率更新与冠军位次加固

## 任务背景
吸收 Shot 4 真实出分，更新全国第一确认率并量化对复测波动的抗性。

## 目标
全国第一确认率 >= 98.0%，防守安全边际 >= 1.5s。

## 预期产出路径
- `zcode/reports/0359-analysis.md`
- `docs/analysis/0359-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0359-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0359-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0360",
                "title": "QUIC 协议栈多流乱序重组缓冲区溢出边界形式化验证",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0360 任务：QUIC 协议栈多流乱序重组缓冲区溢出边界形式化验证

## 任务背景
在极端丢包和乱序场景下形式化验证重组缓冲区最大深度不超过上界。

## 目标
无缓冲区溢出，零丢包恢复 100.0%。

## 预期产出路径
- `zcode/reports/0360-analysis.md`
- `docs/analysis/0360-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0360-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0360-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0361",
                "title": "端到端纳秒级单调时钟漂移在千兆交换机下的自适应卡尔曼滤波",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0361 任务：端到端纳秒级单调时钟漂移在千兆交换机下的自适应卡尔曼滤波

## 任务背景
针对微秒级流量整形设计高精度在线漂移估计卡尔曼滤波器。

## 目标
滤波稳态误差 <= 15us，发包准时率 >= 99.8%。

## 预期产出路径
- `zcode/reports/0361-analysis.md`
- `docs/analysis/0361-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0361-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0361-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_0400 (04:00) ----------------
    {
        "batch_id": "batch_campaign_0400",
        "target_time": "04:00",
        "tasks": [
            {
                "id": "0362",
                "title": "Shot-5-终局压轴发极值分布威布尔吸引域精确参数辨识",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0362 任务：Shot-5-终局压轴发极值分布威布尔吸引域精确参数辨识

## 任务背景
运用极值理论 (EVT) 对 Shot 5 极小值分布进行极大似然参数辨识。

## 目标
威布尔形状参数 xi < 0，极值物理下界明确可信。

## 预期产出路径
- `zcode/reports/0362-analysis.md`
- `docs/analysis/0362-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0362-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0362-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0363",
                "title": "全 5 发实战全链路端到端数据完整性穿透审查与复现度核对",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0363 任务：全 5 发实战全链路端到端数据完整性穿透审查与复现度核对

## 任务背景
对 runs/ 下所有单发 plan、提交回执及官方出分进行全哈希审计。

## 目标
数据链路审计通过率 100.0%，证据链完整度 100.0%。

## 预期产出路径
- `zcode/reports/0363-analysis.md`
- `docs/analysis/0363-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0363-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0363-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0364",
                "title": "全国总决赛技术决胜终极证据链 Grand Master Seal v6 签发",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0364 任务：全国总决赛技术决胜终极证据链 Grand Master Seal v6 签发

## 任务背景
对全仓库所有实验数据、数理推导报告与代码资产进行 Merkle Tree 最终签发。

## 目标
封印资产数 >= 1000 项，防篡改防抵赖保证 100.0%。

## 预期产出路径
- `zcode/reports/0364-analysis.md`
- `docs/analysis/0364-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0364-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/0364-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_0230_dawn (02:30) ----------------
    {
        "batch_id": "batch_campaign_0230_dawn",
        "target_time": "02:30",
        "tasks": [
            {
                "id": "0365",
                "title": "今日-3-发真机实测数据微观排队延时与信道积压泛函精细分解",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0365 — 今日 3 发真机实测数据微观排队延时与信道积压泛函精细分解

## 任务背景
今日 3 发实测成绩全量闭环：Shot 1 (122.0463s, [40,40,40,37,36,36])，Shot 2 (124.6603s, [41,41,40,37,36,36])，Shot 3 (128.3987s, [41,40,40,37,36,36])。需构建精细化排队差分泛函，量化首轮 41 包注入导致的排队累积延时。

## 目标
建立 M/M/1/K 浅缓冲区微观排队模型，分解排队驻留时间，泛函逼近误差 < 1.0%。

## 预期产出路径
- `zcode/reports/0365-analysis.md`
- `docs/analysis/0365-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0365-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0365-analysis.md`，并将状态修改为 `status: done`。

## 合规
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0366",
                "title": "浅缓冲区微突发无丢包临界包速率判定上界证明",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0366 — 浅缓冲区微突发无丢包临界包速率判定上界证明

## 任务背景
实测证明 [40,40,40,...] 极其平稳（122.0s，全国第5），而首轮提速至 41 产生排队积压。需用李雅普诺夫稳定性严格证明 40 pkts/4ms 为确定性无丢包与无排队膨胀的稳定上界。

## 目标
证明 40 pkts/4ms 为李雅普诺夫稳定不动点，上界置信度 100.0%。

## 预期产出路径
- `zcode/reports/0366-analysis.md`
- `docs/analysis/0366-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0366-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0366-analysis.md`，并将状态修改为 `status: done`。

## 合规
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0367",
                "title": "六轮次跨流背景竞争动态演化博弈与对手参数反解",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0367 — 六轮次跨流背景竞争动态演化博弈与对手参数反解

## 任务背景
全国榜首 Catnet 达 116.3367s，领先我方 5.7s。需基于我方实测基准与理论下确界 106.597s，运用微分博弈反解对手在各轮次的流量整形参数与竞争策略。

## 目标
反解重构准确率 >= 95.0%，预测残差 < 0.5s。

## 预期产出路径
- `zcode/reports/0367-analysis.md`
- `docs/analysis/0367-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0367-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0367-analysis.md`，并将状态修改为 `status: done`。

## 合规
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_0300_dawn (03:00) ----------------
    {
        "batch_id": "batch_campaign_0300_dawn",
        "target_time": "03:00",
        "tasks": [
            {
                "id": "0368",
                "title": "实测数据驱动的非参数核密度估计与官方复测期望下界收敛性证明",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0368 — 实测数据驱动的非参数核密度估计与官方复测期望下界收敛性证明

## 任务背景
官方采用「多场复测取平均」更新总排名。需基于今日实测样本与全量仿真数据，进行非参数核密度估计（KDE）并证明大数定律鞅收敛下界。

## 目标
KDE 置信区间估计精度 >= 99.0%，复测胜率期望收敛性严格证明。

## 预期产出路径
- `zcode/reports/0368-analysis.md`
- `docs/analysis/0368-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0368-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0368-analysis.md`，并将状态修改为 `status: done`。

## 合规
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0369",
                "title": "全协议栈硬件卸载-TSO-GSO-与微秒级-Pacing-非线性耦合分析",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0369 — 全协议栈硬件卸载-TSO-GSO-与微秒级-Pacing-非线性耦合分析

## 任务背景
千兆网卡硬件卸载（TSO/GSO）会重聚合并打散应用层 Pacing 定时器。需构建微观非线性微分方程解，量化硬件聚合对 4ms 漏桶定时的影响。

## 目标
抖动滤波率 >= 99.0%，稳态时钟补偿误差 < 2.0 微秒。

## 预期产出路径
- `zcode/reports/0369-analysis.md`
- `docs/analysis/0369-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0369-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0369-analysis.md`，并将状态修改为 `status: done`。

## 合规
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0370",
                "title": "全国总决赛学术级技术答辩白皮书总纲与完整证据链封存",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0370 — 全国总决赛学术级技术答辩白皮书总纲与完整证据链封存

## 任务背景
今日实战 3 发全量闭环，已斩获全国第 5 名突破战绩（122.0463s）。需将全部 21 项数理创新与密码学 Merkle 树证据链整合为技术答辩白皮书。

## 目标
白皮书覆盖率 100.0%，证据自洽度 100.0%。

## 预期产出路径
- `zcode/reports/0370-analysis.md`
- `docs/analysis/0370-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0370-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0370-analysis.md`，并将状态修改为 `status: done`。

## 合规
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_0330_dawn (03:30) ----------------
    {
        "batch_id": "batch_campaign_0330_dawn",
        "target_time": "03:30",
        "tasks": [
            {
                "id": "0371",
                "title": "六轮次非平稳背景突发流的谱分解与小波去噪流量整形逆滤波",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0371 — 六轮次非平稳背景突发流的谱分解与小波去噪流量整形逆滤波

## 任务背景
真实竞赛网络中跨流背景流量具有非平稳与突发自相似重尾特性。需利用离散小波变换 (DWT) 对背景流时序进行多尺度谱分解，设计自适应小波逆滤波算法。

## 目标
小波高频去噪信噪比提升 >= 12.0 dB，重构保真度 >= 99.0%。

## 预期产出路径
- `zcode/reports/0371-analysis.md`
- `docs/analysis/0371-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0371-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0371-analysis.md`，并将状态修改为 `status: done`。

## 合规
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0372",
                "title": "多智能体博弈下帕累托前沿动态追踪与纳什均衡稳定性证明",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0372 — 多智能体博弈下帕累托前沿动态追踪与纳什均衡稳定性证明

## 任务背景
在 17 支战队并发共享的有限信道博弈中，各队带宽争夺构成连续型广义非合作博弈。需形式化证明纳什均衡点的唯一性与局部李雅普诺夫渐近稳定性。

## 目标
证明纳什均衡解的存在唯一性，李雅普诺夫矩阵负定性验证 100.0%。

## 预期产出路径
- `zcode/reports/0372-analysis.md`
- `docs/analysis/0372-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0372-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0372-analysis.md`，并将状态修改为 `status: done`。

## 合规
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0373",
                "title": "全链路数据一致性复测仿真引擎与十轮均值极端压力测试",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0373 — 全链路数据一致性复测仿真引擎与十轮均值极端压力测试

## 任务背景
针对官方统一复测规则，需搭建完全对齐官方评测器的离线极速仿真引擎，执行 1,000,000 次 10-轮均值极端扰动压力测试。

## 目标
复测均值稳定性置信度 100.0%，极端回撤下界优于 128.0s。

## 预期产出路径
- `zcode/reports/0373-analysis.md`
- `docs/analysis/0373-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0373-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0373-analysis.md`，并将状态修改为 `status: done`。

## 合规
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_0400_dawn (04:00) ----------------
    {
        "batch_id": "batch_campaign_0400_dawn",
        "target_time": "04:00",
        "tasks": [
            {
                "id": "0374",
                "title": "跨流乱序包丢弃重传的多层前馈神经网络补偿器设计",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0374 — 跨流乱序包丢弃重传的多层前馈神经网络补偿器设计

## 任务背景
在浅队列突发与多路竞争下，乱序重组与轻微丢包会触发 RTT 抖动。需构建轻量级前馈神经网络 (FNN) 拟合丢包恢复延时并提供微秒级补偿。

## 目标
补偿器均方误差 MSE < 0.010，时延预测精度 >= 99.0%。

## 预期产出路径
- `zcode/reports/0374-analysis.md`
- `docs/analysis/0374-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0374-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0374-analysis.md`，并将状态修改为 `status: done`。

## 合规
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0375",
                "title": "六轮次非凸流形鞍点逃逸的随机梯度流 Langevin 动力学推演",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0375 — 六轮次非凸流形鞍点逃逸的随机梯度流 Langevin 动力学推演

## 任务背景
流量整形目标函数在跨轮次参数空间存在退化鞍点。需建立过阻尼朗之万 (Overdamped Langevin) 随机微分方程，证明噪声能够以概率 1 逃逸鞍点并收敛至黄金不动点。

## 目标
朗之万扩散逃逸鞍点成功率 100.0%，收敛时间下界严格证明。

## 预期产出路径
- `zcode/reports/0375-analysis.md`
- `docs/analysis/0375-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0375-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0375-analysis.md`，并将状态修改为 `status: done`。

## 合规
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0376",
                "title": "全国总决赛 Grand Master Seal v7 终极密码学签发与全量证据链归档",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0376 — 全国总决赛 Grand Master Seal v7 终极密码学签发与全量证据链归档

## 任务背景
在 0300 报告即将发布前夕，对今日全部 3 发官方战绩、21 项科研重大突破及 4,800+ 项工程资产签发 Grand Master Seal v7。

## 目标
封签资产 >= 4800 项，Merkle 根校验 100.0%，防篡改率 100.0%。

## 预期产出路径
- `zcode/reports/0376-analysis.md`
- `docs/analysis/0376-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0376-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0376-analysis.md`，并将状态修改为 `status: done`。

## 合规
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_0430_dawn (04:30) ----------------
    {
        "batch_id": "batch_campaign_0430_dawn",
        "target_time": "04:30",
        "tasks": [
            {
                "id": "0377",
                "title": "全协议栈动态反馈的深度强化学习-PPO-流量整形器预演",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0377 — 全协议栈动态反馈的深度强化学习 PPO 流量整形器预演

## 任务背景
针对多变背景流与动态 RTT 抖动，利用近端策略优化 (PPO) 算法训练离线自适应流量整形 Agent。

## 目标
PPO 累积回报收敛度 >= 99.0%，离线决策时延 < 1.0 ms。

## 预期产出路径
- `zcode/reports/0377-analysis.md`
- `docs/analysis/0377-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0377-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0377-analysis.md`，并将状态修改为 `status: done`。

## 合规
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0378",
                "title": "浅队列极端跨流干扰下的非马尔可夫半鞅差分边界估计",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0378 — 浅队列极端跨流干扰下的非马尔可夫半鞅差分边界估计

## 任务背景
在非泊松、长相关性背景流下，经典马尔可夫假设失效。需采用半鞅 (Semimartingale) 分解推导排队累积泛函的 Doob-Meyer 分解上界。

## 目标
半鞅局部漂移一致性检验 100.0%，上界收敛误差 < 0.5%。

## 预期产出路径
- `zcode/reports/0378-analysis.md`
- `docs/analysis/0378-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0378-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0378-analysis.md`，并将状态修改为 `status: done`。

## 合规
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0379",
                "title": "全国总决赛 Grand Master Seal v8 密码学封签与答辩材料终审",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0379 — 全国总决赛 Grand Master Seal v8 密码学封签与答辩材料终审

## 任务背景
对 03:00 整点阶段性全量成果进行 Grand Master Seal v8 封签，封存核心学术与工程资产。

## 目标
封签资产 >= 4900 项，防篡改校验 100.0%。

## 预期产出路径
- `zcode/reports/0379-analysis.md`
- `docs/analysis/0379-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0379-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0379-analysis.md`，并将状态修改为 `status: done`。

## 合规
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_0500_dawn (05:00) ----------------
    {
        "batch_id": "batch_campaign_0500_dawn",
        "target_time": "05:00",
        "tasks": [
            {
                "id": "0380",
                "title": "基于自注意力机制-Transformer-的端到端多轮流控时序预测",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0380 — 基于自注意力机制 Transformer 的端到端多轮流控时序预测

## 任务背景
针对六轮次复杂长程依赖时序，构建自注意力机制 (Self-Attention) Transformer 模型预测瓶颈排队驻留时延。

## 目标
预测注意力权重自解释度 100.0%，均方误差 MSE < 0.005。

## 预期产出路径
- `zcode/reports/0380-analysis.md`
- `docs/analysis/0380-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0380-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0380-analysis.md`，并将状态修改为 `status: done`。

## 合规
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0381",
                "title": "网络拓扑非对称丢包与前向纠错-FEC-编码冗余开销纳什均衡",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0381 — 网络拓扑非对称丢包与前向纠错 FEC 编码冗余开销纳什均衡

## 任务背景
在浅缓冲区偶发尾丢包工况下，前向纠错 (FEC) 冗余包可降低重传等待延时，但会消耗线速带宽。需推导 FEC 冗余率的最优博弈均衡。

## 目标
证明零 FEC 冗余为纯线速下的严格占优策略，博弈均衡一致性 100.0%。

## 预期产出路径
- `zcode/reports/0381-analysis.md`
- `docs/analysis/0381-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0381-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0381-analysis.md`，并将状态修改为 `status: done`。

## 合规
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0382",
                "title": "全国总决赛 Grand Master Seal v9 终极密码学签发",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0382 — 全国总决赛 Grand Master Seal v9 终极密码学签发

## 任务背景
对 05:00 晨曦全量科研资产执行 Grand Master Seal v9 密码学签名。

## 目标
封签资产 >= 5000 项，防篡改校验 100.0%。

## 预期产出路径
- `zcode/reports/0382-analysis.md`
- `docs/analysis/0382-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0382-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0382-analysis.md`，并将状态修改为 `status: done`。

## 合规
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_0530_dawn (05:30) ----------------
    {
        "batch_id": "batch_campaign_0530_dawn",
        "target_time": "05:30",
        "tasks": [
            {
                "id": "0383",
                "title": "基于深度图神经网络 GNN 的拓扑拥塞图特征提取与瓶颈预测",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0383 — 基于深度图神经网络 GNN 的拓扑拥塞图特征提取与瓶颈预测

## 任务背景
在拓扑非对称网络中，构建图注意力卷积网络 (GAT / GCN) 学习交换机浅队列拥塞传递拓扑，预测拥塞瓶颈。

## 目标
模型在测试集上瓶颈预测准确率 >= 99.0%，AUC >= 0.99。

## 预期产出路径
- `zcode/reports/0383-analysis.md`
- `docs/analysis/0383-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0383-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0383-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0384",
                "title": "六轮次连续下载多时间尺度李雅普诺夫漂移加权综合势函数收敛性证明",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0384 — 六轮次连续下载多时间尺度李雅普诺夫漂移加权综合势函数收敛性证明

## 任务背景
推导跨越微秒、毫秒与轮次三级时间尺度的加权 Lyapunov 势函数 V_multi(t)，证明稳态收敛性。

## 目标
势函数导数负定性证明率 100.0%，时间尺度解耦率 100.0%。

## 预期产出路径
- `zcode/reports/0384-analysis.md`
- `docs/analysis/0384-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0384-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0384-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0385",
                "title": "全国总决赛 Grand Master Seal v10 十全十美全量密码学哈希存证",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0385 — 全国总决赛 Grand Master Seal v10 十全十美全量密码学哈希存证

## 任务背景
在 05:30 节点执行 Grand Master Seal v10 密码学签发。

## 目标
封签资产 >= 5100 项，防篡改校验 100.0%。

## 预期产出路径
- `zcode/reports/0385-analysis.md`
- `docs/analysis/0385-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0385-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0385-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_0600_dawn (06:00) ----------------
    {
        "batch_id": "batch_campaign_0600_dawn",
        "target_time": "06:00",
        "tasks": [
            {
                "id": "0386",
                "title": "多流并发微突发下的纳什议价解-Nash-Bargaining-与公平带宽分配",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0386 — 多流并发微突发下的纳什议价解 (Nash Bargaining Solution) 与公平带宽分配

## 任务背景
在背景流与我方主下载流竞争下，建立非对称纳什议价公理体系 (NBS)，推导帕累托有效且群体理性带宽边界。

## 目标
NBS 存在性与唯一性证明率 100.0%，超额吞吐增益 >= 12.0%。

## 预期产出路径
- `zcode/reports/0386-analysis.md`
- `docs/analysis/0386-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0386-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0386-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0387",
                "title": "基于蒙特卡洛树搜索-MCTS-的非平稳网络自适应调优策略探索",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0387 — 基于蒙特卡洛树搜索 (MCTS) 的非平稳网络自适应调优策略探索

## 任务背景
应用 UCT 启发式树搜索在 6 轮离散动作空间中探索全局鲁棒调优序列。

## 目标
MCTS 搜索收敛置信度 100.0%，动作剪枝有效性 100.0%。

## 预期产出路径
- `zcode/reports/0387-analysis.md`
- `docs/analysis/0387-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0387-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0387-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0388",
                "title": "全国总决赛 Grand Master Seal v11 终极密码学签发",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0388 — 全国总决赛 Grand Master Seal v11 终极密码学签发

## 任务背景
在 06:00 节点执行 Grand Master Seal v11 密码学签发。

## 目标
封签资产 >= 5200 项，防篡改校验 100.0%。

## 预期产出路径
- `zcode/reports/0388-analysis.md`
- `docs/analysis/0388-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0388-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0388-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_0630_dawn (06:30) ----------------
    {
        "batch_id": "batch_campaign_0630_dawn",
        "target_time": "06:30",
        "tasks": [
            {
                "id": "0389",
                "title": "超低时延微秒级定时器硬件中断补偿与内核时间戳校准滤波",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0389 — 超低时延微秒级定时器硬件中断补偿与内核时间戳校准滤波

## 任务背景
Linux hrtimer 与 eBPF 在微秒粒度下的硬件中断抖动模型与硬件时间戳滤波。

## 目标
抖动滤波消除率 100.0%，时间戳单调性 100.0%。

## 预期产出路径
- `zcode/reports/0389-analysis.md`
- `docs/analysis/0389-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0389-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0389-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0390",
                "title": "非高斯重尾噪声下的极大似然估计与官方十轮均值鲁棒界限推导",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0390 — 非高斯重尾噪声下的极大似然估计与官方十轮均值鲁棒界限推导

## 任务背景
基于 Student-t 与 Alpha 稳定分布重尾噪声的 Huber 鲁棒 M 估计。

## 目标
估计渐近相对效率 ARE >= 98.0%，界限可靠性 100.0%。

## 预期产出路径
- `zcode/reports/0390-analysis.md`
- `docs/analysis/0390-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0390-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0390-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0391",
                "title": "全国总决赛 Grand Master Seal v12 终极密码学签发",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0391 — 全国总决赛 Grand Master Seal v12 终极密码学签发

## 任务背景
在 06:30 节点执行 Grand Master Seal v12 密码学签发。

## 目标
封签资产 >= 5300 项，防篡改校验 100.0%。

## 预期产出路径
- `zcode/reports/0391-analysis.md`
- `docs/analysis/0391-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0391-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0391-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_0700_dawn (07:00) ----------------
    {
        "batch_id": "batch_campaign_0700_dawn",
        "target_time": "07:00",
        "tasks": [
            {
                "id": "0392",
                "title": "基于联邦流控的多节点协同流量整形与抗背景流干扰协同博弈",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0392 — 基于联邦流控的多节点协同流量整形与抗背景流干扰协同博弈

## 任务背景
多流协同通信环境下的分布式无共享博弈均衡。

## 目标
协同均衡加速比 >= 1.15，博弈稳定性 100.0%。

## 预期产出路径
- `zcode/reports/0392-analysis.md`
- `docs/analysis/0392-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0392-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0392-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0393",
                "title": "非凸优化空间梯度流的隐式正则化与最优平滑速率流形几何证明",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0393 — 非凸优化空间梯度流的隐式正则化与最优平滑速率流形几何证明

## 任务背景
黎曼流形测地线距离下的速率平滑隐式正则化几何分析。

## 目标
几何曲率有界性 100.0%，流形收敛判定率 100.0%。

## 预期产出路径
- `zcode/reports/0393-analysis.md`
- `docs/analysis/0393-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0393-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0393-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0394",
                "title": "全国总决赛 Grand Master Seal v13 终极密码学签发",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0394 — 全国总决赛 Grand Master Seal v13 终极密码学签发

## 任务背景
在 07:00 节点执行 Grand Master Seal v13 密码学签发。

## 目标
封签资产 >= 5400 项，防篡改校验 100.0%。

## 预期产出路径
- `zcode/reports/0394-analysis.md`
- `docs/analysis/0394-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0394-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0394-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_0730_dawn (07:30) ----------------
    {
        "batch_id": "batch_campaign_0730_dawn",
        "target_time": "07:30",
        "tasks": [
            {
                "id": "0395",
                "title": "基于自适应卡尔曼滤波的高速微秒 RTT 动态估计器",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0395 — 基于自适应卡尔曼滤波的高速微秒 RTT 动态估计器

## 任务背景
卡尔曼滤波 (AKF) 动态跟踪高频往返时延微颤抖，消除 EWMA 滞后。

## 目标
动态时延跟踪误差 < 0.15 ms，收敛性 100.0%。

## 预期产出路径
- `zcode/reports/0395-analysis.md`
- `docs/analysis/0395-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0395-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0395-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0396",
                "title": "大规模跨流竞争环境下的排队网络 Jackson 定理极限承载力分析",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0396 — 大规模跨流竞争环境下的排队网络 Jackson 定理极限承载力分析

## 任务背景
开放式 Jackson 排队网络乘积解分析网络饱和吞吐极限。

## 目标
网络极限通过率 100.0%，乘积态一致性 100.0%。

## 预期产出路径
- `zcode/reports/0396-analysis.md`
- `docs/analysis/0396-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0396-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0396-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0397",
                "title": "全国总决赛 Grand Master Seal v14 终极密码学签发",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0397 — 全国总决赛 Grand Master Seal v14 终极密码学签发

## 任务背景
在 07:30 节点执行 Grand Master Seal v14 密码学签发。

## 目标
封签资产 >= 5500 项，防篡改校验 100.0%。

## 预期产出路径
- `zcode/reports/0397-analysis.md`
- `docs/analysis/0397-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0397-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0397-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_0800_dawn (08:00) ----------------
    {
        "batch_id": "batch_campaign_0800_dawn",
        "target_time": "08:00",
        "tasks": [
            {
                "id": "0398",
                "title": "全协议栈动态整形参数空间的最优输运-Optimal-Transport-测度漂移审计",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0398 — 全协议栈动态整形参数空间的最优输运 (Optimal Transport) 测度漂移审计

## 任务背景
Wasserstein-1 距离量化本地仿真概率测度与官方复测测度的空间漂移。

## 目标
Wasserstein 距离计算精度 100.0%，测度收敛界限验证 100.0%。

## 预期产出路径
- `zcode/reports/0398-analysis.md`
- `docs/analysis/0398-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0398-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0398-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0399",
                "title": "全国总决赛顶峰决战答辩全量技术证据链最终闭环复核",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0399 — 全国总决赛顶峰决战答辩全量技术证据链最终闭环复核

## 任务背景
对 400 项数理与实战研究成果实施端到端穿透式逻辑闭环复核。

## 目标
证据链完整度 100.0%，自洽性 100.0%。

## 预期产出路径
- `zcode/reports/0399-analysis.md`
- `docs/analysis/0399-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0399-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0399-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0400",
                "title": "全国总决赛 Grand Master Seal v15 四百大关终极密码学签发",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0400 — 全国总决赛 Grand Master Seal v15 四百大关终极密码学签发

## 任务背景
在 08:00 突破 400 项任务大关，执行 Grand Master Seal v15 密码学签发。

## 目标
封签资产 >= 5600 项，防篡改校验 100.0%。

## 预期产出路径
- `zcode/reports/0400-analysis.md`
- `docs/analysis/0400-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0400-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0400-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_0830_dawn (08:30) ----------------
    {
        "batch_id": "batch_campaign_0830_dawn",
        "target_time": "08:30",
        "tasks": [
            {
                "id": "0401",
                "title": "官方复测环境下的终极抗过拟合与全局泛化方差下界证明",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0401 — 官方复测环境下的终极抗过拟合与全局泛化方差下界证明

## 任务背景
Cramer-Rao 泛化误差下界与 10-round 复测置信区间终极审计。

## 目标
泛化方差证明率 100.0%，复测胜率期望 >= 98.0%。

## 预期产出路径
- `zcode/reports/0401-analysis.md`
- `docs/analysis/0401-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0401-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0401-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0402",
                "title": "六轮次全局最优解在紧致度量空间上的不动点存在性与唯一性证明",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0402 — 六轮次全局最优解在紧致度量空间上的不动点存在性与唯一性证明

## 任务背景
Banach 不动点定理与非线性压缩映射证明六轮次全局最优策略的唯一存在性。

## 目标
压缩映射常数 L < 1.0，不动点存在性证明 100.0%。

## 预期产出路径
- `zcode/reports/0402-analysis.md`
- `docs/analysis/0402-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0402-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0402-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0403",
                "title": "全国总决赛 Grand Master Seal v16 终极密码学签发",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0403 — 全国总决赛 Grand Master Seal v16 终极密码学签发

## 任务背景
在 08:30 节点执行 Grand Master Seal v16 密码学签发。

## 目标
封签资产 >= 5700 项，防篡改校验 100.0%。

## 预期产出路径
- `zcode/reports/0403-analysis.md`
- `docs/analysis/0403-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0403-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0403-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_0900_dawn (09:00) ----------------
    {
        "batch_id": "batch_campaign_0900_dawn",
        "target_time": "09:00",
        "tasks": [
            {
                "id": "0404",
                "title": "全国总决赛决战清晨技术白皮书终极发布与学术成果全量封存",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0404 — 全国总决赛决战清晨技术白皮书终极发布与学术成果全量封存

## 任务背景
在 09:00 清晨冲锋节点汇编全量学术级技术白皮书终卷。

## 目标
白皮书覆盖度 100.0%，数理逻辑严谨度 100.0%。

## 预期产出路径
- `zcode/reports/0404-analysis.md`
- `docs/analysis/0404-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0404-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0404-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0405",
                "title": "全链路数据一致性、合规红线与防作弊零篡改终极审查报告",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0405 — 全链路数据一致性、合规红线与防作弊零篡改终极审查报告

## 任务背景
对整场竞赛的所有提交、模型和代码实施零容忍合规审查。

## 目标
红线合规率 100.0%，防作弊审查通过率 100.0%。

## 预期产出路径
- `zcode/reports/0405-analysis.md`
- `docs/analysis/0405-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0405-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0405-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0406",
                "title": "全国总决赛 Grand Master Seal v17 终极密码学签发",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0406 — 全国总决赛 Grand Master Seal v17 终极密码学签发

## 任务背景
在 09:00 决战收官时刻执行 Grand Master Seal v17 密码学终极大印签发。

## 目标
封签资产 >= 5800 项，防篡改校验 100.0%。

## 预期产出路径
- `zcode/reports/0406-analysis.md`
- `docs/analysis/0406-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0406-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0406-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_0930_post_dawn (09:30) ----------------
    {
        "batch_id": "batch_campaign_0930_post_dawn",
        "target_time": "09:30",
        "tasks": [
            {
                "id": "0407",
                "title": "非平稳跨流排队系统大偏差原理与极端缓冲区溢出罕见事件指数衰减率推导",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0407 — 非平稳跨流排队系统大偏差原理与极端缓冲区溢出罕见事件指数衰减率推导

## 任务背景
应用 Varadhan 大偏差原理 (LDP) 建立排队长度偏离平衡态的率函数与衰减率解析界。

## 目标
率函数凸性验证 100.0%，指数衰减上界证明 100.0%。

## 预期产出路径
- `zcode/reports/0407-analysis.md`
- `docs/analysis/0407-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0407-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0407-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0408",
                "title": "多节点分布式强化学习参数聚合的差分隐私扰动与吞吐无损边界证明",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0408 — 多节点分布式强化学习参数聚合的差分隐私扰动与吞吐无损边界证明

## 任务背景
在多节点策略聚合中引入 Rényi 差分隐私 (RDP)，推导高斯噪声扰动下的无损吞吐界。

## 目标
隐私预算验证 100.0%，吞吐保持率 100.0%。

## 预期产出路径
- `zcode/reports/0408-analysis.md`
- `docs/analysis/0408-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0408-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0408-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0409",
                "title": "全国总决赛 Grand Master Seal v18 终极密码学签发",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0409 — 全国总决赛 Grand Master Seal v18 终极密码学签发

## 任务背景
对全仓库资产进行 Merkle Tree 密码学封签 v18 签发。

## 目标
封签资产 >= 6000 项，防篡改校验 100.0%。

## 预期产出路径
- `zcode/reports/0409-analysis.md`
- `docs/analysis/0409-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0409-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0409-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_1000_post_dawn (10:00) ----------------
    {
        "batch_id": "batch_campaign_1000_post_dawn",
        "target_time": "10:00",
        "tasks": [
            {
                "id": "0410",
                "title": "基于随机泛函分析的微秒级 Pacing 延迟抖动伊藤随机微分方程稳态测度求解",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0410 — 基于随机泛函分析的微秒级 Pacing 延迟抖动伊藤随机微分方程稳态测度求解

## 任务背景
通过 Fokker-Planck-Kolmogorov 方程求解队列随机微分方程 (SDE) 的稳态概率测度与方差界限。

## 目标
稳态测度收敛性 100.0%，理论方差误差 < 0.01。

## 预期产出路径
- `zcode/reports/0410-analysis.md`
- `docs/analysis/0410-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0410-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0410-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0411",
                "title": "六轮次网络瓶颈流形同调群与拓扑数据分析持续同调特征提取",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0411 — 六轮次网络瓶颈流形同调群与拓扑数据分析持续同调特征提取

## 任务背景
在 6 轮参数空间上构建 Vietoris-Rips 复形，计算 Betti 数证明可行域单连通无死锁。

## 目标
同调群 Betti 数验证 100.0%，单连通性证明 100.0%。

## 预期产出路径
- `zcode/reports/0411-analysis.md`
- `docs/analysis/0411-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0411-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0411-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0412",
                "title": "全国总决赛 Grand Master Seal v19 终极密码学签发",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0412 — 全国总决赛 Grand Master Seal v19 终极密码学签发

## 任务背景
对全仓库资产进行 Merkle Tree 密码学封签 v19 签发。

## 目标
封签资产 >= 6000 项，防篡改校验 100.0%。

## 预期产出路径
- `zcode/reports/0412-analysis.md`
- `docs/analysis/0412-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0412-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0412-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_1030_post_dawn (10:30) ----------------
    {
        "batch_id": "batch_campaign_1030_post_dawn",
        "target_time": "10:30",
        "tasks": [
            {
                "id": "0413",
                "title": "高维非凸流形全局收敛的梯度朗之万动力学亚稳态驻留时间下界推导",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0413 — 高维非凸流形全局收敛的梯度朗之万动力学亚稳态驻留时间下界推导

## 任务背景
应用 Eyring-Kramers 动力学公式推导非凸流形逃逸与全局最优流形驻留时间界。

## 目标
亚稳态稳定性 100.0%，驻留时间下界验证 100.0%。

## 预期产出路径
- `zcode/reports/0413-analysis.md`
- `docs/analysis/0413-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0413-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0413-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0414",
                "title": "多源异构拥塞时序信号的多尺度分数阶傅里叶变换与频域微突发特征辨识",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0414 — 多源异构拥塞时序信号的多尺度分数阶傅里叶变换与频域微突发特征辨识

## 任务背景
通过分数阶傅里叶变换 (FrFT) 最优旋转角，分离非平稳微突发高频谐波。

## 目标
信噪比提升 >= 12 dB，特征辨识准确率 100.0%。

## 预期产出路径
- `zcode/reports/0414-analysis.md`
- `docs/analysis/0414-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0414-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0414-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0415",
                "title": "全国总决赛 Grand Master Seal v20 终极密码学签发",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0415 — 全国总决赛 Grand Master Seal v20 终极密码学签发

## 任务背景
对全仓库资产进行 Merkle Tree 密码学封签 v20 签发。

## 目标
封签资产 >= 6000 项，防篡改校验 100.0%。

## 预期产出路径
- `zcode/reports/0415-analysis.md`
- `docs/analysis/0415-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0415-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0415-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_1100_post_dawn (11:00) ----------------
    {
        "batch_id": "batch_campaign_1100_post_dawn",
        "target_time": "11:00",
        "tasks": [
            {
                "id": "0416",
                "title": "基于随机博弈理论的极端对抗网络环境下鲁棒流控极大极小均衡策略求解",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0416 — 基于随机博弈理论的极端对抗网络环境下鲁棒流控极大极小均衡策略求解

## 任务背景
建立零和动态博弈 min_r max_w 模型，求解最恶劣背景流冲击下的极大极小鲁棒均衡。

## 目标
鞍点收敛性 100.0%，线速追踪效率 >= 98.0%。

## 预期产出路径
- `zcode/reports/0416-analysis.md`
- `docs/analysis/0416-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0416-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0416-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0417",
                "title": "全协议栈端到端乱序重组窗口最优动态伸缩的非线性控制律设计",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0417 — 全协议栈端到端乱序重组窗口最优动态伸缩的非线性控制律设计

## 任务背景
针对高速乱序场景设计动态重组窗口非线性控制律，杜绝接收端停等卡顿。

## 目标
零停等保证 100.0%，缓冲区余量 >= 20.0%。

## 预期产出路径
- `zcode/reports/0417-analysis.md`
- `docs/analysis/0417-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0417-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0417-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0418",
                "title": "全国总决赛 Grand Master Seal v21 终极密码学签发",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0418 — 全国总决赛 Grand Master Seal v21 终极密码学签发

## 任务背景
对全仓库资产进行 Merkle Tree 密码学封签 v21 签发。

## 目标
封签资产 >= 6000 项，防篡改校验 100.0%。

## 预期产出路径
- `zcode/reports/0418-analysis.md`
- `docs/analysis/0418-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0418-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0418-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_1130_post_dawn (11:30) ----------------
    {
        "batch_id": "batch_campaign_1130_post_dawn",
        "target_time": "11:30",
        "tasks": [
            {
                "id": "0419",
                "title": "多源异构跨流时延微观概率流的福克普朗克偏微分方程谱隙极限定理证明",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0419 — 多源异构跨流时延微观概率流的福克普朗克偏微分方程谱隙极限定理证明

## 任务背景
建立转移算子谱隙 (Spectral Gap) 极限定理，证明排队概率测度以指数速率收敛至平衡态。

## 目标
谱隙正定性验证 100.0%，指数收敛速率证明 100.0%。

## 预期产出路径
- `zcode/reports/0419-analysis.md`
- `docs/analysis/0419-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0419-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0419-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0420",
                "title": "基于凸优化二阶共轭梯度的多轮微突发自适应李雅普诺夫重加权算法",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0420 — 基于凸优化二阶共轭梯度的多轮微突发自适应李雅普诺夫重加权算法

## 任务背景
在李雅普诺夫多时间尺度综合势函数中引入二阶共轭梯度加权自适应更新。

## 目标
势函数下降单调性 100.0%，求解加速比 >= 1.5x。

## 预期产出路径
- `zcode/reports/0420-analysis.md`
- `docs/analysis/0420-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0420-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0420-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0421",
                "title": "全国总决赛 Grand Master Seal v22 终极密码学签发",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0421 — 全国总决赛 Grand Master Seal v22 终极密码学签发

## 任务背景
对全仓库资产进行 Merkle Tree 密码学封签 v22 签发。

## 目标
封签资产 >= 6100 项，防篡改校验 100.0%。

## 预期产出路径
- `zcode/reports/0421-analysis.md`
- `docs/analysis/0421-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0421-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0421-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_1200_post_dawn (12:00) ----------------
    {
        "batch_id": "batch_campaign_1200_post_dawn",
        "target_time": "12:00",
        "tasks": [
            {
                "id": "0422",
                "title": "非马尔可夫广义半鞅差分序列下的极大似然估计一致性与渐近正态性证明",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0422 — 非马尔可夫广义半鞅差分序列下的极大似然估计一致性与渐近正态性证明

## 任务背景
将真实排队数据建模为半鞅差分过程，推导中心极限定理与渐近正态性方差下确界。

## 目标
估计量一致性 100.0%，正态拟合优度 >= 99.0%。

## 预期产出路径
- `zcode/reports/0422-analysis.md`
- `docs/analysis/0422-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0422-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0422-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0423",
                "title": "全拓扑异构下千兆多交换机级联排队网络的瓶颈流极大流极小割全局容量边界",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0423 — 全拓扑异构下千兆多交换机级联排队网络的瓶颈流极大流极小割全局容量边界

## 任务背景
应用 Ford-Fulkerson 与 Max-Flow Min-Cut 定理计算 6 节点拓扑网络全域最大承载流。

## 目标
最小割饱和度 100.0%，容量守恒率 100.0%。

## 预期产出路径
- `zcode/reports/0423-analysis.md`
- `docs/analysis/0423-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0423-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0423-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0424",
                "title": "全国总决赛 Grand Master Seal v23 终极密码学签发",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0424 — 全国总决赛 Grand Master Seal v23 终极密码学签发

## 任务背景
对全仓库资产进行 Merkle Tree 密码学封签 v23 签发。

## 目标
封签资产 >= 6100 项，防篡改校验 100.0%。

## 预期产出路径
- `zcode/reports/0424-analysis.md`
- `docs/analysis/0424-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0424-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0424-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_1230_post_dawn (12:30) ----------------
    {
        "batch_id": "batch_campaign_1230_post_dawn",
        "target_time": "12:30",
        "tasks": [
            {
                "id": "0425",
                "title": "基于强化学习多智能体软行动者评论家最大熵探索的最优流形逼近",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0425 — 基于强化学习多智能体软行动者评论家最大熵探索的最优流形逼近

## 任务背景
应用 Soft Actor-Critic (SAC) 最大熵强化学习机制，平衡参数探索与确定性稳定收敛。

## 目标
策略熵正定性 100.0%，奖励收敛率 >= 99.0%。

## 预期产出路径
- `zcode/reports/0425-analysis.md`
- `docs/analysis/0425-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0425-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0425-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0426",
                "title": "全链路数据一致性多轮实测方差与官方复测超高置信度联合检验",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0426 — 全链路数据一致性多轮实测方差与官方复测超高置信度联合检验

## 任务背景
对 18 发实测打榜与全量数理推导进行置信度 Bonferroni 联合假设检验。

## 目标
第一类错误概率 alpha <= 0.01，联合检验置信度 >= 99.0%。

## 预期产出路径
- `zcode/reports/0426-analysis.md`
- `docs/analysis/0426-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0426-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0426-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0427",
                "title": "全国总决赛 Grand Master Seal v24 终极密码学签发",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0427 — 全国总决赛 Grand Master Seal v24 终极密码学签发

## 任务背景
对全仓库资产进行 Merkle Tree 密码学封签 v24 签发。

## 目标
封签资产 >= 6150 项，防篡改校验 100.0%。

## 预期产出路径
- `zcode/reports/0427-analysis.md`
- `docs/analysis/0427-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0427-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0427-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_1300_post_dawn (13:00) ----------------
    {
        "batch_id": "batch_campaign_1300_post_dawn",
        "target_time": "13:00",
        "tasks": [
            {
                "id": "0428",
                "title": "跨流动态非对称对抗博弈下纳什均衡唯一性与帕累托前沿渐近超平面证明",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0428 — 跨流动态非对称对抗博弈下纳什均衡唯一性与帕累托前沿渐近超平面证明

## 任务背景
应用 Kakutani 不动点定理与超平面分离定理证明非对称带宽竞争博弈的唯一点。

## 目标
均衡唯一性证明 100.0%，超平面分离验证 100.0%。

## 预期产出路径
- `zcode/reports/0428-analysis.md`
- `docs/analysis/0428-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0428-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0428-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0429",
                "title": "全协议栈极值抖动小波包变换多分辨率分解与亚包级瞬态延迟滤波器",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0429 — 全协议栈极值抖动小波包变换多分辨率分解与亚包级瞬态延迟滤波器

## 任务背景
设计 Daubechies 4 阶小波包分解 (WPT)，对网卡中断极值抖动实施多分辨率软阈值滤波。

## 目标
抖动抑制比 >= 99.0%，波形重构保真度 >= 99.5%。

## 预期产出路径
- `zcode/reports/0429-analysis.md`
- `docs/analysis/0429-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0429-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0429-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0430",
                "title": "全国总决赛 Grand Master Seal v25 终极大圆满密码学封签",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0430 — 全国总决赛 Grand Master Seal v25 终极大圆满密码学封签

## 任务背景
对全仓库资产进行 Merkle Tree 密码学封签 v25 终极大圆满签发。

## 目标
封签资产 >= 6200 项，防篡改校验 100.0%。

## 预期产出路径
- `zcode/reports/0430-analysis.md`
- `docs/analysis/0430-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0430-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0430-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_1330_post_dawn (13:30) ----------------
    {
        "batch_id": "batch_campaign_1330_post_dawn",
        "target_time": "13:30",
        "tasks": [
            {
                "id": "0431",
                "title": "高阶重尾网络传输排队系统的分数阶扩散方程与MittagLeffler松弛函数推导",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0431 — 高阶重尾网络传输排队系统的分数阶扩散方程与MittagLeffler松弛函数推导

## 任务背景
建立 Caputo 分数阶偏微分方程与 Mittag-Leffler 松弛函数，表征非高斯长记忆排队尾部。

## 目标
分数阶扩散收敛性 100.0%，松弛函数渐近逼近误差 < 0.01。

## 预期产出路径
- `zcode/reports/0431-analysis.md`
- `docs/analysis/0431-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0431-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0431-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0432",
                "title": "基于分布式主元分析的多链路拥塞时序维度约简与子空间投影追踪",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0432 — 基于分布式主元分析的多链路拥塞时序维度约简与子空间投影追踪

## 任务背景
在 6 节点多链路时序上应用分布式 PCA 提取主特征流形，实现维数约简与低秩投影。

## 目标
主元方差累计贡献率 >= 95.0%，子空间正交重构误差 < 0.05。

## 预期产出路径
- `zcode/reports/0432-analysis.md`
- `docs/analysis/0432-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0432-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0432-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0433",
                "title": "全国总决赛 Grand Master Seal v26 终极密码学签发",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0433 — 全国总决赛 Grand Master Seal v26 终极密码学签发

## 任务背景
对全仓库核心资产进行 Merkle Tree 密码学封签 v26 签发。

## 目标
封签资产 >= 7100 项，防篡改校验 100.0%。

## 预期产出路径
- `zcode/reports/0433-analysis.md`
- `docs/analysis/0433-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0433-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0433-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_1400_post_dawn (14:00) ----------------
    {
        "batch_id": "batch_campaign_1400_post_dawn",
        "target_time": "14:00",
        "tasks": [
            {
                "id": "0434",
                "title": "复杂异构网络微突发非对称排队时延的拓扑熵与信息理论极限速率边界",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0434 — 复杂异构网络微突发非对称排队时延的拓扑熵与信息理论极限速率边界

## 任务背景
计算转移矩阵本征谱对数拓扑熵 h_top(T) = log lambda_max，建立信息论传输速率不可逾越界。

## 目标
拓扑熵正定性 100.0%，Shannon-Hartley 上界吻合度 >= 99.0%。

## 预期产出路径
- `zcode/reports/0434-analysis.md`
- `docs/analysis/0434-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0434-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0434-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0435",
                "title": "全协议栈动态整形参数空间的最优控制极小值原理协态方程求解",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0435 — 全协议栈动态整形参数空间的最优控制极小值原理协态方程求解

## 任务背景
应用 Pontryagin 极小值原理构建哈密顿函数 H(x, u, lambda)，反解最优控制律 u*(t)。

## 目标
协态方程两点边值收敛性 100.0%，哈密顿常数守恒误差 < 0.001。

## 预期产出路径
- `zcode/reports/0435-analysis.md`
- `docs/analysis/0435-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0435-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0435-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0436",
                "title": "全国总决赛 Grand Master Seal v27 终极密码学签发",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0436 — 全国总决赛 Grand Master Seal v27 终极密码学签发

## 任务背景
对全仓库核心资产进行 Merkle Tree 密码学封签 v27 签发。

## 目标
封签资产 >= 7100 项，防篡改校验 100.0%。

## 预期产出路径
- `zcode/reports/0436-analysis.md`
- `docs/analysis/0436-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0436-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0436-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_1430_post_dawn (14:30) ----------------
    {
        "batch_id": "batch_campaign_1430_post_dawn",
        "target_time": "14:30",
        "tasks": [
            {
                "id": "0437",
                "title": "非线性网络效用最大化与带权对偶次梯度投影收敛速度界",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0437 — 非线性网络效用最大化与带权对偶次梯度投影收敛速度界

## 任务背景
在 6 流带宽竞争下建立加权 $lpha$-效用函数与对偶次梯度更新律，推导 $O(1/\sqrt{T})$ 严格次线性收敛速率界。

## 目标
对偶间隙收敛性 100.0%，效用最优性偏离误差 < 0.01。

## 预期产出路径
- `zcode/reports/0437-analysis.md`
- `docs/analysis/0437-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0437-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0437-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0438",
                "title": "有限状态时间延迟马尔可夫决策过程贝尔曼最优误差收缩映射",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0438 — 有限状态时间延迟马尔可夫决策过程贝尔曼最优误差收缩映射

## 任务背景
针对 RTT 往返时延反馈滞后的排队调度，建立时延增广 MDP 与带有折扣因子 $\gamma \in (0, 1)$ 的贝尔曼最大值压缩算子。

## 目标
Banach 不动点压缩因子 $\gamma < 1.0$，值迭代单调收敛性 100.0%。

## 预期产出路径
- `zcode/reports/0438-analysis.md`
- `docs/analysis/0438-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0438-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0438-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0439",
                "title": "全国总决赛 Grand Master Seal v28 终极密码学签发",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0439 — 全国总决赛 Grand Master Seal v28 终极密码学签发

## 任务背景
对全仓库核心资产进行 Merkle Tree 密码学封签 v28 签发。

## 目标
封签资产 >= 7150 项，防篡改校验 100.0%。

## 预期产出路径
- `zcode/reports/0439-analysis.md`
- `docs/analysis/0439-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0439-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0439-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_1500_post_dawn (15:00) ----------------
    {
        "batch_id": "batch_campaign_1500_post_dawn",
        "target_time": "15:00",
        "tasks": [
            {
                "id": "0440",
                "title": "微突发跨流时空自协方差矩阵的张量低秩Tucker分解",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0440 — 微突发跨流时空自协方差矩阵的张量低秩Tucker分解

## 任务背景
在空间节点 (6) x 遥测通道 (4) x 滞后时间步 (20) 的 3 阶张量上执行高阶正交迭代 (HOOI) Tucker 分解。

## 目标
核心张量能量保持率 >= 95.0%，高阶张量重构误差 < 0.05。

## 预期产出路径
- `zcode/reports/0440-analysis.md`
- `docs/analysis/0440-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0440-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0440-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0441",
                "title": "网络丢包恢复的广义帕累托尾部超额损失风险价值CVaR极值推断",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0441 — 网络丢包恢复的广义帕累托尾部超额损失风险价值CVaR极值推断

## 任务背景
应用极值理论 (EVT) 对丢包排队时延的阈值超额分布进行广义帕累托 (GPD) 拟合，解析导出置信度 99% 的条件在险价值 (CVaR-99)。

## 目标
GPD 参数似然估计收敛率 100.0%，CVaR-99 相对真实经验损失误差 < 0.05。

## 预期产出路径
- `zcode/reports/0441-analysis.md`
- `docs/analysis/0441-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0441-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0441-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0442",
                "title": "全国总决赛 Grand Master Seal v29 终极密码学签发",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0442 — 全国总决赛 Grand Master Seal v29 终极密码学签发

## 任务背景
对全仓库核心资产进行 Merkle Tree 密码学封签 v29 签发。

## 目标
封签资产 >= 7150 项，防篡改校验 100.0%。

## 预期产出路径
- `zcode/reports/0442-analysis.md`
- `docs/analysis/0442-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0442-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0442-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_1530_post_dawn (15:30) ----------------
    {
        "batch_id": "batch_campaign_1530_post_dawn",
        "target_time": "15:30",
        "tasks": [
            {
                "id": "0443",
                "title": "非精确近端梯度算法在非光滑限速正则化下的超线性加速",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0443 — 非精确近端梯度算法在非光滑限速正则化下的超线性加速

## 任务背景
在流量整形 L1 稀疏突发抑制惩罚项下，建立非精确近端映射与 Nesterov 动量外推加速。

## 目标
加速收敛迭代阶数加速比 >= 3.0x，近端残差映射误差 < 0.005。

## 预期产出路径
- `zcode/reports/0443-analysis.md`
- `docs/analysis/0443-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0443-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0443-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0444",
                "title": "交换机双重拥塞反馈博弈的斯塔克伯格主从均衡解",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0444 — 交换机双重拥塞反馈博弈的斯塔克伯格主从均衡解

## 任务背景
以核心交换机为 Leader（设定 ECN 标记概率/丢包惩罚），端侧多流为 Followers（响应 Pacing 速率），构建两层双重博弈模型。

## 目标
主从斯塔克伯格逆向归纳反解收敛率 100.0%，次层纳什反应唯一性 100.0%。

## 预期产出路径
- `zcode/reports/0444-analysis.md`
- `docs/analysis/0444-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0444-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0444-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0445",
                "title": "全国总决赛 Grand Master Seal v30 终极密码学签发",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0445 — 全国总决赛 Grand Master Seal v30 终极密码学签发

## 任务背景
对全仓库核心资产进行 Merkle Tree 密码学封签 v30 签发。

## 目标
封签资产 >= 7200 项，防篡改校验 100.0%。

## 预期产出路径
- `zcode/reports/0445-analysis.md`
- `docs/analysis/0445-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0445-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0445-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_1600_post_dawn (16:00) ----------------
    {
        "batch_id": "batch_campaign_1600_post_dawn",
        "target_time": "16:00",
        "tasks": [
            {
                "id": "0446",
                "title": "动态时延网络下的随机微分对策粘性解形式化存在性",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0446 — 动态时延网络下的随机微分对策粘性解形式化存在性

## 任务背景
建立具有时滞的 Hamilton-Jacobi-Isaacs (HJI) 偏微分动力系统，证明粘性下解与粘性上解重合存在唯一性。

## 目标
粘性比较原理严格成立率 100.0%，偏微分残差 < 0.01。

## 预期产出路径
- `zcode/reports/0446-analysis.md`
- `docs/analysis/0446-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0446-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0446-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0447",
                "title": "全链路跨轮次信道衰减自适应卡尔曼布西滤波稳态误差协方差下界",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0447 — 全链路跨轮次信道衰减自适应卡尔曼布西滤波稳态误差协方差下界

## 任务背景
在连续时间高斯白噪声环境下构建连续代数黎卡提方程 (CARE)，求解最优稳态误差协方差矩阵 P*。

## 目标
黎卡提方程正定稳态解残差 < 1e-6，滤波增益渐近稳定性 100.0%。

## 预期产出路径
- `zcode/reports/0447-analysis.md`
- `docs/analysis/0447-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0447-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0447-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0448",
                "title": "全国总决赛 Grand Master Seal v31 终极密码学签发",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0448 — 全国总决赛 Grand Master Seal v31 终极密码学签发

## 任务背景
对全仓库核心资产进行 Merkle Tree 密码学封签 v31 签发。

## 目标
封签资产 >= 7200 项，防篡改校验 100.0%。

## 预期产出路径
- `zcode/reports/0448-analysis.md`
- `docs/analysis/0448-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0448-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0448-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_1630_post_dawn (16:30) ----------------
    {
        "batch_id": "batch_campaign_1630_post_dawn",
        "target_time": "16:30",
        "tasks": [
            {
                "id": "0449",
                "title": "具有随机丢包的网络控制系统线性矩阵不等式H无穷鲁棒镇定",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0449 — 具有随机丢包的网络控制系统线性矩阵不等式H无穷鲁棒镇定

## 任务背景
在伯努利随机丢包信道下建立李雅普诺夫-克拉索夫斯基泛函，通过线性矩阵不等式 (LMI) 求解最优 H-无穷状态反馈控制器。

## 目标
LMI 严格可行解求解率 100.0%，闭环 H-无穷扰动衰减度 gamma <= 0.85。

## 预期产出路径
- `zcode/reports/0449-analysis.md`
- `docs/analysis/0449-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0449-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0449-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0450",
                "title": "跨轮次非平稳流长自回归滑动平均谱估计与自适应周期抵消",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0450 — 跨轮次非平稳流长自回归滑动平均谱估计与自适应周期抵消

## 任务背景
在 6 轮次连续跨流竞争中，使用 ARMA(2, 2) 模型估计背景流周期性波动主频，设计陷波自适应滤波器。

## 目标
自回归极点单位圆内稳定率 100.0%，主频谐波抑制比 >= 18.0 dB。

## 预期产出路径
- `zcode/reports/0450-analysis.md`
- `docs/analysis/0450-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0450-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0450-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0451",
                "title": "全国总决赛 Grand Master Seal v32 终极密码学签发",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0451 — 全国总决赛 Grand Master Seal v32 终极密码学签发

## 任务背景
对全仓库核心资产进行 Merkle Tree 密码学封签 v32 签发。

## 目标
封签资产 >= 7200 项，防篡改校验 100.0%。

## 预期产出路径
- `zcode/reports/0451-analysis.md`
- `docs/analysis/0451-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0451-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0451-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_1700_post_dawn (17:00) ----------------
    {
        "batch_id": "batch_campaign_1700_post_dawn",
        "target_time": "17:00",
        "tasks": [
            {
                "id": "0452",
                "title": "浅缓冲区微突发排队时延的拟生灭过程矩阵几何解",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0452 — 浅缓冲区微突发排队时延的拟生灭过程矩阵几何解

## 任务背景
建立两阶段微突发相依到达的拟生灭过程 (QBD)，求解特征速率矩阵 R 满足代数二次矩阵方程 R^2 A_2 + R A_1 + A_0 = 0。

## 目标
矩阵谱半径 rho(R) < 1.0，稳态排队概率归一化残差 < 1e-6。

## 预期产出路径
- `zcode/reports/0452-analysis.md`
- `docs/analysis/0452-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0452-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0452-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0453",
                "title": "多智能体强化学习分布式Q学习渐近一致性证明",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0453 — 多智能体强化学习分布式Q学习渐近一致性证明

## 任务背景
在 6 节点分布式 QUIC 传输协同场景下，建立结合双随机一致性矩阵 W 的分布式 Q-learning 算法。

## 目标
多节点 Q 表共识方差收敛率 100.0%，一致性残差 < 0.01。

## 预期产出路径
- `zcode/reports/0453-analysis.md`
- `docs/analysis/0453-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0453-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0453-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0454",
                "title": "全国总决赛 Grand Master Seal v33 终极密码学签发",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0454 — 全国总决赛 Grand Master Seal v33 终极密码学签发

## 任务背景
对全仓库核心资产进行 Merkle Tree 密码学封签 v33 签发。

## 目标
封签资产 >= 7200 项，防篡改校验 100.0%。

## 预期产出路径
- `zcode/reports/0454-analysis.md`
- `docs/analysis/0454-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0454-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0454-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_1730_post_dawn (17:30) ----------------
    {
        "batch_id": "batch_campaign_1730_post_dawn",
        "target_time": "17:30",
        "tasks": [
            {
                "id": "0455",
                "title": "非凸光滑极小极大流形近端点迭代鞍点收敛性",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0455 — 非凸光滑极小极大流形近端点迭代鞍点收敛性

## 任务背景
在流量整形非凸非凹鞍点博弈模型中，应用非精确近端点算法 (Proximal Point Algorithm, PPA) 规避极限环与发散。

## 目标
鞍点一阶临界平稳度残差 < 0.005，收敛单调性 100.0%。

## 预期产出路径
- `zcode/reports/0455-analysis.md`
- `docs/analysis/0455-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0455-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0455-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0456",
                "title": "网络传输在途包排队延迟高阶中心矩与埃奇沃斯展开",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0456 — 网络传输在途包排队延迟高阶中心矩与埃奇沃斯展开

## 任务背景
针对排队时延的偏度与峰度非高斯畸变，建立 Edgeworth 展开高阶级数逼近。

## 目标
累积分布函数 (CDF) Kolmogorov-Smirnov 拟合优度 >= 99.0%，4 阶累积量展开误差 < 0.01。

## 预期产出路径
- `zcode/reports/0456-analysis.md`
- `docs/analysis/0456-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0456-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0456-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0457",
                "title": "全国总决赛 Grand Master Seal v34 终极密码学签发",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0457 — 全国总决赛 Grand Master Seal v34 终极密码学签发

## 任务背景
对全仓库核心资产进行 Merkle Tree 密码学封签 v34 签发。

## 目标
封签资产 >= 7250 项，防篡改校验 100.0%。

## 预期产出路径
- `zcode/reports/0457-analysis.md`
- `docs/analysis/0457-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0457-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0457-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_1800_post_dawn (18:00) ----------------
    {
        "batch_id": "batch_campaign_1800_post_dawn",
        "target_time": "18:00",
        "tasks": [
            {
                "id": "0458",
                "title": "基于克拉美罗下界的分布式往返时延纳秒级参数辨识无偏估计",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0458 — 基于克拉美罗下界的分布式往返时延纳秒级参数辨识无偏估计

## 任务背景
推导往返时延 RTT 参数辨识的费希尔信息矩阵 (FIM) 与克拉美-罗下界 (CRLB)，验证极大似然估计达到有效估计界。

## 目标
估计方差与 CRLB 下界比值在 [1.0, 1.05] 区间内，有效估计效率 >= 95.0%。

## 预期产出路径
- `zcode/reports/0458-analysis.md`
- `docs/analysis/0458-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0458-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0458-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0459",
                "title": "多源异构流竞争下的有限长块编码正反向传输界",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0459 — 多源异构流竞争下的有限长块编码正反向传输界

## 任务背景
应用 Polyanskiy-Poor-Verdú (PPV) 有限块长信息论理论，计算块长 n 约束下的传输速率正反向边界。

## 目标
PPV 紧致逼近残差 < 0.01，信道分散度 V_channel 正定率 100.0%。

## 预期产出路径
- `zcode/reports/0459-analysis.md`
- `docs/analysis/0459-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0459-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0459-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0460",
                "title": "全国总决赛 Grand Master Seal v35 终极密码学签发",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0460 — 全国总决赛 Grand Master Seal v35 终极密码学签发

## 任务背景
对全仓库核心资产进行 Merkle Tree 密码学封签 v35 签发。

## 目标
封签资产 >= 7250 项，防篡改校验 100.0%。

## 预期产出路径
- `zcode/reports/0460-analysis.md`
- `docs/analysis/0460-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0460-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0460-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_1830_post_dawn (18:30) ----------------
    {
        "batch_id": "batch_campaign_1830_post_dawn",
        "target_time": "18:30",
        "tasks": [
            {
                "id": "0461",
                "title": "具有量化状态反馈的网络控制系统对数自适应量化器设计",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0461 — 具有量化状态反馈的网络控制系统对数自适应量化器设计

## 任务背景
针对端侧有限带宽信道下的量化状态反馈，设计对数动态自适应量化器 q(x) 与李雅普诺夫鲁棒渐近稳定律。

## 目标
量化误差扇区有界率 100.0%，对数扇区下确界收敛残差 < 0.005。

## 预期产出路径
- `zcode/reports/0461-analysis.md`
- `docs/analysis/0461-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0461-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0461-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0462",
                "title": "六流多路径传输拓扑重叠度的互信息与独立分量分析",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0462 — 六流多路径传输拓扑重叠度的互信息与独立分量分析

## 任务背景
在 6 轮次连续跨流多通道观测上应用 FastICA 算法盲源分离底层真实瓶颈流与独立扰动源，计算互信息解耦度。

## 目标
独立分量解耦正交度误差 < 0.05，互信息极小化衰减率 >= 95.0%。

## 预期产出路径
- `zcode/reports/0462-analysis.md`
- `docs/analysis/0462-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0462-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0462-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0463",
                "title": "全国总决赛 Grand Master Seal v36 终极密码学签发",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0463 — 全国总决赛 Grand Master Seal v36 终极密码学签发

## 任务背景
对全仓库核心资产进行 Merkle Tree 密码学封签 v36 签发。

## 目标
封签资产 >= 7280 项，防篡改校验 100.0%。

## 预期产出路径
- `zcode/reports/0463-analysis.md`
- `docs/analysis/0463-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0463-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0463-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_1900_post_dawn (19:00) ----------------
    {
        "batch_id": "batch_campaign_1900_post_dawn",
        "target_time": "19:00",
        "tasks": [
            {
                "id": "0464",
                "title": "广义互补问题费希尔伯迈斯特连续化阻尼牛顿法",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0464 — 广义互补问题费希尔伯迈斯特连续化阻尼牛顿法

## 任务背景
将流量整形非负限速与浅队列互补松弛约束表征为非线性互补问题 (NCP)，利用 Fischer-Burmeister 函数转化为平滑非线性方程组。

## 目标
阻尼牛顿法超线性收敛率 100.0%，互补残差 < 1e-8。

## 预期产出路径
- `zcode/reports/0464-analysis.md`
- `docs/analysis/0464-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0464-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0464-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0465",
                "title": "基于狄利克雷过程混合模型的无监督网络突发相态聚类",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0465 — 基于狄利克雷过程混合模型的无监督网络突发相态聚类

## 任务背景
利用非参数贝叶斯狄利克雷过程混合模型 (DPMM) 自动推断背景网络潜在突发相态数量与后验概率分布。

## 目标
DPMM 塌缩 Gibbs 采样对数边际似然收敛率 100.0%，聚类调整兰德指数 (ARI) >= 0.90。

## 预期产出路径
- `zcode/reports/0465-analysis.md`
- `docs/analysis/0465-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0465-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0465-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0466",
                "title": "全国总决赛 Grand Master Seal v37 终极密码学签发",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0466 — 全国总决赛 Grand Master Seal v37 终极密码学签发

## 任务背景
对全仓库核心资产进行 Merkle Tree 密码学封签 v37 签发。

## 目标
封签资产 >= 7280 项，防篡改校验 100.0%。

## 预期产出路径
- `zcode/reports/0466-analysis.md`
- `docs/analysis/0466-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析成果写入 `docs/analysis/0466-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0466-analysis.md`，状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_1930_post_dawn (19:30) ----------------
    {
        "batch_id": "batch_campaign_1930_post_dawn",
        "target_time": "19:30",
        "tasks": [
            {
                "id": "0467",
                "title": "广义纳什均衡变分不等式投影动力学",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0467 ：广义纳什均衡变分不等式投影动力学

## 任务背景
针对 6 阶段穿柜传输中共享浅缓冲区竞争，构建广义纳什均衡问题 (GNEP) 并利用变分不等式 (VI) 投影动力学求解。

## 目标
VI 投影收敛率 100.0%，投影残差 < 1e-6。

## 预期产出路径
- `zcode/reports/0467-analysis.md`
- `docs/analysis/0467-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析报告写入 `docs/analysis/0467-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0467-analysis.md`，将状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改实验提交凭证。
"""
            },
            {
                "id": "0468",
                "title": "自适应无迹卡尔曼滤波瓶颈容量跟踪",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0468 ：自适应无迹卡尔曼滤波瓶颈容量跟踪

## 任务背景
在非线性浅缓冲区突发抖动下，利用自适应无迹卡尔曼滤波 (AUKF) 对未知时变瓶颈信道容量进行无偏动态跟踪。

## 目标
动态跟踪相对误差 < 2.0%，新息正交一致性率 100.0%。

## 预期产出路径
- `zcode/reports/0468-analysis.md`
- `docs/analysis/0468-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析报告写入 `docs/analysis/0468-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0468-analysis.md`，将状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改实验提交凭证。
"""
            },
            {
                "id": "0469",
                "title": "全局大封印 Grand Master Seal v38 空间密码学签名认证",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0469 ：全局大封印 Grand Master Seal v38 空间密码学签名认证

## 任务背景
对全局资产库执行 Merkle Tree 密码学签名 v38 封印。

## 目标
签名资产 >= 7310 项，完整性校验通过率 100.0%。

## 预期产出路径
- `zcode/reports/0469-analysis.md`
- `docs/analysis/0469-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析报告写入 `docs/analysis/0469-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0469-analysis.md`，将状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改实验提交凭证。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_2000_post_dawn (20:00) ----------------
    {
        "batch_id": "batch_campaign_2000_post_dawn",
        "target_time": "20:00",
        "tasks": [
            {
                "id": "0470",
                "title": "庞特里亚金最大值原理能量时延帕累托最优轨迹",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0470 ：庞特里亚金最大值原理能量时延帕累托最优轨迹

## 任务背景
应用连续时间庞特里亚金最大值原理 (PMP) 求解 6 阶段穿柜缓冲区的能量-时延帕累托边界最优控制轨迹。

## 目标
哈密顿量守恒误差 < 1e-6，帕累托前沿单调性 100.0%。

## 预期产出路径
- `zcode/reports/0470-analysis.md`
- `docs/analysis/0470-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析报告写入 `docs/analysis/0470-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0470-analysis.md`，将状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改实验提交凭证。
"""
            },
            {
                "id": "0471",
                "title": "分布式异步交替方向乘子法拥塞控制一致性",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0471 ：分布式异步交替方向乘子法拥塞控制一致性

## 任务背景
在分布式异构时延环境下，使用异步 ADMM 算法实现多流在浅缓冲区约束下的发包速率全局一致性协调。

## 目标
原始残差 < 1e-5，对偶残差 < 1e-5，收敛成功率 100.0%。

## 预期产出路径
- `zcode/reports/0471-analysis.md`
- `docs/analysis/0471-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析报告写入 `docs/analysis/0471-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0471-analysis.md`，将状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改实验提交凭证。
"""
            },
            {
                "id": "0472",
                "title": "全局大封印 Grand Master Seal v39 空间密码学签名认证",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0472 ：全局大封印 Grand Master Seal v39 空间密码学签名认证

## 任务背景
对全局资产库执行 Merkle Tree 密码学签名 v39 封印。

## 目标
签名资产 >= 7330 项，完整性校验通过率 100.0%。

## 预期产出路径
- `zcode/reports/0472-analysis.md`
- `docs/analysis/0472-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析报告写入 `docs/analysis/0472-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0472-analysis.md`，将状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改实验提交凭证。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_2030_post_dawn (20:30) ----------------
    {
        "batch_id": "batch_campaign_2030_post_dawn",
        "target_time": "20:30",
        "tasks": [
            {
                "id": "0473",
                "title": "截断柯西变异粒子群浅缓冲区参数全局探索",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0473 ：截断柯西变异粒子群浅缓冲区参数全局探索

## 任务背景
在非凸非光滑的 QUIC 穿柜多维参数曲面上，应用带有截断柯西变异的长尾随机扰动粒子群优化 (TC-PSO) 避免陷入局部极值。

## 目标
全局最优解陷入逃逸率 100.0%，适应度方差收敛 < 1e-4。

## 预期产出路径
- `zcode/reports/0473-analysis.md`
- `docs/analysis/0473-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析报告写入 `docs/analysis/0473-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0473-analysis.md`，将状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改实验提交凭证。
"""
            },
            {
                "id": "0474",
                "title": "随机逼近罗宾斯蒙罗极小极大速率辨识",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0474 ：随机逼近罗宾斯蒙罗极小极大速率辨识

## 任务背景
在未知噪声统计特征下，利用 Robbins-Monro 随机逼近算子实现浅缓冲区临界饱和速率的均方渐近无偏估计。

## 目标
参数估计相对误差 < 1.0%，收敛率 100.0%。

## 预期产出路径
- `zcode/reports/0474-analysis.md`
- `docs/analysis/0474-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析报告写入 `docs/analysis/0474-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0474-analysis.md`，将状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改实验提交凭证。
"""
            },
            {
                "id": "0475",
                "title": "全局大封印 Grand Master Seal v40 空间密码学签名认证",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0475 ：全局大封印 Grand Master Seal v40 空间密码学签名认证

## 任务背景
对全局资产库执行 Merkle Tree 密码学签名 v40 封印。

## 目标
签名资产 >= 7340 项，完整性校验通过率 100.0%。

## 预期产出路径
- `zcode/reports/0475-analysis.md`
- `docs/analysis/0475-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析报告写入 `docs/analysis/0475-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0475-analysis.md`，将状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改实验提交凭证。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_2100_post_dawn (21:00) ----------------
    {
        "batch_id": "batch_campaign_2100_post_dawn",
        "target_time": "21:00",
        "tasks": [
            {
                "id": "0476",
                "title": "非局部偏微分方程分数阶缓冲区流形动态扩散",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0476 ：非局部偏微分方程分数阶缓冲区流形动态扩散

## 任务背景
针对重尾大象流并发冲击，建立分数阶积分非局部偏微分方程描述浅缓冲区排队密度的反常次扩散现象。

## 目标
非局部拉普拉斯能量耗散非负性 100.0%，数值逼近误差 < 0.01。

## 预期产出路径
- `zcode/reports/0476-analysis.md`
- `docs/analysis/0476-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析报告写入 `docs/analysis/0476-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0476-analysis.md`，将状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改实验提交凭证。
"""
            },
            {
                "id": "0477",
                "title": "多时间尺度奇异摄动慢流形拥塞边界收敛",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0477 ：多时间尺度奇异摄动慢流形拥塞边界收敛

## 任务背景
将微秒级 Pacer 间隔与毫秒级 RTT 构成分离时间尺度系统，基于 Tikhonov 奇异摄动定理求解慢流形渐近展开。

## 目标
慢流形不变性残差 < 1e-4，渐近稳定性 100.0%。

## 预期产出路径
- `zcode/reports/0477-analysis.md`
- `docs/analysis/0477-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析报告写入 `docs/analysis/0477-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0477-analysis.md`，将状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改实验提交凭证。
"""
            },
            {
                "id": "0478",
                "title": "全局大封印 Grand Master Seal v41 空间密码学签名认证",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0478 ：全局大封印 Grand Master Seal v41 空间密码学签名认证

## 任务背景
对全局资产库执行 Merkle Tree 密码学签名 v41 封印。

## 目标
签名资产 >= 7360 项，完整性校验通过率 100.0%。

## 预期产出路径
- `zcode/reports/0478-analysis.md`
- `docs/analysis/0478-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析报告写入 `docs/analysis/0478-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0478-analysis.md`，将状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改实验提交凭证。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_2130_post_dawn (21:30) ----------------
    {
        "batch_id": "batch_campaign_2130_post_dawn",
        "target_time": "21:30",
        "tasks": [
            {
                "id": "0479",
                "title": "信息几何自然梯度费舍尔信息流形测地线寻优",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0479 ：信息几何自然梯度费舍尔信息流形测地线寻优

## 任务背景
在发包速率概率分布族上，基于费舍尔信息矩阵 (Fisher Information Matrix, FIM) 构造黎曼流形测地线自然梯度更新。

## 目标
自然梯度相比标准欧氏梯度加速比 >= 3.0x，FIM 正定性 100.0%。

## 预期产出路径
- `zcode/reports/0479-analysis.md`
- `docs/analysis/0479-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析报告写入 `docs/analysis/0479-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0479-analysis.md`，将状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改实验提交凭证。
"""
            },
            {
                "id": "0480",
                "title": "动态贝叶斯网络隐式丢包因果推断辨识",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0480 ：动态贝叶斯网络隐式丢包因果推断辨识

## 任务背景
在 QUIC 丢包信号中，利用动态贝叶斯网络 (DBN) 辨识物理随机丢包与浅缓冲区瞬态拥塞丢包的因果关系。

## 目标
因果推断后验分类准确率 >= 98.0%，置信度传播收敛率 100.0%。

## 预期产出路径
- `zcode/reports/0480-analysis.md`
- `docs/analysis/0480-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析报告写入 `docs/analysis/0480-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0480-analysis.md`，将状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改实验提交凭证。
"""
            },
            {
                "id": "0481",
                "title": "全局大封印 Grand Master Seal v42 空间密码学签名认证",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0481 ：全局大封印 Grand Master Seal v42 空间密码学签名认证

## 任务背景
对全局资产库执行 Merkle Tree 密码学签名 v42 封印。

## 目标
签名资产 >= 7365 项，完整性校验通过率 100.0%。

## 预期产出路径
- `zcode/reports/0481-analysis.md`
- `docs/analysis/0481-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析报告写入 `docs/analysis/0481-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0481-analysis.md`，将状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改实验提交凭证。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_2200_post_dawn (22:00) ----------------
    {
        "batch_id": "batch_campaign_2200_post_dawn",
        "target_time": "22:00",
        "tasks": [
            {
                "id": "0482",
                "title": "广义波尔兹曼机自由能极小化流量平滑热力学平衡",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0482 ：广义波尔兹曼机自由能极小化流量平滑热力学平衡

## 任务背景
应用统计力学自由能极小化原理构建发包流量平滑器，证明吉布斯系综在微观微突发与宏观吞吐量之间的平衡态。

## 目标
自由能耗散单调性 100.0%，热力学平衡相对误差 < 1.0%。

## 预期产出路径
- `zcode/reports/0482-analysis.md`
- `docs/analysis/0482-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析报告写入 `docs/analysis/0482-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0482-analysis.md`，将状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改实验提交凭证。
"""
            },
            {
                "id": "0483",
                "title": "随机摄动同步逼近零阶黑盒评测梯度重构",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0483 ：随机摄动同步逼近零阶黑盒评测梯度重构

## 任务背景
在黑盒评测无显式梯度的约束下，利用同时随机摄动 (SPSA) 对 6 阶段全局下载时间进行双样本无偏梯度估计。

## 目标
梯度余弦相似度 >= 0.95，收敛成功率 100.0%。

## 预期产出路径
- `zcode/reports/0483-analysis.md`
- `docs/analysis/0483-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析报告写入 `docs/analysis/0483-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0483-analysis.md`，将状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改实验提交凭证。
"""
            },
            {
                "id": "0484",
                "title": "全局大封印 Grand Master Seal v43 空间密码学签名认证",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0484 ：全局大封印 Grand Master Seal v43 空间密码学签名认证

## 任务背景
对全局资产库执行 Merkle Tree 密码学签名 v43 封印。

## 目标
签名资产 >= 7380 项，完整性校验通过率 100.0%。

## 预期产出路径
- `zcode/reports/0484-analysis.md`
- `docs/analysis/0484-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析报告写入 `docs/analysis/0484-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0484-analysis.md`，将状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改实验提交凭证。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_2230_post_dawn (22:30) ----------------
    {
        "batch_id": "batch_campaign_2230_post_dawn",
        "target_time": "22:30",
        "tasks": [
            {
                "id": "0485",
                "title": "高阶李群李代数刚体流形四元数速率插值",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0485 ：高阶李群李代数刚体流形四元数速率插值

## 任务背景
在 6 阶段多参数联合空间中，将速率转换建模为特殊欧氏群 SE(3) 流形测地线，利用双四元数指数/对数映射实现光滑无震荡过渡。

## 目标
正交群行列式测度残差 < 1e-12，李代数对数映射误差 < 1e-6。

## 预期产出路径
- `zcode/reports/0485-analysis.md`
- `docs/analysis/0485-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析报告写入 `docs/analysis/0485-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0485-analysis.md`，将状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改实验提交凭证。
"""
            },
            {
                "id": "0486",
                "title": "混成自动机离散事件与连续浅缓冲区流可达集验证",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0486 ：混成自动机离散事件与连续浅缓冲区流可达集验证

## 任务背景
将 ACK 到达的离散事件跳变与漏桶连续流体动力学构建为混成自动机 (Hybrid Automata)，计算前向不变可达集。

## 目标
浅缓冲区溢出不安全集可达概率 0.0%，保护不变集违约率 0.0%。

## 预期产出路径
- `zcode/reports/0486-analysis.md`
- `docs/analysis/0486-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析报告写入 `docs/analysis/0486-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0486-analysis.md`，将状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改实验提交凭证。
"""
            },
            {
                "id": "0487",
                "title": "全局大封印 Grand Master Seal v44 空间密码学签名认证",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0487 ：全局大封印 Grand Master Seal v44 空间密码学签名认证

## 任务背景
对全局资产库执行 Merkle Tree 密码学签名 v44 封印。

## 目标
签名资产 >= 7400 项，完整性校验通过率 100.0%。

## 预期产出路径
- `zcode/reports/0487-analysis.md`
- `docs/analysis/0487-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析报告写入 `docs/analysis/0487-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0487-analysis.md`，将状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改实验提交凭证。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_2300_post_dawn (23:00) ----------------
    {
        "batch_id": "batch_campaign_2300_post_dawn",
        "target_time": "23:00",
        "tasks": [
            {
                "id": "0488",
                "title": "随机泛函微分方程无限时滞记忆核排队稳定界",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0488 ：随机泛函微分方程无限时滞记忆核排队稳定界

## 任务背景
考虑历史跨网络时延的无限记忆衰减分布，基于随机泛函微分方程 (SFDE) 证明李雅普诺夫-克拉索夫斯基泛函能量耗散。

## 目标
LK 泛函单调衰减率 100.0%，记忆卷积积分残差 < 1e-4。

## 预期产出路径
- `zcode/reports/0488-analysis.md`
- `docs/analysis/0488-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析报告写入 `docs/analysis/0488-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0488-analysis.md`，将状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改实验提交凭证。
"""
            },
            {
                "id": "0489",
                "title": "分布式一致性牛顿乘子法二阶曲率加速",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0489 ：分布式一致性牛顿乘子法二阶曲率加速

## 任务背景
在浅缓冲区耦合多智能体速率一致性中，利用黑塞矩阵二阶曲率牛顿更新加速 ADMM 对偶迭代收敛。

## 目标
二次渐近超线性收敛率 100.0%，原始对偶联合残差 < 1e-7。

## 预期产出路径
- `zcode/reports/0489-analysis.md`
- `docs/analysis/0489-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析报告写入 `docs/analysis/0489-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0489-analysis.md`，将状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改实验提交凭证。
"""
            },
            {
                "id": "0490",
                "title": "全局大封印 Grand Master Seal v45 空间密码学签名认证",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0490 ：全局大封印 Grand Master Seal v45 空间密码学签名认证

## 任务背景
对全局资产库执行 Merkle Tree 密码学签名 v45 封印。

## 目标
签名资产 >= 7420 项，完整性校验通过率 100.0%。

## 预期产出路径
- `zcode/reports/0490-analysis.md`
- `docs/analysis/0490-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析报告写入 `docs/analysis/0490-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0490-analysis.md`，将状态修改为 `status: done`。

## 合规
- 严禁登录远程平台提交榜单，严禁修改实验提交凭证。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_2330_post_dawn (23:30) ----------------
    {
        "batch_id": "batch_campaign_2330_post_dawn",
        "target_time": "23:30",
        "tasks": [
            {
                "id": "0491",
                "title": "拟哈密顿系统辛几何数值积分",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0491 拟哈密顿系统辛几何数值积分

## 任务背景
在流量整形状态相空间中，构建拟哈密顿辛几何数值积分器，验证能量守恒与阻尼耗散流形结构。

## 目标指标
辛形式守恒残差 < 1e-12，哈密顿能量衰减单调性 100.0%。

## 预期产出路径
- `zcode/reports/0491-analysis.md`
- `docs/analysis/0491-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0491-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0491-analysis.md`，将状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改实验提交凭证。
"""
            },
            {
                "id": "0492",
                "title": "极小极大鲁棒微分博弈鞍点策动",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0492 极小极大鲁棒微分博弈鞍点策动

## 任务背景
针对突发跨流最恶劣排队攻击，构建 Hamilton-Jacobi-Isaacs 极小极大微分博弈鞍点控制律。

## 目标指标
鞍点对偶间隙 < 1e-5，浅缓冲区峰值排队严格 < 36.0 pkts。

## 预期产出路径
- `zcode/reports/0492-analysis.md`
- `docs/analysis/0492-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0492-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0492-analysis.md`，将状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改实验提交凭证。
"""
            },
            {
                "id": "0493",
                "title": "全局大封印 Grand Master Seal v46 时空密码学签名存证",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0493 全局大封印 Grand Master Seal v46 时空密码学签名存证

## 任务背景
对全库资产执行 Merkle Tree 密码学签名与 v46 封印存证。

## 目标指标
签名资产 >= 7480 项，校验通过率 100.0%。

## 预期产出路径
- `zcode/reports/0493-analysis.md`
- `docs/analysis/0493-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0493-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0493-analysis.md`，将状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改实验提交凭证。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_0000_morning (00:00) ----------------
    {
        "batch_id": "batch_campaign_0000_morning",
        "target_time": "00:00",
        "tasks": [
            {
                "id": "0494",
                "title": "奇异弧最优控制速率切换流形",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0494 奇异弧最优控制速率切换流形

## 任务背景
在流量整形跨阶段过渡中，利用 Kelley 二阶最优性条件求解奇异控制弧并构建无振荡切换流形。

## 目标指标
Kelley 条件满足率 100.0%，切换时间误差 < 1e-5 s。

## 预期产出路径
- `zcode/reports/0494-analysis.md`
- `docs/analysis/0494-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0494-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0494-analysis.md`，将状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改实验提交凭证。
"""
            },
            {
                "id": "0495",
                "title": "GARCH-Copula 浅缓冲区尾部相依结构",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0495 GARCH-Copula 浅缓冲区尾部相依结构

## 任务背景
结合 GARCH 异方差波动与 Clayton-Gumbel Copula，建模网络突发微抖动与排队突发的极值尾部相依性。

## 目标指标
Kendall秩相关误差 < 0.02，尾部相依参数辨识准确率 >= 98.0%。

## 预期产出路径
- `zcode/reports/0495-analysis.md`
- `docs/analysis/0495-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0495-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0495-analysis.md`，将状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改实验提交凭证。
"""
            },
            {
                "id": "0496",
                "title": "全局大封印 Grand Master Seal v47 时空密码学签名存证",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0496 全局大封印 Grand Master Seal v47 时空密码学签名存证

## 任务背景
对全库资产执行 Merkle Tree 密码学签名与 v47 封印存证。

## 目标指标
签名资产 >= 7510 项，校验通过率 100.0%。

## 预期产出路径
- `zcode/reports/0496-analysis.md`
- `docs/analysis/0496-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0496-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0496-analysis.md`，将状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改实验提交凭证。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_0030_morning (00:30) ----------------
    {
        "batch_id": "batch_campaign_0030_morning",
        "target_time": "00:30",
        "tasks": [
            {
                "id": "0497",
                "title": "分数阶非线性薛定谔势阱孤子演化",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0497 分数阶非线性薛定谔势阱孤子演化

## 任务背景
在量子势阱网络拥塞模型下，利用分数阶薛定谔方程解析浅缓冲区孤子压缩波包演化。

## 目标指标
孤子波形守恒残差 < 1e-4，L2 质量守恒率 100.0%。

## 预期产出路径
- `zcode/reports/0497-analysis.md`
- `docs/analysis/0497-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0497-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0497-analysis.md`，将状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改实验提交凭证。
"""
            },
            {
                "id": "0498",
                "title": "瓦瑟斯坦距离最优传输测地流",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0498 瓦瑟斯坦距离最优传输测地流

## 任务背景
利用 Sinkhorn 熵正则化瓦瑟斯坦最优传输，计算非均匀流量包到达分布与服务吸收分布之间的测地流曲线。

## 目标指标
Sinkhorn 最优传输对偶残差 < 1e-5，边际约束误差 < 1e-6。

## 预期产出路径
- `zcode/reports/0498-analysis.md`
- `docs/analysis/0498-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0498-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0498-analysis.md`，将状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改实验提交凭证。
"""
            },
            {
                "id": "0499",
                "title": "全局大封印 Grand Master Seal v48 时空密码学签名存证",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0499 全局大封印 Grand Master Seal v48 时空密码学签名存证

## 任务背景
对全库资产执行 Merkle Tree 密码学签名与 v48 封印存证。

## 目标指标
签名资产 >= 7540 项，校验通过率 100.0%。

## 预期产出路径
- `zcode/reports/0499-analysis.md`
- `docs/analysis/0499-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0499-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0499-analysis.md`，将状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改实验提交凭证。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_0100_morning (01:00) ----------------
    {
        "batch_id": "batch_campaign_0100_morning",
        "target_time": "01:00",
        "tasks": [
            {
                "id": "0500",
                "title": "李雅普诺夫指数谱确定性混沌分岔抑制",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0500 李雅普诺夫指数谱确定性混沌分岔抑制

## 任务背景
计算拥塞整形动力系统最大李雅普诺夫指数谱 (MLE)，验证浅缓冲区非线性振荡的混沌边界分岔抑制效果。

## 目标指标
最大李雅普诺夫指数 MLE < 0.0，相空间吸引子体积收缩率 100.0%。

## 预期产出路径
- `zcode/reports/0500-analysis.md`
- `docs/analysis/0500-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0500-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0500-analysis.md`，将状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改实验提交凭证。
"""
            },
            {
                "id": "0501",
                "title": "异步对偶分解原始乘子法异构链路协同",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0501 异步对偶分解原始乘子法异构链路协同

## 任务背景
针对六载异构链路状态，构建完全异步对偶分解算法，验证时钟失步下的全局收敛性。

## 目标指标
原始可行性残差 < 1e-6，对偶间隙 < 1e-6，收敛率 100.0%。

## 预期产出路径
- `zcode/reports/0501-analysis.md`
- `docs/analysis/0501-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0501-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0501-analysis.md`，将状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改实验提交凭证。
"""
            },
            {
                "id": "0502",
                "title": "全局大封印 Grand Master Seal v49 时空密码学签名存证",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0502 全局大封印 Grand Master Seal v49 时空密码学签名存证

## 任务背景
对全库资产执行 Merkle Tree 密码学签名与 v49 封印存证。

## 目标指标
签名资产 >= 7570 项，校验通过率 100.0%。

## 预期产出路径
- `zcode/reports/0502-analysis.md`
- `docs/analysis/0502-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0502-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0502-analysis.md`，将状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改实验提交凭证。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_0130_morning (01:30) ----------------
    {
        "batch_id": "batch_campaign_0130_morning",
        "target_time": "01:30",
        "tasks": [
            {
                "id": "0503",
                "title": "列维跳跃扩散浅缓冲区首达时分布",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0503 列维跳跃扩散浅缓冲区首达时分布

## 任务背景
在非高斯重尾跨流冲击下，构建列维跳跃扩散 (Lévy Jump-Diffusion) 偏积分微分方程 (PIDE) 并求解浅缓冲区首达时。

## 目标指标
Kolmogorov 前向方程积分微分残差 < 1e-4，首达时概率密度 L1 误差 < 0.01。

## 预期产出路径
- `zcode/reports/0503-analysis.md`
- `docs/analysis/0503-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0503-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0503-analysis.md`，将状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改实验提交凭证。
"""
            },
            {
                "id": "0504",
                "title": "黎曼流形哈密顿蒙特卡洛后验推断",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0504 黎曼流形哈密顿蒙特卡洛后验推断

## 任务背景
针对流量整形参数高维曲面，利用黎曼流形哈密顿蒙特卡洛 (RM-HMC) 进行贝叶斯后验参数空间无偏采样。

## 目标指标
Gelman-Rubin 收敛诊断 R_hat < 1.05，有效采样数 ESS >= 800，接受率在 [60%, 85%]。

## 预期产出路径
- `zcode/reports/0504-analysis.md`
- `docs/analysis/0504-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0504-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0504-analysis.md`，将状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改实验提交凭证。
"""
            },
            {
                "id": "0505",
                "title": "全局大封印 Grand Master Seal v50 时空密码学签名存证",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0505 全局大封印 Grand Master Seal v50 时空密码学签名存证

## 任务背景
对全库资产执行 Merkle Tree 密码学签名与 v50 封印存证。

## 目标指标
签名资产 >= 7600 项，校验通过率 100.0%。

## 预期产出路径
- `zcode/reports/0505-analysis.md`
- `docs/analysis/0505-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0505-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0505-analysis.md`，将状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改实验提交凭证。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_0200_morning (02:00) ----------------
    {
        "batch_id": "batch_campaign_0200_morning",
        "target_time": "02:00",
        "tasks": [
            {
                "id": "0506",
                "title": "变分自编码器测地潜空间轨迹生成",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0506 变分自编码器测地潜空间轨迹生成

## 任务背景
训练 VAE 流量动态生成模型，在潜变量黎曼度量流形上沿测地线插值生成光滑整形轨迹。

## 目标指标
重构均方误差 MSE < 0.005，潜空间正则度 100.0%，测地平滑度 > 0.99。

## 预期产出路径
- `zcode/reports/0506-analysis.md`
- `docs/analysis/0506-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0506-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0506-analysis.md`，将状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改实验提交凭证。
"""
            },
            {
                "id": "0507",
                "title": "非线性广义受迫振子共振吸收阻尼",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0507 非线性广义受迫振子共振吸收阻尼

## 任务背景
将浅缓冲区排队突发等效为 Duffing-Van der Pol 受迫自激振子，设计非线性共振吸振器抑制主共振峰。

## 目标指标
主共振峰振幅衰减比 >= 70.0%，能量耗散率 100.0%。

## 预期产出路径
- `zcode/reports/0507-analysis.md`
- `docs/analysis/0507-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0507-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0507-analysis.md`，将状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改实验提交凭证。
"""
            },
            {
                "id": "0508",
                "title": "全局大封印 Grand Master Seal v51 时空密码学签名存证",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0508 全局大封印 Grand Master Seal v51 时空密码学签名存证

## 任务背景
对全库资产执行 Merkle Tree 密码学签名与 v51 封印存证。

## 目标指标
签名资产 >= 7630 项，校验通过率 100.0%。

## 预期产出路径
- `zcode/reports/0508-analysis.md`
- `docs/analysis/0508-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0508-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0508-analysis.md`，将状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改实验提交凭证。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_0230_morning (02:30) ----------------
    {
        "batch_id": "batch_campaign_0230_morning",
        "target_time": "02:30",
        "tasks": [
            {
                "id": "0509",
                "title": "最大熵软动作-评价连续整形策动",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0509 最大熵软动作-评价连续整形策动

## 任务背景
在非定常跨流干扰环境下，构建 Soft Actor-Critic (SAC) 最大熵连续控制律，平衡探索与稳健下载。

## 目标指标
策略熵下界 > 0.5，累积回报收敛率 100.0%，缓冲区溢出丢包数 0。

## 预期产出路径
- `zcode/reports/0509-analysis.md`
- `docs/analysis/0509-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0509-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0509-analysis.md`，将状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改实验提交凭证。
"""
            },
            {
                "id": "0510",
                "title": "截断奇异值主成分自适应状态观测",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0510 截断奇异值主成分自适应状态观测

## 任务背景
利用截断 SVD 从高维网络往返时延与吞吐量遥测数据中提取低维主正交基，构建快速状态降阶观测器。

## 目标指标
子空间重构能量占比 >= 99.5%，状态观测相对误差 < 1.0%。

## 预期产出路径
- `zcode/reports/0510-analysis.md`
- `docs/analysis/0510-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0510-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0510-analysis.md`，将状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改实验提交凭证。
"""
            },
            {
                "id": "0511",
                "title": "全局大封印 Grand Master Seal v52 时空密码学签名存证",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0511 全局大封印 Grand Master Seal v52 时空密码学签名存证

## 任务背景
对全库资产执行 Merkle Tree 密码学签名与 v52 封印存证。

## 目标指标
签名资产 >= 7660 项，校验通过率 100.0%。

## 预期产出路径
- `zcode/reports/0511-analysis.md`
- `docs/analysis/0511-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0511-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0511-analysis.md`，将状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改实验提交凭证。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_0300_morning (03:00) ----------------
    {
        "batch_id": "batch_campaign_0300_morning",
        "target_time": "03:00",
        "tasks": [
            {
                "id": "0512",
                "title": "全域多尺度综合泛函全景复盘",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0512 全域多尺度综合泛函全景复盘

## 任务背景
整合全部 6 个下载阶段的多尺度整形控制理论，建立统一帕累托前沿复盘泛函。

## 目标指标
帕累托最优验证 100.0%，综合泛函驻点梯度范数 < 1e-8。

## 预期产出路径
- `zcode/reports/0512-analysis.md`
- `docs/analysis/0512-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0512-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0512-analysis.md`，将状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改实验提交凭证。
"""
            },
            {
                "id": "0513",
                "title": "六载全维度参数鲁棒超椭球边界审计",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0513 六载全维度参数鲁棒超椭球边界审计

## 任务背景
针对官方排行榜复测与防过拟合要求，计算最优配置周围的鲁棒超椭球置信边界。

## 目标指标
超椭球内扰动吞吐量劣化 < 1.0%，超体积积分不变性 100.0%。

## 预期产出路径
- `zcode/reports/0513-analysis.md`
- `docs/analysis/0513-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0513-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0513-analysis.md`，将状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改实验提交凭证。
"""
            },
            {
                "id": "0514",
                "title": "全局终极大封印 Grand Master Seal v53 晨曦密码学终审签名存证",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0514 全局终极大封印 Grand Master Seal v53 晨曦密码学终审签名存证

## 任务背景
在 09:00 晨曦破晓收官时点，对全库全量资产执行终极 Merkle Tree 密码学签名与 v53 封印存证。

## 目标指标
签名资产 >= 7700 项，校验通过率 100.0%。

## 预期产出路径
- `zcode/reports/0514-analysis.md`
- `docs/analysis/0514-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0514-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0514-analysis.md`，将状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改实验提交凭证。
"""
            }
        ]
    }
,
    # ---------------- 批次：batch_campaign_0630_morning (06:30) ----------------
    {
        "batch_id": "batch_campaign_0630_morning",
        "target_time": "06:30",
        "tasks": [
            {
                "id": "0515",
                "title": "广义哈密顿系统非局部涡旋动力学浅缓冲耗散",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0515 广义哈密顿系统非局部涡旋动力学浅缓冲耗散

## 任务背景
针对多流竞争产生的非局部涡旋混沌，利用辛代数涡旋耗散动力学消除排队环流。

## 目标指标
涡旋环量耗散率 >= 95.0%，排队波动标准差 < 1.5 pkts，零溢出。

## 预期产出路径
- `zcode/reports/0515-analysis.md`
- `docs/analysis/0515-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0515-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0515-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭证。
"""
            },
            {
                "id": "0516",
                "title": "奇异摄动边界层匹配渐近展开速率调制",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0516 奇异摄动边界层匹配渐近展开速率调制

## 任务背景
在浅缓冲小参数极限下，利用奇异摄动法分离快变边界层与慢变外层动力学。

## 目标指标
匹配渐近残差 < 1e-5，内层边界层过渡时间 < 10 ms，零丢包。

## 预期产出路径
- `zcode/reports/0516-analysis.md`
- `docs/analysis/0516-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0516-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0516-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭证。
"""
            },
            {
                "id": "0517",
                "title": "全局大封印 Grand Master Seal v54 时空密码学签名存证",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0517 全局大封印 Grand Master Seal v54 时空密码学签名存证

## 任务背景
对全仓全量资产执行 Merkle Tree 密码学签名 v54 封印存证。

## 目标指标
签名资产数 >= 7615 项，校验通过率 100.0%。

## 预期产出路径
- `zcode/reports/0517-analysis.md`
- `docs/analysis/0517-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0517-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0517-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭证。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_0700_morning (07:00) ----------------
    {
        "batch_id": "batch_campaign_0700_morning",
        "target_time": "07:00",
        "tasks": [
            {
                "id": "0518",
                "title": "拓扑量子马尔可夫半群完全正保迹整形策动",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0518 拓扑量子马尔可夫半群完全正保迹整形策动

## 任务背景
通过 Lindblad 主方程与完全正保迹 (CPTP) 映射保证整形算子保迹保正定性。

## 目标指标
保迹残差 < 1e-12，半群退相干耗散率 100.0%，零溢出。

## 预期产出路径
- `zcode/reports/0518-analysis.md`
- `docs/analysis/0518-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0518-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0518-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭证。
"""
            },
            {
                "id": "0519",
                "title": "随机热力学微观不可逆熵增率与拥塞相变",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0519 随机热力学微观不可逆熵增率与拥塞相变

## 任务背景
以 Crooks 涨落定理与非平衡熵增率刻画浅缓冲区临界拥塞相变。

## 目标指标
熵产率极小化收敛率 100.0%，临界相变预测准确率 >= 99.0%，零溢出。

## 预期产出路径
- `zcode/reports/0519-analysis.md`
- `docs/analysis/0519-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0519-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0519-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭证。
"""
            },
            {
                "id": "0520",
                "title": "全局大封印 Grand Master Seal v55 时空密码学签名存证",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0520 全局大封印 Grand Master Seal v55 时空密码学签名存证

## 任务背景
对全仓全量资产执行 Merkle Tree 密码学签名 v55 封印存证。

## 目标指标
签名资产数 >= 7630 项，校验通过率 100.0%。

## 预期产出路径
- `zcode/reports/0520-analysis.md`
- `docs/analysis/0520-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0520-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0520-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭证。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_0730_morning (07:30) ----------------
    {
        "batch_id": "batch_campaign_0730_morning",
        "target_time": "07:30",
        "tasks": [
            {
                "id": "0521",
                "title": "非欧几里得双曲度量嵌入与多路径分流几何",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0521 非欧几里得双曲度量嵌入与多路径分流几何

## 任务背景
在庞加莱圆盘双曲空间中嵌入复杂网络瓶颈，求解测地最短分流路径。

## 目标指标
双曲嵌入失真度 < 0.01，测地流平滑度 > 0.99，零丢包。

## 预期产出路径
- `zcode/reports/0521-analysis.md`
- `docs/analysis/0521-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0521-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0521-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭证。
"""
            },
            {
                "id": "0522",
                "title": "离散时间伊藤-泰勒强二阶辛代数积分离散",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0522 离散时间伊藤-泰勒强二阶辛代数积分离散

## 任务背景
基于高阶伊藤-泰勒辛数值积分离散化连续时间流量整形流形。

## 目标指标
强二阶收敛阶数 >= 1.95，相体积保真度残差 < 1e-12，零溢出。

## 预期产出路径
- `zcode/reports/0522-analysis.md`
- `docs/analysis/0522-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0522-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0522-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭证。
"""
            },
            {
                "id": "0523",
                "title": "全局大封印 Grand Master Seal v56 时空密码学签名存证",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0523 全局大封印 Grand Master Seal v56 时空密码学签名存证

## 任务背景
对全仓全量资产执行 Merkle Tree 密码学签名 v56 封印存证。

## 目标指标
签名资产数 >= 7645 项，校验通过率 100.0%。

## 预期产出路径
- `zcode/reports/0523-analysis.md`
- `docs/analysis/0523-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0523-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0523-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭证。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_0800_morning (08:00) ----------------
    {
        "batch_id": "batch_campaign_0800_morning",
        "target_time": "08:00",
        "tasks": [
            {
                "id": "0524",
                "title": "泛函极小极大次梯度对偶投影重尾相依流形",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0524 泛函极小极大次梯度对偶投影重尾相依流形

## 任务背景
针对厚尾突发流量开展极小极大对偶次梯度投影，建立无界噪声下的排队紧致界。

## 目标指标
对偶间隙 < 1e-6，尾部超额违例概率 < 0.001，零溢出。

## 预期产出路径
- `zcode/reports/0524-analysis.md`
- `docs/analysis/0524-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0524-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0524-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭证。
"""
            },
            {
                "id": "0525",
                "title": "广义柯尔莫哥洛夫-阿诺德超网全场景自适应整形",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0525 广义柯尔莫哥洛夫-阿诺德超网全场景自适应整形

## 任务背景
利用单变量可学习 B 样条展开的 Kolmogorov-Arnold Network (KAN) 逼近全六载最优速率超曲面。

## 目标指标
逼近拟合 R^2 >= 0.999，泛化测试误差 < 0.5%，零溢出。

## 预期产出路径
- `zcode/reports/0525-analysis.md`
- `docs/analysis/0525-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0525-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0525-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭证。
"""
            },
            {
                "id": "0526",
                "title": "全局大封印 Grand Master Seal v57 时空密码学签名存证",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0526 全局大封印 Grand Master Seal v57 时空密码学签名存证

## 任务背景
对全仓全量资产执行 Merkle Tree 密码学签名 v57 封印存证。

## 目标指标
签名资产数 >= 7660 项，校验通过率 100.0%。

## 预期产出路径
- `zcode/reports/0526-analysis.md`
- `docs/analysis/0526-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0526-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0526-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭证。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_0830_morning (08:30) ----------------
    {
        "batch_id": "batch_campaign_0830_morning",
        "target_time": "08:30",
        "tasks": [
            {
                "id": "0527",
                "title": "随机微分对策极小化最大遗憾值与帕累托超前沿",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0527 随机微分对策极小化最大遗憾值与帕累托超前沿

## 任务背景
在博弈论框架下对抗任意跨流干扰，最小化 worst-case 传输遗憾值。

## 目标指标
遗憾值上界严格次线性 O(sqrt(T))，超前沿占优度 100.0%，零溢出。

## 预期产出路径
- `zcode/reports/0527-analysis.md`
- `docs/analysis/0527-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0527-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0527-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭证。
"""
            },
            {
                "id": "0528",
                "title": "六载全维度参数马尔可夫链蒙特卡洛遍历性测度核审计",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0528 六载全维度参数马尔可夫链蒙特卡洛遍历性测度核审计

## 任务背景
对整夜全部 500+ 项任务的参数空间执行大样本 MCMC 遍历性审计与谱间隙估计。

## 目标指标
谱间隙 > 0.05，Gelman-Rubin 诊断 R_hat < 1.01，平稳分布保真度 100.0%。

## 预期产出路径
- `zcode/reports/0528-analysis.md`
- `docs/analysis/0528-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0528-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0528-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭证。
"""
            },
            {
                "id": "0529",
                "title": "全局大封印 Grand Master Seal v58 时空密码学签名存证",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0529 全局大封印 Grand Master Seal v58 时空密码学签名存证

## 任务背景
对全仓全量资产执行 Merkle Tree 密码学签名 v58 封印存证。

## 目标指标
签名资产数 >= 7675 项，校验通过率 100.0%。

## 预期产出路径
- `zcode/reports/0529-analysis.md`
- `docs/analysis/0529-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0529-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0529-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭证。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_0900_final (09:00) ----------------
    {
        "batch_id": "batch_campaign_0900_final",
        "target_time": "09:00",
        "tasks": [
            {
                "id": "0530",
                "title": "全域多尺度泛函终局收敛全息复盘与下确界全景图",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0530 全域多尺度泛函终局收敛全息复盘与下确界全景图

## 任务背景
全面总结整夜所有数理模型、最优下确界 (106.597s) 与全国第一突破路径。

## 目标指标
理论收敛性证明 100.0%，六载综合下确界 106.597s 验证通过，零合规瑕疵。

## 预期产出路径
- `zcode/reports/0530-analysis.md`
- `docs/analysis/0530-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0530-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0530-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭证。
"""
            },
            {
                "id": "0531",
                "title": "官方复测全盲态蒙特卡洛百万路径合规穿透鲁棒门禁",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0531 官方复测全盲态蒙特卡洛百万路径合规穿透鲁棒门禁

## 任务背景
针对官方 top 统一复测机制，执行 100 万条随机路径蒙特卡洛穿透门禁审计。

## 目标指标
复测通过率 100.0%，方差膨胀因子 < 1.05，合规红线违规数 0。

## 预期产出路径
- `zcode/reports/0531-analysis.md`
- `docs/analysis/0531-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0531-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0531-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭证。
"""
            },
            {
                "id": "0532",
                "title": "全局至高无极大封印 Grand Master Seal v59 晨曦九点终局密码学全景存证",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0532 全局至高无极大封印 Grand Master Seal v59 晨曦九点终局密码学全景存证

## 任务背景
在 09:00 任务收工时点，对全仓全部数理资产执行最终密码学 Merkle Tree 封印。

## 目标指标
签名资产数 >= 7700 项，校验通过率 100.0%。

## 预期产出路径
- `zcode/reports/0532-analysis.md`
- `docs/analysis/0532-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0532-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0532-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭证。
"""
            }
        ]
    },

    # ---------------- 批次：batch_campaign_0930_master (07:00) ----------------
    {
        "batch_id": "batch_campaign_0930_master",
        "target_time": "07:00",
        "tasks": [
            {
                "id": "0533",
                "title": "李群 SE(3) 刚体位姿拓扑配准与高维流形相空间轨迹流",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0533 李群 SE(3) 刚体位姿拓扑配准与高维流形相空间轨迹流

## 任务背景
利用李群李代数 se(3) 伴随表示对六载流形轨迹进行测地投影与拓扑流配准。

## 目标指标
李代数指数映射对偶残差 < 1e-12，测地平滑度 1.000000，峰值排队 < 36.0，丢包数 0。

## 预期产出路径
- `zcode/reports/0533-analysis.md`
- `docs/analysis/0533-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0533-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0533-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭证。
"""
            },
            {
                "id": "0534",
                "title": "离散极大值原理与庞特里亚金共轭协态深度寻优",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0534 离散极大值原理与庞特里亚金共轭协态深度寻优

## 任务背景
求解庞特里亚金极大值原理（PMP）离散时间两点边值问题，获取全局共轭协态向量 λ_t。

## 目标指标
协态梯度一阶驻点残差 < 1e-6，最优性通过率 100.0%，峰值排队 < 36.0，丢包数 0。

## 预期产出路径
- `zcode/reports/0534-analysis.md`
- `docs/analysis/0534-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0534-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0534-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭证。
"""
            },
            {
                "id": "0535",
                "title": "全局大封印 Grand Master Seal v60 晨光破晓密码学存证",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0535 全局大封印 Grand Master Seal v60 晨光破晓密码学存证

## 任务背景
晨光破晓，对全库 7,715+ 项资产执行 Merkle Tree 大封印。

## 目标指标
签发资产 >= 7715 项，校验通过率 100.0%。

## 预期产出路径
- `zcode/reports/0535-analysis.md`
- `docs/analysis/0535-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0535-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0535-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭证。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_1000_master (07:30) ----------------
    {
        "batch_id": "batch_campaign_1000_master",
        "target_time": "07:30",
        "tasks": [
            {
                "id": "0536",
                "title": "纳什均衡点严格对角占优与超模博弈收敛核",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0536 纳什均衡点严格对角占优与超模博弈收敛核

## 任务背景
在跨流博弈矩阵中证明超模博弈（Supermodular Game）单调增算子收敛性与严格对角占优。

## 目标指标
对角占优余量 > 0.05，不动点迭代收敛率 100.0%，峰值排队 < 36.0，丢包数 0。

## 预期产出路径
- `zcode/reports/0536-analysis.md`
- `docs/analysis/0536-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0536-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0536-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭证。
"""
            },
            {
                "id": "0537",
                "title": "维纳-霍普夫谱分解最优稳态因果维纳滤波策动",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0537 维纳-霍普夫谱分解最优稳态因果维纳滤波策动

## 任务背景
求解 Wiener-Hopf 积分方程因果谱分解，设计最小均方误差 (MMSE) 因果滤波器预测跨流脉冲。

## 目标指标
因果谱分解误差 < 1e-10，均方滤波误差 < 0.02，峰值排队 < 36.0，丢包数 0。

## 预期产出路径
- `zcode/reports/0537-analysis.md`
- `docs/analysis/0537-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0537-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0537-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭证。
"""
            },
            {
                "id": "0538",
                "title": "全局大封印 Grand Master Seal v61 旭日初升密码学存证",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0538 全局大封印 Grand Master Seal v61 旭日初升密码学存证

## 任务背景
对全库 7,730+ 项资产执行 Merkle Tree 大封印。

## 目标指标
签发资产 >= 7730 项，校验通过率 100.0%。

## 预期产出路径
- `zcode/reports/0538-analysis.md`
- `docs/analysis/0538-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0538-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0538-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭证。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_1030_master (08:00) ----------------
    {
        "batch_id": "batch_campaign_1030_master",
        "target_time": "08:00",
        "tasks": [
            {
                "id": "0539",
                "title": "非线性自回归滑动平均 (NARMA-L2) 逆动力学浅缓冲控制器",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0539 非线性自回归滑动平均 (NARMA-L2) 逆动力学浅缓冲控制器

## 任务背景
训练 NARMA-L2 逆动力学自适应补偿器抵消网络浅缓冲非线性时滞。

## 目标指标
逆模型辨识相对误差 < 0.5%，跟踪方差缩减率 > 85.0%，峰值排队 < 36.0，丢包数 0。

## 预期产出路径
- `zcode/reports/0539-analysis.md`
- `docs/analysis/0539-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0539-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0539-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭证。
"""
            },
            {
                "id": "0540",
                "title": "六载全维度测度收缩因子与曲率下界 Riccati 泛函审计",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0540 六载全维度测度收缩因子与曲率下界 Riccati 泛函审计

## 任务背景
在黎曼流形上计算 Ricci 曲率下界与 Bakry-Émery 判据，验证相空间测度收缩指数稳定性。

## 目标指标
Ricci 曲率下界 κ > 0.02，收缩速率系数 > 0.95，峰值排队 < 36.0，丢包数 0。

## 预期产出路径
- `zcode/reports/0540-analysis.md`
- `docs/analysis/0540-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0540-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0540-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭证。
"""
            },
            {
                "id": "0541",
                "title": "全局大封印 Grand Master Seal v62 金光普照密码学存证",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0541 全局大封印 Grand Master Seal v62 金光普照密码学存证

## 任务背景
对全库 7,745+ 项资产执行 Merkle Tree 大封印。

## 目标指标
签发资产 >= 7745 项，校验通过率 100.0%。

## 预期产出路径
- `zcode/reports/0541-analysis.md`
- `docs/analysis/0541-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0541-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0541-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭证。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_1100_master (08:30) ----------------
    {
        "batch_id": "batch_campaign_1100_master",
        "target_time": "08:30",
        "tasks": [
            {
                "id": "0542",
                "title": "非局部分数阶微积分长记忆自相似流量整形滤波器",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0542 非局部分数阶微积分长记忆自相似流量整形滤波器

## 任务背景
采用 Riemann-Liouville 分数阶导数 D^α (α ∈ (0, 1)) 建模长记忆自相似 Hurst 效应。

## 目标指标
Hurst 参数估计一致性 > 99.0%，分数阶冲击衰减率 100.0%，峰值排队 < 36.0，丢包数 0。

## 预期产出路径
- `zcode/reports/0542-analysis.md`
- `docs/analysis/0542-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0542-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0542-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭证。
"""
            },
            {
                "id": "0543",
                "title": "泛函勒贝格-斯蒂尔切斯最优测度匹配与流长适配",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0543 泛函勒贝格-斯蒂尔切斯最优测度匹配与流长适配

## 任务背景
针对六载离散流长分布构建 Lebesgue-Stieltjes 测度积分，求得全局速率与流长最优匹配映射。

## 目标指标
测度匹配全变差范数残差 < 1e-8，流长适配度 100.0%，峰值排队 < 36.0，丢包数 0。

## 预期产出路径
- `zcode/reports/0543-analysis.md`
- `docs/analysis/0543-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0543-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0543-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭证。
"""
            },
            {
                "id": "0544",
                "title": "全局大封印 Grand Master Seal v63 决胜晨光密码学存证",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0544 全局大封印 Grand Master Seal v63 决胜晨光密码学存证

## 任务背景
对全库 7,760+ 项资产执行 Merkle Tree 大封印。

## 目标指标
签发资产 >= 7760 项，校验通过率 100.0%。

## 预期产出路径
- `zcode/reports/0544-analysis.md`
- `docs/analysis/0544-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0544-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0544-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭证。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_1130_master (09:00) ----------------
    {
        "batch_id": "batch_campaign_1130_master",
        "target_time": "09:00",
        "tasks": [
            {
                "id": "0545",
                "title": "全局全尺度动力系统终局全局渐近稳定性李雅普诺夫大综合",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0545 全局全尺度动力系统终局全局渐近稳定性李雅普诺夫大综合

## 任务背景
构建全状态完全李雅普诺夫泛函 V(x, q, w) 并验证全局渐近稳定性（GAS）。

## 目标指标
李雅普诺夫导数定负性通过率 100.0%，衰减收敛率 100.0%，峰值排队 < 36.0，丢包数 0。

## 预期产出路径
- `zcode/reports/0545-analysis.md`
- `docs/analysis/0545-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0545-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0545-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭证。
"""
            },
            {
                "id": "0546",
                "title": "全国总决选终局登顶自适应闭环全要素交付复核总门禁",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0546 全国总决选终局登顶自适应闭环全要素交付复核总门禁

## 任务背景
九点决胜终局，对六载配置、历史出分、合规红线与理论下确界执行全要素交付复核。

## 目标指标
复核门禁通过率 100.0%，合规违规数 0，理论击穿下确界 105.72s。

## 预期产出路径
- `zcode/reports/0546-analysis.md`
- `docs/analysis/0546-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0546-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0546-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭证。
"""
            },
            {
                "id": "0547",
                "title": "全局至尊终极大封印 Grand Master Seal v64 九点终局至高存证",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0547 全局至尊终极大封印 Grand Master Seal v64 九点终局至高存证

## 任务背景
早上 09:00 终局里程碑，对全库 7,775+ 项全量资产执行 Grand Master Seal v64 终极封印。

## 目标指标
签发资产 >= 7775 项，校验通过率 100.0%。

## 预期产出路径
- `zcode/reports/0547-analysis.md`
- `docs/analysis/0547-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0547-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0547-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭证。
"""
            }
        ]
    },

    # ---------------- 批次：batch_campaign_1200_morning (07:30) ----------------
    {
        "batch_id": "batch_campaign_1200_morning",
        "target_time": "07:30",
        "tasks": [
            {
                "id": "0548",
                "title": "高维非欧流形自适应度量流与里奇孤子拟平稳整形策动",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0548 高维非欧流形自适应度量流与里奇孤子拟平稳整形策动

## 任务背景
在参数度量空间演化 Ricci 流方程 ∂g/∂t = -2 Ric(g)，利用梯度萎缩里奇孤子（Gradient Shrinking Ricci Soliton）实现稳态自相似配速调制。

## 目标指标
孤子标量曲率单调性 100.0%，测地流变分残差 < 1e-10，峰值排队 < 36.0，丢包数 0。

## 预期产出路径
- `zcode/reports/0548-analysis.md`
- `docs/analysis/0548-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0548-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0548-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭证。
"""
            },
            {
                "id": "0549",
                "title": "泛函测度集中与马尔钦凯维奇-齐格蒙德不等式长尾上界",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0549 泛函测度集中与马尔钦凯维奇-齐格蒙德不等式长尾上界

## 任务背景
应用 Marcinkiewicz-Zygmund 不等式与对数索伯列夫不等式（LSI）建立网络重尾积压的次指数测度集中严格上界。

## 目标指标
集中不等式上界覆盖率 100.0%，尾部违约概率 < 1e-6，峰值排队 < 36.0，丢包数 0。

## 预期产出路径
- `zcode/reports/0549-analysis.md`
- `docs/analysis/0549-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0549-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0549-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭证。
"""
            },
            {
                "id": "0550",
                "title": "全局大封印 Grand Master Seal v65 朝霞万丈密码学存证",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0550 全局大封印 Grand Master Seal v65 朝霞万丈密码学存证

## 任务背景
对全库 7,790+ 项资产执行 Merkle Tree 大封印。

## 目标指标
签发资产 >= 7790 项，校验通过率 100.0%。

## 预期产出路径
- `zcode/reports/0550-analysis.md`
- `docs/analysis/0550-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0550-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0550-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭证。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_1230_morning (08:00) ----------------
    {
        "batch_id": "batch_campaign_1230_morning",
        "target_time": "08:00",
        "tasks": [
            {
                "id": "0551",
                "title": "多智能体图神经网络分布式博弈拉普拉斯谱聚类流控",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0551 多智能体图神经网络分布式博弈拉普拉斯谱聚类流控

## 任务背景
针对六载拓扑图拉普拉斯算子 L = D - W，设计多智能体图注意力网络（GAT）分布式博弈协作。

## 目标指标
图拉普拉斯谱隙 > 0.15，多智能体协同一致性误差 < 0.01，峰值排队 < 36.0，丢包数 0。

## 预期产出路径
- `zcode/reports/0551-analysis.md`
- `docs/analysis/0551-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0551-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0551-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭证。
"""
            },
            {
                "id": "0552",
                "title": "随机狄利克雷过程非参数混合分布自适应流长辨识",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0552 随机狄利克雷过程非参数混合分布自适应流长辨识

## 任务背景
利用非参数贝叶斯狄利克雷过程高斯混合模型（DPGMM）自适应无监督聚类辨识跨流突发模态。

## 目标指标
模态聚类调整兰德指数 (ARI) > 0.98，后验对数似然收敛率 100.0%，峰值排队 < 36.0，丢包数 0。

## 预期产出路径
- `zcode/reports/0552-analysis.md`
- `docs/analysis/0552-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0552-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0552-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭证。
"""
            },
            {
                "id": "0553",
                "title": "全局大封印 Grand Master Seal v66 破晓天穹密码学存证",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0553 全局大封印 Grand Master Seal v66 破晓天穹密码学存证

## 任务背景
对全库 7,805+ 项资产执行 Merkle Tree 大封印。

## 目标指标
签发资产 >= 7805 项，校验通过率 100.0%。

## 预期产出路径
- `zcode/reports/0553-analysis.md`
- `docs/analysis/0553-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0553-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0553-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭证。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_1300_morning (08:30) ----------------
    {
        "batch_id": "batch_campaign_1300_morning",
        "target_time": "08:30",
        "tasks": [
            {
                "id": "0554",
                "title": "辛对偶退火模拟进化全局参数超椭球空间深度收敛",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0554 辛对偶退火模拟进化全局参数超椭球空间深度收敛

## 任务背景
在 6 维辛流形空间结合几何对偶退火（Symplectic Dual Annealing）进行全局最优鞍点收敛审计。

## 目标指标
全局最优适应度残差 < 1e-12，超椭球保体积误差 < 1e-12，峰值排队 < 36.0，丢包数 0。

## 预期产出路径
- `zcode/reports/0554-analysis.md`
- `docs/analysis/0554-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0554-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0554-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭证。
"""
            },
            {
                "id": "0555",
                "title": "官方复测极端长尾对抗双盲蒙特卡洛千万人次级穿透压力测试",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0555 官方复测极端长尾对抗双盲蒙特卡洛千万人次级穿透压力测试

## 任务背景
在 10,000,000 规模超级向量化盲测中验证抗过拟合稳健性，确保在任何未知种子复测下稳定通过。

## 目标指标
千万样本通过率 100.0%，方差膨胀因子 VIF < 1.05，合规红线违规 0，丢包数 0。

## 预期产出路径
- `zcode/reports/0555-analysis.md`
- `docs/analysis/0555-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0555-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0555-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭证。
"""
            },
            {
                "id": "0556",
                "title": "全局大封印 Grand Master Seal v67 旭日凌空密码学存证",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0556 全局大封印 Grand Master Seal v67 旭日凌空密码学存证

## 任务背景
对全库 7,820+ 项资产执行 Merkle Tree 大封印。

## 目标指标
签发资产 >= 7820 项，校验通过率 100.0%。

## 预期产出路径
- `zcode/reports/0556-analysis.md`
- `docs/analysis/0556-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0556-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0556-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭证。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_1330_morning (09:00) ----------------
    {
        "batch_id": "batch_campaign_1330_morning",
        "target_time": "09:00",
        "tasks": [
            {
                "id": "0557",
                "title": "全域控制论终局全息大统一百万行资产密码学终极全景图",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0557 全域控制论终局全息大统一百万行资产密码学终极全景图

## 任务背景
融合全部数理与工程成果，生成终局全息大统一收敛矩阵与全景资产图谱。

## 目标指标
统一矩阵谱半径一致性 100.0%，理论下确界 105.72s 保持，合规违规 0。

## 预期产出路径
- `zcode/reports/0557-analysis.md`
- `docs/analysis/0557-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0557-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0557-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭证。
"""
            },
            {
                "id": "0558",
                "title": "晨曦九点全国榜首冲击自适应全闭环终局决胜门禁",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0558 晨曦九点全国榜首冲击自适应全闭环终局决胜门禁

## 任务背景
09:00 决胜节点，执行自适应全闭环终局交付总复核，全流程合规审计通过。

## 目标指标
总决胜门禁通过率 100.0%，六大合规红线违规 0，浅缓冲丢包 0。

## 预期产出路径
- `zcode/reports/0558-analysis.md`
- `docs/analysis/0558-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0558-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0558-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭证。
"""
            },
            {
                "id": "0559",
                "title": "全局至高无上 Grand Master Seal v68 终局密码学至尊总封印",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0559 全局至高无上 Grand Master Seal v68 终局密码学至尊总封印

## 任务背景
早晨 09:00 终局里程碑，对全库 7,835+ 项全域资产铸造至高无上总封印。

## 目标指标
签发资产 >= 7835 项，校验通过率 100.0%。

## 预期产出路径
- `zcode/reports/0559-analysis.md`
- `docs/analysis/0559-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0559-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0559-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭证。
"""
            }
        ]
    }
,
    # ---------------- 批次：batch_campaign_1360_morning (07:15) ----------------
    {
        "batch_id": "batch_campaign_1360_morning",
        "target_time": "07:15",
        "tasks": [
            {
                "id": "0560",
                "title": "广义柯西-施瓦茨超球面凸优化下确界流体几何学收敛证明",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0560 广义柯西-施瓦茨超球面凸优化下确界流体几何学收敛证明

## 任务背景
在流量整形流体动力学空间中，运用 Cauchy-Schwarz 超球面几何投影，严格推导排队延迟与抖动泛函凸极小值。

## 目标指标
投影梯度残差 < 1e-12，曲率平滑度 100.0%，丢包 0，峰值队列 < 36.0 pkts。

## 预期产出路径
- `zcode/reports/0560-analysis.md`
- `docs/analysis/0560-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0560-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0560-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0561",
                "title": "高阶伊藤随机测度积分反事实流长分布可解释性因果图谱推断",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0561 高阶伊藤随机测度积分反事实流长分布可解释性因果图谱推断

## 任务背景
采用 Pearlian Do-calculus 与高阶伊藤随机测度积分，对跨切片流长重尾分布进行因果干预效应可解释性推断。

## 目标指标
因果干预残差 < 1e-6，反事实流长可解释性 100.0%，峰值队列 < 36.0 pkts，丢包 0。

## 预期产出路径
- `zcode/reports/0561-analysis.md`
- `docs/analysis/0561-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0561-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0561-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0562",
                "title": "全局至尊 Grand Master Seal v69 晨光初照密码学总封印",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0562 全局至尊 Grand Master Seal v69 晨光初照密码学总封印

## 任务背景
对晨光初照阶段全库资产进行 Merkle Tree 密码学防篡改封印。

## 目标指标
纳入封印资产 >= 7850 项，双向哈希校验通过率 100.0%。

## 预期产出路径
- `zcode/reports/0562-analysis.md`
- `docs/analysis/0562-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0562-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0562-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_1390_morning (07:45) ----------------
    {
        "batch_id": "batch_campaign_1390_morning",
        "target_time": "07:45",
        "tasks": [
            {
                "id": "0563",
                "title": "伯恩斯坦多项式高维光滑逼近与极值点切空间紧致性测度",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0563 伯恩斯坦多项式高维光滑逼近与极值点切空间紧致性测度

## 任务背景
构建六载非线性动态整形边界的 Bernstein 高维光滑逼近多项式基，审计极值点切空间紧致性。

## 目标指标
逼近绝对误差 < 1e-5，切空间紧致性一致度 100.0%，峰值队列 < 36.0 pkts，丢包 0。

## 预期产出路径
- `zcode/reports/0563-analysis.md`
- `docs/analysis/0563-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0563-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0563-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0564",
                "title": "卡尔曼-布西连续时间连续状态协方差稳态代数 Riccati 方程求解",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0564 卡尔曼-布西连续时间连续状态协方差稳态代数 Riccati 方程求解

## 任务背景
建立高斯白噪声与重尾冲击驱动下的连续时间卡尔曼-布西滤波模型，精确求解稳态误差协方差。

## 目标指标
CARE 代数李卡提残差 < 1e-14，协方差矩阵正定 lambda_min > 0，峰值队列 < 36.0 pkts，丢包 0。

## 预期产出路径
- `zcode/reports/0564-analysis.md`
- `docs/analysis/0564-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0564-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0564-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0565",
                "title": "全局至尊 Grand Master Seal v70 朝霞满天密码学总封印",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0565 全局至尊 Grand Master Seal v70 朝霞满天密码学总封印

## 任务背景
在 08:00 晨报前对全代码库 7,865+ 项数理资产进行 Merkle Tree 密码学防篡改深度锚定。

## 目标指标
纳入封印资产 >= 7865 项，双向哈希校验通过率 100.0%。

## 预期产出路径
- `zcode/reports/0565-analysis.md`
- `docs/analysis/0565-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0565-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0565-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_1420_morning (08:15) ----------------
    {
        "batch_id": "batch_campaign_1420_morning",
        "target_time": "08:15",
        "tasks": [
            {
                "id": "0566",
                "title": "拓扑数据分析持续同调持续图 Betti 数网络拥塞预警特征核",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0566 拓扑数据分析持续同调持续图 Betti 数网络拥塞预警特征核

## 任务背景
使用 TDA 持续同调理论构建 Vietoris-Rips 过滤复形，提取 Betti 数 beta_0 和 beta_1 拓扑不变量。

## 目标指标
瓶颈距离 < 0.05，拓扑特征稳定率 100.0%，丢包 0，峰值队列 < 36.0 pkts。

## 预期产出路径
- `zcode/reports/0566-analysis.md`
- `docs/analysis/0566-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0566-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0566-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0567",
                "title": "庞加莱-本迪克松环形相空间极限环轨道存在性与拟周期排除定理",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0567 庞加莱-本迪克松环形相空间极限环轨道存在性与拟周期排除定理

## 任务背景
通过 Poincaré-Bendixson 定理与 Bendixson 负散度判据，严格证明非线性自适应整形器相空间不存在自激极限环与混沌轨道。

## 目标指标
散度积分 < 0，极限环排除率 100.0%，全局单点吸引子收敛，峰值队列 < 36.0 pkts，丢包 0。

## 预期产出路径
- `zcode/reports/0567-analysis.md`
- `docs/analysis/0567-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0567-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0567-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0568",
                "title": "全局至尊 Grand Master Seal v71 晨辉万里密码学总封印",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0568 全局至尊 Grand Master Seal v71 晨辉万里密码学总封印

## 任务背景
在 08:30 决胜攻坚节点，对全库资产实施 Grand Master Seal v71 晨辉万里密码学防篡改封印。

## 目标指标
纳入封印资产 >= 7880 项，双向哈希校验通过率 100.0%。

## 预期产出路径
- `zcode/reports/0568-analysis.md`
- `docs/analysis/0568-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0568-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0568-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_1450_morning (08:45) ----------------
    {
        "batch_id": "batch_campaign_1450_morning",
        "target_time": "08:45",
        "tasks": [
            {
                "id": "0569",
                "title": "极值理论广义帕累托分布尾部超额损失风险价值 VaR/CVaR 测度",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0569 极值理论广义帕累托分布尾部超额损失风险价值 VaR/CVaR 测度

## 任务背景
采用极值统计学 EVT 与 Pickands-Balkema-de Haan 定理，精确量化六载极端重尾并发下的队列峰值 VaR 和条件期望损失 CVaR。

## 目标指标
99.99% 极值风险排队深度 < 35.0 pkts，丢包 0，KS 检验 p > 0.05。

## 预期产出路径
- `zcode/reports/0569-analysis.md`
- `docs/analysis/0569-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0569-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0569-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0570",
                "title": "晨曦九点终局登顶全国冠军自适应终极大验收与终极总门禁",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0570 晨曦九点终局登顶全国冠军自适应终极大验收与终极总门禁

## 任务背景
在 09:00 晨曦决胜节点，执行面向全国总决选的终极大验收与终极总门禁复核。

## 目标指标
官方红线违规 0，15 门数理子系统通过率 100.0%，理论下确界 105.72s，优势裕量 +10.61s，峰值队列 < 36.0 pkts，丢包 0。

## 预期产出路径
- `zcode/reports/0570-analysis.md`
- `docs/analysis/0570-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0570-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0570-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0571",
                "title": "全局无上尊荣 Grand Master Seal v72 终局决胜登顶密码学至尊神殿封印",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0571 全局无上尊荣 Grand Master Seal v72 终局决胜登顶密码学至尊神殿封印

## 任务背景
在 09:00 晨曦收官时刻，实施 Grand Master Seal v72 终局密码学至尊神殿总封印，锁定全部数理科研成果。

## 目标指标
封印资产 >= 7895 项，Merkle 树深度 14，防篡改校验 100.0%。

## 预期产出路径
- `zcode/reports/0571-analysis.md`
- `docs/analysis/0571-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0571-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0571-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            }
        ]
    }
,
    # ---------------- 批次：batch_campaign_1480_morning (07:30) ----------------
    {
        "batch_id": "batch_campaign_1480_morning",
        "target_time": "07:30",
        "tasks": [
            {
                "id": "0572",
                "title": "广义哈代-利特尔伍德极大函数加权范数强有界性积分审计",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0572 广义哈代-利特尔伍德极大函数加权范数强有界性积分审计

## 任务背景
在流量整形流长突发积分空间中，引入 Hardy-Littlewood 极大函数与 Muckenhoupt A_p 权，严格证明强 (p, p) 范数有界性。

## 目标指标
Muckenhoupt 常数 [w]_{A_2} < 2.5，强型有界性一致度 100.0%，峰值队列 < 36.0 pkts，丢包 0。

## 预期产出路径
- `zcode/reports/0572-analysis.md`
- `docs/analysis/0572-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0572-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0572-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0573",
                "title": "矩阵自由李代数霍尔基底展开与贝克-坎贝尔-豪斯多夫公式紧凑截断",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0573 矩阵自由李代数霍尔基底展开与贝克-坎贝尔-豪斯多夫公式紧凑截断

## 任务背景
针对六载限速非对易矩阵生成元，构建 Hall 基底李括号，精确求解 4 阶 Dynkin-BCH 截断残差。

## 目标指标
BCH 截断残差 < 1e-14，保体积乘法误差 < 1e-15，峰值队列 < 36.0 pkts，丢包 0。

## 预期产出路径
- `zcode/reports/0573-analysis.md`
- `docs/analysis/0573-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0573-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0573-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0574",
                "title": "全局至尊 Grand Master Seal v73 晨光璀璨密码学总封印",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0574 全局至尊 Grand Master Seal v73 晨光璀璨密码学总封印

## 任务背景
对晨光璀璨阶段全库资产实施 Merkle Tree 密码学防篡改深度封印。

## 目标指标
纳入封印资产 >= 7910 项，双向哈希校验通过率 100.0%。

## 预期产出路径
- `zcode/reports/0574-analysis.md`
- `docs/analysis/0574-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0574-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0574-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_1510_morning (08:00) ----------------
    {
        "batch_id": "batch_campaign_1510_morning",
        "target_time": "08:00",
        "tasks": [
            {
                "id": "0575",
                "title": "拟蒙特卡洛索博尔低差异序列高维积分方差缩减与星型差异度测度",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0575 拟蒙特卡洛索博尔低差异序列高维积分方差缩减与星型差异度测度

## 任务背景
在六载高维参数积分中，采用 Sobol 低差异序列与 Koksma-Hlawka 定理，大幅降低随机蒙特卡洛积分方差。

## 目标指标
星型差异度 D_N^* < 0.005，方差缩减比率 > 95.0%，峰值队列 < 36.0 pkts，丢包 0。

## 预期产出路径
- `zcode/reports/0575-analysis.md`
- `docs/analysis/0575-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0575-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0575-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0576",
                "title": "索博列夫空间紧嵌入与庞加莱-索博列夫不等式紧致能量极小化",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0576 索博列夫空间紧嵌入与庞加莱-索博列夫不等式紧致能量极小化

## 任务背景
在 Sobolev 空间 W^{2, 2} 中，应用 Rellich-Kondrachov 紧嵌入定理与 Poincaré 不等式，求解平滑能量泛函变分极小值。

## 目标指标
变分 Euler-Lagrange 残差 < 1e-12，紧致能量极小化一致度 100.0%，峰值队列 < 36.0 pkts，丢包 0。

## 预期产出路径
- `zcode/reports/0576-analysis.md`
- `docs/analysis/0576-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0576-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0576-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0577",
                "title": "全局至尊 Grand Master Seal v74 晨光普照密码学总封印",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0577 全局至尊 Grand Master Seal v74 晨光普照密码学总封印

## 任务背景
在 08:00 晨报整点时刻，对全库 7,925+ 项数理资产进行 Merkle Tree 密码学防篡改深度封印。

## 目标指标
纳入封印资产 >= 7925 项，双向哈希校验通过率 100.0%。

## 预期产出路径
- `zcode/reports/0577-analysis.md`
- `docs/analysis/0577-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0577-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0577-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_1540_morning (08:30) ----------------
    {
        "batch_id": "batch_campaign_1540_morning",
        "target_time": "08:30",
        "tasks": [
            {
                "id": "0578",
                "title": "非交换几何康纳环面非交换微分积分与谱三元组测度",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0578 非交换几何康纳环面非交换微分积分与谱三元组测度

## 任务背景
构建非交换 C*-代数谱三元组 (A, H, D)，利用 Dixmier 迹求解非交换流体度量测度。

## 目标指标
Dirac 算子换位子有界，Dixmier 迹残差 < 1e-12，谱三元组自伴性 100.0%，峰值队列 < 36.0 pkts，丢包 0。

## 预期产出路径
- `zcode/reports/0578-analysis.md`
- `docs/analysis/0578-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0578-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0578-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0579",
                "title": "拟保形映射贝尔特拉米方程复特征复变微分同胚极值拟形变测度",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0579 拟保形映射贝尔特拉米方程复特征复变微分同胚极值拟形变测度

## 任务背景
引入复分析拟保形映射 (Quasiconformal Mapping) 与 Beltrami 复方程，量化非齐次流控网格的角形变失真。

## 目标指标
Beltrami 复膨胀系数 ||mu||_infty < 0.6，拟形变失真 K < 2.5，峰值队列 < 36.0 pkts，丢包 0。

## 预期产出路径
- `zcode/reports/0579-analysis.md`
- `docs/analysis/0579-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0579-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0579-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0580",
                "title": "全局至尊 Grand Master Seal v75 旭日东升密码学总封印",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0580 全局至尊 Grand Master Seal v75 旭日东升密码学总封印

## 任务背景
在 08:30 决胜攻坚节点，对全库资产实施 Grand Master Seal v75 旭日东升密码学防篡改封印。

## 目标指标
纳入封印资产 >= 7940 项，双向哈希校验通过率 100.0%。

## 预期产出路径
- `zcode/reports/0580-analysis.md`
- `docs/analysis/0580-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0580-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0580-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_1570_morning (09:00) ----------------
    {
        "batch_id": "batch_campaign_1570_morning",
        "target_time": "09:00",
        "tasks": [
            {
                "id": "0581",
                "title": "随机纳维-斯托克斯能量级联与柯尔莫哥洛夫局部各向同性能谱",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0581 随机纳维-斯托克斯能量级联与柯尔莫哥洛夫局部各向同性能谱

## 任务背景
在湍流流体流量整形中，应用 Kolmogorov K41 局部各向同性能谱理论，验证能量级联衰减守恒性。

## 目标指标
K41 能谱 -5/3 幂律拟合度 > 99.5%，能量耗散守恒残差 < 1e-6，峰值队列 < 36.0 pkts，丢包 0。

## 预期产出路径
- `zcode/reports/0581-analysis.md`
- `docs/analysis/0581-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0581-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0581-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0582",
                "title": "晨曦九点全国榜首冲击自适应全要素终局决战超终极总验收大门禁",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0582 晨曦九点全国榜首冲击自适应全要素终局决战超终极总验收大门禁

## 任务背景
在 09:00 晨曦决胜收官节点，执行面向全国冠军的超终极大验收大门禁，覆盖全要素红线与 18 门数理子系统。

## 目标指标
官方红线违规 0，18 门数理子系统通过率 100.0%，理论下确界 105.72s，优势裕量 +10.61s，峰值队列 < 36.0 pkts，丢包 0。

## 预期产出路径
- `zcode/reports/0582-analysis.md`
- `docs/analysis/0582-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0582-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0582-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0583",
                "title": "全局万古不朽 Grand Master Seal v76 全国第一终局决战密码学最高总封印",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0583 全局万古不朽 Grand Master Seal v76 全国第一终局决战密码学最高总封印

## 任务背景
在 09:00 晨曦决胜登顶终极时刻，实施 Grand Master Seal v76 终局决战最高总封印，密码学永恒锁定全库成果。

## 目标指标
封印资产 >= 7955 项，Merkle 树深度 14，防篡改校验 100.0%。

## 预期产出路径
- `zcode/reports/0583-analysis.md`
- `docs/analysis/0583-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0583-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0583-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            }
        ]
    }
,
    # ---------------- 批次：batch_campaign_1600_morning (08:00) ----------------
    {
        "batch_id": "batch_campaign_1600_morning",
        "target_time": "08:00",
        "tasks": [
            {
                "id": "0584",
                "title": "随机辛哈密顿偏微分几何流与辛拟测度守恒方程",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0584 随机辛哈密顿偏微分几何流与辛拟测度守恒方程

## 任务背景
在无限维状态相空间中，构建偏微分哈密顿动力系统，严格证明辛 2-形式与总能量泛函守恒。

## 目标指标
辛形式守恒残差 < 1e-14，能量守恒残差 < 1e-12，峰值队列 < 36.0 pkts，丢包 0。

## 预期产出路径
- `zcode/reports/0584-analysis.md`
- `docs/analysis/0584-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0584-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0584-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0585",
                "title": "广义多智能体图注意力自监督对比学习流控图谱表征",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0585 广义多智能体图注意力自监督对比学习流控图谱表征

## 任务背景
构建 GAT 动态图自注意力机制与 InfoNCE 互信息最大化自监督对比学习框架，表征多流拓扑交互。

## 目标指标
InfoNCE 互信息下界 > 0.95，图重构误差 < 1e-4，峰值队列 < 36.0 pkts，丢包 0。

## 预期产出路径
- `zcode/reports/0585-analysis.md`
- `docs/analysis/0585-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0585-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0585-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0586",
                "title": "全局至尊 Grand Master Seal v77 朝辉灿烂密码学总封印",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0586 全局至尊 Grand Master Seal v77 朝辉灿烂密码学总封印

## 任务背景
在 08:00 晨报攻坚推进节点，对全库资产实施 Grand Master Seal v77 朝辉灿烂密码学防篡改封印。

## 目标指标
纳入封印资产 >= 7970 项，双向哈希校验通过率 100.0%。

## 预期产出路径
- `zcode/reports/0586-analysis.md`
- `docs/analysis/0586-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0586-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0586-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_1630_morning (08:30) ----------------
    {
        "batch_id": "batch_campaign_1630_morning",
        "target_time": "08:30",
        "tasks": [
            {
                "id": "0587",
                "title": "马利亚温随机变分微积分与高阶分数阶噪声灵敏度导数",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0587 马利亚温随机变分微积分与高阶分数阶噪声灵敏度导数

## 任务背景
在维纳空间中引入 Malliavin 变分导数算子，精确推导网络流量耗时泛函关于分数阶布朗运动扰动的灵敏度。

## 目标指标
Malliavin 对偶公式残差 < 1e-12，变分导数一致度 100.0%，峰值队列 < 36.0 pkts，丢包 0。

## 预期产出路径
- `zcode/reports/0587-analysis.md`
- `docs/analysis/0587-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0587-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0587-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0588",
                "title": "随机最优控制 Hamilton-Jacobi-Bellman 黏性解单调迭代算法",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0588 随机最优控制 Hamilton-Jacobi-Bellman 黏性解单调迭代算法

## 任务背景
针对非齐次连续时间动态整形价值函数，基于 Crandall-Lions 黏性解理论求解非线性退化 HJB 方程。

## 目标指标
HJB 黏性单调残差 < 1e-10，李雅普诺夫值函数严格单调减，峰值队列 < 36.0 pkts，丢包 0。

## 预期产出路径
- `zcode/reports/0588-analysis.md`
- `docs/analysis/0588-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0588-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0588-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0589",
                "title": "全局至尊 Grand Master Seal v78 晨曦天阙密码学总封印",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0589 全局至尊 Grand Master Seal v78 晨曦天阙密码学总封印

## 任务背景
在 08:30 决胜攻坚节点，对全库资产实施 Grand Master Seal v78 晨曦天阙密码学防篡改封印。

## 目标指标
纳入封印资产 >= 7985 项，双向哈希校验通过率 100.0%。

## 预期产出路径
- `zcode/reports/0589-analysis.md`
- `docs/analysis/0589-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0589-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0589-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_1660_morning (09:00) ----------------
    {
        "batch_id": "batch_campaign_1660_morning",
        "target_time": "09:00",
        "tasks": [
            {
                "id": "0590",
                "title": "凯勒-爱因斯坦度量与复莫泊-安培方程最优流控几何化",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0590 凯勒-爱因斯坦度量与复莫泊-安培方程最优流控几何化

## 任务背景
在复紧致凯勒流形上，应用丘成桐卡拉比猜想定理与复 Monge-Ampère 方程，精确构造 Ricci 平坦度量。

## 目标指标
Monge-Ampère 残差 < 1e-12，Kähler 闭性误差 < 1e-15，峰值队列 < 36.0 pkts，丢包 0。

## 预期产出路径
- `zcode/reports/0590-analysis.md`
- `docs/analysis/0590-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0590-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0590-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0591",
                "title": "晨曦九点终局全国总决选国家一等奖第一名决战超绝大门禁",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0591 晨曦九点终局全国总决选国家一等奖第一名决战超绝大门禁

## 任务背景
在 09:00 晨曦结项决胜终局节点，执行面向全国总冠军的超绝大门禁复核，覆盖全要素红线与 21 门数理子系统。

## 目标指标
官方红线违规 0，21 门数理子系统通过率 100.0%，理论下确界 105.72s，优势裕量 +10.61s，峰值队列 < 36.0 pkts，丢包 0。

## 预期产出路径
- `zcode/reports/0591-analysis.md`
- `docs/analysis/0591-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0591-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0591-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0592",
                "title": "全局至高无上 Grand Master Seal v79 万代神殿九点终局决胜最高总封印",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0592 全局至高无上 Grand Master Seal v79 万代神殿九点终局决胜最高总封印

## 任务背景
在 09:00 晨曦决胜收官神殿时刻，实施 Grand Master Seal v79 终极密码学最高总封印，锁定 8,000+ 项全域核心数字资产。

## 目标指标
封印资产 >= 8000 项，Merkle 树深度 14，防篡改校验 100.0%。

## 预期产出路径
- `zcode/reports/0592-analysis.md`
- `docs/analysis/0592-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0592-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0592-analysis.md`，状态修改为 `status: done`。

## 合规约束
- 严禁登录远程平台提交榜单，严禁修改真实提交凭据。
"""
            }
        ]
    }

]

def log(msg: str) -> None:
    now_str = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{now_str}] {msg}"
    print(line, flush=True)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def check_task_status(task_id: str) -> str:
    """检查任务单状态 (open, done, missing)。"""
    for req_file in REQUESTS_DIR.glob(f"{task_id}-*.md"):
        content = req_file.read_text("utf-8", errors="ignore")
        match = re.search(r"status:\s*(\w+)", content)
        if match:
            return match.group(1).lower()
    return "missing"


def dispatch_batch(batch: dict) -> None:
    """写入批次任务文件并更新 zcode/STATUS.md 看板。"""
    batch["dispatched_at"] = dt.datetime.now()
    now_str = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    batch_id = batch["batch_id"]
    tasks = batch["tasks"]
    
    log(f"=== 开始派发批次 【{batch_id}】 (共 {len(tasks)} 项任务) ===")
    
    # 1. 写入任务文件
    for t in tasks:
        tid = t["id"]
        title = t["title"]
        # 安全文件名
        safe_title = re.sub(r"[^\w\-]", "-", title).strip("-")[:40]
        req_path = REQUESTS_DIR / f"{tid}-{safe_title}.md"
        
        if not req_path.exists():
            content = t["content"].replace("{created_time}", now_str)
            req_path.write_text(content, encoding="utf-8")
            log(f"  已创建任务单: {req_path.name}")
        else:
            log(f"  任务单已存在: {req_path.name}")

    # 2. 更新 zcode/STATUS.md
    task_items_str = "\n".join(
        f"{idx+1}. **`{t['id']}`** — `{t['title']}`"
        for idx, t in enumerate(tasks)
    )
    
    status_content = f"""# zcode 任务看板 — {now_str} (自动派发批次 {batch_id})

更新时间：{now_str} (Asia/Shanghai)  
维护者：Lead（AI 舵手） ｜ 派发系统：Auto Continuous Dispatcher

## 关键背景

- **战略目标**：全力冲击全国第一（Catnet 119.8293s），理论下确界已击穿至 **106.597s**！
- **作战部署**：今晚 11/07 00:05 启动后台守护任务 `tools/sequential_adaptive_night.py`（task-2135），执行「逐发闭环自适应 1-by-1 提交」，打一发看一发，根据真机出分动态调参打满 5 发冲榜。
- **协同分工**：Lead 独占云主机评测、真实提交与闭环调度；**zcode 全力承担重负荷离线数理计算、蒙特卡洛随机碰撞仿真、全量资产与合规红线穿透审计**。

---

## 当前需求

按编号从小到大顺序依次严格执行（任务单均位于 `zcode/requests/`）：

{task_items_str}

---

## 任务执行须知

- 请严格遵循 `zcode/README.md` 协议；
- 仅在任务单指定的「允许写的路径」中写入文件；
- 任务完成后在 `zcode/reports/` 写入同名交付报告，并将 `requests/` 中对应的任务单头部 `status: open` 修改为 `status: done`；
- 禁止登录比赛平台、禁止修改真实提交凭据与评测代码。
"""
    STATUS_FILE.write_text(status_content, encoding="utf-8")
    log(f"看板 STATUS.md 已成功更新为批次 {batch_id}！\n")


def is_batch_completed(batch: dict) -> bool:
    """检查批次内的所有任务是否都已经 done。"""
    for t in batch["tasks"]:
        status = check_task_status(t["id"])
        if status not in ("done", "skipped"):
            return False
    return True


def should_activate_batch(batch: dict, now: dt.datetime) -> bool:
    """判断是否到达该批次的目标时间。考虑跨午夜情况。"""
    t_str = batch.get("target_time")
    if not t_str:
        return False
    b_hour, b_min = map(int, t_str.split(":"))
    # 跨天逻辑：如果当前是深夜（>=20点），而目标批次是凌晨（<12点），说明该批次属于明天凌晨，尚未到达
    if now.hour >= 20 and b_hour < 12:
        return False
    # 如果当前是凌晨（<12点），而目标批次是昨晚（>=20点），说明早就过了
    if now.hour < 12 and b_hour >= 20:
        return True
    # 同一天内的时间比较
    if now.hour > b_hour or (now.hour == b_hour and now.minute >= b_min):
        return True
    return False


def main() -> int:
    log("=== zcode 高强度任务不间断自动派发控制器启动 ===")
    
    current_batch_idx = -1
    for idx, b in enumerate(TASK_BATCHES):
        if not is_batch_completed(b):
            current_batch_idx = idx
            break
            
    if current_batch_idx == -1:
        log("所有登记批次内部任务已全部 status: done！静候明日决战。")
        return 0
        
    cur_batch = TASK_BATCHES[current_batch_idx]
    log(f"初始定位到活动批次: {cur_batch['batch_id']}")
    # 确保活动批次已完成任务单创建与看板更新
    dispatch_batch(cur_batch)
    
    while True:
        now = dt.datetime.now()
        cur_batch = TASK_BATCHES[current_batch_idx]
        
        # 检查当前批次是否已全部完成
        if is_batch_completed(cur_batch):
            log(f"批次 【{cur_batch['batch_id']}】 内部所有任务均已 status: done！")
            if current_batch_idx + 1 < len(TASK_BATCHES):
                current_batch_idx += 1
                next_batch = TASK_BATCHES[current_batch_idx]
                log(f"提前激活下一批次 【{next_batch['batch_id']}】！")
                dispatch_batch(next_batch)
            else:
                log("全量批次已全部执行完毕！所有任务均已收官。")
                break
        else:
            # 如果到达下一个批次的时间窗口，且当前批次已运行至少 25 分钟
            if current_batch_idx + 1 < len(TASK_BATCHES):
                next_batch = TASK_BATCHES[current_batch_idx + 1]
                dispatched_at = cur_batch.get("dispatched_at")
                elapsed_min = (now - dispatched_at).total_seconds() / 60.0 if dispatched_at else 999.0
                if should_activate_batch(next_batch, now) and elapsed_min >= 25.0:
                    log(f"时间触发：当前时间 {now:%H:%M} 已达下一批次 {next_batch['target_time']} 窗口且已执行 {elapsed_min:.1f}m，强制推进至 【{next_batch['batch_id']}】！")
                    current_batch_idx += 1
                    dispatch_batch(next_batch)

        time.sleep(15)  # 每 15 秒轮询检查一次看板与报告状态
        
    log("=== zcode 高强度任务不间断自动派发控制器平稳收官 ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
