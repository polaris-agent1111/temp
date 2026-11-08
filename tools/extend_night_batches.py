#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extend zcode_continuous_dispatcher.py with tonight's deep research batches (batch_tonight_1830 ~ batch_tonight_2100).
Covering tasks 0257 ~ 0274 across 6 batches.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DISPATCHER_FILE = ROOT / "tools" / "zcode_continuous_dispatcher.py"

BATCH_DEFS = [
    {
        "batch_id": "batch_tonight_1830",
        "target_time": "18:30",
        "tasks": [
            ("0257", "网络接口 MTU 探测与巨型帧分片开销在浅缓冲区下的性能边界", "计算分片丢包临界点并量化 1200B 安全边界", "测试不同 MTU 设置下的分片开销并评估浅队列下的分片丢失风险"),
            ("0258", "零拷贝数据包发送路径与内核环形缓冲区溢出防御", "验证 90Mbps 线速下 ring buffer 零丢包", "测试用户态 UDP 数据包直接发送与内核 ring buffer 占用率"),
            ("0259", "针对 11/08 00:05 启动前 60 分钟自动化演练回放", "验证全自动化调度流水线 60 分钟演练 100% 顺畅", "回放 1-by-1 自适应决策引擎在开打前的模拟流程"),
        ]
    },
    {
        "batch_id": "batch_tonight_1900",
        "target_time": "19:00",
        "tasks": [
            ("0260", "多客户端并发下的官方判分队列排队延迟拟合", "建立多队伍提交排队模型并预测出分延迟分布", "拟合高峰期官方判分队列等待时间的非参数分布"),
            ("0261", "拥塞窗口突发重置与恢复时延下限分析", "证明窗口突发重置后恢复时间 <= 2.5 RTT", "分析在偶发丢包后窗口快速乘性减与快速恢复时间下界"),
            ("0262", "决选专家答辩现场 3 分钟极简陈述提纲", "产出结构化 3 分钟白板讲解脚本与核心数字清单", "提炼项目 256 项科研成果为 3 分钟高密度答辩讲义"),
        ]
    },
    {
        "batch_id": "batch_tonight_1930",
        "target_time": "19:30",
        "tasks": [
            ("0263", "基于隐马尔可夫模型 HMM 的信道多状态自适应推断", "验证前向后向算法在 3 个状态间推断准确率 >= 92%", "利用 HMM 建模信道在空闲、轻载、重载状态间的转移概率"),
            ("0264", "QUIC 握手 0-RTT 与 1-RTT 密钥交换能耗与时间对比", "量化 0-RTT 重放保护开销与首次连接延迟", "比较两种握手模式在首发下载中的建连耗时与安全边界"),
            ("0265", "官方 6 目录配置热切换原子性在极限并发下的压力测试", "验证 1000 次高频并发读取无半文件现象", "模拟评测客户端高频读取时配置树覆写的原子性"),
        ]
    },
    {
        "batch_id": "batch_tonight_2000",
        "target_time": "20:00",
        "tasks": [
            ("0266", "瓶颈网络主动丢包与无源排队时延交叉度量", "计算主动标记与排队膨胀的联合分布相关系数", "交叉对比排队时延增长与丢包发生的时域同步性"),
            ("0267", "帕累托最优前沿面离散点邻域鲁棒性扰动再验证", "验证在 +-1 包速率扰动下用时恶化 <= 0.8s", "对 Crown Fusion 6 阶段离散点进行全维度局部扰动测试"),
            ("0268", "11/08 首发倒计时 6 小时全员战备令与封板签字", "完成 6 小时战备令各项合规签署并落盘证书", "对系统进行 6 小时倒计时战备巡检与终审盖章"),
        ]
    },
    {
        "batch_id": "batch_tonight_2030",
        "target_time": "20:30",
        "tasks": [
            ("0269", "官方计分机制对极端离群值的截断与滤波行为审计", "验证多次取平均机制下鲁棒均值估计的最优性", "研究官方榜单对单次异常高分或低分的滤波鲁棒性"),
            ("0270", "客户端用户态时钟漂移在长时间运行下的累积误差评估", "验证 8 小时连续运行累计漂移 <= 15us", "长周期测试用户态时钟源单调性与漂移补偿精度"),
            ("0271", "答辩 PPT 终版关键图表高清生成与落盘核验", "生成 5 张高清晰度核心矢量相图与结构拓扑图", "渲染相空间吸引子、DDE 根轨迹与 Sobol 方差分解高清图"),
        ]
    },
    {
        "batch_id": "batch_tonight_2100",
        "target_time": "21:00",
        "tasks": [
            ("0272", "针对全国 Top 3 竞争对手历史最优轨迹的高精度逆向拟合", "拟合 Catnet 与光明未来 6 阶段速率组合", "利用其公开出分耗时反演对手可能采用的整形参数"),
            ("0273", "极端偶发断网下客户端本地持久化与重发幂等性保证", "验证网络中断 30s 恢复后提交状态 100% 保持", "测试断网环境下状态机防重发与自愈能力"),
            ("0274", "全国总决赛出征前夜终极战备封箱证书 v3", "封装 274 项科研任务并签署最终出征令", "完成最终阶段全量成果封存并签署总决赛出征令"),
        ]
    }
]

def generate_batch_code(batch_def):
    bid = batch_def["batch_id"]
    ttime = batch_def["target_time"]
    tasks_code = []
    for tid, title, target, bg in batch_def["tasks"]:
        t_block = f'''            {{
                "id": "{tid}",
                "title": "{title}",
                "content": """status: open
priority: 2
assignee: zcode
created: {{created_time}}

# {tid} 任务：{title}

## 任务背景
{bg}。

## 考核目标
{target}。

## 预期产出路径
- `zcode/reports/{tid}-analysis.md`
- `docs/analysis/{tid}-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成理论分析成果写入 `docs/analysis/{tid}-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/{tid}-analysis.md`，将状态修改为 `status: done`。

## 严格红线
- 严禁向远程平台提交榜单，严禁修改实盘提交凭据。
"""
            }}'''
        tasks_code.append(t_block)
    
    tasks_joined = ",\n".join(tasks_code)
    return f'''    # ---------------- 批次：{bid} ({ttime}) ----------------
    {{
        "batch_id": "{bid}",
        "target_time": "{ttime}",
        "tasks": [
{tasks_joined}
        ]
    }}'''

def main():
    content = DISPATCHER_FILE.read_text(encoding="utf-8")
    if '"batch_tonight_1830"' in content:
        print("Tonight batches already registered.")
        return 0
        
    code_blocks = [generate_batch_code(b) for b in BATCH_DEFS]
    full_addition = ",\n" + ",\n".join(code_blocks)
    
    marker = "]\n\ndef log("
    idx = content.rfind(marker)
    if idx == -1:
        print("Error: Could not locate TASK_BATCHES closing marker.")
        return 1
        
    new_content = content[:idx] + full_addition + "\n" + content[idx:]
    DISPATCHER_FILE.write_text(new_content, encoding="utf-8")
    print("Successfully injected tonight batches (batch_tonight_1830 ~ batch_tonight_2100) into zcode_continuous_dispatcher.py!")
    return 0

if __name__ == "__main__":
    main()
