# H0 analysis (CONFIRMATORY)

Run: `python research/src/fidelity.py --sim v1 --seeds 100` -> `results/v1_cubic_100.json`.

| metric | v1 | constant model |
|---|---|---|
| LOO-RMSE (10 pts) | 22.69 s | ~8.4 s |
| Spearman | -0.06 | n/a |
| staircase gap | +0.63 s | official -11.04 s |
| trap gate | 226 s, PASS | |

Prediction confirmed: v1 has no skill. Without the post-hoc "binding floor" clamp used in its own
selftest, v1 predicts 196.8 s for `30/50/5000` (official 140.5 s).

## What it rules out
- **Timer model `eff = ceil(interval / 4 ms) * 4 ms` is refuted** by `30/50/5000`: it would make the
  5000 us interval fire every 8 ms (3750 pps, ~170-200 s), but officially `30/50/5000` (140.5 s) behaves
  like the other 6000-6750 pps points (`24/60/4000` 150.7 s, `27/40/4000` 141.7 s).
  A model of the form `eff = max(interval, ~4 ms) + small latency` is consistent with all three.
- v1's download never benefits from a higher cap: all 4000 us leak points come out 129.6-130.8 s,
  so v1 has no low-rate penalty (official 24/60 is +17.6 s over 36/40) and no staircase effect.
  The low-rate penalty means the download often could go faster than ~50-60 Mbps, i.e. the
  background leaves large idle gaps that a paced download can grab. v1's aggregate background
  (single AIMD rate, FIFO flow drain) does not create such gaps.

## Next
H1: rebuild the background as per-flow TCP over a Poisson (TrafficGenerator) arrival process with
offered load = 100 % of the bottleneck, make the download CC selectable (lsquic default is BBRv1),
and make queue size and timer latency explicit parameters.
