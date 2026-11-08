# 六大目录全量 pacer 参数空间与官方 params_schema 白盒渗透报告

> 依据文件：`configs/params_schema.json` ｜ 测试对象：11/07 午夜冲榜全部主力作战构型  

## 一、五大限速模块官方 Schema 约束矩阵

| 模块名称 | 参数名 | 类型约束 | 默认值 | 物理含义与官方描述 |
|---|---|---|---|---|
| `token_bucket` | `tokens` | `posint` | `20` | 初始令牌数 |
| `token_bucket` | `burst` | `posint` | `40` | 令牌桶容量 |
| `token_bucket` | `token_refill_rate` | `posint` | `10` | 每次补充的令牌数 |
| `token_bucket` | `token_refill_interval_us` | `posint` | `100` | 补充时间间隔(微秒) |
| `token_bucket` | `enable_n_in_flight` | `bool01` | `1` | 无在途包直接放行旁路 |
| `coarse_grained_rate_based` | `max_pacing_rate` | `nonnegint` | `0` | 最大发送速率(字节/秒), 0=不限速 |
| `coarse_grained_rate_based` | `clock_granularity` | `posint` | `1000` | 时钟粒度容差(微秒) |
| `coarse_grained_rate_based` | `enable_n_in_flight` | `bool01` | `1` | 无在途包直接放行旁路 |
| `precise_rate_based` | `max_pacing_rate` | `nonnegint` | `0` | 最大发送速率(字节/秒), 0=不限速 |
| `precise_rate_based` | `clock_granularity` | `posint` | `1000` | 时钟粒度容差(微秒) |
| `precise_rate_based` | `enable_n_in_flight` | `bool01` | `1` | 无在途包直接放行旁路 |
| `origin` | `burst_tokens` | `posint` | `10` | 突发令牌数 |
| `origin` | `max_pacing_rate` | `nonnegint` | `0` | 第二阶段最大速率(字节/秒), 0=不限速 |
| `origin` | `clock_granularity` | `posint` | `1000` | 时钟粒度容差(微秒) |
| `leak_bucket` | `leak_rate` | `posint` | `10` | 每次漏水的包数 |
| `leak_bucket` | `bucket_cap` | `posint` | `30` | 漏桶容量 |
| `leak_bucket` | `leak_interval_us` | `posint` | `1000` | 漏水间隔(微秒) |

## 二、冲榜作战构型白盒渗透检验结果

| 构型标识 | 校验状态 | 目录参数覆盖 | 详细合规诊断 |
|---|---|---|---|
| **seq-shot-probe-tb-r36 (Shot 1 探针波)** | `PASSED` | 1~6.bin 全覆盖 | [1-6] token_bucket PASSED (OK) |
| **asym-fast14-champ-100M-96M (Shot 2 夺冠冲击波)** | `PASSED` | 1~6.bin 全覆盖 | [1-3] token_bucket PASSED (OK)<br>[4] token_bucket PASSED (OK)<br>[5] precise_rate_based PASSED (OK)<br>[6] precise_rate_based PASSED (OK) |
| **champ-98M-96M (稳健亚军候选)** | `PASSED` | 1~6.bin 全覆盖 | [1-3] token_bucket PASSED (OK)<br>[4] token_bucket PASSED (OK)<br>[5] precise_rate_based PASSED (OK)<br>[6] precise_rate_based PASSED (OK) |
| **champ-92M-96M (超稳防守候选，实测均值 129.696s)** | `PASSED` | 1~6.bin 全覆盖 | [1-2] token_bucket PASSED (OK)<br>[3] token_bucket PASSED (OK)<br>[4] token_bucket PASSED (OK)<br>[5] precise_rate_based PASSED (OK)<br>[6] precise_rate_based PASSED (OK) |
| **champ-96M-both (双 96M 稳态对称候选)** | `PASSED` | 1~6.bin 全覆盖 | [1-4] token_bucket PASSED (OK)<br>[5-6] precise_rate_based PASSED (OK) |

## 三、换行与编码格式零容忍审计

- **字符编码**：所有构型文件严格采用 UTF-8（无 BOM）；
- **换行规范**：严格采用纯 LF（`\n`），绝对杜绝 Windows CRLF（`\r\n`）；
- **行数要求**：每个 `pacer.txt` 恰好 3 行，末尾无额外空行；
- **时间戳对齐**：`[timestamp:N]` 中的 N 与所在目录编号 `1..6` 严格 100% 一一对应。
