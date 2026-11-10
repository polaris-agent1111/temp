---
name: verify
description: Drive iDSN 六载穿柜 Python CLIs to verify configuration generation, pacer validation, and result analysis with isolated offline evidence. Consult the feature map for leaderboard and Lead-only remote evaluation or submission checks.
---

# iDSN verification driver

Read `README.md`, `CONTRIBUTING.md`, and [features/README.md](features/README.md) from the repository before choosing a journey. Primary surface: short-lived Python CLI commands, not a local web server. Remote surfaces are the public leaderboard API and the shared competition VM. This skill does not grant Lead authority or submission permission.

## Launch

Run from the repository root in Nushell. Use `.venv/Scripts/python.exe` on Windows; on other systems use an interpreter with `requests` and `websocket-client`. The README asks for Python 3.14; this skill was exercised with Python 3.15.2. Do not treat that as verification of 3.14.

```nu
.venv/Scripts/python.exe -c "import requests, websocket; print('dependencies ready')"
```

If dependencies are absent, install the two documented packages into the local environment. For an existing venv without pip, `uv --no-cache pip install --python .venv/Scripts/python.exe requests websocket-client` works. Package installation needs package-index access; the verification drive itself does not. Use a writable temporary directory if the sandbox's default temp directory fails. Do not replace an existing venv.

Choose a fresh run name for every attempt. The following concrete run name is an example invocation; if it already exists, choose a new one consistently across all commands.

```nu
.venv/Scripts/python.exe .agents/skills/verify/scripts/control.py launch --run cli-check-01
.venv/Scripts/python.exe .agents/skills/verify/scripts/control.py doctor --run cli-check-01
```

Readiness is `READY verify-cli-check-01; ... offline CLI; no service/port`. Launch copies five unchanged source/schema files into `runs/evals/verify-cli-check-01/work/`, records their hashes and dependency versions, and creates an empty scratch directory. No migrations, account, seed credentials, server, or port are required. The analysis journey creates explicitly synthetic local input, never contest measurements.

Separate run names can run concurrently: each has its own sources, configurations, temp files, and input ledger. Never drive the shared VM concurrently; it has a single `question` tree. Never reuse a tag in the real checkout: the generator deletes and rebuilds that tag's directory.

## Doctor

`control.py doctor --run cli-check-01` is read-only. It requires the owning checkout, the same Python executable, both installed dependencies, and unchanged source hashes in both the checkout and the isolated copy. Run it first when something looks wrong. A missing/stale workspace requires cleanup and a new launch, not a bypass of the hash check. It does not validate remote authentication or VM readiness.

## Drive

The helper invokes actual CLI entry points with `runpy.run_path(..., run_name='__main__')` in separate Python subprocesses. It passes the real arguments and does not call internal setters or replace `VmShell`. It denies network/DNS attempts, child-process launches, credential-file reads, and writes outside the scratch directory via Python audit events. This is a guard for these Python commands, not a security sandbox for arbitrary native extensions. All inherited `IDSN_*` values are removed and an unused dummy VM password avoids credential lookup during import.

```nu
.venv/Scripts/python.exe .agents/skills/verify/scripts/control.py drive --run cli-check-01 --feature all
```

Or choose one of `generation`, `validation`, `analysis` on a fresh run. Each drive is single-use: launch a new run for another drive. The [feature map](features/README.md) lists the precise commands and expected states. `all` covers only the three offline features; the two remote feature files remain separate. A nonzero driver exit is failure even if some CLI transcripts passed.

## Evidence

Evidence stays under `runs/evals/verify-cli-check-01/`, which the current `.gitignore` already excludes:

- `manifest.json`: source hashes, Python/dependency versions, checkout identity, and digest of Git refs.
- One JSON per command: exact argv, cwd, stdout, stderr, exit code, and before/after file hashes. A CLI error is captured before the driver rejects it.
- `boundary-events.jsonl`: blocked audit events without sensitive event arguments. Passing drives require zero events.
- `config-uniform/`, `config-default/`, `config-mixed/`: retained generated trees for a second, independent view of persisted bytes. Empty default directories are intentional.
- `analysis-input.jsonl`: synthetic input used only by the analysis feature.
- `proof.json` and `cleanup.json`: bounded outcome and teardown record.

Proof must pair a real user action with its observable result, exit status, and stored-file effects. Do not claim a feature from only its final output. For generation, the helper verifies exact UTF-8/LF bytes, timestamps and filenames, and checks that the uniform dry-run changes only six pacer files: no archive, evaluation log, result row, or submission row. It observes denied network boundaries and compares Git ref digests. Do not infer safety from `dry-run`: `client/submit_vm.py` defaults to a dry-run that still connects to and runs checks on the shared VM.

The isolated copy uses unchanged source, but omits credentials, existing results, contest binaries and the remote VM. Setup performed by the helper is source copying, a scratch temp directory, dummy import-time password, and synthetic analysis data. Remote upload/format checks, scheduling, official scores, and real authentication remain unverified until their mapped journeys run on the real target. No mock or synthetic result establishes contest performance. Report each mapped entry point as passed, failed, or unverified; one passing feature does not prove the whole map.

## Cleanup

Run cleanup after success **and after every failed drive or partial launch** that created a manifest. It deletes only the owned `work` directory, refuses linked paths, and retains proof. No service is launched; child commands have a 30-second timeout and subprocess creation is denied inside the driven program. Never kill processes by name.

```nu
.venv/Scripts/python.exe .agents/skills/verify/scripts/control.py cleanup --run cli-check-01
.venv/Scripts/python.exe .agents/skills/verify/scripts/control.py evidence --run cli-check-01
```

The last command must print `EVIDENCE PASS` after cleanup. For a failed drive, keep the failure transcripts; `evidence` should fail because there is no passing proof. Never remove the enclosing evidence directory as routine cleanup.

## Helpers

[scripts/control.py](scripts/control.py) is an executable Python script; invoke it with the interpreter as shown above. `--help` lists actions and features. `_exec` is its private child entry point, not a general-purpose command runner. Keep assertions enabled: do not use `python -O`.

When CLI flags or entry points change, update the matching feature and helper together and rerun their journeys. Use `/maintain-verification-skill` for maintaining this map.
