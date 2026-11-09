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
