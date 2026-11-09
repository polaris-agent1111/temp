# Research log

## 2026-11-09 bootstrap
- Workspace placed under `research/` to keep the competition repo root clean.
- Calibration dataset: `data/official_points.json` (11 official points, 1 excluded for unknown config),
  `data/local_official_eval_points.json` (local runs of the official evaluator, noisy).
- Facts found: lsquic master defaults to BBRv1; TrafficGenerator = Poisson request arrivals on
  persistent TCP connections, offered load = -b (100 Mbps here = 100% of the bottleneck).
- Continuity: Kiro CLI has no /loop; research continues within the session and resumes from
  `research-state.yaml` + `findings.md`.
- H0 protocol locked before running.

## 2026-11-09 inner loop H0-H3
- H0 (confirmed): sim v1 has no skill. LOO-RMSE is 22.7 s against 9.04 s for the constant model;
  Spearman -0.06.
- H1 (refuted): sim_v2, a per-flow TCP background model, was run over a 24-variant grid. The best
  LOO-RMSE is 9.8 s. No variant beats the constant model. Cubic download starves under a
  100 %-offered background.
- H2: official repeat sd is 0.47 s. The U-fit residual is 1.48 s. Whether S2-S1 is significant
  depends on CRN behaviour.
- H3: the prediction (chaotic) was refuted. Fixing the bg seed cuts variance 20x. Exploratory
  result: +-1-packet effects are seed-specific (sd 2.0 s, mean 0.4 s).

## Outer loop cycle 1: PIVOT
Absolute simulator fidelity cannot be identified from 10 totals, so I stopped pursuing it. Next
steps:
- Treat the official evaluator as a fixed-seed benchmark.
- Spend submissions only on structural contrasts expected to be >= 5 s.
- Use paired-seed local comparisons.

Progress report: `to_human/progress-01.html`.

## 2026-11-09 H4
- Locked the structural submission plan (experiments/H4-submission-design/protocol.md) with predictions and a decision tree. Candidate pacer trees are rendered and validated. Offline paired check: C1/C2 collapse is a sim_v2 BBR artefact; C3 -0.7 s; C4 +0.1 s.
- Waiting on the human to submit and report official scores.
