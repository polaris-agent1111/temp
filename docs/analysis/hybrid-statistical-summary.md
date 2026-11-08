# Hybrid 混合构型统计总览与选型口径

> **数据源**：`runs/results.jsonl` ｜ **候选构型**：37 种 ｜ **原始场次**：421 ｜ **排除 invalid**：0 ｜ **排除 load**：0
> **口径**：官方按「重复多次取平均」计分，top 提交会统一复测。本表按**均值**排序；`Min` 只是本地单场最好，**不是官方预期**。

## 一、各构型统计（按均值升序）

| 构型 (Base Tag) | n | Min | Median | **Mean** | Std | CV | 95% CI | 1~4.bin Min (Mean) | 5.bin Min (Mean) | 6.bin Min (Mean) | 状态 |
|---|---:|---:|---:|---:|---:|---:|---|---|---|---|---|
| `test-hybrid-tb4-p100M-p96M-g500` | 1 | **125.441s** | 125.441s | **125.441s** | 0.00s | 0.0% | - | 23.91s (23.91s) | 35.06s (35.06s) | 66.47s (66.47s) | LOW_N(1<3) |
| `test-hybrid-tb4-asym40-60-p98M-champ` | 1 | **128.352s** | 128.352s | **128.352s** | 0.00s | 0.0% | - | 26.57s (26.57s) | 32.68s (32.68s) | 69.11s (69.11s) | LOW_N(1<3) |
| `test-hybrid-tb4-p100M-p96M-g800` | 1 | **129.498s** | 129.498s | **129.498s** | 0.00s | 0.0% | - | 26.88s (26.88s) | 31.29s (31.29s) | 71.33s (71.33s) | LOW_N(1<3) |
| `test-hybrid-tb4-p92M-p96M` | 3 | **119.268s** | 126.887s | **129.696s** | 12.08s | 9.3% | ±30.01s | 23.28s (26.09s) | 34.68s (39.24s) | 58.03s (64.36s) | HIGH_CV(9.3%) |
| `test-hybrid-champ-100M-g1k` | 1 | **130.212s** | 130.212s | **130.212s** | 0.00s | 0.0% | - | 26.25s (26.25s) | 30.13s (30.13s) | 73.83s (73.83s) | LOW_N(1<3) |
| `test-hybrid-tb4-fast14-champ` | 3 | **131.018s** | 133.291s | **133.785s** | 3.04s | 2.3% | ±7.56s | 24.05s (26.76s) | 27.99s (29.99s) | 75.29s (77.03s) | OK |
| `test-hybrid-tb4-p100M-p96M` | 4 | **116.542s** | 134.066s | **134.011s** | 16.52s | 12.3% | ±26.29s | 23.98s (26.06s) | 31.03s (35.78s) | 61.53s (72.17s) | HIGH_CV(12.3%); MIN_FAR_BELOW_MEAN |
| `test-hybrid-tb-precise` | 1 | **135.273s** | 135.273s | **135.273s** | 0.00s | 0.0% | - | 36.85s (36.85s) | 29.24s (29.24s) | 69.18s (69.18s) | LOW_N(1<3) |
| `test-hybrid-tb4-p96M-both` | 1 | **135.289s** | 135.289s | **135.289s** | 0.00s | 0.0% | - | 25.49s (25.49s) | 40.30s (40.30s) | 69.50s (69.50s) | LOW_N(1<3) |
| `test-hybrid-tb4-p98M-champ` | 1 | **135.388s** | 135.388s | **135.388s** | 0.00s | 0.0% | - | 29.63s (29.63s) | 31.53s (31.53s) | 74.22s (74.22s) | LOW_N(1<3) |
| `test-hybrid-tb4-2k-champ` | 1 | **135.893s** | 135.893s | **135.893s** | 0.00s | 0.0% | - | 27.19s (27.19s) | 35.09s (35.09s) | 73.61s (73.61s) | LOW_N(1<3) |
| `test-hybrid-tb-asym40-50-champ` | 1 | **136.027s** | 136.027s | **136.027s** | 0.00s | 0.0% | - | 31.45s (31.45s) | 35.29s (35.29s) | 69.29s (69.29s) | LOW_N(1<3) |
| `test-hybrid-opt-g1k` | 2 | **129.370s** | 136.958s | **136.958s** | 10.73s | 7.8% | ±96.41s | 27.39s (28.72s) | 36.50s (37.14s) | 61.55s (71.10s) | LOW_N(2<3); HIGH_CV(7.8%) |
| `test-hybrid-champ-g1k` | 2 | **134.867s** | 137.975s | **137.975s** | 4.40s | 3.2% | ±39.49s | 23.48s (28.80s) | 40.73s (42.80s) | 66.23s (66.37s) | LOW_N(2<3) |
| `test-hybrid-tb4-precise125M` | 1 | **138.028s** | 138.028s | **138.028s** | 0.00s | 0.0% | - | 24.24s (24.24s) | 39.91s (39.91s) | 73.88s (73.88s) | LOW_N(1<3) |
| `test-hybrid-tb4-2k-p98M-champ` | 1 | **139.575s** | 139.575s | **139.575s** | 0.00s | 0.0% | - | 30.23s (30.23s) | 35.56s (35.56s) | 73.78s (73.78s) | LOW_N(1<3) |
| `test-hybrid-tb4-p100M-p96M-g1500` | 1 | **139.718s** | 139.718s | **139.718s** | 0.00s | 0.0% | - | 29.26s (29.26s) | 42.01s (42.01s) | 68.44s (68.44s) | LOW_N(1<3) |
| `test-hybrid-tb4-precise-con` | 1 | **139.869s** | 139.869s | **139.869s** | 0.00s | 0.0% | - | 23.74s (23.74s) | 37.83s (37.83s) | 78.30s (78.30s) | LOW_N(1<3) |
| `test-hybrid-v2` | 1 | **140.001s** | 140.001s | **140.001s** | 0.00s | 0.0% | - | 31.98s (31.98s) | 35.32s (35.32s) | 72.71s (72.71s) | LOW_N(1<3) |
| `test-hybrid-tb4-asym40-55-champ` | 1 | **140.179s** | 140.179s | **140.179s** | 0.00s | 0.0% | - | 31.70s (31.70s) | 35.63s (35.63s) | 72.85s (72.85s) | LOW_N(1<3) |
| `test-hybrid-tb-asym40-60-champ` | 7 | **134.107s** | 141.218s | **142.206s** | 7.41s | 5.2% | ±6.86s | 28.26s (30.90s) | 29.38s (36.12s) | 69.61s (75.19s) | HIGH_CV(5.2%) |
| `test-hybrid-tb4-precise2` | 3 | **137.748s** | 141.874s | **142.921s** | 5.77s | 4.0% | ±14.33s | 23.63s (28.68s) | 31.91s (35.21s) | 76.44s (79.03s) | OK |
| `test-hybrid-tb5-precise1-g1k` | 1 | **144.916s** | 144.916s | **144.916s** | 0.00s | 0.0% | - | 30.97s (30.97s) | 34.53s (34.53s) | 79.41s (79.41s) | LOW_N(1<3) |
| `test-hybrid-tb4-fast14-asym40-60-champ` | 6 | **138.632s** | 145.000s | **145.069s** | 5.59s | 3.9% | ±5.86s | 28.92s (30.99s) | 32.48s (36.38s) | 71.23s (77.70s) | OK |
| `test-hybrid-tb50-champ` | 1 | **145.271s** | 145.271s | **145.271s** | 0.00s | 0.0% | - | 30.57s (30.57s) | 37.58s (37.58s) | 77.12s (77.12s) | LOW_N(1<3) |
| `test-hybrid-tb4-p100M-p96M-g1200` | 1 | **146.172s** | 146.172s | **146.172s** | 0.00s | 0.0% | - | 28.03s (28.03s) | 39.26s (39.26s) | 78.88s (78.88s) | LOW_N(1<3) |
| `test-hybrid-tb-leak` | 1 | **147.066s** | 147.066s | **147.066s** | 0.00s | 0.0% | - | 29.89s (29.89s) | 30.77s (30.77s) | 86.41s (86.41s) | LOW_N(1<3) |
| `test-hybrid-tb4-p100M-p96M-g950` | 1 | **148.432s** | 148.432s | **148.432s** | 0.00s | 0.0% | - | 28.10s (28.10s) | 40.20s (40.20s) | 80.13s (80.13s) | LOW_N(1<3) |
| `test-hybrid-tb4-asym40-70-champ` | 1 | **148.630s** | 148.630s | **148.630s** | 0.00s | 0.0% | - | 29.96s (29.96s) | 46.10s (46.10s) | 72.56s (72.56s) | LOW_N(1<3) |
| `test-hybrid-tb4-p100M-p95M-champ` | 1 | **149.241s** | 149.241s | **149.241s** | 0.00s | 0.0% | - | 28.31s (28.31s) | 39.90s (39.90s) | 81.03s (81.03s) | LOW_N(1<3) |
| `test-hybrid-tb3-precise3-champ` | 1 | **149.980s** | 149.980s | **149.980s** | 0.00s | 0.0% | - | 33.05s (33.05s) | 27.65s (27.65s) | 89.27s (89.27s) | LOW_N(1<3) |
| `test-hybrid-tb4-opt5-precise6` | 1 | **150.220s** | 150.220s | **150.220s** | 0.00s | 0.0% | - | 33.61s (33.61s) | 44.84s (44.84s) | 71.77s (71.77s) | LOW_N(1<3) |
| `test-hybrid-tb4-p98M-p96M` | 1 | **150.427s** | 150.427s | **150.427s** | 0.00s | 0.0% | - | 30.06s (30.06s) | 52.45s (52.45s) | 67.92s (67.92s) | LOW_N(1<3) |
| `test-hybrid-tb4-p100M-p96M-g1050` | 1 | **150.687s** | 150.687s | **150.687s** | 0.00s | 0.0% | - | 29.59s (29.59s) | 30.89s (30.89s) | 90.21s (90.21s) | LOW_N(1<3) |
| `test-hybrid-tb4-p100M-p97M-champ` | 1 | **151.015s** | 151.015s | **151.015s** | 0.00s | 0.0% | - | 32.80s (32.80s) | 34.90s (34.90s) | 83.31s (83.31s) | LOW_N(1<3) |
| `test-origin4-precise2-champ` | 1 | **157.999s** | 157.999s | **157.999s** | 0.00s | 0.0% | - | 46.87s (46.87s) | 29.66s (29.66s) | 81.47s (81.47s) | LOW_N(1<3) |
| `test-hybrid-tb4-precise-g4k-92M` | 1 | **166.196s** | 166.196s | **166.196s** | 0.00s | 0.0% | - | 30.81s (30.81s) | 39.74s (39.74s) | 95.64s (95.64s) | LOW_N(1<3) |

## 二、选型提示

以下构型在官方复测口径下证据不足，不建议直接作为主推：
- `test-hybrid-tb4-p100M-p96M-g500`：LOW_N(1<3)
- `test-hybrid-tb4-asym40-60-p98M-champ`：LOW_N(1<3)
- `test-hybrid-tb4-p100M-p96M-g800`：LOW_N(1<3)
- `test-hybrid-tb4-p92M-p96M`：HIGH_CV(9.3%)
- `test-hybrid-champ-100M-g1k`：LOW_N(1<3)
- `test-hybrid-tb4-p100M-p96M`：HIGH_CV(12.3%); MIN_FAR_BELOW_MEAN
- `test-hybrid-tb-precise`：LOW_N(1<3)
- `test-hybrid-tb4-p96M-both`：LOW_N(1<3)
- `test-hybrid-tb4-p98M-champ`：LOW_N(1<3)
- `test-hybrid-tb4-2k-champ`：LOW_N(1<3)
- `test-hybrid-tb-asym40-50-champ`：LOW_N(1<3)
- `test-hybrid-opt-g1k`：LOW_N(2<3); HIGH_CV(7.8%)
- `test-hybrid-champ-g1k`：LOW_N(2<3)
- `test-hybrid-tb4-precise125M`：LOW_N(1<3)
- `test-hybrid-tb4-2k-p98M-champ`：LOW_N(1<3)
- `test-hybrid-tb4-p100M-p96M-g1500`：LOW_N(1<3)
- `test-hybrid-tb4-precise-con`：LOW_N(1<3)
- `test-hybrid-v2`：LOW_N(1<3)
- `test-hybrid-tb4-asym40-55-champ`：LOW_N(1<3)
- `test-hybrid-tb-asym40-60-champ`：HIGH_CV(5.2%)
- `test-hybrid-tb5-precise1-g1k`：LOW_N(1<3)
- `test-hybrid-tb50-champ`：LOW_N(1<3)
- `test-hybrid-tb4-p100M-p96M-g1200`：LOW_N(1<3)
- `test-hybrid-tb-leak`：LOW_N(1<3)
- `test-hybrid-tb4-p100M-p96M-g950`：LOW_N(1<3)
- `test-hybrid-tb4-asym40-70-champ`：LOW_N(1<3)
- `test-hybrid-tb4-p100M-p95M-champ`：LOW_N(1<3)
- `test-hybrid-tb3-precise3-champ`：LOW_N(1<3)
- `test-hybrid-tb4-opt5-precise6`：LOW_N(1<3)
- `test-hybrid-tb4-p98M-p96M`：LOW_N(1<3)
- `test-hybrid-tb4-p100M-p96M-g1050`：LOW_N(1<3)
- `test-hybrid-tb4-p100M-p97M-champ`：LOW_N(1<3)
- `test-origin4-precise2-champ`：LOW_N(1<3)
- `test-hybrid-tb4-precise-g4k-92M`：LOW_N(1<3)

## 三、跨构型理论下界（不是单次可达成绩）

- 1~4.bin 跨构型最小：`23.279s`
- 5.bin 跨构型最小：`27.651s`
- 6.bin 跨构型最小：`58.034s`
- 合成下界：**108.964s**

这三项来自不同构型的不同单场，合成值只是理论下界，不能写成冲冠目标或官方预期。

## 四、选型门槛

- 候选：n≥3，报告 mean/median/std/CV；不足 3 次只记为探索点。
- 主推：n≥8–10，CV≤5%，均值相对锚点有明确优势，且邻域扰动仍稳定。
- 禁止 min-of-N / 极值红利；重复实验用于估计方差，不是抽低分。
- 本地与官方分开陈述：`local_best`、`local_mean`、`official_score` 不得混用。
