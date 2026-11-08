#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extend zcode_continuous_dispatcher.py with comprehensive evening and night batches.
From batch_2100 to batch_0200 (21:00 to 02:00+, covering the 11/08 midnight campaign).
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DISPATCHER_FILE = ROOT / "tools" / "zcode_continuous_dispatcher.py"

NEW_BATCHES_CODE = '''
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
'''

def main():
    with open(DISPATCHER_FILE, "r", encoding="utf-8") as f:
        content = f.read()
        
    idx = content.find("def log(")
    if idx == -1:
        print("Error: Could not find def log in dispatcher script.")
        return 1
        
    # Find the closing bracket of TASK_BATCHES before def log
    sub = content[:idx]
    bracket_pos = sub.rfind("]")
    if bracket_pos == -1:
        print("Error: Could not find closing bracket of TASK_BATCHES.")
        return 1
        
    new_content = sub[:bracket_pos] + ",\n" + NEW_BATCHES_CODE.strip() + "\n]\n\n" + content[idx:]
    
    with open(DISPATCHER_FILE, "w", encoding="utf-8") as f:
        f.write(new_content)
        
    print("Successfully appended batches 2100 ~ 2330 (tasks 0152 ~ 0169) to zcode_continuous_dispatcher.py!")
    return 0

if __name__ == "__main__":
    main()
