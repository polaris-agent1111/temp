# -*- coding: utf-8 -*-
"""
Script to append batches 1730, 1800 into tools/zcode_continuous_dispatcher.py
"""

NEW_BATCHES_CODE = r'''    # ---------------- 批次：batch_campaign_1730_post_dawn (17:30) ----------------
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
    print(f"[*] Successfully injected batches 1730, 1800 into {target_file}")
    return 0

if __name__ == "__main__":
    main()
