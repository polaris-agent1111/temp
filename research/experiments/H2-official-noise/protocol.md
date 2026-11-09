# H2: How large is the noise floor of official scores?

## Question
The team treats official differences of ~2.6 s as mechanism evidence. One example is S2 = 124.66 s
vs S1 = 122.05 s, read as "41 packets breaks the 40-packet red line". Is a difference that small
distinguishable from noise?

## Method (`research/src/official_noise.py`)
1. Repeat noise: pooled CV over identical configs submitted more than once (v1/v1b; another team's
   same config x4).
2. Config-to-config noise upper bound: residual sd of `T = a + b*rate + c*rate^2 + d*cap` on the
   6 uniform leak 4000 us points.
3. z-scores of S2-S1, S3-S1 and uniform36/40-S1 under both noise levels.

## Prediction
Repeat sd < 1 s at ~122 s. Fit residual sd is 1.5-2.5 s. S2-S1 is not significant at p < 0.05
under the fit-residual noise. The staircase gain over uniform 36/40 (-11 s) is significant.
