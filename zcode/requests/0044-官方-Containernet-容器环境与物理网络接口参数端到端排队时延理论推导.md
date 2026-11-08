status: done
priority: 1
assignee: zcode
created: 2026-11-06 20:08

# 0044 — 官方 Containernet 容器环境与物理网络接口参数端到端排队时延理论推导

## 背景
根据官方赛题文档与平台代码逆向，评测拓扑由 Mininet/Containernet 容器驱动，瓶颈链路带宽 $C = 100\text{ Mbps}$，双向时延 $RTT = 70\text{ ms}$，瓶颈交换机 Drop-tail 队列长度为 $B = 40\text{ packets}$。为支撑明日 00:05 真实提交与后续答辩，需对网络端到端传输时延、排队时延与缓冲膨胀进行严密的数学建模。

## 目标
产出《端到端网络排队时延与 BDP 管道容量严格数理推导报告》，给出不同包速率 $R$ 与突发大小 $Burst$ 下排队时延 $D_q$、单向传输时延 $OWD$ 及队列溢出临界条件的解析表达式。

## 允许写的路径
- `zcode/reports/0044-queuing-delay-derivation.md`
- `docs/analysis/network-queuing-delay-theory.md`
- `zcode/scripts/` 目录下的辅助计算脚本

## 具体动作
1. **网络基础参量确立**：
   - 瓶颈带宽 $C = 100\text{ Mbps} = 1.25\times 10^7\text{ B/s}$，平均包长 $L = 1200\text{ bytes}$；
   - 线速包服务率 $\mu = C / L \approx 10,416.7\text{ packets/s}$，单包服务时延 $1/\mu = 96\mu\text{s}$；
   - 交换机物理缓冲区排空时延 $T_{\text{drain}} = 40 \times 96\mu\text{s} = 3.84\text{ ms}$；
   - 管道 BDP 容量：$BDP = C \times RTT = 1.25\times 10^7 \times 0.070 = 875,000\text{ bytes} \approx 729\text{ packets}$。
2. **瞬态突发排队模型推导**：
   - 针对令牌桶突发 $Burst = 40$ 与 $Burst = 60$：
     - 计算在 $t=0$ 慢启动时刻，突发倾泻对交换机队列深度的冲击函数 $Q(t) = \max(0, Burst - \mu t)$；
     - 严格推导为什么 $Burst \le 60$ 时，只要连接在途包处于排空状态，交换机队列不会发生丢包（结合 $3.84\text{ms}$ 排空时延与 $70\text{ms}$ RTT）。
3. **稳态精确控速排队模型推导**：
   - 针对 `precise_rate_based` 速率 $R = 96\text{ Mbps}$（即 $12\text{ MB/s}$）：
     - 计算主动让出的 $4\text{ Mbps}$ 排空余量下，队列积压的瞬态恢复指数衰减常数 $\alpha$；
     - 给出对抗 $10\text{MB} \sim 30\text{MB}$ 背景流冲击时的最大队列驻留时延。
4. **交付**：
   - 形成完整推导写入 `docs/analysis/network-queuing-delay-theory.md`；
   - 撰写交付报告 `zcode/reports/0044-queuing-delay-derivation.md`，并将头部修改为 `status: done`。

## 禁止
- 不登录平台、不提交榜单、不修改真实提交凭据。
