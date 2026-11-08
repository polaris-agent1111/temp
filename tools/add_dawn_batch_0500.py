# -*- coding: utf-8 -*-
import sys

def main():
    with open('tools/zcode_continuous_dispatcher.py', 'r', encoding='utf-8') as f:
        text = f.read()

    idx = text.rfind('    }\n]')
    if idx == -1:
        print("Anchor '    }\\n]' not found!")
        return 1

    new_batches = ''',
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
    }'''

    updated = text[:idx] + '    }' + new_batches + '\n]' + text[idx+7:]
    with open('tools/zcode_continuous_dispatcher.py', 'w', encoding='utf-8') as f:
        f.write(updated)
    print("Successfully appended batch 0500 to tools/zcode_continuous_dispatcher.py")
    return 0

if __name__ == '__main__':
    sys.exit(main())
