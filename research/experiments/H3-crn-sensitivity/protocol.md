# H3: With fixed background seeds, does a small config change resample the noise?

## Why
H2 leaves two readings of the official noise:
- sd 0.47 s (repeat noise only) would make S2-S1 = +2.6 s significant.
- sd 1.48 s (fit residual) would not.
The deciding fact is whether a fixed TrafficGenerator seed keeps the bg realisation aligned with
the download when the config changes slightly. Common random numbers only reduce noise if the system
is not chaotic. This is a generic dynamical property, so an inaccurate simulator can still answer it
qualitatively.

## Method (`research/src/crn_test.py`, sim_v2 best variant: q400, bbr, bg_rto 0.5, warmup 5)
For K = 6 bg seeds:
- (a) bg-seed sd: sd across bg seeds for the base config. This is the local evaluator, where
  seed = system time.
- (b) repeat sd: same bg seed, 6 jitter seeds (system randomness only, start jitter 0-20 ms).
  This plays the role of the official identical-config repeat.
- (c) perturbation sd: same bg seed and same jitter seed, 6 near-identical configs.
  - Base: S1 staircase.
  - Variants change one dir by +-1 packet: dir1 41, dir2 39, dir4 36, dir4 38, dir5 37, dir6 35.
Statistic: mean over seeds of the within-seed sd for (b) and (c), compared with (a).

## Prediction
The system is close to chaotic: (c) is about the same as (b), and both are > 0.5 x (a). If so, a
fixed official seed does not make small config differences meaningful, and the fit-residual noise
(~1.5 s per score at n=3) is the right noise model.
