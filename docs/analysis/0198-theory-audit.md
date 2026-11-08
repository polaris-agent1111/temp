# 0198 任务理论审计报告：QUIC 流量整形网络层与传输层开销 (Header Overhead) 微观精算

## 1. 协议栈报文结构与开销分解
在评测环境采用的 QUIC over UDP/IP 协议栈中，客户端配置的 MTU 为 $1200\text{ 字节}$。对每一层协议开销进行微观精算：
1. **IPv4 头部**: 无可选字段标准头，固定为 $20\text{ 字节}$；
2. **UDP 头部**: 标准端口与长度校验头，固定为 $8\text{ 字节}$；
3. **QUIC 1-RTT 短报头**: Header Form ($1\text{B}$) + Connection ID ($8\text{B}$) + Packet Number ($2\text{B}$) = $11\text{ 字节}$；
4. **QUIC AEAD 密文认证标签 (Auth Tag)**: AES-128-GCM 固定为 $16\text{ 字节}$；
5. **QUIC STREAM 帧控制字段**: Type ($1\text{B}$) + Stream ID ($2\text{B}$) + Offset/Length ($2\text{B}$) = $5\text{ 字节}$。

**总协议开销**: $20 + 8 + 11 + 16 + 5 = 60\text{ 字节}$（占比 $5.00\%$）。
**有效载荷 (Goodput Payload)**: $1200 - 60 = 1140\text{ 字节}$（载荷有效率 $95.00\%$）。

## 2. 漏率参数与真实物理/应用层吞吐量映射
在 $4000\mu\text{s}$（$0.004\text{s}$）整型周期下，各离散漏率对应的线速吞吐（Wire Throughput）与有效吞吐（Goodput）换算如下：
$$\text{Wire Throughput (Mbps)} = \frac{r \times 1200 \times 8}{0.004 \times 10^6} = r \times 2.40\text{ Mbps}$$
$$\text{Goodput (Mbps)} = \text{Wire Throughput} \times 0.9500 = r \times 2.28\text{ Mbps}$$

实测换算表：
- **Rate 36 pkts/4ms**: 线速 $86.40\text{ Mbps}$，有效载荷 $82.08\text{ Mbps}$（回退安全边界，低于瓶颈容量 $90\text{Mbps}$，零排队积压）；
- **Rate 37 pkts/4ms**: 线速 $88.80\text{ Mbps}$，有效载荷 $84.36\text{ Mbps}$（稳健平原点，贴近 $90\text{Mbps}$ 极限）；
- **Rate 40 pkts/4ms**: 线速 $96.00\text{ Mbps}$，有效载荷 $91.20\text{ Mbps}$；
- **Rate 41 pkts/4ms**: 线速 $98.40\text{ Mbps}$，有效载荷 $93.48\text{ Mbps}$（冲刺加速点，充分压缩前段传输时间）。

## 3. 结论
微观精算严密解释了为何 $r=36\sim 37$ 是长期排队自净的物理稳态点，而 $r=41$ 能够安全实现突发加速而不击穿 $100\text{Mbps}$ 交换机硬门限。
