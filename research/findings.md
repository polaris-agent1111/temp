# Findings (outer loop cycle 1, 2026-11-09)

## Current understanding
1. **Neither offline simulator can rank configs against the official evaluator.** The metric is
   LOO-RMSE over the 10 official points after one global offset. The constant "predict the mean"
   model scores 9.04 s.
   - v1 (`local-eval/tools/offline_pacer_sim.py`): 22.7 s, Spearman -0.06. It also has no
     staircase gain.
   - sim_v2 (`research/src/sim_v2.py`: per-flow TCP background with Poisson arrivals, explicit
     queue/CC/timer): best variant 9.8 s, median about 16 s, over 24 structural variants.
   - Both miss the right wall: 40-44 packet bursts are slow officially but not in either model.
   - Both mispredict `30/50/5000` and the 1 ms trap.
   The unknowns are background responsiveness, download CC, queue size, timer semantics and leak
   "reject" semantics. They outnumber what 10 totals can identify.
2. **The official evaluator is effectively a fixed-seed benchmark.**
   - Identical-config repeats: pooled CV 0.39 %, i.e. 0.47 s at 122 s.
   - The local evaluator has a single-run sd of 11.6 s, because it seeds from system time.
   - sim_v2 reproduces this split: fixing the bg seed cuts variance about 20x (H3).
3. **With the seed fixed, small config changes give seed-specific effects of +-2 s.** In sim_v2,
   +-1-packet changes to the S1 staircase average +0.4 s, with sd 2.0 s across seeds (H3).
   - The official S2-S1 (+2.6 s) and S3-S1 (+2.7 s) are within that band.
   - They are real for the fixed official seeds but are not evidence of a "40-packet red line".
   - They would likely not survive the rule's new-seed re-test of top submissions.
4. **The staircase gain over uniform 36/40 (-11.0 s) is large** compared with every noise source
   (z >= 5). It is the only structural official result we can trust as transferable. The mechanism
   is still unknown: front rate 40, cap = rate, or both.

## Patterns and insights
- Variance in this task is dominated by the background realisation. The 10-30 MB flows mostly land
  on files 5-6. Any comparison that does not fix the background (local runs with different
  timestamps, or different sim seeds) needs about 100 runs to resolve 2 s.
- Common random numbers work. When comparing configs locally, use the **same bg seed** for both and
  compare paired differences. TrafficGenerator accepts `-s`, so the local evaluator could do this
  if its `BASE_CONFIG.background.seed` could be set. The guide says the wrapper passes no seed,
  which makes local A/B 20x noisier than it needs to be.

## Lessons and constraints
- Never use `leak_interval_us < 4000` (official: 9/30/1000 -> 245 s).
- Do not use either simulator's absolute numbers or rankings to pick submissions.
- An official difference < ~5 s from a 1-packet tweak is not a transferable mechanism result.
- In sim_v2, the background must be modelled at offered load 100 %. Without background RTO, the
  per-flow TCP background never yields bandwidth; with Cubic, the download then starves.

## Open questions
- What mechanism produces the 11 s staircase gain? A test that fits within the noise budget needs
  configs that differ by >= 5 s in expectation:
  - uniform 40/40 (not yet submitted)
  - S1 with caps restored to 40 (bucket-cap effect)
- Do bypass modules (token_bucket / precise with `enable_n_in_flight=1`) behave on the official 4 ms
  timer as they do locally? Only one official point exists: tb 100/200/20, 140.9 s, with burst 200.
  This is the largest information gap. It is also where the leaderboard top (116 s) probably is.
