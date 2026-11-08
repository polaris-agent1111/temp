#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""向 zcode_continuous_dispatcher.py 自动化扩充晚间深水区批次库（17:30 ~ 19:00 批次）.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DISPATCHER_FILE = ROOT / "tools" / "zcode_continuous_dispatcher.py"

LATE_EVENING_BATCHES = [
    # ---------------- 批次：batch_1730 (17:30) ----------------
    ("batch_1730", "17:30", [
        ("0131", "BBR 与 CUBIC 在非平稳背景流竞争下的 Jain 公平性指数时间演化方程", "推导控速流在不同排空余量下与背景 CUBIC/BBR 竞争时的 Jain 公平性指数演化轨迹。"),
        ("0132", "基于高斯混合模型 (GMM) 的测试床多模态时延聚类与离群点识别", "利用 EM 算法拟合 94 场实测样本的多模态分布，精确剔除极端偶发离群点。"),
        ("0133", "微突发注入对交换机虚拟 FIFO 队列缓冲占用的拉普拉斯变换极点分析", "在频域求解队列瞬态阻尼比与共振极点，证明 4ms 周期系统处于过阻尼区。")
    ]),
    # ---------------- 批次：batch_1800 (18:00) ----------------
    ("batch_1800", "18:00", [
        ("0134", "端到端网络 RTT 相位同步对 QUIC Pacing 发包抖动的频域谐波分析", "建立发包时钟与网络 RTT 反馈相位的傅里叶频域模型，分析混叠谐波抑制。"),
        ("0135", "针对官方评测打榜 API 调用的指数退避与分布式重试熔断器设计", "设计面向 11/08 打榜的高可用 API 访问熔断器，保障网络抖动下 100% 稳态通信。"),
        ("0136", "全量 130+ 审计报告与数理交付物哈希索引链与 Markdown 知识图谱生成", "构建从 0041 至 0136 全部交付报告的完整技术拓扑图与 SHA-256 哈希链。")
    ]),
    # ---------------- 批次：batch_1830 (18:30) ----------------
    ("batch_1830", "18:30", [
        ("0137", "QUIC 拥塞窗口快速重传定时器在微突发丢包下的幂律衰减动力学", "严格推导突发丢包触发快速重传时的拥塞窗口衰减幂律指数。"),
        ("0138", "网络流长 Pareto 重尾指数对稳态排空余量的最坏情景弹性系数测定", "计算背景流 Pareto 重尾参数 alpha 摄动时，排空余量对溢出概率的弹性系数。"),
        ("0139", "基于鞅论 (Martingale Theory) 的多轮复测均值上确界停时定理证明", "利用 Doob 鞅收敛定理证明 5 轮复测均值严格以概率 1 收敛至真值。")
    ]),
    # ---------------- 批次：batch_1900 (19:00) ----------------
    ("batch_1900", "19:00", [
        ("0140", "11/07 晚间 19:00 对手反扑监测与前十战队动作全景雷达", "全盘扫描晚间 19 点榜单变动，评估 Catnet 与其他队伍在晚高峰的提交动作。"),
        ("0141", "多核多线程并发评测环境下 CPU 缓存失效与 TLB 击穿开销测度", "量化评测容器多核进程并发时的 L2/L3 Cache 污染与页表失效边界。"),
        ("0142", "面向决赛终评的一等奖技术创新点与答辩核心说服力矩阵编排", "提炼六大核心技术创新点，编排国家一等奖答辩的说服力矩阵。")
    ])
]

def format_batch(batch_id, target_time, tasks):
    task_entries = []
    for tid, title, desc in tasks:
        content = f"""status: open
priority: 2
assignee: zcode
created: {{created_time}}

# {tid} — {title}

## 背景
{desc} 本项任务服务于全国第一夺冠成果巩固、物理抗抖动建模与 11/08 闭环自适应逐发决策。

## 目标
产出具有深度学术价值与工程说服力的数理分析与审计交付件。

## 允许写的路径
- `zcode/reports/{tid}-analysis.md`
- `docs/analysis/{tid}-theory-audit.md`
- `zcode/scripts/` 目录下的辅助分析计算脚本

## 具体动作
1. 深入建模并编写 Python 验证脚本；
2. 形成分析成果写入 `docs/analysis/{tid}-theory-audit.md`；
3. 撰写标准交付报告写入 `zcode/reports/{tid}-analysis.md`，并将任务头部修改为 `status: done`。

## 禁止
- 不登录平台、不提交榜单、不修改真实提交凭据。
"""
        task_entries.append(f"""            {{
                "id": "{tid}",
                "title": "{title}",
                "content": \"\"\"{content}\"\"\"
            }}""")
    
    tasks_str = ",\n".join(task_entries)
    return f"""    # ---------------- 批次：{batch_id}（{target_time}） ----------------
    {{
        "batch_id": "{batch_id}",
        "target_time": "{target_time}",
        "tasks": [
{tasks_str}
        ]
    }}"""

def main():
    text = DISPATCHER_FILE.read_text("utf-8")
    
    if "batch_1730" in text:
        print("已经是扩充后的批次，无需重复追加。")
        return 0
        
    formatted_batches = []
    for bid, tm, tlist in LATE_EVENING_BATCHES:
        formatted_batches.append(format_batch(bid, tm, tlist))
        
    all_new_str = ",\n" + ",\n".join(formatted_batches) + "\n]"
    
    idx = text.rfind("\n]")
    if idx == -1:
        print("找不到 TASK_BATCHES 闭合括号！")
        return 1
        
    new_text = text[:idx] + all_new_str + text[idx+2:]
    DISPATCHER_FILE.write_text(new_text, encoding="utf-8")
    print(f"成功将 {len(LATE_EVENING_BATCHES)} 个新批次（共 {len(LATE_EVENING_BATCHES)*3} 项高强度任务）追加至 {DISPATCHER_FILE.name}！")
    return 0

if __name__ == "__main__":
    sys.exit(main())
