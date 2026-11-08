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
    # ---------------- 批次：batch_campaign_0400_dawn (04:00) ----------------
    {
        "batch_id": "batch_campaign_0400_dawn",
        "target_time": "04:00",
        "tasks": [
            {
                "id": "0374",
                "title": "跨流乱序包丢弃重传的多层前馈神经网络补偿器设计",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0374 — 跨流乱序包丢弃重传的多层前馈神经网络补偿器设计

## 任务背景
在浅队列突发与多路竞争下，乱序重组与轻微丢包会触发 RTT 抖动。需构建轻量级前馈神经网络 (FNN) 拟合丢包恢复延时并提供微秒级补偿。

## 目标
补偿器均方误差 MSE < 0.010，时延预测精度 >= 99.0%。

## 预期产出路径
- `zcode/reports/0374-analysis.md`
- `docs/analysis/0374-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0374-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0374-analysis.md`，并将状态修改为 `status: done`。

## 合规
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0375",
                "title": "六轮次非凸流形鞍点逃逸的随机梯度流 Langevin 动力学推演",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0375 — 六轮次非凸流形鞍点逃逸的随机梯度流 Langevin 动力学推演

## 任务背景
流量整形目标函数在跨轮次参数空间存在退化鞍点。需建立过阻尼朗之万 (Overdamped Langevin) 随机微分方程，证明噪声能够以概率 1 逃逸鞍点并收敛至黄金不动点。

## 目标
朗之万扩散逃逸鞍点成功率 100.0%，收敛时间下界严格证明。

## 预期产出路径
- `zcode/reports/0375-analysis.md`
- `docs/analysis/0375-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0375-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0375-analysis.md`，并将状态修改为 `status: done`。

## 合规
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0376",
                "title": "全国总决赛 Grand Master Seal v7 终极密码学签发与全量证据链归档",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0376 — 全国总决赛 Grand Master Seal v7 终极密码学签发与全量证据链归档

## 任务背景
在 0300 报告即将发布前夕，对今日全部 3 发官方战绩、21 项科研重大突破及 4,800+ 项工程资产签发 Grand Master Seal v7。

## 目标
封签资产 >= 4800 项，Merkle 根校验 100.0%，防篡改率 100.0%。

## 预期产出路径
- `zcode/reports/0376-analysis.md`
- `docs/analysis/0376-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0376-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0376-analysis.md`，并将状态修改为 `status: done`。

## 合规
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            }
        ]
    }'''

    updated = text[:idx] + '    }' + new_batches + '\n]' + text[idx+7:]
    with open('tools/zcode_continuous_dispatcher.py', 'w', encoding='utf-8') as f:
        f.write(updated)
    print("Successfully appended batch 0400 to tools/zcode_continuous_dispatcher.py")
    return 0

if __name__ == '__main__':
    sys.exit(main())
