status: done
priority: 2
assignee: zcode
created: 2026-11-05 15:15

# 0009 — pacer 参数 schema + 本地校验工具

## 背景

Lead 每次做参数实验前，都要先把配置传到云主机跑 `format_check_client`，一来一回 1–2 分钟；而且踩过「CRLF 换行导致服务端解析失败」的坑，格式检查程序却仍报通过。需要一个**本地校验器**：在生成配置的瞬间就查出来，避免浪费云主机时间和提交额度。

## 允许写的路径

- `configs/params_schema.json`（参数规范，机器可读）
- `tools/validate_pacer.py`（校验器）
- `zcode/reports/0009-validator.md`（交付摘要）

## 数据来源

`docs/extracted/流量整形模块使用说明.md` 与 `docs/extracted/六载穿柜.md`（只读）。

## 交付要求

### 1. `configs/params_schema.json`

按五个模块整理，结构自定但要包含：模块名、参数名、类型、是否必填、默认值、取值范围、模块内约束。必须覆盖：
- `token_bucket`: tokens / burst / token_refill_rate / token_refill_interval_us / enable_n_in_flight
- `coarse_grained_rate_based`, `precise_rate_based`: max_pacing_rate / clock_granularity / enable_n_in_flight
- `origin`: burst_tokens / max_pacing_rate / clock_granularity
- `leak_bucket`: leak_rate / bucket_cap / leak_interval_us

### 2. `tools/validate_pacer.py`

命令行用法：`python tools/validate_pacer.py <question目录> [--json]`

检查项（逐条输出通过/失败+原因，一次列全）：
1. 目录必须是 `1`…`6` 六个子目录，不允许多/少；
2. 每个子目录最多一个 `pacer.txt`，不允许子目录或其他文件；
3. 文件必须是 **UTF-8、LF 换行、无 CRLF、无末尾换行**（这是运行时能正确解析的关键，必须报错而不是警告）；
4. 恰好三行，顺序为 `[timestamp:N]` / `pacer_mode:<模块>` / `pacer_config:k=v,...`；
5. `N` 必须等于目录名；
6. 模块名必须在五个之内；
7. 参数名必须属于该模块；数值类型/范围/约束（如 `burst`≥`tokens`、`bucket_cap`≥`leak_rate`）必须满足；
8. 允许 `pacer_config:` 后为空（使用模块默认值），也允许整个子目录不放文件。
退出码：0 全通过，1 有错误。

### 3. 自测

在 `tools/` 下放 3 个样例目录（或脚本内生成临时目录）覆盖：合法配置、CRLF 配置、非法参数配置，并在报告里给出运行输出。

## 禁止

- 不操作云主机、不提交、不改 `harness/`、`client/`、`runs/`。
- 不引入额外依赖（只用标准库）。

## 交付

完成后把本文件头改成 `status: done`，摘要里贴出三种样例的校验输出。
