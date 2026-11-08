# -*- coding: utf-8 -*-
"""
Script to append batches 1630, 1700 into tools/zcode_continuous_dispatcher.py
"""

NEW_BATCHES_CODE = r'''    # ---------------- 批次：batch_campaign_1630_post_dawn (16:30) ----------------
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
    }
'''

def main():
    target_file = "tools/zcode_continuous_dispatcher.py"
    with open(target_file, "r", encoding="utf-8") as f:
        content = f.read()

    needle = '            }\n        ]\n    }\n\n]'
    if needle not in content:
        needle = '            }\n        ]\n    }\n]'
        if needle not in content:
            print("[!] Needle not found!")
            return 1

    replacement = '            }\n        ]\n    },\n' + NEW_BATCHES_CODE + '\n]'
    new_content = content.replace(needle, replacement, 1)
    with open(target_file, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"[*] Successfully injected batches 1630, 1700 into {target_file}")
    return 0

if __name__ == "__main__":
    main()
