# H1 analysis (CONFIRMATORY grid + EXPLORATORY debugging)

Grid: `results/grid1.csv` (24 variants: queue {40,120,400} x bg_rto {0.5,1} x warmup {5,30} x lat {0,1000},
cc = bbr, 24 seeds each). Cubic variants were dropped: the download collapses (runs hit t_max) because
the per-flow background never yields enough bandwidth; see below.

| | best sim2 (q400, rto 0.5, warmup 5, lat 0) | v1 | constant model |
|---|---|---|---|
| LOO-RMSE | 9.82 s | 22.69 s | 9.04 s |
| Spearman | 0.35 | -0.06 | - |
| staircase gap | -2.5 s | +0.6 s | official -11.0 s |

- P1 (beats constant) **refuted**: 0/24 variants beat 9.04 s. Best is 9.8 s; the median is ~16 s.
- P2 (left wall) holds in all variants (+5.6 to +46 s), but only because the model penalises every
  low rate, including the 1 ms trap, which comes out 285-390 s against an official 245 s.
- P3 (staircase gap < -3 s) holds in 5/24 variants, scattered with no pattern in the structural axes.
  It is not robust.
- Systematic errors common to every variant:
  - The right wall is missing. 40/60, 42/60 and 44/60 are underpredicted by 6-18 s.
  - `30/50/5000` is overpredicted by 16-28 s.
- Monte Carlo SE at 24 seeds is 1.5-9 s RMS per point. That is too large to rank configurations that
  differ by 2-3 s without 200+ seeds per point.

## Diagnosis (exploratory)
- With offered background load = 100 % of the link (TrafficGenerator `-b 100`), the background
  flow count grows during the run: 115-180 active flows by the end of a run. The bottleneck stays
  saturated, so the download sees 6-25 % loss.
  - BBRv1 survives because it ignores loss.
  - Cubic collapses.
- In reality the download gets ~38 Mbps (official 133 s). So the real background must be more
  responsive or less persistent than this model. The relevant real details are not in the docs:
  - TCP CC of the background
  - number of concurrent connections
  - whether requests are serialized per connection
- The remaining structural unknowns (download CC, queue size, background responsiveness, timer
  semantics, leak "reject" semantics) give more free choices than 10 totals can pin down.

## What this rules out
- A mechanistic simulator calibrated only on the official totals cannot rank pacer configs at the
  2-3 s level: the error budget is too large. Simulators v1 and v2 should not be used to choose
  submissions; use them only for qualitative mechanism checks.
- "Local sim says X is better" should not be treated as evidence.

## Direction
PIVOT. Instead of improving absolute fidelity, quantify how noisy the official signal itself is (H2).
Then decide what each remaining submission can teach us.
