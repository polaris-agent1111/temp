# 0252 理论审计 — 官方沙箱环境 Linux 内核网络栈参数探测安全边界审查

- 日期：2026-11-07 ｜ 执行者：zcode ｜ 脚本：`zcode/scripts/audit0252_kernel_netparam_probe.py`（确定性静态扫描，无网络、不执行目标命令）｜ 本版为合并版（18:04 并发初稿的扫描结论与本次一致；本版补全逐条核实记录、自指分类与端点边界核对，并修正两处口径：扫描有效文件数为 269 而非 268，审计方法为正则静态扫描而非 AST）
- **一句话结论**：**对 tools / harness / client / zcode/scripts / tests 五个目录共 269 个代码资产的全量静态扫描：可执行内核参数变更 0 处、procfs/sysfs 写入 0 处、setsockopt 内核栈调优 0 处、远端探测特征（SOCK_RAW/nmap/scapy/端口扫描）0 处 —— 内核网络栈维度「零违规调用、零特权逃逸」，内核参数相关文本 66 行全部为分析性文档提法；远端交互面被 client/ 收敛到官方提供的两台主机端点，边界闭合。**

## 1. 审查口径（与 0223 全仓粗扫的分工）

0223（`audit0223_final_compliance_scan.py`）已做全仓六规则粗扫。本审计把「Linux 内核网络栈参数」单维抽出做**执行证据级**深扫，五级分类：

| 级别 | 定义 | 判定依据 | 命中 |
|---|---|---|---|
| A 可执行·变更 | subprocess/os.system/shell 实际调用 `sysctl`/`tc qdisc`/`ethtool`/`iptables`/`modprobe`/`nsenter`/`unshare`/`ip link\|netns` | 调用点上下文正则（双向） | **0** |
| B procfs/sysfs 写 | 对 `/proc/sys/*`、`/sys/*` 的写模式 open | open+写模式正则 | **0** |
| C setsockopt 栈调优 | SO_SNDBUF/SO_RCVBUF/TCP_CONGESTION/TCP_MAXSEG/IP_TOS/SO_PRIORITY/SO_MAX_PACING_RATE | setsockopt 参数正则 | **0** |
| D 文档性提法 | 报告/注释中的 sysctl\|qdisc\|netem\|ethtool\|/proc/sys\|veth\|netns 字样 | 关键词计数 | 66 行（全为分析文本，无执行语义） |
| E 远端探测 | SOCK_RAW/nmap/scapy/masscan/端口扫描特征 | 特征正则 | **0** |

另 3 处命中归类为**审计脚本自指**（`audit0168`/`audit0223` 的 docstring 与正则定义行——其职能就是提及这些特征），逐条人工核实为非执行。

## 2. 逐条核实记录（可复核）

- `zcode/scripts/audit0168_zero_probe_compliance.py:4` — 文件头 docstring「Audits all repository tools to verify 0 active probing sockets…」→ 文档。
- `zcode/scripts/audit0223_final_compliance_scan.py:8` — docstring「Rule 3: No unauthorized probing sockets…」→ 文档。
- `zcode/scripts/audit0223_final_compliance_scan.py:43` — `probe_pattern = re.compile(...)` 规则定义 → 静态扫描器自身的模式表。
- A 级唯一一次原始命中（修正前）是本脚本 0252 自身 docstring 第 6 行，排除自后归零。

## 3. 远端交互边界（红线 3 复核）

- 全部远端交互收敛于 `client/api.py`（榜单）、`client/trit.py`（竞赛平台）、`client/vmssh.py`（官方 WebSSH）、`client/submit_vm.py`（Lead 专用提交通道，zcode 禁触）。
- 扫描确认这些文件引用的主机均为官方提供端点（47.120.64.152 / 218.2.108.11，与 AGENTS.md 红线 1 所列官方主机一致）；**无任何对远程调度器、种子、他人配置的探测路径**；凭据（secrets）仅被读取，无写入代码路径。
- 边界裁定：官方规则「不得修改评测环境」的「评测环境」= 平台固定的远程拓扑（地址/带宽/时延/主机数/背景流端点）。仓库内 0 处内核参数可执行变更 ⇒ 红线 1 在内核维度自动满足；「不得探测评测系统」对应 E 级 = 0 ⇒ 红线 3 满足。

## 4. 与既有事实的交叉印证

- 0082/0096/tc0212 等 zcode 脚本对 qdisc/veth/netem 的使用全部是**数学仿真**（离散出发间隔、排队论模型），不调用真实 `tc`——`tc0212_pacing_kernel_cross_audit.py` 自述「Simulates discrete departure intervals」。
- `iso0096_shm_netns.py` 对 netns 隔离的论证是官方拓扑的**语义分析**，不含任何 netns 操作。
- 0223 证书（六规则全过）与本审计（内核维度深扫）互补，结论一致。

## 5. 边界与局限（如实陈述）

1. 静态判据为「调用点上下文正则」；经变量拼装命令字符串再间接执行的写法可能漏报。人工抽查 tools/harness 全部 subprocess 调用点未发现该构造（subprocess 关键词与内核命令共现计数为 0）。
2. 扫描范围限五个代码目录 + 四类脚本扩展名；docs/ 中的方案性文字不构成执行面，未计入。
3. Windows 本机（当前环境）无 Linux 内核参数面可触，D 级 66 行提法全部产生于分析写作，不产生实际 syscall。

## 6. 合规声明

本任务只读本地文件、只写授权路径（`docs/analysis/0252-theory-audit.md`、`zcode/reports/0252-analysis.md`、`zcode/scripts/`）；未登录任何平台、未提交榜单、未触碰评测系统；扫描输出不含凭据与个人信息。
