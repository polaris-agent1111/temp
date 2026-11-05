status: done (由 Lead 在云主机内完成，本任务作废)
priority: 1
assignee: zcode
created: 2026-11-04 23:40

# 0001 — 环境预检与工具链就绪

## 背景

我们要在本地复现 iDSN 挑战赛的 QUIC 仿真评测（目前复现包还没拿到），并用并行搜索压总下载时间。先确认这台机器能不能扛住：16 核 32 线程 / 15.2 GB 内存（当前可用约 2.8 GB）/ Windows 11 / WSL2 Debian 已装未启动 / Python 3.14.3。

## 目标

产出一份"机器能不能用、怎么用"的体检报告，并把 Python 优化依赖装好。

## 允许写的路径

- `zcode/reports/0001-env-check.md`（报告，必写）
- `docs/env-report.md`（同样内容摘要，可写）
- 允许：`pip install --user optuna cma`（只装这两个 + 依赖），允许在 WSL 里执行**只读**检查命令。

## 具体动作

1. Windows 侧：CPU/内存/磁盘（`Get-CimInstance Win32_Processor`、`Win32_OperatingSystem`、`Get-PSDrive C,E`），当前内存占用 Top5 进程。
2. WSL 侧（`wsl -e ...`，启动即可，不要装包）：`cat /etc/os-release`、`nproc`、`free -g`、`df -h /`、`gcc --version`、`python3 --version`、`ls /proc/sys/net/ipv4`，并确认 `wsl -e uname -m`。
3. 评估：16 核跑 8–12 个仿真进程是否现实（结合可用内存给结论）。
4. Python 3.14 安装 `optuna`、`cma`，验证 `import optuna`、`import cma`；记录版本。
5. 顺带确认：能否用 `python -m venv` 建虚拟环境（在 `E:\Download\iDSN\env\.venv-probe` 建完即删）。

## 禁止

- 不要 `apt install`、不要改 WSL 配置（`.wslconfig`）、不要关机/重启服务。
- 不要动 `client/`、`runs/`、`harness/`、根目录的 `PLAN.md`/`STATUS.md`。

## 交付

`zcode/reports/0001-env-check.md`，必须包含：
- 结论：能跑几个并行仿真进程，瓶颈是内存还是 CPU；
- 一张"资源现状"表；
- optuna/cma 是否可用及版本；
- 3 条给 Lead 的可执行建议（例如"跑批前关掉 X"）。

完成后把本文件头改成 `status: done`。


## 结项说明（Lead, 2026-11-05 10:40）

实际评测不在本机进行，而在竞赛云主机（4C/8G，Ubuntu 22.04）内的 Containernet 仿真环境执行；Lead 已通过平台 WebSSH 打通 shell 并跑通评测（默认配置 167.663s）。本任务已作废，无需执行。
