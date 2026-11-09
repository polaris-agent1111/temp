# H1: A mechanistic simulator (sim2) with per-flow TCP background reproduces the official response

## Hypothesis
v1 fails because its background is a single aggregate rate. TrafficGenerator really issues Poisson
requests (lambda = 100 Mbps / mean flow size, i.e. offered load 100 % of the bottleneck), each served
by its own TCP flow that starts in slow start. This produces (a) idle or light periods that a fast
download can grab, so low pacing caps hurt (official left wall: 24/60 -> 150.7 s), and (b) shared
drop-tail losses when the download bursts, so very high per-tick bursts hurt (right wall).

## Model (research/src/sim_v2.py)
- Bottleneck: 100 Mbps fluid drop-tail queue of Q packets, 1 ms ticks, FIFO departures by class share.
- Background: Poisson arrivals, WebSearch CDF sizes, per-flow Reno-like AIMD (slow start from IW10,
  halve on loss, one reduction per flow per RTT), RTT = 70 ms + queueing delay.
- Download: 6 sequential connections, 1 RTT handshake each, CC in {cubic, bbr}.
- Pacer modules as in the official doc. Timer: periodic actions fire every max(interval, 4 ms) + lat.
- Structural unknowns swept: Q in {40, 120, 400}, cc in {cubic, bbr}, lat in {0, 1 ms}.

## Metric (same as H0, locked)
LOO-RMSE over the 10 non-trap official points; Spearman; staircase gap (official -11.04 s); trap gate.

## Predictions
- P1: the best variant beats the constant model (LOO-RMSE < 8.4 s) and v1 (22.7 s).
- P2: the best variant has a left wall: pred(24/60) - pred(36/40) > +5 s.
- P3: the staircase gap is negative (< -3 s) for the best variant.
If P1 fails for all variants, the per-flow background is not the missing mechanism.

## Overfitting guard
12 variants vs 10 points: report the full grid, not only the winner, and only trust structure that
holds for several neighbouring variants.
