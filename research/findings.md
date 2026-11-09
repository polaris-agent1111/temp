# Findings

## Current understanding
(bootstrap) Official scores are near-deterministic per config (repeat spread 0.3-0.8 %), so the official
evaluator is a low-noise black box with ~40 queries left (5/day to 11/16). The offline simulator v1 is
reported to miss the staircase gain (sim ~133 s for both champion and uniform 36; official 122.0 vs 133.1).

## Patterns and insights

## Lessons and constraints
- Never use `leak_interval_us < 4000` (official 4 ms timer: 9/30/1000 -> 245 s).

## Open questions
- Is the 11 s staircase gain from the front-file rate (40), from cap = rate, or from fixed-seed luck?
