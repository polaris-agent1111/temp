#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extend continuous task dispatcher with 11/08 campaign battle batches:
- batch_dawn_0030 (Tasks 0293, 0294, 0295)
- batch_dawn_0100 (Tasks 0296, 0297, 0298)
- batch_dawn_0130 (Tasks 0299, 0300, 0301)
- batch_dawn_0200 (Tasks 0302, 0303, 0304)
"""

import sys
from pathlib import Path

def extend_campaign_batches():
    disp_path = Path("tools/zcode_continuous_dispatcher.py")
    content = disp_path.read_text(encoding="utf-8")

    new_batches_code = ''',
    # ---------------- 批次：batch_dawn_0030 (00:30) ----------------
    {
        "batch_id": "batch_dawn_0030",
        "target_time": "00:30",
        "tasks": [
            {
                "id": "0293",
                "title": "Shot 1 真实出分榜单提取与信道拥塞度贝叶斯反演",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0293 任务：Shot 1 真实出分榜单提取与信道拥塞度贝叶斯反演

## 任务背景
Shot 1 提交后，建立官方 API 出分反演模型，通过首发实测下载时间 T1，后验推导信道实际排队延迟与交叉流突发强度。

## 目标
验证出分后验推导算法，输出拥塞度置信区间，后验反演准确率 >= 90.0%。

## 预期产出路径
- `zcode/reports/0293-analysis.md`
- `docs/analysis/0293-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0293-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0293-analysis.md`，状态修改为 `status: done`。

## 合规守则
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0294",
                "title": "Shot 2 动态自适应分支决策与热切换无缝注入",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0294 任务：Shot 2 动态自适应分支决策与热切换无缝注入

## 任务背景
验证根据 Shot 1 真实出分（<=122.5s / 122.5~125s / >125s）动态分发 Shot 2（冲冠主力 / 超宽平台 / 防守堡垒）的热切换机制。

## 目标
验证决策 DAG 状态机切换延迟 <= 5ms，无死锁，状态落盘 100% 幂等。

## 预期产出路径
- `zcode/reports/0294-analysis.md`
- `docs/analysis/0294-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0294-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0294-analysis.md`，状态修改为 `status: done`。

## 合规守则
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0295",
                "title": "官方复测鲁棒性裕度在线交叉验证",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0295 任务：官方复测鲁棒性裕度在线交叉验证

## 任务背景
官方采用多次复测取平均更新排行榜。在首发与次发后，实时在线模拟复测均值稳定性，防止陷入尖锐孤立点。

## 目标
完成 1,000 次蒙特卡洛复测抽样，验证 3 次复测均值漂移 <= 1.2s，方差稳健度 >= 85.0%。

## 预期产出路径
- `zcode/reports/0295-analysis.md`
- `docs/analysis/0295-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0295-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0295-analysis.md`，状态修改为 `status: done`。

## 合规守则
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_dawn_0100 (01:00) ----------------
    {
        "batch_id": "batch_dawn_0100",
        "target_time": "01:00",
        "tasks": [
            {
                "id": "0296",
                "title": "Shot 2 真机出分与全国排名异动追踪",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0296 任务：Shot 2 真机出分与全国排名异动追踪

## 任务背景
跟踪 Shot 2 榜单变动，对标全国第一 Catnet (119.8293s) 与 光明未来 (117.0257s)，计算胜率与差距分段。

## 目标
验证排名变动捕获延迟 <= 10s，胜率评估置信度 >= 95.0%。

## 预期产出路径
- `zcode/reports/0296-analysis.md`
- `docs/analysis/0296-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0296-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0296-analysis.md`，状态修改为 `status: done`。

## 合规守则
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0297",
                "title": "Shot 3 进攻/防守动态权重博弈分配",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0297 任务：Shot 3 进攻/防守动态权重博弈分配

## 任务背景
在已获得前两发真实成绩后，基于博弈论分配 Shot 3 的进攻性（冲 116s）与防守性（固化前三）权重系数。

## 目标
求解纳什均衡混合策略最优权重，攻防综合期望效用提升 >= 15.0%。

## 预期产出路径
- `zcode/reports/0297-analysis.md`
- `docs/analysis/0297-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0297-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0297-analysis.md`，状态修改为 `status: done`。

## 合规守则
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0298",
                "title": "浅缓冲区纳什均衡与多租户挤出效应微观建模",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0298 任务：浅缓冲区纳什均衡与多租户挤出效应微观建模

## 任务背景
深夜时段其他参赛队伍与官方背景流在 30 包浅缓冲区的竞争行为，微观仿真定步长匀速流对激进脉冲流的自然挤出效应。

## 目标
证明定步长流在浅缓冲区的带宽占有率优势 >= 65.0%，主动丢包率为 0。

## 预期产出路径
- `zcode/reports/0298-analysis.md`
- `docs/analysis/0298-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0298-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0298-analysis.md`，状态修改为 `status: done`。

## 合规守则
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_dawn_0130 (01:30) ----------------
    {
        "batch_id": "batch_dawn_0130",
        "target_time": "01:30",
        "tasks": [
            {
                "id": "0299",
                "title": "Shot 3 真机成绩吸收与全国前三排位巩固",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0299 任务：Shot 3 真机成绩吸收与全国前三排位巩固

## 任务背景
吸收 Shot 3 真机成绩，更新全队 5 发战绩置信区间与登上领奖台（Top 3）的联合概率。

## 目标
验证三发成绩联合分布，领奖台概率达到 >= 92.0%。

## 预期产出路径
- `zcode/reports/0299-analysis.md`
- `docs/analysis/0299-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0299-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0299-analysis.md`，状态修改为 `status: done`。

## 合规守则
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0300",
                "title": "11/08 决胜半程战果推演与 Shot 4 决战终局参数微调",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0300 任务：11/08 决胜半程战果推演与 Shot 4 决战终局参数微调

## 任务背景
过半程后（已发 3 发，剩余 2 发），对 Shot 4 进行参数级微调（±0.5 pkts/tick 或微调 precise rate 12MB/s），锁定最终冲击窗口。

## 目标
验证微调邻域稳定性，单调收敛概率 >= 95.0%。

## 预期产出路径
- `zcode/reports/0300-analysis.md`
- `docs/analysis/0300-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0300-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0300-analysis.md`，状态修改为 `status: done`。

## 合规守则
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0301",
                "title": "极端高负载宿主机下 UDP 丢包重传尾部延迟对冲",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0301 任务：极端高负载宿主机下 UDP 丢包重传尾部延迟对冲

## 任务背景
在大文件阶段（5.bin 与 6.bin），仿真宿主机遭遇外部高负载突发时的 QUIC 尾部丢包重传惩罚，验证 pacing 抑制定律。

## 目标
证明平滑 pacing 下重传次数下降 >= 80.0%，尾部 P99 延迟压缩 <= 15ms。

## 预期产出路径
- `zcode/reports/0301-analysis.md`
- `docs/analysis/0301-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0301-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0301-analysis.md`，状态修改为 `status: done`。

## 合规守则
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_dawn_0200 (02:00) ----------------
    {
        "batch_id": "batch_dawn_0200",
        "target_time": "02:00",
        "tasks": [
            {
                "id": "0302",
                "title": "Shot 4 真机出分捕获与全国第一绝杀点位校验",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0302 任务：Shot 4 真机出分捕获与全国第一绝杀点位校验

## 任务背景
捕获 Shot 4 真机出分，若已击败第一名（<117.0257s），启动保分与统一复测防护；若仍有微小差距，计算 Shot 5 绝杀概率。

## 目标
完成绝杀边界灵敏度分析，判定决胜状态机转移至 Shot 5 冲顶或收官。

## 预期产出路径
- `zcode/reports/0302-analysis.md`
- `docs/analysis/0302-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0302-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0302-analysis.md`，状态修改为 `status: done`。

## 合规守则
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0303",
                "title": "Shot 5 终局压轴发全油门冲击策略裁决",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0303 任务：Shot 5 终局压轴发全油门冲击策略裁决

## 任务背景
今日官方最后一发（5/5 终局之战），根据前 4 发最优成绩与全场排名，执行绝对冲刺或最终护城河锁定。

## 目标
验证 Shot 5 裁决逻辑无死循环，全场最优成绩确定性极大化。

## 预期产出路径
- `zcode/reports/0303-analysis.md`
- `docs/analysis/0303-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0303-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0303-analysis.md`，状态修改为 `status: done`。

## 合规守则
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            },
            {
                "id": "0304",
                "title": "全 5 发端到端闭环自适应实验归档与复盘模型构建",
                "content": """status: open
priority: 1
assignee: zcode
created: {created_time}

# 0304 任务：全 5 发端到端闭环自适应实验归档与复盘模型构建

## 任务背景
在 11/08 5 发官方提交全部出分并登榜后，全面归档真机出分、排名跃迁、各阶段下载耗时、闭环决策记录，完成终极复盘。

## 目标
生成完整 11/08 决战复盘报告与全景数据报表，验证反过拟合纪律与大样本复测一致性。

## 预期产出路径
- `zcode/reports/0304-analysis.md`
- `docs/analysis/0304-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/0304-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0304-analysis.md`，状态修改为 `status: done`。

## 合规守则
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
"""
            }
        ]
    }
'''

    func_marker = "def log(msg:"
    idx = content.find(func_marker)
    if idx == -1:
        print("Function marker def log not found")
        return False

    sub_content = content[:idx]
    last_bracket = sub_content.rfind("]")
    if last_bracket == -1:
        print("Last bracket not found")
        return False

    updated_content = content[:last_bracket] + new_batches_code + content[last_bracket:]
    disp_path.write_text(updated_content, encoding="utf-8")
    print("Successfully extended batches with campaign batches up to batch_dawn_0200 (Tasks 0293 ~ 0304)!")
    return True

if __name__ == "__main__":
    extend_campaign_batches()
