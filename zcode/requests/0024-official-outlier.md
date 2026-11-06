status: done
priority: 1
assignee: zcode
created: 2026-11-05 21:50

# 0024 — 官方异常点排查：为什么 S5 本地 123.4 却官方 141.7

## 现象

| 提交 | 配置 | 本地 | 官方 | 放大 |
|---|---|---|---|---|
| S4 | `leak_bucket 36/40/4000` | 130.32（n=5） | **133.086** | +2.1% |
| S5 | `leak_bucket 27/40/4000` | 123.41（n=1） | **141.727** | +14.8% |

两个配置只差 `leak_rate`（36 vs 27），官方却差了 8.64 s，而**本地方向相反**（27 更快）。这不是普通噪声，必须解释。

## 任务

`docs/analysis/official-outlier.md`，要求：

1. **列出所有可能的机制**，每条给「支持证据 / 反对证据 / 如何用 1 次提交判别」：
   - 官方定时器粒度 G 与 leak_rate 的**乘性交互**（若官方有效包速率 = leak_rate / G，则 rate 27 → 6750 包/s，rate 36 → 9000 包/s；**假设 G 不是固定 4 ms 而是与系统负载相关的 4–6 ms**，rate 27 可能刚好落在「咬合边界」以下）
   - 官方 3 次重复取平均时出现**单次坏样本**（例如 (133+133+159)/3=141.7）
   - cap=40 在 rate=27 下导致**桶长期空/满**（rate 27 与 cap 40 的比例 = 1.48，rate 36 与 cap 40 = 1.11；桶容量相对漏出量的比例可能影响突发行为）
   - 官方评测机在 16:24 那个窗口**被其它队的提交干扰**（可用 `intel/raw/leaderboard_*.json` 的 submission_log 核对 16:00–17:30 有多少队提交）
   - 官方环境对 `leak_rate` 有**下限 clamp**（例如内部把 rate 钳到 ≥30）
2. **定量推演**：假设机制是「官方有效包速率 = rate/G」，用 S4 与 S5 两个点反解 G 与包长 p，看是否有解；若无解，说明该机制被排除。用 `tools/timer_model.py` 或新写脚本算，给出计算过程。
3. **判别实验**：给出 **3 个各只花 1 次提交**的实验，每个说明「投什么、若结果 A 说明什么、若结果 B 说明什么」。优先设计能同时区分多种机制的实验。
4. **对探测序列的影响**：如果 S5 是「坏抽样」，我们继续按本地均值排序即可；如果是「rate 有阈值」，则必须改变 11/07 的探测计划（指出具体怎么改）。
5. **一句话结论**：S5 到底是坏运气还是系统性问题。

## 输入（只读）

`runs/official_results.jsonl`、`runs/submissions.jsonl`、`runs/results.jsonl`、`docs/knowledge/timer-granularity.md`、`tools/timer_model.py`、`report/官方探测分析.md`、`intel/raw/leaderboard_*.json`（尤其 `submission_log` 与 16:00–17:30 的提交记录）。

## 禁止

不提交、不登录、不碰云主机、不编造数据；结论必须标注「推断」与「待验证」。

## 交付

`docs/analysis/official-outlier.md` + `zcode/reports/0024-outlier.md`（1 页摘要 + 判别实验清单）。完成后把本文件头改成 `status: done`。
