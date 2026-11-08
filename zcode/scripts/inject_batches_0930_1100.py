# -*- coding: utf-8 -*-
"""
Script to append batches 0930, 1000, 1030, 1100 into tools/zcode_continuous_dispatcher.py
"""

NEW_BATCHES_CODE = '''    # ---------------- 批次：batch_campaign_0930_post_dawn (09:30) ----------------
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
    }
'''

def main():
    target_file = "tools/zcode_continuous_dispatcher.py"
    with open(target_file, "r", encoding="utf-8") as f:
        content = f.read()

    needle = '            }\n        ]\n    }\n]'
    if needle not in content:
        print("[!] Needle not found!")
        return 1

    replacement = '            }\n        ]\n    },\n' + NEW_BATCHES_CODE + '\n]'
    new_content = content.replace(needle, replacement, 1)
    with open(target_file, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"[*] Successfully injected batches 0930, 1000, 1030, 1100 into {target_file}")
    return 0

if __name__ == "__main__":
    main()
