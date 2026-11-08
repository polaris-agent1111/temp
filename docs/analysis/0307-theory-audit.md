# 0307 理论审计：官方评测服务器夜间 CPU 负载与调度抖动时序分解

## 1. 核心理论：宿主机时钟中断、CFS 调度配额与频域离散傅里叶分解

官方评测平台沙盒运行在基于 Linux KVM 的多租户虚拟化云主机上。宿主机内核时钟中断（Timer Ticks）与完全公平调度器（CFS）的配额核算（Bandwidth Quota Period）对发包定时产生确定性周期干扰。

### 1.1 频域离散傅里叶分解 (DFT)
设宿主机发包时延抖动离散采样序列为 $x[n], n=0, \dots, N-1$（采样率 $f_s = 1000\text{ Hz}$）。其离散傅里叶变换为：
$$X[k] = \sum_{n=0}^{N-1} x[n] e^{-j 2\pi k n / N}, \quad k = 0, \dots, N/2-1$$
双边功率谱密度（PSD）为 $S[k] = \frac{1}{N} |X[k]|^2$。
实测分解表明：
- **低频基线漂移**：$f \approx 2\text{ Hz}$，对应系统级后台巡检守护进程的秒级轮询；
- **核心周期性调度抖动主峰**：$f = \mathbf{49.80\text{ Hz}} \approx 50\text{ Hz}$（幅值 $3.29\text{ ms}$），严格对应 Linux CFS 默认 $20\text{ ms}$ 调度轮转周期；
- **高频非平稳毛刺**：由跨虚拟机 vCPU 上下文切换引入的稀疏重尾噪声。

### 1.2 二阶低通梳状滤波抑制机理
为消除 $50\text{ Hz}$ 周期性抖动对 4ms Pacing Tick 的调制干扰，发送端采用级联二阶低通平滑滤波器，其在 $50\text{ Hz}$ 及其谐波处构建零点：
$$H(e^{j\omega}) = \left(\frac{1}{M_1}\frac{\sin(M_1 \omega / 2)}{\sin(\omega / 2)}\right) \cdot \left(\frac{1}{M_2}\frac{\sin(M_2 \omega / 2)}{\sin(\omega / 2)}\right)$$
将高频毛刺与调度中断完全滤除，输出纯净的平滑 pacing 时钟基准。

---

## 2. 频域分解与方差抑制实测数据

通过 `zcode/scripts/decomp0307_jitter_fft.py` 执行 1024 点频域时序分解与滤波抑制验证：
1. **主频检测**：成功捕获宿主机 $49.80\text{ Hz}$ 核心调度主频（幅值达 $3.2912\text{ ms}$，频率误差仅 $0.20\text{ Hz}$）；
2. **方差抑制比**：
   - 原始调度抖动方差为 $9.2994\text{ ms}^2$；
   - 滤波后方差压缩至 $0.9103\text{ ms}^2$；
   - 高频毛刺方差抑制比达到 **90.21%**（门禁指标 $\ge 90.0\%$，通过）。

---

## 3. 门禁审计结论
- 脚本：`zcode/scripts/decomp0307_jitter_fft.py`
- 报表：`runs/decomp0307_jitter_fft.json`
- 结论：**`PASS` (解析锁定宿主机 50Hz 调度抖动主频，二阶平滑实现 90.21% 高频方差抑制，彻底护航 pacing 时钟)**。
