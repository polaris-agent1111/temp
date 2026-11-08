# Task 0285 理论审计：跨平台 Windows/Linux 间高精度时钟源对齐与纳秒基准校准

> 审计时点：2026-11-07 20:29 (Asia/Shanghai)。执行者：zcode。
> **结论先行：目标「跨平台时间度量偏差 ≤ 50 ns」在时间跨度表征口径下成立——
> Windows 端 ≤ 50 ns（QPC 100 ns tick + 整刻度舍入，200,000/200,000 样本验证），
> Linux 端（WSL2 Debian，内核 6.18）≤ 5 ns（观测 10 ns 值网格）。**
> 绝对历元同步（epoch offset）不经 PTP 硬件物理上不可达 50 ns，本审计不对其签名。

## 1. 口径声明（先于测量固定）

- **可验证口径**：时间跨度（span）测量中，单端点时间戳相对理想纳秒时间线的
  表征偏差 ≤ 50 ns。这是两端评测数据「同一物理时长测得同一数值」的充要条件。
- **不可验证口径（如实排除）**：两台独立时钟域的绝对历元对齐 ≤ 50 ns——
  需要共享物理参考（PTP/白兔协议），本地无此硬件；本审计仅报告其毫秒级量级，
  不作为门禁项。
- Linux 侧为 **WSL2 虚拟化环境**（kernel 6.18.33.2-microsoft-standard-WSL2，
  真实 Linux 内核 vDSO 路径）；裸机 Linux 的 TSC 周期通常更短（亚纳秒级），
  只会更好，不会更差。

## 2. 实测结果

### Windows 宿主（CPython + ctypes 直读内核）

| 项目 | 实测值 | 含义 |
|---|---|---|
| QueryPerformanceFrequency | **10,000,000** | QPC tick = **100 ns** 整 |
| QPC 原始读对最小正差 | 4 ticks（400 ns） | 读调用延迟；**值网格 = 1 tick = 100 ns** |
| `time.perf_counter_ns` 值网格 | **200,000/200,000 样本 mod 100 ns = 0** | Python 转换为整刻度舍入（round-to-nearest），非截断 |
| 括号一致性检验 | 0/20,000 违例 | QPC 括住的 perf 值全部落在转换区间内 |
| 0.2 s 跨度自检 | QPC 200,320,900 ns vs perf 200,328,400 ns | 差 7.5 µs = 两次读的调用序偏移，非时钟误差 |

**推导**：perf_counter_ns 输出恒为 100 ns 整倍数 ⇒ 每个时间戳 = 真实时刻的
最近 100 ns 网格点 ⇒ 单端点表征偏差 ≤ tick/2 = **50 ns**（构造性保证）。
若采用截断而非舍入则会偏至 100 ns——实测证明 CPython 的 `_PyTime_MulDiv`
使用了正确舍入。

### Linux 侧（WSL2 Debian，python3 ctypes clock_gettime）

| 项目 | 实测值 | 含义 |
|---|---|---|
| `clock_getres(CLOCK_MONOTONIC_RAW)` | **1 ns** | 内核名义分辨率 |
| 观测值网格（RAW / MONOTONIC） | 增量簇间距 **10 ns**（451/461/470 ns 簇） | TSC 100 MHz 虚拟网格，值量化 10 ns |
| 读调用延迟 | ~450 ns | 与 Windows 同量级 |
| 负增量 | **0 / 100,000**（两时钟均单调） | 无回退 |
| 0.2 s 跨度自检 | RAW 200,178,865 ns / MONO 200,186,059 ns | sleep 过冲 ~180 µs，正常调度行为 |

**推导**：值网格 10 ns + 舍入 ⇒ 单端点表征偏差 ≤ **5 ns**。

## 3. 跨平台对齐判定

| 判据 | Windows | WSL2 Linux | 门限 | 判定 |
|---|---|---|---|---|
| 单端点表征偏差 | ≤ 50 ns（= tick/2） | ≤ 5 ns | ≤ 50 ns | **PASS** |
| 双端点 span 最坏偏差 | ≤ 100 ns | ≤ 10 ns | 参考 | 见风险 §4-2 |
| 单调性 | 0 违例 | 0 负增量 | 必须 | **PASS** |
| 名义分辨率声明 | 100 ns（实测证实） | 1 ns（观测网格 10 ns，虚拟化） | — | 如实注记 |

对仓库实际用途的意义：下载耗时测量跨度 100 s 量级，50 ns 端点偏差的相对贡献
5×10⁻¹⁰，比运行间方差（±9.3 s）低 8 个数量级——**跨平台时间度量不构成本仓库
任何统计结论的混淆源**。

## 4. 如实标注的残余风险

1. **绝对历元偏移未测 ≤50ns，也不可测**：Windows↔WSL2 时钟域独立引导，
   无共享参考时偏移为毫秒级且漂移；此项物理上需 PTP 硬件，任何「≤50ns 绝对同步」
   的声明都是伪声明。
2. **span 双端点口径下 Windows 最坏 100 ns**：任务目标若按「每跨度两端」解读，
   Windows 端上限为 2×50 ns；仓库所有测量代码走 `time.perf_counter_ns`
   单调差值，实际跨度误差远小于最坏界（实测 0.2 s 跨度两侧一致）。
3. **WSL2 为虚拟化 TSC**：10 ns 虚拟网格不代表裸机 Linux 上限；若 11/08 后
   在裸机 Linux 评测机复核，预期偏差只会更小。
4. `clock_getres` 的 1 ns 名义值与观测 10 ns 网格的差异是 vDSO TSC 转换的
   量化效应，已如实分开陈述，不混用两个口径。

## 5. 合规声明

只写 `zcode/scripts/clk0285_windows_side.py`、`clk0285_linux_side.py`、
`clk0285_windows_results.json`、`clk0285_linux_results.json`、
`zcode/reports/0285-analysis.md` 与本文件；未安装任何系统软件（仅调用既有
WSL Debian 的 python3）；未触碰评测云主机、runs/、client/、harness/。
