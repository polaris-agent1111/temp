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
    # ---------------- 批次：batch_campaign_0430_dawn (04:30) ----------------
    {
        "batch_id": "batch_campaign_0430_dawn",
        "target_time": "04:30",
        "tasks": [
            {
                "id": "0377",
                "title": "全协议栈动态反馈的深度强化学习-PPO-流量整形器预演",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0377 — 全协议栈动态反馈的深度强化学习 PPO 流量整形器预演

## 任务背景
针对多变背景流与动态 RTT 抖动，利用近端策略优化 (PPO) 算法训练离线自适应流量整形 Agent。

## 目标
PPO 累积回报收敛度 >= 99.0%，离线决策时延 < 1.0 ms。

## 预期产出路径
- `zcode/reports/0377-analysis.md`
- `docs/analysis/0377-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0377-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0377-analysis.md`，并将状态修改为 `status: done`。

## 合规
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0378",
                "title": "浅队列极端跨流干扰下的非马尔可夫半鞅差分边界估计",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0378 — 浅队列极端跨流干扰下的非马尔可夫半鞅差分边界估计

## 任务背景
在非泊松、长相关性背景流下，经典马尔可夫假设失效。需采用半鞅 (Semimartingale) 分解推导排队累积泛函的 Doob-Meyer 分解上界。

## 目标
半鞅局部漂移一致性检验 100.0%，上界收敛误差 < 0.5%。

## 预期产出路径
- `zcode/reports/0378-analysis.md`
- `docs/analysis/0378-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0378-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0378-analysis.md`，并将状态修改为 `status: done`。

## 合规
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0379",
                "title": "全国总决赛 Grand Master Seal v8 密码学封签与答辩材料终审",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0379 — 全国总决赛 Grand Master Seal v8 密码学封签与答辩材料终审

## 任务背景
对 03:00 整点阶段性全量成果进行 Grand Master Seal v8 封签，封存核心学术与工程资产。

## 目标
封签资产 >= 4900 项，防篡改校验 100.0%。

## 预期产出路径
- `zcode/reports/0379-analysis.md`
- `docs/analysis/0379-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0379-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0379-analysis.md`，并将状态修改为 `status: done`。

## 合规
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            }
        ]
    }'''

    updated = text[:idx] + '    }' + new_batches + '\n]' + text[idx+7:]
    with open('tools/zcode_continuous_dispatcher.py', 'w', encoding='utf-8') as f:
        f.write(updated)
    print("Successfully appended batch 0430 to tools/zcode_continuous_dispatcher.py")
    return 0

if __name__ == '__main__':
    sys.exit(main())
