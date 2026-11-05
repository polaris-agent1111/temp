status: done
priority: 3
assignee: zcode
created: 2026-11-05 15:15

# 0008 — 复核材料包（复现 / 答辩备用）

## 背景

比赛截止后官方会统一复测、查重与合规检查（11/18 前完成预评审），并列名次还看「可复现性/可解释性」。需要一份随时能交出去的复核材料包：配置、步骤、证据、校验脚本，别人拿到能独立复现我们的成绩。

## 允许写的路径

- `report/复核材料/`（整个目录都可写，可新建）
- `zcode/reports/0008-review-package.md`

## 交付内容（目录结构）

```
report/复核材料/
├── README.md              # 一页说明：我们做了什么、怎么复现、目录导航
├── best-configs/
│   ├── README.md          # 每个候选配置的本地成绩（均值/标准差/来源 tag）
│   └── <tag>/1..6/pacer.txt   # 从 runs/configs/ 复制（含 2–3 个候选）
├── reproduce.md           # 逐步复现：目录结构、format_check_client、competition_question1 命令、结果文件含义
├── methodology.md         # 方法摘要（可引用技术报告，不用重复长文）
└── checklist.md           # 复核自检清单（格式/换行/时间戳/非法参数/结果可复现等，逐条打勾）
```

要求：
1. 候选配置从 `runs/configs/` 里挑**本地表现最好的 2–3 个**（参考 `report/实验结果-数据表.md`），复制时保持文件字节完全一致（**LF、无末尾换行**）。
2. `reproduce.md` 里的命令必须是真实可执行的（参考 `docs/extracted/实验详细手册.md`），并说明「评测机需 4 核以上、单次约 3–4 分钟」。
3. `checklist.md` 要覆盖已知坑：CRLF 会导致服务端解析失败并出现 80.18s 假成功；`[timestamp:N]` 必须等于目录号；`burst`≥`tokens`、`bucket_cap`≥`leak_rate` 等约束。
4. 不写任何真实凭据（GUID、密码、token），GUID 一律用 `<团队GUID>` 占位。

## 禁止

- 不操作云主机、不跑评测、不改其他目录。

## 交付

完成后把本文件头改成 `status: done`，摘要里列出所有文件路径与字节数。
