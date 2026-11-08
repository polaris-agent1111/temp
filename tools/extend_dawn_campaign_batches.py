# -*- coding: utf-8 -*-
"""
Extend zcode continuous dispatcher with dawn battle batches (01:00 - 04:00)
Covering Tasks 0344 to 0364 for continuous high-intensity execution on 11/08.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DISPATCHER_PATH = ROOT / "tools" / "zcode_continuous_dispatcher.py"

def build_batch(batch_id, target_time, tasks_info):
    task_entries = []
    for tid, title, bg, goal in tasks_info:
        task_str = f"""            {{
                "id": "{tid}",
                "title": "{title}",
                "content": \"\"\"status: open
priority: 1
assignee: zcode
created: {{created_time}}

# {tid} 任务：{title}

## 任务背景
{bg}

## 目标
{goal}

## 预期产出路径
- `zcode/reports/{tid}-analysis.md`
- `docs/analysis/{tid}-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成分析写入 `docs/analysis/{tid}-theory-audit.md`；
3. 撰写总结研报写入 `zcode/reports/{tid}-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改真实提交凭据。
\"\"\"
            }}"""
        task_entries.append(task_str)
    
    joined = ",\n".join(task_entries)
    return f"""    # ---------------- 批次：{batch_id} ({target_time}) ----------------
    {{
        "batch_id": "{batch_id}",
        "target_time": "{target_time}",
        "tasks": [
{joined}
        ]
    }}"""

dawn_batches = [
    ("batch_campaign_0100", "01:00", [
        ("0344", "Shot-1-实测成绩微观信道特征提取与基准校准", "基于 Shot 1 真实出分数据，提取微秒级瓶颈信道吞吐与背景流特征。", "信道容量估计精度 >= 95.0%，后验方差降幅 >= 60.0%。"),
        ("0345", "Shot-2-皇冠冲顶与超宽平台多准则效用函数贝叶斯决策", "在 Shot 1 出分后，对皇冠冲顶与超宽平台方案进行多准则期望效用量化。", "决策置信度 >= 95.0%，期望遗憾度 Regret <= 0.05。"),
        ("0346", "高并发微秒级令牌桶漏出方差与跨流时延抖动分解", "分析 bucket_cap=40 与 leak_interval=4000us 在多流并发下的方差衰减。", "抖动方差衰减率 >= 80.0%，零主动丢包。")
    ]),
    ("batch_campaign_0130", "01:30", [
        ("0347", "基于李代数群 SO(3) 的六轮次速率流形对称性与退化阻尼", "运用 Lie Group SO(3) 对 6 轮次速率向量流形进行群对称性约束与退化阻尼分析。", "流形曲率保持在 [0.01, 0.05]，退化阻尼因子 >= 0.85。"),
        ("0348", "自适应 QUIC ACK 压缩在线检测与滑动平滑滤波补偿", "针对反向信道可能发生的 ACK 堆叠与脉冲释放，构建二阶滑动平滑滤波补偿器。", "ACK 堆叠平滑滤除率 >= 90.0%，突发脉冲因子 F <= 1.05。"),
        ("0349", "官方排行榜 top 10 竞争者动态演进马尔可夫链转移概率估计", "构建 top 10 竞争者分数动态演进的一阶马尔可夫链状态转移矩阵。", "状态预测准确率 >= 88.0%，榜首击穿概率置信度 >= 95.0%。")
    ]),
    ("batch_campaign_0200", "02:00", [
        ("0350", "Shot-2-出分后验高斯过程主动学习后验采样与 Shot-3 点位重构", "吸收 Shot 2 真机出分，利用 GPR 进行期望提升 (EI) 采样优化 Shot 3 构型。", "代理模型后验 MSE <= 0.01，局部最优发现概率 >= 95.0%。"),
        ("0351", "非对称排队网络吉布斯采样与瓶颈路由器驻留时间泛函推演", "使用 Gibbs 采样推演 6 个轮次在瓶颈路由器排队驻留时间的概率泛函。", "泛函收敛误差 <= 2.0%，稳态分布逼近度 >= 95.0%。"),
        ("0352", "官方统一复测十场均值极端重尾蒙特卡洛应力测试 (1,000,000 次抽样)", "对官方 10 场抽样复测进行百万次重尾碰撞仿真，量化夺冠数学确定性。", "百万次抽样冠军保持率 >= 99.5%，下侧 CVaR-99 >= 116.5s。")
    ]),
    ("batch_campaign_0230", "02:30", [
        ("0353", "Shot-3-出分成绩吸收与前三名位次锁定稳定性度量", "吸收 Shot 3 真机成绩，评估全国前三名锁定稳健性与位次弹性。", "前三名锁定率 100.0%，位次弹性绝对值 <= 0.10。"),
        ("0354", "微秒级网络栈中断聚合对 Pacing 定时精度的扰动分析与软时钟补偿", "分析网卡 GRO/LRO 及中断聚合对 4000us Pacing 的扰动并设计软补偿算法。", "时钟抖动滤除率 >= 92.0%，发包间隔标准差 <= 20us。"),
        ("0355", "基于库恩-塔克 (KKT) 条件的六流流量整形多目标凸优化解析解", "构建以最大化总吞吐并最小化方差为目标的带约束拉格朗日凸优化模型。", "KKT 互补松弛性满足度 100.0%，理论最优解差距 <= 0.5%。")
    ]),
    ("batch_campaign_0300", "03:00", [
        ("0356", "Shot-4-决胜绝杀点位自适应探索与方差极小化联合优化", "结合 Shot 1~3 累积出分流形，求解 Shot 4 兼顾冲分与极低方差的Pareto前沿。", "Pareto 最优解优度 >= 95.0%，预期提速 >= 0.8s。"),
        ("0357", "跨轮次连接状态持久化与快速重传防饿死动态权重配比", "验证 1 至 6 轮次状态继承时的在途数据持久化与 ACK 丢包防饿死机制。", "重传恢复延迟 <= 1.0 RTT，防饿死保护率 100.0%。"),
        ("0358", "多租户浅队列博弈演化博弈 ESS 进化稳定策略证明", "运用复制动态方程证明 4000us 均匀 Pacing 策略在浅队列博弈中为严格 ESS。", "ESS 吸引子收敛速度 >= 0.85，抗扰稳定性 100.0%。")
    ]),
    ("batch_campaign_0330", "03:30", [
        ("0359", "Shot-4-出分击穿全国第一后验概率更新与冠军位次加固", "吸收 Shot 4 真实出分，更新全国第一确认率并量化对复测波动的抗性。", "全国第一确认率 >= 98.0%，防守安全边际 >= 1.5s。"),
        ("0360", "QUIC 协议栈多流乱序重组缓冲区溢出边界形式化验证", "在极端丢包和乱序场景下形式化验证重组缓冲区最大深度不超过上界。", "无缓冲区溢出，零丢包恢复 100.0%。"),
        ("0361", "端到端纳秒级单调时钟漂移在千兆交换机下的自适应卡尔曼滤波", "针对微秒级流量整形设计高精度在线漂移估计卡尔曼滤波器。", "滤波稳态误差 <= 15us，发包准时率 >= 99.8%。")
    ]),
    ("batch_campaign_0400", "04:00", [
        ("0362", "Shot-5-终局压轴发极值分布威布尔吸引域精确参数辨识", "运用极值理论 (EVT) 对 Shot 5 极小值分布进行极大似然参数辨识。", "威布尔形状参数 xi < 0，极值物理下界明确可信。"),
        ("0363", "全 5 发实战全链路端到端数据完整性穿透审查与复现度核对", "对 runs/ 下所有单发 plan、提交回执及官方出分进行全哈希审计。", "数据链路审计通过率 100.0%，证据链完整度 100.0%。"),
        ("0364", "全国总决赛技术决胜终极证据链 Grand Master Seal v6 签发", "对全仓库所有实验数据、数理推导报告与代码资产进行 Merkle Tree 最终签发。", "封印资产数 >= 1000 项，防篡改防抵赖保证 100.0%。")
    ])
]

def main():
    content = DISPATCHER_PATH.read_text(encoding="utf-8")
    
    # 查找 TASK_BATCHES 的末尾，即最后一个 def log 之前
    idx = content.rfind("def log(")
    if idx == -1:
        print("[ERROR] 无法找到 def log(")
        return 1
        
    pos_bracket = content.rfind("]", 0, idx)
    if pos_bracket == -1:
        print("[ERROR] 无法找到 TASK_BATCHES 的结尾中括号 ']'")
        return 1
        
    # 生成新批次代码
    new_batches_code = ",\n" + ",\n".join([build_batch(bid, t, tasks) for bid, t, tasks in dawn_batches])
    
    # 在 pos_bracket 之前插入
    new_content = content[:pos_bracket] + new_batches_code + "\n" + content[pos_bracket:]
    
    DISPATCHER_PATH.write_text(new_content, encoding="utf-8")
    print(f"[SUCCESS] 成功向 TASK_BATCHES 追加 {len(dawn_batches)} 个晨间决战批次（覆盖 0344 ~ 0364 共 21 项任务）！")
    return 0

if __name__ == "__main__":
    sys.exit(main())
