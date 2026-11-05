# 0009 报告：pacer 参数 schema + 本地校验工具

- 完成时间：2026-11-05 16:55
- 执行者：zcode
- 结论：机器可读 schema（五模块、参数/默认值/类型/约束全覆盖）+ 零依赖校验器（8 项检查一次列全、exit 0/1、--json、--selftest）已交付；自测三样例全过，并在**真实历史坑配置**（CRLF 的 `ctl-tokenbucket-default`）上复现 18 处报错、在已提交配置 `submit-v1` 上通过。

## 产出文件

- `configs/params_schema.json` — 五模块参数规范：token_bucket（tokens/burst/token_refill_rate/token_refill_interval_us/enable_n_in_flight）、coarse/precise（max_pacing_rate/clock_granularity/enable_n_in_flight）、origin（burst_tokens/max_pacing_rate/clock_granularity）、leak_bucket（leak_rate/bucket_cap/leak_interval_us）；含类型（posint/nonnegint/bool01）、默认值、约束（burst≥tokens、bucket_cap≥leak_rate）、文件格式规则（UTF-8/LF/无末尾换行/三行/timestamp=目录号）。
- `tools/validate_pacer.py` — 用法 `python tools/validate_pacer.py <question目录> [--json]`；8 项检查（目录恰 1..6、目录内仅 pacer.txt、UTF-8/LF/无 CRLF/无末尾换行【报错非警告】、三行顺序、timestamp=目录号、五模块白名单、参数名/类型/范围/约束、空参数与空目录合法）；退出码 0/1；仅标准库。
- `zcode/reports/0009-validator.md`（本报告）

## 自测输出（`python tools/validate_pacer.py --selftest`，三样例由脚本在临时目录生成）

**1) 合法配置** → 退出码 0（期望 0）OK：
```
== 自测样例 [valid] 退出码 0 (期望 0) -> OK ==
   (无错误)
```

**2) CRLF 配置** → 退出码 1（期望 1）OK（每目录 3 条，仅列目录 1）：
```
== 自测样例 [crlf] 退出码 1 (期望 1) -> OK ==
   - [检查3] 1\pacer.txt: 含 CRLF 换行 (Windows 文本模式写出的 \r\n 会导致服务端解析失败/假成功), 必须纯 LF
   - [检查3] 1\pacer.txt: 文件末尾不允许有换行 (无末尾换行)
   - [检查4] 1\pacer.txt: 必须恰好 3 行, 实际 4 行
   （目录 2–6 同样三条，共 18 条错误）
```

**3) 非法参数配置** → 退出码 1（期望 1）OK（覆盖 6 类错误）：
```
== 自测样例 [invalid] 退出码 1 (期望 1) -> OK ==
   - [检查2] 6: 只允许 pacer.txt, 发现其它文件: extra.txt
   - [检查5] 1\pacer.txt: timestamp=9 与目录名 1 不一致 (必须等于目录号)
   - [检查7] 2\pacer.txt: 约束违反: burst 必须 >= tokens (当前 burst=20, tokens=50)
   - [检查7] 3\pacer.txt: 模块 origin 不认识参数 'rate_limit' (允许: burst_tokens, max_pacing_rate, clock_granularity)
   - [检查6] 4\pacer.txt: 未知模块 'random_module', 只允许: token_bucket, coarse_grained_rate_based, precise_rate_based, origin, leak_bucket
   - [检查3] 5\pacer.txt: 文件末尾不允许有换行 (无末尾换行)
   - [检查4] 5\pacer.txt: 必须恰好 3 行, 实际 4 行
SELFTEST PASS
```

## 真实数据回归

- `python tools/validate_pacer.py runs/configs/submit-v1` → **[PASS] 全部检查通过**，exit 0（已提交 v1 配置合规）。
- `python tools/validate_pacer.py runs/configs/ctl-tokenbucket-default` → **[FAIL] 18 处错误**（CRLF+末尾换行+4 行）——正是当年产生 80.18 s 假成功的配置，校验器在提交前即可拦下。
- `--json` 输出 `{"ok": true, "error_count": 0, "errors": [], ...}`，可接入生成流水线。

## 未完成/风险

- schema 中 max_pacing_rate 等「正整数」按文档表记为 nonnegint 以容纳默认 0（不限速）——与文档「正整数」表述的出入已在 schema desc 标注。
- 校验器不检查「速率换算合理性」（如 max_pacing_rate 单位 B/s vs bit/s 口算），那是 0006 风险条目，靠人工。
- 未对 question 根目录的 `.DS_Store` 类隐藏文件给豁免——按平台规范一律报错（严格从紧）。

## 给 Lead 的建议（可选）

- 生成配置的脚本里在写完 pacer.txt 后直接 `python tools/validate_pacer.py <dir> --json` 一步把关，替代 1–2 分钟的云主机 format_check 往返；提交前仍以官方 format_check 为准（双重把关）。
