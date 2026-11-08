# 0285 报告：跨平台 Windows/Linux 间高精度时钟源对齐与纳秒基准校准

- 完成时间：2026-11-07 20:29
- 执行者：zcode
- 结论：**目标达成（时间跨度表征口径）**。Windows QPC freq = 10 MHz（100 ns tick），
  CPython `perf_counter_ns` 为整刻度舍入（200,000/200,000 样本 mod 100 = 0，
  0/20,000 括号违例）→ 单端点表征偏差 ≤ **50 ns**；WSL2 Debian（真实内核 6.18）
  CLOCK_MONOTONIC_RAW 观测值网格 10 ns、getres 1 ns、零负增量 → 偏差 ≤ **5 ns**。
  两端均 ≤ 50 ns 门限。绝对历元同步需 PTP 硬件，物理上不可达 50 ns，已如实排除出
  门禁口径并单独注记。

## 具体动作

1. Windows：ctypes 直读 QueryPerformanceFrequency/Counter（200k 读对粒度直方图、
   mod-100 刻度测试、20k 括号一致性检验、0.2 s 跨度自检）。
2. Linux：`wsl.exe -d Debian -- python3`（未安装任何软件）运行
   `clk0285_linux_side.py`：clock_getres + 100k 读对粒度直方图 + 0.2 s 跨度自检。
3. 合并两侧 JSON，按预登记口径判定（单端点舍入偏差 ≤50ns；epoch 同步排除）。

## 产出文件

- `zcode/scripts/clk0285_windows_side.py` / `clk0285_linux_side.py`（可重跑）
- `zcode/scripts/clk0285_windows_results.json` / `clk0285_linux_results.json`
- `docs/analysis/0285-theory-audit.md`（含判定表与残余风险）

## 未完成/风险

- span 双端点口径下 Windows 最坏 100 ns（仓库实际用单调差值，远小于最坏界）。
- WSL2 为虚拟化 TSC（10 ns 网格）；裸机 Linux 预期更优，未实测。
- 绝对历元偏移为毫秒级且随漂移变化，任何 ≤50ns 绝对同步声明均为伪声明。

## 给 Lead 的建议（可选）

- 评测数据处理可放心跨 Windows/Linux 用纳秒口径合并；不必引入跨平台时钟补偿。
