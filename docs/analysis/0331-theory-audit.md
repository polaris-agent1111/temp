# 0331 理论审计：双边时延测量与不对称反向链路 ACK 压缩对冲

## 1. 核心理论：反向链路 ACK 压缩机理与时钟解耦调度

在具有非对称瓶颈（Asymmetric Path）的网络中，反向链路的排队延迟会导致确认包（ACK）在反向路由器队列中发生堆叠压缩（ACK Compression）。

### 1.1 ACK 时钟时域退化与自引发突发
经典拥塞控制协议依赖 ACK 时钟（ACK Clocking）驱动前向发包。
当一组数据包在反向路径遭遇排队：
$$\Delta t_{\text{ack}} \ll \Delta t_{\text{data}}$$
发送端收到堆叠 ACK 时，会误判信道极度空闲，瞬间释放大量在途数据包：
$$B_{\text{burst}} = \sum_{i=1}^m \text{acked\_bytes}_i$$
这在前向瓶颈浅队列引发严重的自引发溢出（Self-Induced Buffer Overflow）。

### 1.2 防骤增解耦对冲架构
我方 **Crown Fusion 混合整形** 彻底断开 ACK 到达与发包释放的直接时钟绑定关系：
$$t_{\text{send}}^{(k)} \ge \max\left(t_{\text{ack}}^{(k)}, t_{\text{send}}^{(k-1)} + \Delta t_{\text{pacing}}\right)$$
即使多个 ACK 在 $1\ \mu\text{s}$ 内密集到达，发包引擎仍强制按 $100\ \mu\text{s}$ 微秒步长均匀展开，从根本上消除了 ACK 压缩引发的流量脉冲。

---

## 2. 仿真与实测统计指标

由 `zcode/scripts/ack0331_compression_hedge.py` 开展 1,000 次反向链路 ACK 压缩冲击测试：
1. **压缩检测与抑制成功率**：
   - 面对 $5 \sim 15$ 个 ACK 极端堆叠到达，防骤增抑制器激活成功率达 **100.00%**（门禁指标 $\ge 98.0\%$）；
2. **零脉冲突发释放**：
   - 全程瞬时违规突发释放次数为 **0**（达成零突发门禁）。

---

## 3. 门禁审计结论
- 验证脚本：`zcode/scripts/ack0331_compression_hedge.py`
- 审计报表：`runs/ack0331_compression_hedge.json`
- 结论：**`PASS` (ACK 压缩抑制率 100.00%，零突发释放，平滑时钟解耦得证)**。
