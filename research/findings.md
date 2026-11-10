# Findings (outer loop cycle 2, 2026-11-10)

This file replaces the cycle 1 findings of 2026-11-09. Cycle 1 rested on 10 official points.
Cycle 2 uses all 26 official shots, listed with full pacer.txt text in
`research/data/official_and_local_data_inventory.md`. The new data refutes two cycle 1 claims.
See "Corrections" at the end.

## Current understanding

### 1. Official scores are noisy for configs that are not pacer-limited
Three configs were submitted twice with byte-identical pacer trees:

| Config | Shot 1 (s) | Shot 2 (s) | Difference (s) |
|---|---|---|---|
| Champion leak 40,40,40,37,36,36 (#16, #26) | 122.05 | 133.20 | 11.2 |
| leak 40,40,40,36,36,36 (#12, #25) | 124.37 | 136.71 | 12.3 |
| tb front + precise back (#14, #15) | 140.02 | 155.16 | 15.1 |

- From these pairs, the sd of one official shot is about 9 s.
- The 9 shots of the high-rate leak staircase family give an official mean of 129.7 s and an
  sd of 5.4 s.
- Use 5-9 s as the sd of one official shot for high-rate configs.
- Pacer-limited configs are much less noisy: leak 9/1000 scored 246.0 s and 244.0 s (#01, #02).
  The pacer cap, not the background traffic, sets their time.

### 2. Official runs of the high-rate leak family are about 5.6 s faster than local runs
- Local, champion config, n = 45: mean 135.3 s, sd 10.3 s.
- Official, staircase family, 9 shots: mean 129.7 s.
- Use this offset to translate local results of high-rate leak configs into official ones.

### 3. Files 5-6 decide the score
- Local per-file means for the champion, n = 9: files 1-4 together take 28.8 s, file 5 34.1 s,
  and file 6 73.0 s.
- Files 5 and 6 also carry most of the variance. File 6 alone has an sd of 6-9 s.

### 4. Pacing files 5-6 near the fair share is the largest local gain found so far
- Config U4-base:
  - Files 1-4 use the champion config.
  - Files 5-6 use `token_bucket tokens=20, burst=40, token_refill_rate=20,
    token_refill_interval_us=4000, enable_n_in_flight=1`.
  - The nominal cap is 20 packets per 4 ms, about 50 Mbps at 1250 B per packet.
- Local results, n = 12 each, interleaved, from `~/polaris/local-eval/evals/cand-U4-*` on the VM:

  | Config | Mean (s) | sd (s) | File 6 (s) |
  |---|---|---|---|
  | U4-base, refill 20 / 4000 us | 116.9 | 8.1 | 59.2 |
  | U4-i8k, refill 40 / 8000 us | 118.7 | 3.2 | 60.6 |
  | U4-r24, refill 24 / 4000 us | 120.1 | 7.5 | 62.7 |
  | Champion (local reference, n = 45) | 135.3 | 10.3 | about 73 |

- The differences among the three U4 variants are not significant (t below 1.1).
- Mechanism: on file 6, the champion reaches about 35 Mbps against a 90 Mbps cap, so loss limits
  it. U4 reaches about 44 Mbps against a 50 Mbps cap, so its own pacer limits it and it loses
  fewer packets.

### 5. U4 loses most of its gain in the official evaluator
- U4-base scored 130.0 s officially (one shot).
- Applying the offset from finding 2, its predicted official score is 116.9 - 5.6 = 111.3 s. The
  measured score is 18.7 s slower than that.
- With a single-shot sd of 5-9 s, z is about 2-3.5. The loss is probably real, but it rests on
  one shot.
- The official bottleneck bandwidth is not the likely cause. Three facts argue against it:
  - The high-rate family is faster officially than locally (finding 2).
  - The rules fix the access and uplink links at 100 Mbps (`local-eval/docs/official/01_rules.md`).
  - The leaderboard top, 116 s, implies an average of at least 43 Mbps.

### 6. The official pacer timer probably runs on 4 ms ticks
This is a working hypothesis (M-tick). It has not been measured, because the kernel of the
official container is not observable. Under M-tick:
- The pacer acts on 4 ms ticks, once the elapsed time reaches the configured interval.
- Any interval below 4000 us therefore becomes 4 ms.
- At exactly 4000 us, timing jitter sometimes costs a second tick. The average period is then
  about 5 ms, so the effective rate is about 0.8 x nominal.

| Official shot | M-tick prediction | Measured |
|---|---|---|
| leak 9/1000 x6 (#01, #02) | 9 pkts / 4 ms, about 22 Mbps, collapse | 246.0 s, 244.0 s |
| leak 10, 10, 10, 10, 9, 9 / 1000 (#20) | about 25 Mbps, about 200 s | 208.6 s |
| leak 20, 20, 20, 19, 18, 18 / 2000 (#19) | 45-50 Mbps cap on all files | 129.2 s |
| U4-base (files 5-6 at 20 / 4000) | about 40 Mbps on files 5-6, below fair share | 130.0 s |
| leak 24/60, 27/40 / 4000 (#07, #05) | 48-54 Mbps effective, near or below fair share | 150.7 s, 141.7 s |

M-delta is the competing model: every wake-up fires a fixed 1 ms late. It fits the 4000 us shots
just as well. It fails #20, where it predicts about 140 s against a measured 208.6 s.

## Patterns and insights
- To judge a config officially, submit it at least twice. One shot carries 5-9 s of noise for
  high-rate configs.
- Prefer configs whose prediction does not depend on which timer model is true.
  - A 3000 us interval is the clearest case. Under both M-tick and M-delta, its official period
    is exactly 4 ms.
  - So U4-i3k (refill 20 / 3000 us on files 5-6) should run at 50 Mbps officially either way.
- Pacer-limited configs have lower variance, both locally (U4-i8k sd 3.2 s) and officially
  (#01, #02). Lower variance also protects against the rule that top submissions are re-tested
  with a new seed.
- The local evaluator seeds its background traffic from system time, and the binary exposes no
  seed option: `--help` lists only `--output-dir`, `--result-json`, `--format-log-dir`, and
  `--version`. Local A/B tests must therefore interleave configs and use n >= 12 to resolve
  about 3 s.

## Lessons and constraints
- Never use `leak_interval_us < 4000` with a rate tuned for the local 1 ms timer (#01, #02, #20).
- Do not read a single official shot as a measurement of a config. Compare family means.
- Do not use either simulator's absolute numbers or rankings to pick submissions. Cycle 1 showed
  that neither has predictive skill.
- Write predictions down before each submission in
  `research/experiments/H7-timer-lag/predictions.md`. Do not edit a prediction after its score
  arrives.

## Open questions
- Does U4-i3k recover the local U4 gain officially? Predicted about 112 s under both timer models.
- Is the U4-base loss (130.0 s) real? A second official shot of U4-base would settle it.
- Does the 4 ms tick also slow the front files? Champion files 1-4 at 40/4000 would run at about
  80 Mbps officially. Officially the front files may be faster at 40/3000.

## Corrections to cycle 1
| Cycle 1 claim | Status | Evidence |
|---|---|---|
| "The official evaluator is effectively a fixed-seed benchmark; repeat sd 0.47 s" | Refuted for high-rate configs | Identical pairs differ by 11-15 s (finding 1). The low sd came from v1/v1b, which is pacer-limited, and from an opponent's 4 shots whose config is unknown. |
| "Small config changes give seed-specific effects of +-2 s, real for the fixed official seeds" | Unsupported | It assumed the fixed-seed claim above. The sim_v2 result itself (H3) stands, but it says nothing about the official evaluator. |
| "The staircase gain over uniform 36/40 is -11.0 s, z >= 5" | Overstated | It compared single shots: 122.05 s against 133.09 s. The family mean of 129.7 s against 133.09 s gives about -3.4 s, which is within one-shot noise. |
| "G = 4000 us rounding" (`local-eval/docs/background/timer-granularity.md`) | Partly refuted | It predicted 27/40/4000 at about 134 s; the measured score was 141.7 s. It also predicts no penalty for U4-base, which scored 130.0 s. M-tick extends it. |
