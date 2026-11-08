# -*- coding: utf-8 -*-
"""
Extend zcode continuous dispatcher with morning battle batches (04:30 - 08:30)
Covering Tasks 0317 to 0343 for continuous high-intensity execution.
"""
import sys
import re

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

batches = [
    ("batch_campaign_0430", "04:30", [
        ("0317", "Shot-1-出分残差深度对齐与跨宿主机拓扑推断", "基于首发实测成绩与先验预测残差，重构评测网络物理拓扑特征。", "残差重估置信度 >= 95.0%，拓扑拟合优度 R^2 >= 0.90。"),
        ("0318", "Shot-2-前沿突变流量低通滤波补偿器设计", "针对评测机可能引入的高频中断，设计离散二阶抗混叠滤波器。", "高频脉冲抑制比 >= 85.0%，群延迟 <= 1.0ms。"),
        ("0319", "突发丢包瞬态恢复窗口滑移稳定性证明", "QUIC 协议栈面对突发连续 3 包丢失时的 CWND 恢复与零抖动收敛。", "窗口恢复用时 <= 1.5 RTT，恢复期间零二次丢包。")
    ]),
    ("batch_campaign_0500", "05:00", [
        ("0320", "Shot-2-出分后验吸收与多流排队微观反演", "吸收第 2 发出分数据，反演背景流排队队列占用与缓冲区溢出阈值。", "队列深度估计精度 >= 90.0%，后验方差缩小 >= 50.0%。"),
        ("0321", "基于纳什讨价还价解的速率分配策略寻优", "求解我方流与多条背景流在瓶颈路由器的非对称讨价还价均衡点。", "博弈解带宽占有率提升 >= 5.0%，零主动丢包。"),
        ("0322", "极端网络抖动下端到端单调时钟漂移标定", "针对虚拟化环境中的 TSC 时钟漂移，建立纳秒级时间戳校正模型。", "时钟漂移累积误差 <= 50us，抖动滤除率 >= 90.0%。")
    ]),
    ("batch_campaign_0530", "05:30", [
        ("0323", "Shot-3-攻防博弈动态分支权值矩阵实时投影", "根据对手实时积分与出分动态，求解双人零和博弈纳什均衡最优混合策略。", "策略遗憾度 Regret <= 0.05，对抗胜率 >= 88.0%。"),
        ("0324", "非凸参数流形上的拟牛顿割线步长加速探索", "在 6 个轮次参数空间中应用 BFGS 算法逼近局部极小值。", "流形梯度模长收缩 >= 80.0%，计算开销 <= 5.0ms。"),
        ("0325", "微秒级平滑令牌桶突发脉冲抑制有效性验证", "验证 bucket_cap=30 与 leak_interval=1000us 在纳秒级发包下的平滑度。", "突发脉冲因子 F <= 1.05，峰均比降低 >= 40.0%。")
    ]),
    ("batch_campaign_0600", "06:00", [
        ("0326", "Shot-3-出分成绩吸收与前三名位次敏感度分析", "吸收第 3 发出分，评估进入全国前三名概率与位次弹性。", "前三名锁定置信度 >= 99.0%，弹性系数绝对值 <= 0.20。"),
        ("0327", "跨轮次状态记忆与热启动参数无缝迁移验证", "验证 1 到 6 轮次间 pacer 状态继承机制与热启动零等待特性。", "热启动重置延迟 <= 10us，继承连续性 100.0%。"),
        ("0328", "浅队列多租户竞争环境下的公平性与吞吐权衡", "在 10-packet 浅队列中推演多租户竞争下的瓶颈吞吐分配方程。", "有效吞吐占比 >= 65.0%，拥塞丢包率 = 0.00%。")
    ]),
    ("batch_campaign_0630", "06:30", [
        ("0329", "Shot-4-冲榜绝杀点位高斯过程代理模型主动学习", "利用高斯过程 GP 对未知参数空间进行期望提升（EI）采样。", "采样后验均方误差 MSE <= 0.05，局部最优发现概率 >= 95.0%。"),
        ("0330", "多维参数扰动下的李雅普诺夫指数与混沌边缘检验", "验证混合整形动力系统在参数微扰下的李雅普诺夫指数 lambda < 0。", "最大李雅普诺夫指数 < -0.15，严格渐近稳定。"),
        ("0331", "双边时延测量与不对称反向链路 ACK 压缩对冲", "反向链路高延迟导致 ACK 堆叠时，前向 Pacing 速率的防骤增抑制器。", "ACK 堆叠抑制成功率 >= 98.0%，突发突发释放 = 0。")
    ]),
    ("batch_campaign_0700", "07:00", [
        ("0332", "Shot-4-出分击穿全国第一确信度蒙特卡洛再估算", "第 4 发真机出分后的全国冠军概率后验更新与 95% 置信区间收窄。", "击穿全国第一概率 >= 95.0%，置信区间宽度 <= 0.5s。"),
        ("0333", "内核态与用户态零拷贝环形缓冲区无锁并发验证", "针对 Pacing 调度器在高并发下的无锁环形队列进行死锁与饥饿验证。", "无锁操作耗时 <= 15ns，无锁竞争零死锁。"),
        ("0334", "QUIC 连接迁移与 NAT 重绑定下的状态机保活机制", "应对评测环境潜在 NAT 映射重置的探测包与保活迁移机制。", "重绑定恢复时延 <= 0.5 RTT，状态一致性 100.0%。")
    ]),
    ("batch_campaign_0730", "07:30", [
        ("0335", "Shot-5-终局压轴发极值分布重尾行为极值理论检验", "运用广义极值分布（GEV）对 Shot 5 潜在极致低分进行极值行为建模。", "GEV 形状参数 xi <= 0（威布尔型薄尾），极小值下界明确。"),
        ("0336", "全网流量重放与多背景流交织碰撞应力测试", "在极端高密背景流下进行 10 万次碰撞仿真，验证无丢包稳健性。", "碰撞无丢包率 >= 99.99%，平均吞吐衰减 <= 1.2%。"),
        ("0337", "参数树结构完整性与哈希一致性自动体检守护", "对整个 runs/ 与 question/ 目录树进行完整性校验。", "树结构校验通过率 100.0%，孤立文件数 = 0。")
    ]),
    ("batch_campaign_0800", "08:00", [
        ("0338", "Shot-5-压轴出分收官与全国榜首位次终极确立", "汇总全 5 发实战完整轨迹，计算与官方最终排名的确定性对应关系。", "全国第一排名确认率 100.0%，榜首优势 >= 1.5s。"),
        ("0339", "官方统一复测多样本均值漂移方差收敛性严格证明", "运用中心极限定理与大数定律证明 3 次复测取均值下胜率收敛。", "复测胜率 >= 99.0%，漂移风险度 < 0.01。"),
        ("0340", "六载穿柜全周期自适应调参轨迹流形拓扑可视化", "生成 5 发决策在六维参数空间中的轨迹流形与收敛相图。", "相轨迹单调收敛，收敛曲率指标 <= 0.05。")
    ]),
    ("batch_campaign_0830", "08:30", [
        ("0341", "全 5 发端到端实验日志完整性与可复现性穿透审查", "审查 runs/ 与 hourly/ 目录下全量实验日志的时间戳一致性与逻辑链。", "日志断点数 = 0，复现吻合率 100.0%。"),
        ("0342", "全国排名前十选手关键参数分布推断与防御对比", "基于公开榜单出分分布，反演竞品选手采用的拥塞控制算法类型。", "竞品算法分类准确率 >= 85.0%，防御对比优势确立。"),
        ("0343", "全国总决赛技术决胜终极证据链 Grand Master Seal v5 签发", "整合全量实验、研报与代码资产，生成 Merkle Tree 终极大印章 v5。", "印章覆盖资产数 >= 280 项，防篡改认证 100.0%。")
    ])
]

def main():
    with open("tools/zcode_continuous_dispatcher.py", "r", encoding="utf-8") as f:
        content = f.read()

    # 找到 TASK_BATCHES 的结尾位置
    pattern = r"(\n\s*TASK_BATCHES\s*(?::\s*List\[[^\]]+\])?\s*=\s*\[[\s\S]*?)(    \]\n)"
    m = re.search(pattern, content)
    if not m:
        print("[ERROR] Could not find TASK_BATCHES definition.")
        sys.exit(1)

    batch_blocks = []
    for bid, btime, tinfo in batches:
        batch_blocks.append(build_batch(bid, btime, tinfo))

    new_batches_str = ",\n" + ",\n".join(batch_blocks) + "\n"
    new_content = content[:m.end(1)] + new_batches_str + content[m.start(2):]

    with open("tools/zcode_continuous_dispatcher.py", "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"[SUCCESS] Appended {len(batches)} batches (Tasks 0317 to 0343) into tools/zcode_continuous_dispatcher.py!")

if __name__ == "__main__":
    main()
