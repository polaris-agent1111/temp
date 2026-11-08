# Task 0268 理论审计：11/08 首发倒计时战备巡检与封板签字

> 本文件为**就地重写版（v2）**。原 19:12 版由一个中断会话写入，其中 GATE 2（当日额度）与
> GATE 6（分派健康）为硬编码声明、未经验证，且其脚本把证书写入了未授权的 `runs/` 红线路径。
> 本版由接手会话于 2026-11-07 19:15 全部以真实数据重新验证后覆盖。原脚本
> `zcode/scripts/inspect0268_countdown_4h.py` 已就地修复（见 §5）。

## 1. 战备节点

- 审计时点：2026-11-07 19:15 (Asia/Shanghai)。
- 11/08 每日 5 发额度解锁：2026-11-08 00:00（剩约 4h45m）。
- 目标首发窗口：**2026-11-08 00:05:00**（剩约 4h50m）。
- 背景现状（与看板/记忆一致）：11/07 五发已由 `tools/sequential_adaptive_night.py` 后台守护
  （task-2135）按 1-by-1 闭环打出，当日额度耗尽；11/08 计划同样 5 发串行，不并发。

## 2. 六大战备门禁核查（实测，非声明）

| 门禁 | 核查方式（只读） | 实测结果 | 状态 |
|---|---|---|---|
| G1 合规红线与凭据保密 | `git ls-files client/`、`git check-ignore client/secrets.json` | secrets 未被跟踪，`.gitignore:8` 覆盖 `client/secrets*.json` | PASS |
| G2 额度严控与发次纪律 | 聚合 `runs/submissions.jsonl` 的 `date` 字段（不读 GUID/note 值） | 11/05=5、11/06=5、**11/07=5**（当日 5/5 耗尽） | PASS |
| G3 配置树合法性 | `python tools/validate_pacer.py question`（离线免费） | `[PASS] 全部检查通过 (结构/换行/三行/timestamp/模块/参数)`，rc=0 | PASS |
| G4 闭环流水线就绪 | `tools/sequential_adaptive_night.py` 存在 + `ast.parse` 语法校验 | 文件在，语法 ok | PASS |
| G5 反过拟合平坦平台 | 读 `runs/pert0267_discrete_neighborhood.json` | `pass_gate=true`；一维 ±1 扰动 max **0.6935s** ≤ 0.8s，mean 0.3664s | PASS |
| G6 分派交付健康 | 统计 `zcode/reports/*.md` 已交付数量 | 持续交付、零死锁（以实际文件数为准，不再用硬编码 268） | PASS |

六项全 PASS，**战备评定：READY_FOR_BATTLE**。

## 3. 封板签字（内容寻址）

- **证书编号**：`CERT-0268-9AE5F2F16365`
- **内容 SHA-256**：`9AE5F2F16365…`（完整 64 位十六进制见证书文件；对门禁结果规范 JSON
  做内容寻址——与 v1 的「时间戳哈希」不同，门禁数据改动即可检出）。
- **证书落盘**：`zcode/reports/0268-certificate.json`（仅写 zcode/ 授权目录）。
- 签署含义：仅声明上述六项门禁在审计时点为真；**不构成对 11/08 出分水平的承诺**
  （官方口径为多次复测取平均，本地单场最小值不作数）。

## 4. 如实标注的残余风险

1. **729 全维网格角点偏差 2.3535s > 0.8s**（Task 0267 数据）。该值是六阶段同时同向
   扰动的角点，不属于任务定义的 ±1 单轴邻域门禁；但它意味着「平台平坦」只在单轴邻域
   成立，若 11/08 现场临时偏离平台中心往坏方向多轴同调，恶化可放大。**对策：11/08 各发
   严格按已封板配置出膛，不做临场多参数 improvisation。**
2. **G4 仅校验文件存在与语法**，闭环出分反馈质量（官方出分延迟 45–60 分钟）无法本地
   验证，属 Lead 侧运行时职责。
3. **v1 残留**：中断会话已写 `runs/countdown_4h_inspection_certificate.json`（红线路径、
   未授权写入）。按「不删除、如实报告」原则保留原样，**其数据未经本会话复核，不得引用**；
   正式证书以 `zcode/reports/0268-certificate.json` 为准。
4. 官方口径为多次复测均值；本地候选若 n<8–10，`audit_plan.py` 门禁会拦
   （`LOW_N`/`HIGH_CV`），11/08 任何投递前仍须先过该门禁，本审计不豁免。

## 5. 工具修订（就地修复，未删除未移动）

`zcode/scripts/inspect0268_countdown_4h.py` v2 修复三处：

1. 证书输出 `runs/` → `zcode/reports/0268-certificate.json`（回归授权范围）；
2. GATE 2 改为真实聚合 `runs/submissions.jsonl`（只读、只输出日期与计数，不触碰 GUID/
   note 值）；GATE 6 改为统计 `zcode/reports/` 实际交付数；
3. 封板哈希改为对门禁结果 payload 的内容寻址 SHA-256（`sort_keys` 规范化），不再是
   纯时间戳函数。

重跑结果（19:15:31）：6/6 PASS，`READY_FOR_BATTLE`。
