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
    # ---------------- 批次：batch_campaign_0330_dawn (03:30) ----------------
    {
        "batch_id": "batch_campaign_0330_dawn",
        "target_time": "03:30",
        "tasks": [
            {
                "id": "0371",
                "title": "六轮次非平稳背景突发流的谱分解与小波去噪流量整形逆滤波",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0371 — 六轮次非平稳背景突发流的谱分解与小波去噪流量整形逆滤波

## 任务背景
真实竞赛网络中跨流背景流量具有非平稳与突发自相似重尾特性。需利用离散小波变换 (DWT) 对背景流时序进行多尺度谱分解，设计自适应小波逆滤波算法。

## 目标
小波高频去噪信噪比提升 >= 12.0 dB，重构保真度 >= 99.0%。

## 预期产出路径
- `zcode/reports/0371-analysis.md`
- `docs/analysis/0371-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0371-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0371-analysis.md`，并将状态修改为 `status: done`。

## 合规
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0372",
                "title": "多智能体博弈下帕累托前沿动态追踪与纳什均衡稳定性证明",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0372 — 多智能体博弈下帕累托前沿动态追踪与纳什均衡稳定性证明

## 任务背景
在 17 支战队并发共享的有限信道博弈中，各队带宽争夺构成连续型广义非合作博弈。需形式化证明纳什均衡点的唯一性与局部李雅普诺夫渐近稳定性。

## 目标
证明纳什均衡解的存在唯一性，李雅普诺夫矩阵负定性验证 100.0%。

## 预期产出路径
- `zcode/reports/0372-analysis.md`
- `docs/analysis/0372-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0372-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0372-analysis.md`，并将状态修改为 `status: done`。

## 合规
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0373",
                "title": "全链路数据一致性复测仿真引擎与十轮均值极端压力测试",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0373 — 全链路数据一致性复测仿真引擎与十轮均值极端压力测试

## 任务背景
针对官方统一复测规则，需搭建完全对齐官方评测器的离线极速仿真引擎，执行 1,000,000 次 10-轮均值极端扰动压力测试。

## 目标
复测均值稳定性置信度 100.0%，极端回撤下界优于 128.0s。

## 预期产出路径
- `zcode/reports/0373-analysis.md`
- `docs/analysis/0373-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析并写入 `docs/analysis/0373-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0373-analysis.md`，并将状态修改为 `status: done`。

## 合规
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            }
        ]
    }'''

    updated = text[:idx] + '    }' + new_batches + '\n]' + text[idx+7:]
    with open('tools/zcode_continuous_dispatcher.py', 'w', encoding='utf-8') as f:
        f.write(updated)
    print("Successfully appended batch 0330 to tools/zcode_continuous_dispatcher.py")
    return 0

if __name__ == '__main__':
    sys.exit(main())
