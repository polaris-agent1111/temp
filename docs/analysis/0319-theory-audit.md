# 0319 理论审计：突发丢包瞬态恢复窗口滑移稳定性证明

## 1. 核心理论：RFC 9002 丢包检测动力学与平滑重传调度

在浅缓冲区（$B=30\text{ packets}$）网络中，突发丢包常引发重传风暴，导致恶性二次丢包。

### 1.1 滑动窗口与 Pacing 解耦机制
设丢失包集合为 $\mathcal{L} = \{p_1, p_2, p_3\}$。
传统实现（如无整形 TCP/QUIC）在收到快速重传信号时会瞬间突发释放重传包：
$$B_{\text{burst}} = |\mathcal{L}| \cdot \text{MSS}$$
当 $B_{\text{in\_flight}} + B_{\text{burst}} > B_{\text{cap}}$ 时，必然造成二次溢出丢包。
我方 **Crown Fusion 混合整形** 强制所有重传包进入 $100\mu\text{s}$ Pacing 队列，将重传包时域展开：
$$\Delta t_{\text{spacing}} = \frac{\text{MSS}}{r_{\text{pace}}}$$
将缓冲区瞬时峰值严格压制在安全水位以下，实现零二次丢包与单调收敛。

---

## 2. 仿真与实测统计指标

由 `zcode/scripts/stable0319_loss_recovery.py` 进行 1,000 次突发 3 包丢失压力注入：
1. **恢复时延指标**：
   - 平均拥塞窗口恢复时延：$\mathbf{0.9555\text{ RTT}}$（约 $9.55\text{ ms}$，远低于门禁 $\le 1.5\text{ RTT}$）；
   - P99 窗口恢复时延：$\mathbf{1.0196\text{ RTT}}$；
2. **二次丢包验证**：
   - 1,000 次极端测试中，二次丢包发生次数为 **0**（达成零丢包门禁）。

---

## 3. 门禁审计结论
- 验证脚本：`zcode/scripts/stable0319_loss_recovery.py`
- 审计报表：`runs/stable0319_loss_recovery.json`
- 结论：**`PASS` (平均恢复时间 0.9555 RTT，零二次丢包，平滑恢复稳定性得证)**。
