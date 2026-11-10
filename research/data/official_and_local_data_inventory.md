# 官方提交配置与成绩全景台账 & 本地数据核查报告

> 生成依据：`runs/compare/official_ledger.json`、`runs/compare/local_stats.json`、`intel/raw/leaderboard_20261110T003531.json` 及仓库内实测记录。

## 1. 官方提交流水汇总表（11/05 ~ 11/10，合计 26 发）

| # | 服务器受理时间 | Tag / 提交标识 | 官方成绩 (s) | 构型摘要 | 对应 VM / 来源记录 |
|---|---|---|---|---|---|
| 01 | `2026-11-05 13:25:17` | `submit-v1` | **245.9950** | leak(9/30/1000us) ×6（六目录全同） | 早期脚本 `submit-v1` |
| 02 | `2026-11-05 14:23:59` | `submit-v1b` | **243.9583** | leak(9/30/1000us) ×6（六目录全同） | 早期脚本 `submit-v1` |
| 03 | `2026-11-05 15:25:37` | `submit-s3-tokenbucket` | **140.9270** | tb(100/200,r20/1000us) ×6（六目录全同） | VM / 平台记录 |
| 04 | `2026-11-05 15:55:45` | `submit-s4-leak-coarse` | **133.0860** | leak(36/40/4000us) ×6（六目录全同） | VM / 平台记录 |
| 05 | `2026-11-05 16:24:13` | `submit-s5-leak-27-4000` | **141.7273** | leak(27/40/4000us) ×6（六目录全同） | VM / 平台记录 |
| 06 | `2026-11-06 00:05:19` | `leak-30-50-5000` | **140.4793** | leak(30/50/5000us) ×6（六目录全同） | VM / 平台记录 |
| 07 | `2026-11-06 00:50:58` | `leak-24-60-4000` | **150.6757** | leak(24/60/4000us) ×6（六目录全同） | VM / 平台记录 |
| 08 | `2026-11-06 00:56:29` | `hr-40-60-4000` | **137.3840** | leak(40/60/4000us) ×6（六目录全同） | VM / 平台记录 |
| 09 | `2026-11-06 00:56:35` | `hr-42-60-4000` | **137.0910** | leak(42/60/4000us) ×6（六目录全同） | VM / 平台记录 |
| 10 | `2026-11-06 00:56:40` | `hr-44-60-4000` | **142.7837** | leak(44/60/4000us) ×6（六目录全同） | VM / 平台记录 |
| 11 | `2026-11-07 00:05:04` | `seq-w1107-shot1-probe-tb-r36` | **143.5610** | tb(40/40,r36/4000us,inflight=1) ×6（六目录全同） | VM / 平台记录 |
| 12 | `2026-11-07 00:28:42` | `seq-w1107-shot2-fallback-leak-fast` | **124.3683** | f1-3:leak(40/40/4000us) \| f4-6:leak(36/36/4000us) | VM / 平台记录 |
| 13 | `2026-11-07 00:37:32` | `seq-w1107-shot3-champ-98M-96M` | **143.1357** | f1-2:tb(40/40,r40/4000us,inflight=1) \| f3:tb(40/40,r38/4000us,inflight=1) \| f4:tb(40/40,r36/4000us,inflight=1) \| f5:precise(98Mbps,clock=1000us,inflight=1) \| f6:precise(96Mbps,clock=1000us,inflight=1) | VM / 平台记录 |
| 14 | `2026-11-07 00:56:30` | `seq-w1107-shot4-asym-fast14-champ-100M-96M` | **140.0247** | f1-3:tb(40/60,r40/4000us,inflight=1) \| f4:tb(40/60,r38/4000us,inflight=1) \| f5:precise(100Mbps,clock=1000us,inflight=1) \| f6:precise(96Mbps,clock=1000us,inflight=1) | VM / 平台记录 |
| 15 | `2026-11-07 01:06:43` | `seq-w1107-shot5-asym-fast14-champ-100M-96M` | **155.1607** | f1-3:tb(40/60,r40/4000us,inflight=1) \| f4:tb(40/60,r38/4000us,inflight=1) \| f5:precise(100Mbps,clock=1000us,inflight=1) \| f6:precise(96Mbps,clock=1000us,inflight=1) | VM / 平台记录 |
| 16 | `2026-11-08 00:05:04` | `1108-shot-steady-40x3-37-36-36-s1` | **122.0463** | f1-3:leak(40/40/4000us) \| f4:leak(37/37/4000us) \| f5-6:leak(36/36/4000us) | VM / 平台记录 |
| 17 | `2026-11-08 01:59:26` | `1108-shot-crown-41x2-40-37-36x2-s2` | **124.6603** | f1-2:leak(41/41/4000us) \| f3:leak(40/40/4000us) \| f4:leak(37/37/4000us) \| f5-6:leak(36/36/4000us) | VM / 平台记录 |
| 18 | `2026-11-08 02:10:47` | `1108-shot-crown-pert-40on2-s3` | **128.3987** | f1:leak(41/41/4000us) \| f2-3:leak(40/40/4000us) \| f4:leak(37/37/4000us) \| f5-6:leak(36/36/4000us) | VM / 平台记录 |
| 19 | `2026-11-08 23:11:45` | `1108-shot4-freq2k-p96M-safe` | **129.1967** | f1-3:leak(20/38/2000us) \| f4:leak(19/36/2000us) \| f5-6:leak(18/35/2000us) | VM / 平台记录 |
| 20 | `2026-11-08 23:13:44` | `1108-shot5-asym-champ-strike` | **208.6470** | f1-2:leak(10/32/1000us) \| f3-4:leak(10/30/1000us) \| f5-6:leak(9/26/1000us) | VM / 平台记录 |
| 21 | `2026-11-09 00:18:04` | `surgical-hybrid-precise6-96M` | **143.4920** | f1-3:leak(40/40/4000us) \| f4:leak(37/37/4000us) \| f5:leak(36/36/4000us) \| f6:precise(96Mbps,clock=1000us,inflight=1) | 队友 PR #4 探针 |
| 22 | `2026-11-09 08:11:23` | `1109b-shotA-low56` | **132.1750** | f1-3:leak(40/40/4000us) \| f4:leak(37/37/4000us) \| f5-6:leak(35/35/4000us) | `~/cfg_1109b-shotA-low56` |
| 23 | `2026-11-09 08:11:27` | `1109b-shotB-high56` | **128.5580** | f1-3:leak(40/40/4000us) \| f4-6:leak(37/37/4000us) | `~/cfg_1109b-shotB-high56` |
| 24 | `2026-11-09 08:11:31` | `1109b-shotC-f4high` | **136.7817** | f1-3:leak(40/40/4000us) \| f4:leak(38/38/4000us) \| f5-6:leak(36/36/4000us) | `~/cfg_1109b-shotC-f4high` |
| 25 | `2026-11-09 08:11:35` | `1109b-shotD-f4low` | **136.7057** | f1-3:leak(40/40/4000us) \| f4-6:leak(36/36/4000us) | `~/cfg_1109b-shotD-f4low` |
| 26 | `2026-11-10 00:04:52` | `1110-w1-crown-a` / `1110-rep-crown-1` | **133.1970** | leak(40/40,37,36@4ms) 冠军构型复测 | `~/cfg_1110-w1-crown-a` (当日 1/5) |

### 1.1 VM 路径专项核查（~/cfg_1109b-shotA…D、cfg_1110-rep-*、cfg_1110-w1-*）

- **`~/cfg_1109b-shotA…D`（全部已出分）**：
  - Shot A (`1109b-shotA-low56`): `2026-11-09 08:11:23` → **132.1750 s**（第 22 发）
  - Shot B (`1109b-shotB-high56`): `2026-11-09 08:11:27` → **128.5580 s**（第 23 发）
  - Shot C (`1109b-shotC-f4high`): `2026-11-09 08:11:31` → **136.7817 s**（第 24 发）
  - Shot D (`1109b-shotD-f4low`): `2026-11-09 08:11:35` → **136.7057 s**（第 25 发）
- **`~/cfg_1110-w1-*` 与 `~/cfg_1110-rep-*`**：
  - 来源：`runs/submit_plan_1110_wave1.json` 与 `runs/submit_plan_1110.json`，是 11/10 预先生成的候选提交树。
  - 出分状态：截至 11/10 00:35 快照，团队在 11/10 仅消耗了 **1 次额度**（`2026-11-10 00:04:52`，出分 **133.1970 s**），该次提交对应 `1110-w1-crown-a` / `1110-rep-crown-1`。
  - 其余目录（`1110-w1-crown-b`、`1110-rep-crown-2..3`、`1110-rep-alt-1..2`）**尚未实际提交**，因此在官方榜单上查不到出分。

## 2. 逐发完整 6 文件 pacer.txt 配置规范

### #01 | `submit-v1` | 官方成绩：245.9950 s | 提交时间：2026-11-05 13:25:17
- **签名**：`leak(9/30/1000us) ×6（六目录全同）`
```ini
[timestamp:1]
pacer_mode:leak_bucket
pacer_config:leak_rate=9,bucket_cap=30,leak_interval_us=1000
[timestamp:2]
pacer_mode:leak_bucket
pacer_config:leak_rate=9,bucket_cap=30,leak_interval_us=1000
[timestamp:3]
pacer_mode:leak_bucket
pacer_config:leak_rate=9,bucket_cap=30,leak_interval_us=1000
[timestamp:4]
pacer_mode:leak_bucket
pacer_config:leak_rate=9,bucket_cap=30,leak_interval_us=1000
[timestamp:5]
pacer_mode:leak_bucket
pacer_config:leak_rate=9,bucket_cap=30,leak_interval_us=1000
[timestamp:6]
pacer_mode:leak_bucket
pacer_config:leak_rate=9,bucket_cap=30,leak_interval_us=1000
```

### #02 | `submit-v1b` | 官方成绩：243.9583 s | 提交时间：2026-11-05 14:23:59
- **签名**：`leak(9/30/1000us) ×6（六目录全同）`
```ini
[timestamp:1]
pacer_mode:leak_bucket
pacer_config:leak_rate=9,bucket_cap=30,leak_interval_us=1000
[timestamp:2]
pacer_mode:leak_bucket
pacer_config:leak_rate=9,bucket_cap=30,leak_interval_us=1000
[timestamp:3]
pacer_mode:leak_bucket
pacer_config:leak_rate=9,bucket_cap=30,leak_interval_us=1000
[timestamp:4]
pacer_mode:leak_bucket
pacer_config:leak_rate=9,bucket_cap=30,leak_interval_us=1000
[timestamp:5]
pacer_mode:leak_bucket
pacer_config:leak_rate=9,bucket_cap=30,leak_interval_us=1000
[timestamp:6]
pacer_mode:leak_bucket
pacer_config:leak_rate=9,bucket_cap=30,leak_interval_us=1000
```

### #03 | `submit-s3-tokenbucket` | 官方成绩：140.9270 s | 提交时间：2026-11-05 15:25:37
- **签名**：`tb(100/200,r20/1000us) ×6（六目录全同）`
```ini
[timestamp:1]
pacer_mode:token_bucket
pacer_config:tokens=100,burst=200,token_refill_rate=20,token_refill_interval_us=1000
[timestamp:2]
pacer_mode:token_bucket
pacer_config:tokens=100,burst=200,token_refill_rate=20,token_refill_interval_us=1000
[timestamp:3]
pacer_mode:token_bucket
pacer_config:tokens=100,burst=200,token_refill_rate=20,token_refill_interval_us=1000
[timestamp:4]
pacer_mode:token_bucket
pacer_config:tokens=100,burst=200,token_refill_rate=20,token_refill_interval_us=1000
[timestamp:5]
pacer_mode:token_bucket
pacer_config:tokens=100,burst=200,token_refill_rate=20,token_refill_interval_us=1000
[timestamp:6]
pacer_mode:token_bucket
pacer_config:tokens=100,burst=200,token_refill_rate=20,token_refill_interval_us=1000
```

### #04 | `submit-s4-leak-coarse` | 官方成绩：133.0860 s | 提交时间：2026-11-05 15:55:45
- **签名**：`leak(36/40/4000us) ×6（六目录全同）`
```ini
[timestamp:1]
pacer_mode:leak_bucket
pacer_config:leak_rate=36,bucket_cap=40,leak_interval_us=4000
[timestamp:2]
pacer_mode:leak_bucket
pacer_config:leak_rate=36,bucket_cap=40,leak_interval_us=4000
[timestamp:3]
pacer_mode:leak_bucket
pacer_config:leak_rate=36,bucket_cap=40,leak_interval_us=4000
[timestamp:4]
pacer_mode:leak_bucket
pacer_config:leak_rate=36,bucket_cap=40,leak_interval_us=4000
[timestamp:5]
pacer_mode:leak_bucket
pacer_config:leak_rate=36,bucket_cap=40,leak_interval_us=4000
[timestamp:6]
pacer_mode:leak_bucket
pacer_config:leak_rate=36,bucket_cap=40,leak_interval_us=4000
```

### #05 | `submit-s5-leak-27-4000` | 官方成绩：141.7273 s | 提交时间：2026-11-05 16:24:13
- **签名**：`leak(27/40/4000us) ×6（六目录全同）`
```ini
[timestamp:1]
pacer_mode:leak_bucket
pacer_config:leak_rate=27,bucket_cap=40,leak_interval_us=4000
[timestamp:2]
pacer_mode:leak_bucket
pacer_config:leak_rate=27,bucket_cap=40,leak_interval_us=4000
[timestamp:3]
pacer_mode:leak_bucket
pacer_config:leak_rate=27,bucket_cap=40,leak_interval_us=4000
[timestamp:4]
pacer_mode:leak_bucket
pacer_config:leak_rate=27,bucket_cap=40,leak_interval_us=4000
[timestamp:5]
pacer_mode:leak_bucket
pacer_config:leak_rate=27,bucket_cap=40,leak_interval_us=4000
[timestamp:6]
pacer_mode:leak_bucket
pacer_config:leak_rate=27,bucket_cap=40,leak_interval_us=4000
```

### #06 | `leak-30-50-5000` | 官方成绩：140.4793 s | 提交时间：2026-11-06 00:05:19
- **签名**：`leak(30/50/5000us) ×6（六目录全同）`
```ini
[timestamp:1]
pacer_mode:leak_bucket
pacer_config:leak_rate=30,bucket_cap=50,leak_interval_us=5000
[timestamp:2]
pacer_mode:leak_bucket
pacer_config:leak_rate=30,bucket_cap=50,leak_interval_us=5000
[timestamp:3]
pacer_mode:leak_bucket
pacer_config:leak_rate=30,bucket_cap=50,leak_interval_us=5000
[timestamp:4]
pacer_mode:leak_bucket
pacer_config:leak_rate=30,bucket_cap=50,leak_interval_us=5000
[timestamp:5]
pacer_mode:leak_bucket
pacer_config:leak_rate=30,bucket_cap=50,leak_interval_us=5000
[timestamp:6]
pacer_mode:leak_bucket
pacer_config:leak_rate=30,bucket_cap=50,leak_interval_us=5000
```

### #07 | `leak-24-60-4000` | 官方成绩：150.6757 s | 提交时间：2026-11-06 00:50:58
- **签名**：`leak(24/60/4000us) ×6（六目录全同）`
```ini
[timestamp:1]
pacer_mode:leak_bucket
pacer_config:leak_rate=24,bucket_cap=60,leak_interval_us=4000
[timestamp:2]
pacer_mode:leak_bucket
pacer_config:leak_rate=24,bucket_cap=60,leak_interval_us=4000
[timestamp:3]
pacer_mode:leak_bucket
pacer_config:leak_rate=24,bucket_cap=60,leak_interval_us=4000
[timestamp:4]
pacer_mode:leak_bucket
pacer_config:leak_rate=24,bucket_cap=60,leak_interval_us=4000
[timestamp:5]
pacer_mode:leak_bucket
pacer_config:leak_rate=24,bucket_cap=60,leak_interval_us=4000
[timestamp:6]
pacer_mode:leak_bucket
pacer_config:leak_rate=24,bucket_cap=60,leak_interval_us=4000
```

### #08 | `hr-40-60-4000` | 官方成绩：137.3840 s | 提交时间：2026-11-06 00:56:29
- **签名**：`leak(40/60/4000us) ×6（六目录全同）`
```ini
[timestamp:1]
pacer_mode:leak_bucket
pacer_config:leak_rate=40,bucket_cap=60,leak_interval_us=4000
[timestamp:2]
pacer_mode:leak_bucket
pacer_config:leak_rate=40,bucket_cap=60,leak_interval_us=4000
[timestamp:3]
pacer_mode:leak_bucket
pacer_config:leak_rate=40,bucket_cap=60,leak_interval_us=4000
[timestamp:4]
pacer_mode:leak_bucket
pacer_config:leak_rate=40,bucket_cap=60,leak_interval_us=4000
[timestamp:5]
pacer_mode:leak_bucket
pacer_config:leak_rate=40,bucket_cap=60,leak_interval_us=4000
[timestamp:6]
pacer_mode:leak_bucket
pacer_config:leak_rate=40,bucket_cap=60,leak_interval_us=4000
```

### #09 | `hr-42-60-4000` | 官方成绩：137.0910 s | 提交时间：2026-11-06 00:56:35
- **签名**：`leak(42/60/4000us) ×6（六目录全同）`
```ini
[timestamp:1]
pacer_mode:leak_bucket
pacer_config:leak_rate=42,bucket_cap=60,leak_interval_us=4000
[timestamp:2]
pacer_mode:leak_bucket
pacer_config:leak_rate=42,bucket_cap=60,leak_interval_us=4000
[timestamp:3]
pacer_mode:leak_bucket
pacer_config:leak_rate=42,bucket_cap=60,leak_interval_us=4000
[timestamp:4]
pacer_mode:leak_bucket
pacer_config:leak_rate=42,bucket_cap=60,leak_interval_us=4000
[timestamp:5]
pacer_mode:leak_bucket
pacer_config:leak_rate=42,bucket_cap=60,leak_interval_us=4000
[timestamp:6]
pacer_mode:leak_bucket
pacer_config:leak_rate=42,bucket_cap=60,leak_interval_us=4000
```

### #10 | `hr-44-60-4000` | 官方成绩：142.7837 s | 提交时间：2026-11-06 00:56:40
- **签名**：`leak(44/60/4000us) ×6（六目录全同）`
```ini
[timestamp:1]
pacer_mode:leak_bucket
pacer_config:leak_rate=44,bucket_cap=60,leak_interval_us=4000
[timestamp:2]
pacer_mode:leak_bucket
pacer_config:leak_rate=44,bucket_cap=60,leak_interval_us=4000
[timestamp:3]
pacer_mode:leak_bucket
pacer_config:leak_rate=44,bucket_cap=60,leak_interval_us=4000
[timestamp:4]
pacer_mode:leak_bucket
pacer_config:leak_rate=44,bucket_cap=60,leak_interval_us=4000
[timestamp:5]
pacer_mode:leak_bucket
pacer_config:leak_rate=44,bucket_cap=60,leak_interval_us=4000
[timestamp:6]
pacer_mode:leak_bucket
pacer_config:leak_rate=44,bucket_cap=60,leak_interval_us=4000
```

### #11 | `seq-w1107-shot1-probe-tb-r36` | 官方成绩：143.5610 s | 提交时间：2026-11-07 00:05:04
- **签名**：`tb(40/40,r36/4000us,inflight=1) ×6（六目录全同）`
```ini
[timestamp:1]
pacer_mode:token_bucket
pacer_config:tokens=40,burst=40,token_refill_rate=36,token_refill_interval_us=4000,enable_n_in_flight=1
[timestamp:2]
pacer_mode:token_bucket
pacer_config:tokens=40,burst=40,token_refill_rate=36,token_refill_interval_us=4000,enable_n_in_flight=1
[timestamp:3]
pacer_mode:token_bucket
pacer_config:tokens=40,burst=40,token_refill_rate=36,token_refill_interval_us=4000,enable_n_in_flight=1
[timestamp:4]
pacer_mode:token_bucket
pacer_config:tokens=40,burst=40,token_refill_rate=36,token_refill_interval_us=4000,enable_n_in_flight=1
[timestamp:5]
pacer_mode:token_bucket
pacer_config:tokens=40,burst=40,token_refill_rate=36,token_refill_interval_us=4000,enable_n_in_flight=1
[timestamp:6]
pacer_mode:token_bucket
pacer_config:tokens=40,burst=40,token_refill_rate=36,token_refill_interval_us=4000,enable_n_in_flight=1
```

### #12 | `seq-w1107-shot2-fallback-leak-fast` | 官方成绩：124.3683 s | 提交时间：2026-11-07 00:28:42
- **签名**：`f1-3:leak(40/40/4000us) | f4-6:leak(36/36/4000us)`
```ini
[timestamp:1]
pacer_mode:leak_bucket
pacer_config:leak_rate=40,bucket_cap=40,leak_interval_us=4000
[timestamp:2]
pacer_mode:leak_bucket
pacer_config:leak_rate=40,bucket_cap=40,leak_interval_us=4000
[timestamp:3]
pacer_mode:leak_bucket
pacer_config:leak_rate=40,bucket_cap=40,leak_interval_us=4000
[timestamp:4]
pacer_mode:leak_bucket
pacer_config:leak_rate=36,bucket_cap=36,leak_interval_us=4000
[timestamp:5]
pacer_mode:leak_bucket
pacer_config:leak_rate=36,bucket_cap=36,leak_interval_us=4000
[timestamp:6]
pacer_mode:leak_bucket
pacer_config:leak_rate=36,bucket_cap=36,leak_interval_us=4000
```

### #13 | `seq-w1107-shot3-champ-98M-96M` | 官方成绩：143.1357 s | 提交时间：2026-11-07 00:37:32
- **签名**：`f1-2:tb(40/40,r40/4000us,inflight=1) | f3:tb(40/40,r38/4000us,inflight=1) | f4:tb(40/40,r36/4000us,inflight=1) | f5:precise(98Mbps,clock=1000us,inflight=1) | f6:precise(96Mbps,clock=1000us,inflight=1)`
```ini
[timestamp:1]
pacer_mode:token_bucket
pacer_config:tokens=40,burst=40,token_refill_rate=40,token_refill_interval_us=4000,enable_n_in_flight=1
[timestamp:2]
pacer_mode:token_bucket
pacer_config:tokens=40,burst=40,token_refill_rate=40,token_refill_interval_us=4000,enable_n_in_flight=1
[timestamp:3]
pacer_mode:token_bucket
pacer_config:tokens=40,burst=40,token_refill_rate=38,token_refill_interval_us=4000,enable_n_in_flight=1
[timestamp:4]
pacer_mode:token_bucket
pacer_config:tokens=40,burst=40,token_refill_rate=36,token_refill_interval_us=4000,enable_n_in_flight=1
[timestamp:5]
pacer_mode:precise_rate_based
pacer_config:max_pacing_rate=12250000,clock_granularity=1000,enable_n_in_flight=1
[timestamp:6]
pacer_mode:precise_rate_based
pacer_config:max_pacing_rate=12000000,clock_granularity=1000,enable_n_in_flight=1
```

### #14 | `seq-w1107-shot4-asym-fast14-champ-100M-96M` | 官方成绩：140.0247 s | 提交时间：2026-11-07 00:56:30
- **签名**：`f1-3:tb(40/60,r40/4000us,inflight=1) | f4:tb(40/60,r38/4000us,inflight=1) | f5:precise(100Mbps,clock=1000us,inflight=1) | f6:precise(96Mbps,clock=1000us,inflight=1)`
```ini
[timestamp:1]
pacer_mode:token_bucket
pacer_config:tokens=40,burst=60,token_refill_rate=40,token_refill_interval_us=4000,enable_n_in_flight=1
[timestamp:2]
pacer_mode:token_bucket
pacer_config:tokens=40,burst=60,token_refill_rate=40,token_refill_interval_us=4000,enable_n_in_flight=1
[timestamp:3]
pacer_mode:token_bucket
pacer_config:tokens=40,burst=60,token_refill_rate=40,token_refill_interval_us=4000,enable_n_in_flight=1
[timestamp:4]
pacer_mode:token_bucket
pacer_config:tokens=40,burst=60,token_refill_rate=38,token_refill_interval_us=4000,enable_n_in_flight=1
[timestamp:5]
pacer_mode:precise_rate_based
pacer_config:max_pacing_rate=12500000,clock_granularity=1000,enable_n_in_flight=1
[timestamp:6]
pacer_mode:precise_rate_based
pacer_config:max_pacing_rate=12000000,clock_granularity=1000,enable_n_in_flight=1
```

### #15 | `seq-w1107-shot5-asym-fast14-champ-100M-96M` | 官方成绩：155.1607 s | 提交时间：2026-11-07 01:06:43
- **签名**：`f1-3:tb(40/60,r40/4000us,inflight=1) | f4:tb(40/60,r38/4000us,inflight=1) | f5:precise(100Mbps,clock=1000us,inflight=1) | f6:precise(96Mbps,clock=1000us,inflight=1)`
```ini
[timestamp:1]
pacer_mode:token_bucket
pacer_config:tokens=40,burst=60,token_refill_rate=40,token_refill_interval_us=4000,enable_n_in_flight=1
[timestamp:2]
pacer_mode:token_bucket
pacer_config:tokens=40,burst=60,token_refill_rate=40,token_refill_interval_us=4000,enable_n_in_flight=1
[timestamp:3]
pacer_mode:token_bucket
pacer_config:tokens=40,burst=60,token_refill_rate=40,token_refill_interval_us=4000,enable_n_in_flight=1
[timestamp:4]
pacer_mode:token_bucket
pacer_config:tokens=40,burst=60,token_refill_rate=38,token_refill_interval_us=4000,enable_n_in_flight=1
[timestamp:5]
pacer_mode:precise_rate_based
pacer_config:max_pacing_rate=12500000,clock_granularity=1000,enable_n_in_flight=1
[timestamp:6]
pacer_mode:precise_rate_based
pacer_config:max_pacing_rate=12000000,clock_granularity=1000,enable_n_in_flight=1
```

### #16 | `1108-shot-steady-40x3-37-36-36-s1` | 官方成绩：122.0463 s | 提交时间：2026-11-08 00:05:04
- **签名**：`f1-3:leak(40/40/4000us) | f4:leak(37/37/4000us) | f5-6:leak(36/36/4000us)`
```ini
[timestamp:1]
pacer_mode:leak_bucket
pacer_config:bucket_cap=40,leak_interval_us=4000,leak_rate=40
[timestamp:2]
pacer_mode:leak_bucket
pacer_config:bucket_cap=40,leak_interval_us=4000,leak_rate=40
[timestamp:3]
pacer_mode:leak_bucket
pacer_config:bucket_cap=40,leak_interval_us=4000,leak_rate=40
[timestamp:4]
pacer_mode:leak_bucket
pacer_config:bucket_cap=37,leak_interval_us=4000,leak_rate=37
[timestamp:5]
pacer_mode:leak_bucket
pacer_config:bucket_cap=36,leak_interval_us=4000,leak_rate=36
[timestamp:6]
pacer_mode:leak_bucket
pacer_config:bucket_cap=36,leak_interval_us=4000,leak_rate=36
```

### #17 | `1108-shot-crown-41x2-40-37-36x2-s2` | 官方成绩：124.6603 s | 提交时间：2026-11-08 01:59:26
- **签名**：`f1-2:leak(41/41/4000us) | f3:leak(40/40/4000us) | f4:leak(37/37/4000us) | f5-6:leak(36/36/4000us)`
```ini
[timestamp:1]
pacer_mode:leak_bucket
pacer_config:bucket_cap=41,leak_interval_us=4000,leak_rate=41
[timestamp:2]
pacer_mode:leak_bucket
pacer_config:bucket_cap=41,leak_interval_us=4000,leak_rate=41
[timestamp:3]
pacer_mode:leak_bucket
pacer_config:bucket_cap=40,leak_interval_us=4000,leak_rate=40
[timestamp:4]
pacer_mode:leak_bucket
pacer_config:bucket_cap=37,leak_interval_us=4000,leak_rate=37
[timestamp:5]
pacer_mode:leak_bucket
pacer_config:bucket_cap=36,leak_interval_us=4000,leak_rate=36
[timestamp:6]
pacer_mode:leak_bucket
pacer_config:bucket_cap=36,leak_interval_us=4000,leak_rate=36
```

### #18 | `1108-shot-crown-pert-40on2-s3` | 官方成绩：128.3987 s | 提交时间：2026-11-08 02:10:47
- **签名**：`f1:leak(41/41/4000us) | f2-3:leak(40/40/4000us) | f4:leak(37/37/4000us) | f5-6:leak(36/36/4000us)`
```ini
[timestamp:1]
pacer_mode:leak_bucket
pacer_config:bucket_cap=41,leak_interval_us=4000,leak_rate=41
[timestamp:2]
pacer_mode:leak_bucket
pacer_config:bucket_cap=40,leak_interval_us=4000,leak_rate=40
[timestamp:3]
pacer_mode:leak_bucket
pacer_config:bucket_cap=40,leak_interval_us=4000,leak_rate=40
[timestamp:4]
pacer_mode:leak_bucket
pacer_config:bucket_cap=37,leak_interval_us=4000,leak_rate=37
[timestamp:5]
pacer_mode:leak_bucket
pacer_config:bucket_cap=36,leak_interval_us=4000,leak_rate=36
[timestamp:6]
pacer_mode:leak_bucket
pacer_config:bucket_cap=36,leak_interval_us=4000,leak_rate=36
```

### #19 | `1108-shot4-freq2k-p96M-safe` | 官方成绩：129.1967 s | 提交时间：2026-11-08 23:11:45
- **签名**：`f1-3:leak(20/38/2000us) | f4:leak(19/36/2000us) | f5-6:leak(18/35/2000us)`
```ini
[timestamp:1]
pacer_mode:leak_bucket
pacer_config:bucket_cap=38,leak_interval_us=2000,leak_rate=20
[timestamp:2]
pacer_mode:leak_bucket
pacer_config:bucket_cap=38,leak_interval_us=2000,leak_rate=20
[timestamp:3]
pacer_mode:leak_bucket
pacer_config:bucket_cap=38,leak_interval_us=2000,leak_rate=20
[timestamp:4]
pacer_mode:leak_bucket
pacer_config:bucket_cap=36,leak_interval_us=2000,leak_rate=19
[timestamp:5]
pacer_mode:leak_bucket
pacer_config:bucket_cap=35,leak_interval_us=2000,leak_rate=18
[timestamp:6]
pacer_mode:leak_bucket
pacer_config:bucket_cap=35,leak_interval_us=2000,leak_rate=18
```

### #20 | `1108-shot5-asym-champ-strike` | 官方成绩：208.6470 s | 提交时间：2026-11-08 23:13:44
- **签名**：`f1-2:leak(10/32/1000us) | f3-4:leak(10/30/1000us) | f5-6:leak(9/26/1000us)`
```ini
[timestamp:1]
pacer_mode:leak_bucket
pacer_config:bucket_cap=32,leak_interval_us=1000,leak_rate=10
[timestamp:2]
pacer_mode:leak_bucket
pacer_config:bucket_cap=32,leak_interval_us=1000,leak_rate=10
[timestamp:3]
pacer_mode:leak_bucket
pacer_config:bucket_cap=30,leak_interval_us=1000,leak_rate=10
[timestamp:4]
pacer_mode:leak_bucket
pacer_config:bucket_cap=30,leak_interval_us=1000,leak_rate=10
[timestamp:5]
pacer_mode:leak_bucket
pacer_config:bucket_cap=26,leak_interval_us=1000,leak_rate=9
[timestamp:6]
pacer_mode:leak_bucket
pacer_config:bucket_cap=26,leak_interval_us=1000,leak_rate=9
```

### #21 | `surgical-hybrid-precise6-96M` | 官方成绩：143.4920 s | 提交时间：2026-11-09 00:18:04
- **签名**：`f1-3:leak(40/40/4000us) | f4:leak(37/37/4000us) | f5:leak(36/36/4000us) | f6:precise(96Mbps,clock=1000us,inflight=1)`
```ini
[timestamp:1]
pacer_mode:leak_bucket
pacer_config:bucket_cap=40,leak_interval_us=4000,leak_rate=40
[timestamp:2]
pacer_mode:leak_bucket
pacer_config:bucket_cap=40,leak_interval_us=4000,leak_rate=40
[timestamp:3]
pacer_mode:leak_bucket
pacer_config:bucket_cap=40,leak_interval_us=4000,leak_rate=40
[timestamp:4]
pacer_mode:leak_bucket
pacer_config:bucket_cap=37,leak_interval_us=4000,leak_rate=37
[timestamp:5]
pacer_mode:leak_bucket
pacer_config:bucket_cap=36,leak_interval_us=4000,leak_rate=36
[timestamp:6]
pacer_mode:precise_rate_based
pacer_config:max_pacing_rate=12000000,clock_granularity=1000,enable_n_in_flight=1
```

### #22 | `1109b-shotA-low56` | 官方成绩：132.1750 s | 提交时间：2026-11-09 08:11:23
- **签名**：`f1-3:leak(40/40/4000us) | f4:leak(37/37/4000us) | f5-6:leak(35/35/4000us)`
```ini
[timestamp:1]
pacer_mode:leak_bucket
pacer_config:bucket_cap=40,leak_interval_us=4000,leak_rate=40
[timestamp:2]
pacer_mode:leak_bucket
pacer_config:bucket_cap=40,leak_interval_us=4000,leak_rate=40
[timestamp:3]
pacer_mode:leak_bucket
pacer_config:bucket_cap=40,leak_interval_us=4000,leak_rate=40
[timestamp:4]
pacer_mode:leak_bucket
pacer_config:bucket_cap=37,leak_interval_us=4000,leak_rate=37
[timestamp:5]
pacer_mode:leak_bucket
pacer_config:bucket_cap=35,leak_interval_us=4000,leak_rate=35
[timestamp:6]
pacer_mode:leak_bucket
pacer_config:bucket_cap=35,leak_interval_us=4000,leak_rate=35
```

### #23 | `1109b-shotB-high56` | 官方成绩：128.5580 s | 提交时间：2026-11-09 08:11:27
- **签名**：`f1-3:leak(40/40/4000us) | f4-6:leak(37/37/4000us)`
```ini
[timestamp:1]
pacer_mode:leak_bucket
pacer_config:bucket_cap=40,leak_interval_us=4000,leak_rate=40
[timestamp:2]
pacer_mode:leak_bucket
pacer_config:bucket_cap=40,leak_interval_us=4000,leak_rate=40
[timestamp:3]
pacer_mode:leak_bucket
pacer_config:bucket_cap=40,leak_interval_us=4000,leak_rate=40
[timestamp:4]
pacer_mode:leak_bucket
pacer_config:bucket_cap=37,leak_interval_us=4000,leak_rate=37
[timestamp:5]
pacer_mode:leak_bucket
pacer_config:bucket_cap=37,leak_interval_us=4000,leak_rate=37
[timestamp:6]
pacer_mode:leak_bucket
pacer_config:bucket_cap=37,leak_interval_us=4000,leak_rate=37
```

### #24 | `1109b-shotC-f4high` | 官方成绩：136.7817 s | 提交时间：2026-11-09 08:11:31
- **签名**：`f1-3:leak(40/40/4000us) | f4:leak(38/38/4000us) | f5-6:leak(36/36/4000us)`
```ini
[timestamp:1]
pacer_mode:leak_bucket
pacer_config:bucket_cap=40,leak_interval_us=4000,leak_rate=40
[timestamp:2]
pacer_mode:leak_bucket
pacer_config:bucket_cap=40,leak_interval_us=4000,leak_rate=40
[timestamp:3]
pacer_mode:leak_bucket
pacer_config:bucket_cap=40,leak_interval_us=4000,leak_rate=40
[timestamp:4]
pacer_mode:leak_bucket
pacer_config:bucket_cap=38,leak_interval_us=4000,leak_rate=38
[timestamp:5]
pacer_mode:leak_bucket
pacer_config:bucket_cap=36,leak_interval_us=4000,leak_rate=36
[timestamp:6]
pacer_mode:leak_bucket
pacer_config:bucket_cap=36,leak_interval_us=4000,leak_rate=36
```

### #25 | `1109b-shotD-f4low` | 官方成绩：136.7057 s | 提交时间：2026-11-09 08:11:35
- **签名**：`f1-3:leak(40/40/4000us) | f4-6:leak(36/36/4000us)`
```ini
[timestamp:1]
pacer_mode:leak_bucket
pacer_config:bucket_cap=40,leak_interval_us=4000,leak_rate=40
[timestamp:2]
pacer_mode:leak_bucket
pacer_config:bucket_cap=40,leak_interval_us=4000,leak_rate=40
[timestamp:3]
pacer_mode:leak_bucket
pacer_config:bucket_cap=40,leak_interval_us=4000,leak_rate=40
[timestamp:4]
pacer_mode:leak_bucket
pacer_config:bucket_cap=36,leak_interval_us=4000,leak_rate=36
[timestamp:5]
pacer_mode:leak_bucket
pacer_config:bucket_cap=36,leak_interval_us=4000,leak_rate=36
[timestamp:6]
pacer_mode:leak_bucket
pacer_config:bucket_cap=36,leak_interval_us=4000,leak_rate=36
```

### #26 | `1110-w1-crown-a` / `1110-rep-crown-1` | 官方成绩：133.1970 s | 提交时间：2026-11-10 00:04:52
- **签名**：`f1-3:leak(40/40/4000us) | f4:leak(37/37/4000us) | f5-6:leak(36/36/4000us)`
```ini
[timestamp:1]
pacer_mode:leak_bucket
pacer_config:leak_rate=40,bucket_cap=40,leak_interval_us=4000
[timestamp:2]
pacer_mode:leak_bucket
pacer_config:leak_rate=40,bucket_cap=40,leak_interval_us=4000
[timestamp:3]
pacer_mode:leak_bucket
pacer_config:leak_rate=40,bucket_cap=40,leak_interval_us=4000
[timestamp:4]
pacer_mode:leak_bucket
pacer_config:leak_rate=37,bucket_cap=37,leak_interval_us=4000
[timestamp:5]
pacer_mode:leak_bucket
pacer_config:leak_rate=36,bucket_cap=36,leak_interval_us=4000
[timestamp:6]
pacer_mode:leak_bucket
pacer_config:leak_rate=36,bucket_cap=36,leak_interval_us=4000
```

## 3. 间隔非 4000 µs 的官方点核查

| # | 提交时间 | Tag | 间隔 (µs) | 官方成绩 (s) | 构型特征与结论 |
|---|---|---|---|---|---|
| 01 | 2026-11-05 13:25:17 | `submit-v1` | **1000** | 245.9950 | 1ms 陷阱：官方/本地 ≈ 2.02x |
| 02 | 2026-11-05 14:23:59 | `submit-v1b` | **1000** | 243.9583 | 同上配置复测（方差仅 0.83%） |
| 03 | 2026-11-05 15:25:37 | `submit-s3-tokenbucket` | **1000** | 140.9270 | tb 100/200, refill 20@1000us |
| 06 | 2026-11-06 00:05:19 | `leak-30-50-5000` | **5000** | 140.4793 | 5ms 粒度，大突发慢频 |
| 19 | 2026-11-08 23:11:45 | `1108-shot4-freq2k-p96M-safe` | **2000** | 129.1967 | 2ms 慢频族（未现 1ms 的 2x 减速陷阱） |
| 20 | 2026-11-08 23:13:44 | `1108-shot5-asym-champ-strike` | **1000** | 208.6470 | 1ms 极速降级实证 |
| 13 | 2026-11-07 00:37:32 | `seq-w1107-shot3-champ-98M-96M` | **4000 + 1000** | 143.1357 | 前 4 文件 tb 4ms，后 2 文件 precise 1ms |
| 14 | 2026-11-07 00:56:30 | `seq-w1107-shot4-asym-fast14-champ-100M-96M` | **4000 + 1000** | 140.0247 | 前 4 文件 tb 4ms，后 2 文件 precise 1ms |
| 15 | 2026-11-07 01:06:43 | `seq-w1107-shot5-asym-fast14-champ-100M-96M` | **4000 + 1000** | 155.1607 | 与 #14 同配置复测（相差 15.13s / 10.8%） |
| 21 | 2026-11-09 00:18:04 | `surgical-hybrid-precise6-96M` | **4000 + 1000** | 143.4920 | 前 5 文件 leak 4ms，第 6 文件 precise 1ms |

> **注意**：3000 µs 和 8000 µs 在官方提交中**查无记录**（项目内仅在本地计划 `research-roadmap.md` 中被列为待测方向，未向官方提交过）。

## 4. 采用 token_bucket、precise、origin 的官方点核查

| 模块 | 官方提交记录 | 官方成绩 (s) | 表现与归因 |
|---|---|---|---|
| `token_bucket` | #03 (`submit-s3-tokenbucket`)<br>#11 (`seq-w1107-shot1-probe-tb-r36`)<br>#13 (`seq-w1107-shot3`)<br>#14 (`seq-w1107-shot4`)<br>#15 (`seq-w1107-shot5`) | 140.9270<br>143.5610<br>143.1357<br>140.0247<br>155.1607 | 官方表现均在 140~155s 区间，显著慢于纯 leak_bucket 最优点（122~128s）。此前官方测试的 tb 速率设定过高或处于非结合态。 |
| `precise_rate_based` | #13 (`seq-w1107-shot3`)<br>#14 (`seq-w1107-shot4`)<br>#15 (`seq-w1107-shot5`)<br>#21 (`surgical-hybrid-precise6-96M`) | 143.1357<br>140.0247<br>155.1607<br>143.4920 | 刚性限速锁死突发上限，且 1ms 高精度定时器引发密集系统调用，官方均在 140s+。 |
| `origin` | **0 发（无任何官方记录）** | — | 本地早期测试（如 `s3-origin-*`）触发 ~80s 假成功失效或性能大幅劣于 leak，未被合规入选官方提交。 |

## 5. 官方页面逐文件耗时（Per-file Duration）核查

- **官方平台是否显示逐文件耗时？** **否**。
  - 官方 HTTP 接口 `GET http://47.120.64.152:5000/api/leaderboard` 返回的每条 attempt 数据结构仅包含两项：`{"download_seconds": "...", "submitted_at": "..."}`。
  - 官方评测机制为异步批量评分，`./local_send_client` 仅负责打包上传，不等待、不返回中间各文件下载耗时。
- **逐文件耗时数据出处**：
  - 仅在**云主机本地评测**（运行 `./competition_question1 --result-json <path>`）时，本地测评程序输出 `downloads: {'1.bin': t1, '2.bin': t2, ..., '6.bin': t6}`。
  - 11/10 最新科研进展（`docs/analysis/research-roadmap.md` §2026-11-10 10:35）中观察到的「文件 1-4 慢 3-6 秒，文件 5-6 快 18-19 秒」是**本地评测单场数据**，非官方页面数据。

## 6. 本地重复评测 (n ≥ 3) 对照基准

基于 `runs/compare/local_stats.json`（对本地 501 条有效评测样本清洗后统计）：

| 构型标识 | 逐文件折算 (4ms) | 本地重复次数 (n) | 本地均值 (s) | 本地标准差 (s) | 本地 95% 置信区间 | 对应官方成绩 (s) |
|---|---|---|---|---|---|---|
| **champion (稳态冠军)** | `[40,40,40,37,36,36]` | **n = 45** | **135.25** | 10.30 | [132.16, 138.35] | 122.0463 (#16)<br>133.1970 (#26) |
| **leak-40x3-36x3 (次优)** | `[40,40,40,36,36,36]` | **n = 5** | **134.53** | 13.51 | [117.75, 151.31] | 124.3683 (#12)<br>136.7057 (#25) |
| **leak-41x2-40-37-36x2 (皇冠)** | `[41,41,40,37,36,36]` | **n = 15** | **135.48** | 9.63 | [130.15, 140.81] | 124.6603 (#17) |
| **leak-41-40-40-37-36x2 (平台)** | `[41,40,40,37,36,36]` | **n = 10** | **135.85** | 8.63 | [129.67, 142.02] | 128.3987 (#18) |
| **leak-40x4-37x2 (备选)** | `[40,40,40,40,37,37]` | **n = 10** | **134.74** | 5.41 | [130.87, 138.61] | 官方未投 |
| `1109b-shotA..D` 系列 | `[40,40,40,37,35,35]` 等 | **n = 0** | — | — | — | 128.55 ~ 136.78 |
| `freq2k-2000us` | 2000us 族 | **n = 0** | — | — | — | 129.1967 (#19) |
| `hybrid-precise6` | leak + precise | **n = 0** | — | — | — | 143.4920 (#21) |
