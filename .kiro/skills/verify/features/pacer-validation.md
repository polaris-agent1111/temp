# Pacer validation

Users check a configuration tree locally, get all detected errors, and receive an exit status suitable for scripts.

## Sub-features

- `validation-selftest`: built-in valid, CRLF and invalid samples behave as expected.
- `validation-tree`: generated uniform, empty and mixed trees are accepted.
- `validation-json-rejection`: a user-supplied CRLF file fails with a structured diagnostic.

## How to get to it (user POV)

- Run `python tools/validate_pacer.py --selftest`.
- Pass a question-tree path; optionally add `--json`.

## Driving it with control.py

Preconditions: fresh launch and doctor. Run `control.py drive --run cli-check-01 --feature validation`; use another fresh generation run for the three acceptance journeys.

- **Self-test.** Run `python tools/validate_pacer.py --selftest`. Require exit 0 and `SELFTEST PASS`; inspect valid/CRLF/invalid sample output.
- **Reject file.** The driver creates directories `invalid/1..6` and writes CRLF bytes to `invalid/1/pacer.txt`, then runs `python tools/validate_pacer.py invalid --json`. Require exit 1, `ok: false`, and check 3 explaining the encoding/line-ending failure.
- **Accept file.** The generation feature runs text validation of `runs/configs/uniform` and JSON validation of `runs/configs/default` and `runs/configs/mixed`. Require exit 0 on each. This is separately mapped coverage; self-test does not replace it.
- **Proof.** Retain the rejection command, diagnostics and before/after input hashes; require cleanup and evidence retention.

## Gotchas

- Missing pacer files are allowed, missing numbered directories are not.
- The schema is `configs/params_schema.json`; local acceptance does not establish official-checker acceptance.
- `--selftest --json` prints a final `SELFTEST PASS` line after the JSON, so the entire output is not one JSON document.
- Parameters omitted from the file use module defaults; the validator's cross-field checks apply when both fields are explicitly present.
