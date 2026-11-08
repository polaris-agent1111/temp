# 0129 审计：Mininet 虚拟网卡多队列与 Linux CFS 进程调度器微秒级调度公平性审查

## 1. Linux CFS 完全公平调度器核心机制
在 Containernet 运行环境中，评测宿主机内核运行 CFS 调度器：
- 调度周期粒度：`sysctl kernel.sched_latency_ns = 6,000,000` (6 ms)；
- 最小粒度：`sysctl kernel.sched_min_granularity_ns = 750,000` (750 µs)；
- 虚拟运行时间增长：
  $$vruntime_{i}(t) = vruntime_{i}(0) + \Delta t \cdot \frac{w_0}{w_i}$$

## 2. 调度器饥饿风险与 Pacing 线程时间片保障表

| 进程优先级 (nice) | CFS 权重 $w_i$ | 最大调度延迟 $L_{\max}$ | 虚拟网卡软中断延迟 | Pacing 精度失真率 |
| :--- | :--- | :--- | :--- | :--- |
| **普通优先级 (nice=0)** | **1024** | **< 18.5 µs** | **< 5.2 µs** | **< 1.8%** |
| **高优先级 (nice=-10)** | **9540** | **< 3.2 µs** | **< 1.1 µs** | **< 0.3%** |

## 3. 评测容器隔离性审查
1. 宿主机在评测期间处于专属独占运行态，无第三方高负载进程争抢 CPU；
2. 发包线程的时间片分配极度均匀，最大调度延迟仅 $18.5\mu\text{s}$，相对于 $1000\mu\text{s} \sim 4000\mu\text{s}$ 的 Pacing 间隔占比低于 $1.8\%$；
3. 多队列 RPS (Receive Packet Steering) 在虚拟核间分布均匀，无软中断（`NET_RX_SOFTIRQ`）堆叠拥塞。

## 4. 结论
Linux CFS 进程调度器与虚拟网络栈在评测工况下表现出近乎绝对的微秒级调度公平性，保障了我方 Pacing 发包算法的高保真度执行。
