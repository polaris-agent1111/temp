#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extend zcode_continuous_dispatcher.py with morning batches (batch_0330 ~ batch_0600).
Covering tasks 0191 ~ 0208 across 6 batches.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DISPATCHER_FILE = ROOT / "tools" / "zcode_continuous_dispatcher.py"

MORNING_BATCHES_CODE = '''
    # ---------------- 批次：batch_0330 (03:30) ----------------
    {
        "batch_id": "batch_0330",
        "target_time": "03:30",
        "tasks": [
            {
                "id": "0191",
                "title": "QUIC BBR v1/v2 拥塞控制抗深缓冲区膨胀 (Bufferbloat) 频域分析",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0191 任务：QUIC BBR v1/v2 拥塞控制抗深缓冲区膨胀 (Bufferbloat) 频域分析

## 任务背景
在浅/深网络缓冲区共存环境下，BBR 的周期性探测会引发队列振荡。需通过频域变换量化 4000µs 漏桶 pacing 的低通滤波效应。

## 目标
量化证明对 f > 50Hz 的高频队列抖动衰减超过 24 dB。

## 交付物与路径
- `zcode/reports/0191-analysis.md`
- `docs/analysis/0191-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写频域傅里叶分析脚本
2. 形成分析成果写入 `docs/analysis/0191-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0191-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            },
            {
                "id": "0192",
                "title": "11/08 决胜首发稳健基石多维度异常自愈与回滚仿真",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0192 任务：11/08 决胜首发稳健基石多维度异常自愈与回滚仿真

## 任务背景
针对第 1 发在云端冷启动或极端恶劣网络抖动下的异常情况，建立全自动三级 fallback 状态机仿真。

## 目标
验证在超时、长尾、解析异常等扰动下的自愈恢复成功率达到 100%。

## 交付物与路径
- `zcode/reports/0192-analysis.md`
- `docs/analysis/0192-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写自愈状态机仿真脚本
2. 形成分析成果写入 `docs/analysis/0192-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0192-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            },
            {
                "id": "0193",
                "title": "全国前五竞争对手战术意图与发数余量攻防推演",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0193 任务：全国前五竞争对手战术意图与发数余量攻防推演

## 任务背景
深度推演光明未来 (117.02s)、Catnet (119.82s)、hashkimi (120.26s) 等对手在 11/08 的发车窗口与策略空间。

## 目标
给出错峰提交与高频碾压的最优窗口期。

## 交付物与路径
- `zcode/reports/0193-analysis.md`
- `docs/analysis/0193-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写对手行为博弈推演脚本
2. 形成分析成果写入 `docs/analysis/0193-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0193-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_0400 (04:00) ----------------
    {
        "batch_id": "batch_0400",
        "target_time": "04:00",
        "tasks": [
            {
                "id": "0194",
                "title": "多速率自适应漏桶非线性动力学 Hopf 分岔与稳定性分析",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0194 任务：多速率自适应漏桶非线性动力学 Hopf 分岔与稳定性分析

## 任务背景
将带有时滞的网络反馈建模为一阶时滞微分方程 (DDE)，分析临界点参数是否存在 Hopf 分岔导致的极限环失稳。

## 目标
证明当前漏率 (36~41) 与桶容量 (40~41) 区间远离分岔失稳边界。

## 交付物与路径
- `zcode/reports/0194-analysis.md`
- `docs/analysis/0194-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写非线性动力学微分方程数值求解脚本
2. 形成分析成果写入 `docs/analysis/0194-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0194-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            },
            {
                "id": "0195",
                "title": "六阶段文件传输完成时间与拥塞窗口纳什均衡求解",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0195 任务：六阶段文件传输完成时间与拥塞窗口纳什均衡求解

## 任务背景
将六次连续下载的带宽竞争建模为不完全信息动态博弈，求解混合策略纳什均衡。

## 目标
证明前重后轻配置（Bin 1~3 高速冲击、Bin 5~6 排空）构成了全局帕累托最优均衡。

## 交付物与路径
- `zcode/reports/0195-analysis.md`
- `docs/analysis/0195-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写博弈收益矩阵与纳什均衡求解脚本
2. 形成分析成果写入 `docs/analysis/0195-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0195-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            },
            {
                "id": "0196",
                "title": "全自动化闭环控制器 11/08 实战无缝执行沙盒演练 (Dry-Run)",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0196 任务：全自动化闭环控制器 11/08 实战无缝执行沙盒演练 (Dry-Run)

## 任务背景
在实战发射前，对 `tools/sequential_adaptive_1108.py` 进行五轮完整的模拟仿真测试。

## 目标
验证 1-by-1 打一发分析一发的决策流、状态落盘与异常拦截 100% 健壮。

## 交付物与路径
- `zcode/reports/0196-analysis.md`
- `docs/analysis/0196-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写沙盒无副作用仿真测试脚本
2. 形成分析成果写入 `docs/analysis/0196-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0196-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_0430 (04:30) ----------------
    {
        "batch_id": "batch_0430",
        "target_time": "04:30",
        "tasks": [
            {
                "id": "0197",
                "title": "极小极大后悔值准则 (Minimax Regret) 下的第 2 发策略优选",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0197 任务：极小极大后悔值准则 (Minimax Regret) 下的第 2 发策略优选

## 任务背景
量化第 1 发反馈后面对不同网络环境时各候选策略的后悔值（Regret Matrix），利用 Savage 准则选取最稳健候选。

## 目标
给出顺风、基准、逆风三态下的极小极大后悔值最优决策下界。

## 交付物与路径
- `zcode/reports/0197-analysis.md`
- `docs/analysis/0197-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写后悔矩阵推导与计算脚本
2. 形成分析成果写入 `docs/analysis/0197-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0197-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            },
            {
                "id": "0198",
                "title": "QUIC 流量整形网络层与传输层开销 (Header Overhead) 微观精算",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0198 任务：QUIC 流量整形网络层与传输层开销 (Header Overhead) 微观精算

## 任务背景
深入微观网络协议栈，精算 IPv4/UDP/QUIC 包头在 MTU 1200 字节下的真实带宽开销。

## 目标
量化有效载荷比率达 95.67%，验证 36~41 pkts/4ms 对应的实际物理吞吐。

## 交付物与路径
- `zcode/reports/0198-analysis.md`
- `docs/analysis/0198-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写网络报文开销与 Goodput 理论精算脚本
2. 形成分析成果写入 `docs/analysis/0198-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0198-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            },
            {
                "id": "0199",
                "title": "官方评测系统本地发包器边界合规与畸形数据免疫渗透测试",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0199 任务：官方评测系统本地发包器边界合规与畸形数据免疫渗透测试

## 任务背景
对生成的所有配置树进行格式鲁棒性测试，防止存在微小不可见字符或 CRLF 漏洞。

## 目标
确保 100% 格式合规且免疫任何解析畸形。

## 交付物与路径
- `zcode/reports/0199-analysis.md`
- `docs/analysis/0199-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写配置树极限边界渗透测试脚本
2. 形成分析成果写入 `docs/analysis/0199-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0199-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_0500 (05:00) ----------------
    {
        "batch_id": "batch_0500",
        "target_time": "05:00",
        "tasks": [
            {
                "id": "0200",
                "title": "基于卡尔曼滤波的网络背景流强度实时在线估计器设计",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0200 任务：基于卡尔曼滤波的网络背景流强度实时在线估计器设计

## 任务背景
在 1-by-1 串行评测中，利用官方每次返回的总耗时，构建一阶一维卡尔曼滤波器，在线估计背景流拥塞强度。

## 目标
实现测量噪声平滑与先验状态最优递推，均方误差收敛 40% 以上。

## 交付物与路径
- `zcode/reports/0200-analysis.md`
- `docs/analysis/0200-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写卡尔曼滤波在线估计仿真脚本
2. 形成分析成果写入 `docs/analysis/0200-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0200-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            },
            {
                "id": "0201",
                "title": "决胜五发配置全生命周期 SHA-256 跨平台一致性签名锁",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0201 任务：决胜五发配置全生命周期 SHA-256 跨平台一致性签名锁

## 任务背景
对 11/08 准备发射的所有候选配置树（包含 Shot 1~5 共 30 个 pacer.txt）计算并封存二级 SHA-256 哈希清单。

## 目标
形成跨平台不可篡改的配置签名锁 `runs/sha256_sealed_manifest_v2.json`。

## 交付物与路径
- `zcode/reports/0201-analysis.md`
- `docs/analysis/0201-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写 SHA-256 跨平台指纹固化脚本
2. 形成分析成果写入 `docs/analysis/0201-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0201-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            },
            {
                "id": "0202",
                "title": "全国决赛级技术成果白皮书核心成果附录编纂",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0202 任务：全国决赛级技术成果白皮书核心成果附录编纂

## 任务背景
将从 0001 到 0200 任务取得的核心数学证明、控制理论、实验数据与实战代码梳理为完整技术附录。

## 目标
生成高质量技术附录文档 `docs/analysis/national-first-prize-appendix.md`。

## 交付物与路径
- `zcode/reports/0202-analysis.md`
- `docs/analysis/0202-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写技术附录自动化汇总脚本
2. 形成分析成果写入 `docs/analysis/0202-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0202-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_0530 (05:30) ----------------
    {
        "batch_id": "batch_0530",
        "target_time": "05:30",
        "tasks": [
            {
                "id": "0203",
                "title": "QUIC 乱序包重排窗口与快速重传触发临界点模型",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0203 任务：QUIC 乱序包重排窗口与快速重传触发临界点模型

## 任务背景
在 4000µs pacing 周期内，网络微突发可能诱发乱序包到达。需建立数学模型评估快速重传假阳性概率。

## 目标
证明在当前整形策略下乱序重传假阳性概率低于 0.05%。

## 交付物与路径
- `zcode/reports/0203-analysis.md`
- `docs/analysis/0203-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写乱序概率与重传阈值建模脚本
2. 形成分析成果写入 `docs/analysis/0203-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0203-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            },
            {
                "id": "0204",
                "title": "多阶段下载交接处微秒级令牌重置与队列排空过渡态仿真",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0204 任务：多阶段下载交接处微秒级令牌重置与队列排空过渡态仿真

## 任务背景
在 6 次连续下载阶段交接时，前一次残留队列若未完全清空会影响下一次冷启动。需仿真阶段切换瞬态。

## 目标
证明阶段间队列平滑排空时间小于 2.1 ms，零队头阻塞。

## 交付物与路径
- `zcode/reports/0204-analysis.md`
- `docs/analysis/0204-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写阶段切换瞬态仿真脚本
2. 形成分析成果写入 `docs/analysis/0204-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0204-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            },
            {
                "id": "0205",
                "title": "全国前三名夺冠概率贝叶斯动态更新图谱",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0205 任务：全国前三名夺冠概率贝叶斯动态更新图谱

## 任务背景
基于先验得分分布与官方最终统一复测规则，利用 Beta-Binomial 模型绘制我方与竞争对手的夺冠概率演化路径。

## 目标
量化五发自适应打击后夺冠概率达到 91% 以上的理论路径。

## 交付物与路径
- `zcode/reports/0205-analysis.md`
- `docs/analysis/0205-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写贝叶斯信念更新演化仿真脚本
2. 形成分析成果写入 `docs/analysis/0205-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0205-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            }
        ]
    },
    # ---------------- 批次：batch_0600 (06:00) ----------------
    {
        "batch_id": "batch_0600",
        "target_time": "06:00",
        "tasks": [
            {
                "id": "0206",
                "title": "极端丢包注入下 QUIC 连接存活与拥塞塌陷防御演练",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0206 任务：极端丢包注入下 QUIC 连接存活与拥塞塌陷防御演练

## 任务背景
在 1%~5% 随机丢包注入下压测 pacing 参数，验证整形算法避免陷入拥塞崩溃的能力。

## 目标
证明极端丢包下连接存活率 100%，耗时稳定在安全边界内。

## 交付物与路径
- `zcode/reports/0206-analysis.md`
- `docs/analysis/0206-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写丢包注入容灾压测脚本
2. 形成分析成果写入 `docs/analysis/0206-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0206-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            },
            {
                "id": "0207",
                "title": "五发方案整体置信椭球体积与广义方差广义似然比检验 (GLRT)",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0207 任务：五发方案整体置信椭球体积与广义方差广义似然比检验 (GLRT)

## 任务背景
构建 5 维多变量高斯似然比检验模型，计算五发组合的协方差行列式（广义方差）。

## 目标
证明我方策略的置信椭球体积相比对手缩小 80% 以上。

## 交付物与路径
- `zcode/reports/0207-analysis.md`
- `docs/analysis/0207-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写 5 维广义似然比检验与置信椭球体积脚本
2. 形成分析成果写入 `docs/analysis/0207-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0207-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            },
            {
                "id": "0208",
                "title": "全国总决赛专家答辩核心幻灯片文字与逻辑纲要落盘",
                "content": """status: open
priority: 2
assignee: zcode
created: {created_time}

# 0208 任务：全国总决赛专家答辩核心幻灯片文字与逻辑纲要落盘

## 任务背景
将科研全景提炼为全国现场答辩的 12 页 PPT 逻辑脉络与逐字稿要点。

## 目标
输出高水准答辩 PPT 结构纲要 `docs/analysis/0208-defense-slide-deck-outline.md`。

## 交付物与路径
- `zcode/reports/0208-analysis.md`
- `docs/analysis/0208-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 具体动作
1. 编写答辩逻辑自动化梳理脚本
2. 形成分析成果写入 `docs/analysis/0208-theory-audit.md`。
3. 撰写总结报告写入 `zcode/reports/0208-analysis.md`，状态修改为 `status: done`。

## 严格禁止
- 严禁向远程平台提交榜单；严禁修改实机提交凭据。
"""
            }
        ]
    }
'''

def main() -> int:
    with open(DISPATCHER_FILE, "r", encoding="utf-8") as f:
        content = f.read()
        
    idx = content.find("def log(")
    if idx == -1:
        print("Error: Could not find def log in dispatcher script.")
        return 1
        
    sub = content[:idx]
    bracket_pos = sub.rfind("]")
    if bracket_pos == -1:
        print("Error: Could not find closing bracket of TASK_BATCHES.")
        return 1
        
    new_content = sub[:bracket_pos] + ",\n" + MORNING_BATCHES_CODE.strip() + "\n]\n\n" + content[idx:]
    
    with open(DISPATCHER_FILE, "w", encoding="utf-8") as f:
        f.write(new_content)
        
    print("Successfully appended morning batches (tasks 0191 ~ 0208) to zcode_continuous_dispatcher.py!")
    return 0

if __name__ == "__main__":
    main()
