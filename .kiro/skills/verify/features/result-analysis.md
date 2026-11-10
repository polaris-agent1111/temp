# Result analysis

Users summarize stored experiment records by configuration, omit invalid runs by default, filter tags, and request a readable table or JSON.

## Sub-features

- `analysis-empty`: fresh data directory returns an explicit empty state.
- `analysis-json`: aggregate count and mean match the persisted input.
- `analysis-invalid`: invalid runs enter the group only with `--include-invalid`.
- `analysis-table`: tag-filtered table remains a usable terminal view.

## How to get to it (user POV)

- Run `python harness/analyze.py`, optionally with `--json`, `--tag base`, or `--include-invalid`.

## Driving it with control.py

Preconditions: fresh launch/doctor, no scratch result ledger. Run `control.py drive --run cli-check-01 --feature analysis`.

- **Empty.** Run `python harness/analyze.py --json`. Expect exit 0 and `暂无结果`.
- **Input.** The driver writes three synthetic baseline rows to the scratch `runs/results.jsonl`: valid tag `base` totals 60 and 64; invalid tag `bad` total 1. This is fixture data for a file-reading CLI, not a remote evaluation result.
- **Aggregate.** Run `python harness/analyze.py --json`. Require one baseline group, `n=2`, `mean=62`, and no input-file changes.
- **Include invalid.** Run `python harness/analyze.py --json --include-invalid`. Require `n=3`.
- **Table/filter.** Run `python harness/analyze.py --tag base`. Inspect the captured table: two runs, mean 62, baseline row, and the per-file section. This fixture has empty `downloads`; six per-file cells should be dashes. It does not cover real per-file timing values.
- **Proof.** Preserve `analysis-input.jsonl` and four transcripts, then cleanup/evidence checks. Do not copy or rewrite the checkout's existing result ledger.

## Gotchas

- Empty input with `--json` is a Chinese text message, not `[]`.
- The CLI uses its own script-relative ledger path and has no `--input` option; source copying isolates this fixed path without changing application code.
- Malformed JSON lines are skipped. Structurally incomplete JSON rows may still fail later; do not silently discard failing fixtures.
- These numbers establish aggregation behavior only; real measurements and report writers remain unverified.
