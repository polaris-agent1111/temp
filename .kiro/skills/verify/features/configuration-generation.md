# Configuration generation

Users turn a uniform parameter list, an empty baseline, or a per-download JSON file into the six-download configuration tree without running the competition.

## Sub-features

- `generation-uniform`: one leak-bucket configuration in all six directories.
- `generation-default`: all six directories exist and have no pacer file.
- `generation-mixed`: selected downloads receive configurations; absent entries inherit.

## How to get to it (user POV)

- Run `harness/run_experiment.py --tag ... --mode ... --params ... --dry-run`.
- Omit `--mode` to generate a default baseline.
- Supply `--configs-file` with a JSON mapping of download number to module and parameters.

## Driving it with control.py

Preconditions: fresh launch and passing doctor; no generated tags in scratch. Run `control.py drive --run cli-check-01 --feature generation`.

- **Uniform.** The driver runs `python harness/run_experiment.py --tag uniform --mode leak_bucket --params "leak_rate=9,bucket_cap=30,leak_interval_us=1000" --dry-run`. Expect exit 0 and `[dry-run]`. Reopen all six files: exact three-line UTF-8 bytes, LF, no BOM or trailing newline, matching timestamp. Only these six files may change.
- **Second view.** Run `python tools/validate_pacer.py runs/configs/uniform`. Expect exit 0 and `[PASS]`.
- **Baseline.** Run `python harness/run_experiment.py --tag default --dry-run`. Require directories `1..6`, no pacer files, then validate the tree with `--json`; expect `ok: true`.
- **Mixed.** The driver writes `mixed.json` containing `{"1":["token_bucket",{"tokens":100,"burst":200}],"3":["origin",{}]}` and runs `python harness/run_experiment.py --tag mixed --configs-file mixed.json --dry-run`. Require pacer files only in directories 1 and 3 and a passing JSON tree validation.
- **Evidence.** Retain command transcripts, file snapshots and all three generated trees outside `work`; cleanup, then require the `evidence` action to pass.

## Gotchas

- The generator overwrites existing tag trees and does not validate parameter constraints itself.
- `--repeat` does not create repeated outputs in the dry-run branch.
- `--params` accepts separate `k=v` tokens; the README's comma-separated string also renders the intended line for this example. Do not infer input validation from successful generation.
- This proves local config serialization; it does not prove tar upload, the official format checker, inheritance during actual downloads, or performance.
