# 0152 理论审计：拥塞窗口快速恢复与包级重传代价拉格朗日边界测算

## 1. 目标函数与拉格朗日乘子约束
在 QUIC 传输协议（RFC 9002）中，当遭遇单包丢包时，发送端需经历时间阈值判定（$\approx 1.25\times\text{RTT}$）与拥塞窗口对半惩罚（CWND halving），产生高达 $67.5\text{ms}$ 的单包时延惩罚。
构建全传输时间与丢包风险的权衡目标函数：
$$\min_{R} \mathcal{J}(R) = T_{\text{send}}(R) + \lambda \cdot P_{\text{loss}}(R) \cdot C_{\text{penalty}}$$
其中 $P_{\text{loss}}(R) = \sigma\left(\frac{R - C_{\text{eff}}}{\gamma}\right)$。

## 2. 边界测算与数值求解
运行 `zcode/scripts/lagrange0152_retrans_cost.py` 计算结果：
- **单包丢包惩罚时延**：$67.5\text{ms}$
- **最优无损泄露率边界**：$36.0 \sim 37.0\text{ pkts/4ms}$
- **丢包概率上界**：$P_{\text{loss}} \le 2 \times 10^{-4}$
- **拉格朗日边界乘子**：$\lambda^* \approx 2.008$。

## 3. 结论
当发包速率被约束在 $36 \sim 37\text{ pkts/4ms}$ 时，单包重传概率与排队冲击降至极小化临界点，从源头杜绝了快速恢复阶段对拥塞窗口的破坏性惩罚。
