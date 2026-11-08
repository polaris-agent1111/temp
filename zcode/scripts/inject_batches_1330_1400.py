# -*- coding: utf-8 -*-
"""
Script to append batches 1330, 1400 into tools/zcode_continuous_dispatcher.py
"""

NEW_BATCHES_CODE = '''    # ---------------- 批次：batch_campaign_1330_post_dawn (13:30) ----------------
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
    }
'''

def main():
    target_file = "tools/zcode_continuous_dispatcher.py"
    with open(target_file, "r", encoding="utf-8") as f:
        content = f.read()

    needle = '            }\n        ]\n    }\n\n]'
    if needle not in content:
        # 尝试另一种结尾
        needle = '            }\n        ]\n    }\n]'
        if needle not in content:
            print("[!] Needle not found!")
            return 1

    replacement = '            }\n        ]\n    },\n' + NEW_BATCHES_CODE + '\n]'
    new_content = content.replace(needle, replacement, 1)
    with open(target_file, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"[*] Successfully injected batches 1330, 1400 into {target_file}")
    return 0

if __name__ == "__main__":
    main()
