# H4: Submission plan as pre-registered structural contrasts (for the 11/10 quota)

Status: protocol locked before any official result. The human submits; the agent has no access.

## Design rules (from H2/H3)
- Each shot must differ from the reference S1 (122.05 s) by a structural change with expected
  |effect| >= 5 s. +-1-packet ladders are excluded: their seed-specific effect is +-2 s, and they
  will not survive the new-seed re-test.
- Change one structural factor per shot, so that each result can be attributed.
- Keep 2 of 5 shots for follow-ups chosen after the first 3 results.

## Candidates
All candidates were rendered and validated with `local-eval/tools/validate_pacer.py`: LF line
endings, no trailing newline, PASS. Candidate trees are in `candidates/<name>/1..6/pacer.txt`.

| shot | name | dirs 1-4 | dirs 5-6 | what it isolates |
|---|---|---|---|---|
| 1 | C1-back-precise-g4000 | S1 (leak 40,40,40,37; cap = rate) | precise_rate_based 11,250,000 B/s, clock_granularity 4000, n_in_flight 1 | Back files: rate-based module + bypass vs leak batches, at the same nominal rate (36 pkt / 4 ms x 1250 B) |
| 2 | C2-back-precise-g1000 | same | same, clock_granularity 1000 | Whether a 1 ms tolerance survives the 4 ms official timer. The local best was g = 1000 (58-61 s on 6.bin), but the local VM runs HZ = 1000. |
| 3 | C4-S1-cap40-back | leak 40,40,40, then 37/cap 40 | leak 36 / cap 40 | Cap-vs-rate decomposition of the staircase gain. Locally, uniform 36/36 vs 36/40 = -6 s. |
| (4-5) | follow-up | | | see the decision tree |

C3-front-tokenbypass (token_bucket 40/40 with bypass on dirs 1-4) is held back. Files 1-4 take
~25 s in total, so the expected effect is below the 5 s rule.

## Pre-registered predictions (wide, because no simulator has skill)
- C1: 112-132 s. Point guess 120 s. The direction is genuinely uncertain:
  - Gain: lsquic pacing is min(CC rate, configured), and the bypass helps after loss.
  - Loss: if the CC pacing rate is below the configured rate, the configured rate does not bind.
  - Gain over S1 counts as evidence only if it is >= 3 s.
- C2 vs C1:
  - If the rate-based pacer reschedules from "now" on each 4 ms wake, C2 collapses (> 150 s; the
    timer doc's prediction for 1 ms tolerance is about 205 s).
  - If it keeps an accumulating schedule, C2 lands within 3 s of C1.
  - Either outcome is decisive about the official timer semantics of rate-based modules.
- C4: 124-130 s (S1 + 2-8 s), if the local cap effect transfers. If C4 is within 2 s of S1, then
  cap = rate is not the source of the staircase gain, and the front rate 40 is.

## Decision tree for shots 4-5 (same day, after results)
- C1 < S1 - 3 and C2 ~ C1:
  - Shot 4: C2-style back with 12,000,000 B/s on dir 6 only (local optimum).
  - Shot 5: C1 back + C3 front (full bypass stack).
- C1 < S1 - 3 and C2 collapses:
  - Shot 4: C1 back at 12,000,000 B/s with g 4000.
  - Shot 5: C1 back + C3 front.
- C1 >= S1 - 3, i.e. rate-based gives no gain officially:
  - Do not pursue precise.
  - Shot 4: token_bucket back (tokens 36, burst 40, refill 36 per 4000 us, bypass on) as the
    bypass-only contrast.
  - Hold shot 5.
- In every branch, resubmitting S1 is not needed. Repeat noise is already known (0.47 s).
  **Corrected 2026-11-10:** this is wrong. S1 was resubmitted as #26 and scored 133.20 s against
  122.05 s. The sd of one official shot is about 5-9 s for high-rate configs
  (`research/findings.md`, finding 1). The ">= 5 s structural effect" rule therefore needs two
  shots per config to detect.

## Caveat on the offline check
`sim_v2_paired_check.txt` (16 paired seeds):
- C3 = -0.7 +- 0.5 s and C4 = +0.1 +- 0.2 s vs S1.
- C1/C2 collapse to ~470 s. That collapse is a known artefact: sim_v2's BBR bandwidth filter
  spirals down under 25 % loss, and rate-based modules bind on the CC pacing rate. It contradicts
  the measured local evaluator (precise 12e6 on 6.bin = 58-61 s). Do not read it as a prediction.
