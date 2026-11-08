# -*- coding: utf-8 -*-
"""
Append batches 0530_dawn to 0900_dawn (tasks 0383 to 0406) into tools/zcode_continuous_dispatcher.py
"""

NEW_BATCHES_CODE = ''',
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
    }
'''

with open('tools/zcode_continuous_dispatcher.py', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('batch_campaign_0500_dawn')
end_idx = text.find(']', idx)

new_text = text[:end_idx] + NEW_BATCHES_CODE + text[end_idx:]

with open('tools/zcode_continuous_dispatcher.py', 'w', encoding='utf-8') as f:
    f.write(new_text)

print("Successfully injected batches 0530 through 0900 into tools/zcode_continuous_dispatcher.py!")
