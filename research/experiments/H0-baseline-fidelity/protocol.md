# H0: How well does the existing offline simulator predict official scores?

## What
Run `local-eval/tools/offline_pacer_sim.py` (v1) through `research/src/fidelity.py` on the 11
official calibration points in `research/data/official_points.json`, 100 seeds each, cubic, official regime.

## Locked evaluation metric (applies to all later simulator hypotheses)
- Primary: LOO-RMSE (seconds) of predictions after one global additive offset, over the 10 points
  excluding the 1 ms trap.
- Secondary: Spearman rho over the same 10 points; staircase gap
  `pred(S1) - pred(leak36_40)`, official value -11.04 s.
- Gate: 1 ms trap prediction > 200 s.
- Reference: the constant model (predict the mean) has LOO-RMSE = the sample sd * sqrt(n/(n-1)) of
  the 10 targets. A simulator is only useful if it beats the constant model.

## Prediction
v1 passes the trap gate, has staircase gap near 0 (README says ~0), and its LOO-RMSE is no better than
the constant model (~8 s), because the 10 targets are dominated by the S1/S2 vs uniform contrast
which v1 does not reproduce.
