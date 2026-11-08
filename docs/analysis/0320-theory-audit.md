# 0320 理论审计：Shot 2 出分后验吸收与多流排队微观反演

## 1. 核心理论：M/M/1/K 排队系统贝叶斯后验与方差压缩

在 Shot 2 出分后，系统获得了最新的全链路性能反馈 $y_2$。

### 1.1 微观排队灵敏度与贝叶斯推断
设平均排队队列长度为 $Q$。在传输六个大文件的生命周期中，累积排队时延与 $Q$ 呈强线性响应：
$$T(Q) = T_{\text{base}} + \gamma_Q \cdot Q + \epsilon, \quad \epsilon \sim \mathcal{N}(0, \sigma_{\epsilon}^2)$$
其中灵敏度系数 $\gamma_Q = \frac{\partial T}{\partial Q} \approx 0.25\text{ s/packet}$。
由共轭高斯后验公式：
$$\sigma_{\text{post}}^2 = \left(\frac{1}{\sigma_{\text{prior}}^2} + \frac{\gamma_Q^2}{\sigma_{\epsilon}^2}\right)^{-1}$$
$$\mu_{\text{post}} = \sigma_{\text{post}}^2 \left(\frac{\mu_{\text{prior}}}{\sigma_{\text{prior}}^2} + \frac{\gamma_Q (y_2 - T_{\text{base}})}{\sigma_{\epsilon}^2}\right)$$
单次有效观测即可将队列不确定性方差缩小 90% 以上，为后续轮次精准压榨瓶颈带宽奠定基础。

---

## 2. 仿真与实测统计指标

由 `zcode/scripts/queue0320_microscopic_inversion.py` 开展后验推断测算：
1. **队列反演精度**：
   - 真实队列深度 14.50 包，反演后验均值 **14.64 包**（绝对误差仅 0.14 包）；
   - 反演精度高达 **99.04%**（门禁指标 $\ge 90.0\%$）；
2. **后验方差收缩**：
   - 后验标准差从先验 4.0 包迅速收敛至 **0.3980 包**；
   - 方差缩减比例达到 **99.01%**（门禁指标 $\ge 50.0\%$）。

---

## 3. 门禁审计结论
- 验证脚本：`zcode/scripts/queue0320_microscopic_inversion.py`
- 审计报表：`runs/queue0320_microscopic_inversion.json`
- 结论：**`PASS` (队列反演精度 99.04%，方差缩减率 99.01%)**。
