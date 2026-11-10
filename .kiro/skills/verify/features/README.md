# iDSN verification map

Read this index before selecting a journey. This is the maintained verification source for the top-level user workflows; it is a seed map, not an exhaustive inventory of every research/reporting script in `tools/`.

## Baseline preconditions

- Run from the repository root with the local Python environment and documented dependencies.
- Launch a fresh owned run using `control.py`; require `doctor` readiness and matching source hashes.
- The scratch checkout starts without credentials or experiment data. Analysis seeds synthetic records and labels them as such.
- Every command listed in a feature's drive section is relative to the scratch root unless explicitly marked real checkout/remote. The helper captures exact invocations; do not run those generators against existing production tags.

## Driving conventions

- `control.py` means `python .agents/skills/verify/scripts/control.py` with the selected interpreter.
- Choose one fresh run ID, pass it to launch/doctor/drive/cleanup/evidence, and drive once.
- Record argv, stdout, stderr, exit status, resulting files and feature/entry point. Expected rejection exit codes must be explicit.
- The helper never drives remote commands. Remote journeys require their own preconditions and evidence.
- Cleanup scratch state after failures too; keep transcripts and generated evidence.
- A missing precondition fails the journey with a reason. Do not weaken it or count a different entry point as coverage.

## Features

| Feature | Entry points | Driver | Proof scope |
|---|---|---|---|
| [Configuration generation](configuration-generation.md) | uniform flags, no mode, `--configs-file` | `--feature generation` | six downloads, default/inheritance, persisted bytes |
| [Pacer validation](pacer-validation.md) | `--selftest`, tree path, `--json` | `--feature validation` plus generation | acceptance and user-visible rejection |
| [Result analysis](result-analysis.md) | table, JSON, tag filter, include invalid, empty input | `--feature analysis` | synthetic input only |
| [Leaderboard](leaderboard.md) | `client/api.py board`, `board --save`, watcher | manual real CLI | external; unverified by offline driver |
| [Remote evaluation and submission](remote-evaluation.md) | experiment, sweep, upload, submit, schedulers | Lead on real target | external; unverified by offline driver |

`--feature all` covers all offline rows, not remote rows. Other parameter modules and constraint edge cases can be added as the map grows; the initial generator proof uses `leak_bucket`, `token_bucket`, and `origin`.
