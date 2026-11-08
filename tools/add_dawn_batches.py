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
    # ---------------- 批次：batch_campaign_0230_dawn (02:30) ----------------
    {
        "batch_id": "batch_campaign_0230_dawn",
        "target_time": "02:30",
        "tasks": [
            {
                "id": "0365",
                "title": "今日-3-发真机实测数据微观排队延时与信道积压泛函精细分解",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0365 — 今日 3 发真机实测数据微观排队延时与信道积压泛函精细分解

## 任务背景
今日 3 发实测成绩全量闭环：Shot 1 (122.0463s, [40,40,40,37,36,36])，Shot 2 (124.6603s, [41,41,40,37,36,36])，Shot 3 (128.3987s, [41,40,40,37,36,36])。需构建精细化排队差分泛函，量化首轮 41 包注入导致的排队累积延时。

## 目标
建立 M/M/1/K 浅缓冲区微观排队模型，分解排队驻留时间，泛函逼近误差 < 1.0%。

## 预期产出路径
- `zcode/reports/0365-analysis.md`
- `docs/analysis/0365-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0365-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0365-analysis.md`，并将状态修改为 `status: done`。

## 合规
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0366",
                "title": "浅缓冲区微突发无丢包临界包速率判定上界证明",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0366 — 浅缓冲区微突发无丢包临界包速率判定上界证明

## 任务背景
实测证明 [40,40,40,...] 极其平稳（122.0s，全国第5），而首轮提速至 41 产生排队积压。需用李雅普诺夫稳定性严格证明 40 pkts/4ms 为确定性无丢包与无排队膨胀的稳定上界。

## 目标
证明 40 pkts/4ms 为李雅普诺夫稳定不动点，上界置信度 100.0%。

## 预期产出路径
- `zcode/reports/0366-analysis.md`
- `docs/analysis/0366-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0366-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0366-analysis.md`，并将状态修改为 `status: done`。

## 合规
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0367",
                "title": "六轮次跨流背景竞争动态演化博弈与对手参数反解",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0367 — 六轮次跨流背景竞争动态演化博弈与对手参数反解

## 任务背景
全国榜首 Catnet 达 116.3367s，领先我方 5.7s。需基于我方实测基准与理论下确界 106.597s，运用微分博弈反解对手在各轮次的流量整形参数与竞争策略。

## 目标
反解重构准确率 >= 95.0%，预测残差 < 0.5s。

## 预期产出路径
- `zcode/reports/0367-analysis.md`
- `docs/analysis/0367-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0367-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0367-analysis.md`，并将状态修改为 `status: done`。

## 合规
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_campaign_0300_dawn (03:00) ----------------
    {
        "batch_id": "batch_campaign_0300_dawn",
        "target_time": "03:00",
        "tasks": [
            {
                "id": "0368",
                "title": "实测数据驱动的非参数核密度估计与官方复测期望下界收敛性证明",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0368 — 实测数据驱动的非参数核密度估计与官方复测期望下界收敛性证明

## 任务背景
官方采用「多场复测取平均」更新总排名。需基于今日实测样本与全量仿真数据，进行非参数核密度估计（KDE）并证明大数定律鞅收敛下界。

## 目标
KDE 置信区间估计精度 >= 99.0%，复测胜率期望收敛性严格证明。

## 预期产出路径
- `zcode/reports/0368-analysis.md`
- `docs/analysis/0368-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0368-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0368-analysis.md`，并将状态修改为 `status: done`。

## 合规
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0369",
                "title": "全协议栈硬件卸载-TSO-GSO-与微秒级-Pacing-非线性耦合分析",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0369 — 全协议栈硬件卸载-TSO-GSO-与微秒级-Pacing-非线性耦合分析

## 任务背景
千兆网卡硬件卸载（TSO/GSO）会重聚合并打散应用层 Pacing 定时器。需构建微观非线性微分方程解，量化硬件聚合对 4ms 漏桶定时的影响。

## 目标
抖动滤波率 >= 99.0%，稳态时钟补偿误差 < 2.0 微秒。

## 预期产出路径
- `zcode/reports/0369-analysis.md`
- `docs/analysis/0369-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0369-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0369-analysis.md`，并将状态修改为 `status: done`。

## 合规
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0370",
                "title": "全国总决赛学术级技术答辩白皮书总纲与完整证据链封存",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0370 — 全国总决赛学术级技术答辩白皮书总纲与完整证据链封存

## 任务背景
今日实战 3 发全量闭环，已斩获全国第 5 名突破战绩（122.0463s）。需将全部 21 项数理创新与密码学 Merkle 树证据链整合为技术答辩白皮书。

## 目标
白皮书覆盖率 100.0%，证据自洽度 100.0%。

## 预期产出路径
- `zcode/reports/0370-analysis.md`
- `docs/analysis/0370-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0370-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0370-analysis.md`，并将状态修改为 `status: done`。

## 合规
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            }
        ]
    }'''

    updated = text[:idx] + '    }' + new_batches + '\n]' + text[idx+7:]
    with open('tools/zcode_continuous_dispatcher.py', 'w', encoding='utf-8') as f:
        f.write(updated)
    print("Successfully appended dawn batches to tools/zcode_continuous_dispatcher.py")
    return 0

if __name__ == '__main__':
    sys.exit(main())
