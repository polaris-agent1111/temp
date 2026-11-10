# H7: official timer behaviour — pre-registered predictions

Written on 2026-11-10, before the candidates below were submitted. Do not edit the predictions after a
score comes in; append the result in the Result column instead.

## Data this rests on (official_and_local_data_inventory.md, 26 official shots)
- Identical configs submitted twice: #16/#26 122.05 / 133.20, #12/#25 124.37 / 136.71,
  #14/#15 140.02 / 155.16. Single-shot official sd is about 5-9 s for high-rate configs.
  The earlier "official is fixed-seed, CV 0.39 %" claim only holds for pacer-limited configs
  (#01/#02 leak 9/1000: 246.0 / 244.0).
- High-rate leak staircase family (9 shots): official mean 129.7, sd 5.4. Local (n=45 champion) 135.3.
  Offset: official = local - 5.6 s.
- U4-base (files 5-6 tb refill 20/4000): local 116.9 (n=12), official 130.0.
  Same offset would predict 111.3. Gap +18.7 s, z about 2-3.5 on one shot.

## Competing models of the official pacer timer
- **M-delta**: every wake-up fires about 1 ms late. Period = I + 1000 us.
  Fails #20 (leak 10/1000, official 208.6): predicts about 140.
- **M-tick** (HZ=250 style): the pacer acts on 4 ms ticks when elapsed >= I. I <= 4000 needs one tick,
  but at I = 4000 jitter sometimes needs two, giving an average period of about 5 ms.
  I in (4000, 8000] needs two or three ticks.
  Fits #01/#02/#20 (1 ms -> 4 ms), #19 (2000 us -> 4 ms, 129.2), U4-base (4000 -> ~5 ms).
- **M-none**: no official timer penalty; the U4 gap is noise.

## Predictions (official total, s; tolerance +-8 s for one shot)
| Candidate | Files 5-6 | M-delta | M-tick | M-none |
|---|---|---|---|---|
| U4-i3k | tb 20/40, refill 20 / 3000 us | ~112 (50 Mbps) | ~112 (50 Mbps) | ~118 (local-like 67 Mbps) |
| U4-r25 | tb 20/40, refill 25 / 4000 us | ~112 | ~112 if p ~ 0.25 | ~118 |
| U4-i8k45 | tb 20/40, refill 45 / 8000 us | ~112 | ~117 | ~118 |
| U4-base (done) | refill 20 / 4000 us | 130 | 130 | 111 |

U4-i3k is the robust pick: under M-delta and M-tick its official period is exactly 4 ms, so its
prediction does not depend on the unknown miss probability. Under M-none it behaves like local r24.

## Results
| Date | Candidate | Official | Consistent with |
|---|---|---|---|
| | | | |
