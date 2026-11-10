# Remote evaluation and official submission

The Lead can upload a configuration to the shared VM, evaluate six downloads, retrieve results, and explicitly spend a contest submission slot.

## Sub-features

- `remote-evaluate`: single experiment and repeated runs.
- `remote-sweep`: queue processing, selected tags and per-item failure behavior.
- `remote-upload`: upload and official format check without evaluation.
- `remote-submit-preflight`: default submission command still connects to the VM.
- `remote-submit`: explicit Lead-authorized official submission.
- `remote-schedulers`: batch, adaptive and night schedulers have distinct side effects.

## How to get to it (user POV)

- `harness/run_experiment.py` without `--dry-run`, with optional `--repeat`.
- `harness/sweep.py --queue ...` with optional `--only`.
- `harness/upload_config.py`.
- `client/submit_vm.py`, and explicit `--yes` for official submission.
- `tools/submit_batch.py`, `tools/adaptive_submit.py`, `tools/night_submit.py`.

## Driving it with real CLI

Preconditions: Lead authority for the specific operation, exclusive ownership of the shared VM slot, valid local authentication, fresh collision-free tags, and healthy official binaries. Before proceeding, inspect each command's current arguments and side effects, plus the timestamped `STATUS.md` and `hourly/INDEX.md`. Credentials must remain local and must not enter transcripts. The offline helper refuses these operations.

- **Evaluate.** With a Lead-approved fresh tag, run `python harness/run_experiment.py --tag verify-remote-01 --mode leak_bucket --params "leak_rate=9,bucket_cap=30,leak_interval_us=1000" --repeat 3`. Confirm the tag is unused first. Require all `-r1..3` raw result JSON/log files, corresponding new `runs/results.jsonl` records, six completed downloads per run, and plausible timing. This changes the VM's active question tree.
- **Sweep.** On a separately reserved VM slot, run `python harness/sweep.py --queue runs/queue1.json --only A B` only after inspecting that queue and reserving its tags. Require per-tag results and explicit evidence for any failed item. `ALL DONE` and exit 0 alone do not prove every item succeeded.
- **Upload.** `python harness/upload_config.py --tag verify-upload-01 --mode leak_bucket --params leak_rate=9 bucket_cap=30 leak_interval_us=1000` changes the shared tree. Verify the six remote files and official format-check result; it is not an offline preview.
- **Preflight.** `python client/submit_vm.py` reads local secrets, connects to the VM and runs format checks. Require a passing checker and no new actual-submission record. Do not invoke it as an offline doctor.
- **Submit.** Only with explicit Lead authorization to consume a slot, run `python client/submit_vm.py --yes --note "verification-approved configuration"`. Capture a sanitized receipt and the new local submission record, then verify the corresponding official attempt once available. An accepted upload is not an official score.
- **Schedulers.** Read the chosen scheduler's code first and define a bounded journey for that mode. `--rehearse` still uploads/checks; adaptive dry modes can query the board; the night scheduler waits and later dispatches. None are covered by `control.py drive`.
- **Cleanup.** Preserve sanitized configuration/results/receipt evidence. Release VM ownership through the existing Lead coordination process; restore remote state only by a Lead-approved procedure. Never kill a shared process by name or delete remote results as generic cleanup.

## Gotchas

- Non-Lead agents must not run these journeys. Missing authority is a failed precondition, not permission inferred from requesting this skill.
- The VM has one question tree and evaluation disrupts WebSSH; use the harness's short polling connections.
- One run cannot establish a performance improvement. Local evaluation and official scoring differ.
- Authentication failures must stop; do not repeatedly attempt passwords.
- The default CLI tag paths and remote shell commands are not arbitrary-path safe: use simple fresh alphanumeric/hyphen tags.
- All remote entry points remain unverified until exercised on the real target. Preserve this limitation in the result.
