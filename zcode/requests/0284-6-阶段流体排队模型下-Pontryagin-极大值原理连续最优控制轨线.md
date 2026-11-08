status: done
priority: 2
assignee: zcode
created: 2026-11-07 20:08

# 0284 任务：6 阶段流体排队模型下 Pontryagin 极大值原理连续最优控制轨线

## 任务背景
使用 Pontryagin 极大值原理（PMP）求解受控哈密顿系统（Hamiltonian），推导最优流控的协态方程与开关曲线。

## 目标
证明 Crown Fusion 前期饱和、后期退避的两阶段控制与 PMP 解析 Bang-Coast-Bang 极值轨线重合度 >= 96%。

## 预期产出路径
- `zcode/reports/0284-analysis.md`
- `docs/analysis/0284-theory-audit.md`
- `zcode/scripts/` 目录下的验证脚本

## 执行动作
1. 编写验证脚本并执行；
2. 形成理论审计写入 `docs/analysis/0284-theory-audit.md`；
3. 撰写总结报告写入 `zcode/reports/0284-analysis.md`，状态修改为 `status: done`。

## 合规红线
- 严禁向远程平台提交任务单，严禁修改实际提交凭据。
