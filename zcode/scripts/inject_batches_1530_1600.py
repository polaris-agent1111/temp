# -*- coding: utf-8 -*-
"""
Script to append batches 1530, 1600 into tools/zcode_continuous_dispatcher.py
"""

NEW_BATCHES_CODE = r'''    # ---------------- 批次：batch_campaign_1530_post_dawn (15:30) ----------------
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
    print(f"[*] Successfully injected batches 1530, 1600 into {target_file}")
    return 0

if __name__ == "__main__":
    main()
