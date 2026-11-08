#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extend zcode_continuous_dispatcher.py with evening deep research batches (batch_1130 ~ batch_1400).
Covering tasks 0239 ~ 0256 across 6 batches.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DISPATCHER_FILE = ROOT / "tools" / "zcode_continuous_dispatcher.py"

BATCH_DEFS = [
    {
        "batch_id": "batch_1130",
        "target_time": "11:30",
        "tasks": [
            ("0239", "随机早期检测 RED 丢包概率函数在瓶颈队列的拟合", "计算最大丢包概率点与队列平滑安全裕度", "拟合 RED 线性标记概率函数并量化拥塞发生时的丢包突变拐点"),
            ("0240", "QUIC 乱序重组缓冲区极限内存占用测试", "验证在 100 包乱序下重组内存增加不超过 128KB", "模拟网络抖动下的严重重排序并监控 QUIC 接收端重组队列内存占用"),
            ("0241", "跨阶段速率跳变阶跃响应阻尼衰减度量", "验证从 Rate 41 到 Rate 37 阻尼比 >= 1.0 零超调", "分析六阶段边界漏桶速率突变时的二阶阻尼瞬态衰减响应"),
        ]
    },
    {
        "batch_id": "batch_1200",
        "target_time": "12:00",
        "tasks": [
            ("0242", "官方评分历史波动与周末评测负载周期性自相关 ACF 分析", "验证周末出分波动自相关函数在 lag 1 下降至 0.25 以下", "建立官方出分延迟与系统排队时间序列的自相关分析模型"),
            ("0243", "极小极大遗憾策略在极端网络对抗下的最坏情况分析", "验证在所有极端对抗状态下我方最大遗憾值 <= 2.5s", "基于 Savage 准则分析网络遭遇重度拥塞时各候选树的遗憾值界限"),
            ("0244", "决选方案配置哈希硬编码签名与全量校验审计工具", "生成 100% 格式合规且不可篡改的决选配置指纹清单", "对最终出战的候选树配置进行 SHA-256 全量防篡改签名与校验"),
        ]
    },
    {
        "batch_id": "batch_1230",
        "target_time": "12:30",
        "tasks": [
            ("0245", "针对 11/08 决战日 00:05~03:00 全程五发动态序列决策树推演", "推演 32 条全覆盖分支状态转移并确保无挂起死锁", "模拟 5 发实战序列中各种可能出现的网络反馈分支并建立全覆盖状态转移树"),
            ("0246", "BBRv1 vs BBRv2 vs 准开环漏桶在深浅队列环境下的竞争相图", "绘制相空间轨线并证明准开环漏桶无饥饿与无振荡", "利用相平面方法分析不同拥塞控制算法在浅缓冲区拓扑下的稳态共存相图"),
            ("0247", "决选现场 10 分钟应急排障与备用云节点快速接管手册", "产出标准化应急处置 SOP 并验证故障切换时间 <= 15s", "制定针对网络超时、客户端无响应或证书异常的快速冷启动排障手册"),
        ]
    },
    {
        "batch_id": "batch_1300",
        "target_time": "13:00",
        "tasks": [
            ("0248", "客户端用户态高精度计时器时钟漂移与补偿算法验证", "验证 4ms 发送间隔累计漂移 < 10us", "测试 Python 与用户态底层 clock_nanosleep 的微秒级定时精度与漂移补偿"),
            ("0249", "传输层良好吞吐率 Goodput 理论上限与实测差值微积分", "推导传输协议开销理论下界并验证实测偏差 <= 1.2%", "微积分计算 IPv4/UDP/QUIC/HTTP3 各层报头损耗并核算理论良好吞吐率极限"),
            ("0250", "全国一等奖答辩常见尖锐问题专家反击手册 v2", "增补 Q11~Q15 专家攻击性技术问题并形成标准反击提纲", "补充针对多阶段突发、跨平台泛化能力与参数人工先验的专家刁钻问题反击回答"),
        ]
    },
    {
        "batch_id": "batch_1330",
        "target_time": "13:30",
        "tasks": [
            ("0251", "六阶段不同文件尺寸下漏桶最优充盈速度动态规划验证", "计算离散 Bellman 状态空间下最优路径并证明唯一性", "针对非对称文件尺寸分布建立动态规划递推验证最优前驱状态"),
            ("0252", "官方沙箱环境 Linux 内核网络栈参数探测安全边界审查", "核查零违规调用、零特权逃逸、100% 合规边界", "全量审查本地测试工具对 Linux 内核参数的探测行为确保严格处于官方合规范围内"),
            ("0253", "极端高丢包 5%~10% 环境下 QUIC 发送窗口抗死锁验证", "验证在高丢包下快速恢复机制确保连接 100% 存活", "注入极端恶劣丢包压力测试 QUIC 丢包探测与 PTO 恢复避免发送窗口死锁"),
        ]
    },
    {
        "batch_id": "batch_1400",
        "target_time": "14:00",
        "tasks": [
            ("0254", "决战日前夜系统环境清洁度与无痕化审计证明", "完成全代码库敏感信息与历史垃圾清理并出具审计证明", "排查全仓库是否存在临时日志、调试输出、密钥遗留或非合规代码"),
            ("0255", "5发串行实战发射序列沙盘推演与异常分支自动化熔断机制", "验证超时熔断器在 60 分钟无成绩时自动降级 fallback", "验证在官方平台长时间不出分或出现网络超时时的自动熔断与降级保护机制"),
            ("0256", "全国总决赛技术决胜白皮书归档封存与主哈希清单", "将 256 项科研成果全量打包并封存 master 证书", "归档整理全项目 256 项科研任务与理论推导成果，封存不可篡改的主签名清单"),
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
    if '"batch_1130"' in content:
        print("Evening batches already registered.")
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
    print("Successfully injected evening batches (batch_1130 ~ batch_1400) into zcode_continuous_dispatcher.py!")
    return 0

if __name__ == "__main__":
    main()
