# Public leaderboard

Users inspect standings, optionally save snapshots and a ledger, or watch for a team's next attempt.

## Sub-features

- `board-read`: terminal standings from the public endpoint.
- `board-save`: snapshot plus ledger persistence.
- `board-watch`: bounded watch exits on the requested attempt or timeout.

## How to get to it (user POV)

- `python client/api.py board`
- `python client/api.py board --save`
- `python tools/watch_board.py --team 赛博coder --interval 120 --max-min 300 --want 2`

## Driving it with real CLI

Preconditions: reachable official public endpoint, a dedicated checkout without session/credential files, and network access. The offline helper cannot drive this feature. Report missing network or isolated data as an unmet precondition; no fixture response can prove live standings.

- **Read.** Run `python client/api.py board` in that checkout. Capture argv/exit and sanitized terminal standings; require the total and question rankings rather than treating an HTTP response alone as proof.
- **Save.** Record the existing filenames/hashes under `intel/raw/` and `runs/leaderboard/`; run `python client/api.py board --save`. Require a new snapshot and a new ledger row reflecting the displayed standings. Preserve sanitized copies as evidence outside the disposable checkout.
- **Watch.** Run the bounded watcher command above only when the current attempt count and the target make the journey meaningful. Record starting count, newly observed count or timeout, and the corresponding new `runs/board_watch.jsonl` record. A timeout does not prove an attempt arrived.
- **Cleanup.** Remove only the dedicated checkout owned by this run after preserving evidence; stop only the watcher process this run started if interrupted.

## Gotchas

- Real standings change; record observation time and keep local evaluation separate from official scores.
- `board --save` writes production-style snapshot/ledger paths. Do not run it in a checkout another agent is using for collection.
- The client can load an existing pickled session even for board reads. A credential-free checkout is part of the precondition.
- This feature is unverified by the generated offline smoke run.
