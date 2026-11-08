# -*- coding: utf-8 -*-
"""
Script to append batches 1430, 1500 into tools/zcode_continuous_dispatcher.py
"""

NEW_BATCHES_CODE = '''    # ---------------- 批次：batch_campaign_1430_post_dawn (14:30) ----------------
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
在 6 流带宽竞争下建立加权 $\alpha$-效用函数与对偶次梯度更新律，推导 $O(1/\sqrt{T})$ 严格次线性收敛速率界。

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
    print(f"[*] Successfully injected batches 1430, 1500 into {target_file}")
    return 0

if __name__ == "__main__":
    main()
