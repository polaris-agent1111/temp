# H3 analysis (CONFIRMATORY for (a)-(c); per-seed effect table EXPLORATORY)

`python research/src/crn_test.py` -> `results/crn.json` (sim_v2, 6 bg seeds).

| quantity | sim_v2 | official analogue |
|---|---|---|
| (a) sd across background seeds, S1 | 22.6 s | local evaluator single run ~11.6 s |
| (b) repeat sd (same bg seed, system jitter only) | 1.28 s | 0.47 s (pooled, 3-run avg) |
| (c) within-seed sd across S1 and 6 +-1-packet variants | 1.00 s | - |

The prediction was refuted. The system is not chaotic at the level of total time. Once the
background realisation is fixed, the remaining variance is about 1/20 of the cross-seed variance.
This supports the "fixed seed" reading of the official evaluator.

## The more important part (exploratory): config effects are seed-specific
Each row is the effect of a +-1-packet change relative to S1 in one directory. The six values
are the effect under each of the 6 bg seeds.

| change | mean | sd across seeds | per-seed effect (s) |
|---|---|---|---|
| dir1 41 | +0.47 | 2.00 | 0.2, -1.0, 0.2, 3.8, -1.9, 1.5 |
| dir2 39 | +0.36 | 2.10 | -0.1, -0.7, -1.9, 4.3, 0.6, -0.1 |
| dir4 36 | +0.32 | 0.92 | 0.9, -1.1, 0.3, 0.5, -0.2, 1.5 |
| dir4 38 | -0.39 | 2.01 | -0.2, -0.4, -3.2, 2.7, -1.7, 0.4 |
| dir5 37 | -0.08 | 2.36 | 0.6, -0.2, -4.6, 2.3, 0.4, 0.9 |
| dir6 35 | +0.33 | 1.72 | 0.6, -0.4, -1.3, 3.6, -0.8, 0.2 |

A +-1-packet tweak has an average effect of about 0.4 s. Under any single fixed seed set, though,
the same tweak shows a +-2 s effect (sd), up to 4.6 s. Two consequences follow:
1. Under the fixed official seeds, a 2-3 s official difference from a 1-packet tweak is not mostly
   jitter. It is mostly real, but **for that seed set only**. Two examples:
   - S2-S1 = +2.6 s does not show that 41 breaks a red line.
   - The shift is the size expected from a seed-specific interaction.
2. The rules state that top submissions are re-tested with new seeds. Micro-tuning on the leaderboard
   fits the fixed background realisation. The gain is expected to vanish (mean ~0.4 s) on re-test.

Caveat: sim_v2 has no absolute skill (H1). These are qualitative magnitudes from a model whose
cross-seed sd (22.6 s) is about 2x the local evaluator's (11.6 s). If the real system is less
volatile, the seed-specific effect may be closer to 1 s. Even then, the conclusion holds for
differences of about 2.5 s or less.

## Decision rule derived
- Count an official difference as evidence of a transferable effect only if it is >= ~5 s, or if it
  is reproduced by a structurally different config.
- Spend shots on structural changes (module family, bypass, per-file rate regime) with expected effects
  >= 5 s, not on +-1-packet ladders.
