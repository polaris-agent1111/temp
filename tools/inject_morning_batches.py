#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inject batches 0130, 0200, 0230, 0300 into tools/zcode_continuous_dispatcher.py"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DISPATCHER_PATH = ROOT / "tools" / "zcode_continuous_dispatcher.py"

FINAL_BATCHES_TEXT = '''    # ---------------- 批次：batch_campaign_0130_morning (01:30) ----------------
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
'''

def main():
    text = DISPATCHER_PATH.read_text(encoding="utf-8")
    
    marker = "def log(msg: str) -> None:"
    idx = text.rfind(marker)
    if idx == -1:
        print("[!] Could not find marker")
        return 1
        
    bracket_idx = text.rfind("]", 0, idx)
    brace_idx = text.rfind("}", 0, bracket_idx)
    
    if brace_idx == -1:
        print("[!] Could not find last brace")
        return 1
        
    insert_pos = brace_idx + 1
    new_text = text[:insert_pos] + ",\n" + FINAL_BATCHES_TEXT + "\n" + text[bracket_idx:]
    DISPATCHER_PATH.write_text(new_text, encoding="utf-8")
    print(f"[*] Successfully injected final 4 batches into {DISPATCHER_PATH}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
