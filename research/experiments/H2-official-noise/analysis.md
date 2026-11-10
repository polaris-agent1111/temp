# H2 analysis (CONFIRMATORY)

> **Correction, 2026-11-10.** The repeat-noise figure below (sd 0.47 s) does not hold for
> high-rate configs. Three byte-identical configs were each submitted twice and differ by
> 11.2 s, 12.3 s, and 15.1 s (#16/#26, #12/#25, #14/#15 in
> `research/data/official_and_local_data_inventory.md`). The sd of one official shot is about
> 5-9 s. v1/v1b are pacer-limited, which is why they repeat closely. The z values in the second
> table are therefore too large. "uniform 36/40 - S1" drops to z of about 1-1.5, and S2/S3 are
> within noise. See `research/findings.md`, finding 1.

Output of `python research/src/official_noise.py` (saved to `results/noise.json`):

| quantity | value |
|---|---|
| repeat noise, ours (v1/v1b, 245 s) | sd 1.44 s, CV 0.59 % |
| repeat noise, 大肥鱼 x4 (129 s) | sd 0.37 s, CV 0.29 % |
| pooled repeat CV | 0.39 % -> 0.47 s at 122 s |
| U-fit residual sd (6 pts, 4 params, dof 2) | 1.48 s |

| comparison | diff | z (repeat noise) | z (fit residual) |
|---|---|---|---|
| S2 - S1 (41 on dirs 1-2) | +2.61 s | 3.9 | 1.25 (p = 0.21) |
| S3 - S1 (perturbation) | +2.74 s | 4.1 | 1.31 (p = 0.19) |
| uniform 36/40 - S1 | +11.04 s | 16.5 | 5.3 |

## Reading
- The staircase gain over uniform 36/40 is real under either noise model.
- S2 and S3 are significant only if config changes do not resample the noise. The fit residual
  (1.48 s, which also contains model misfit) is 3x the repeat noise. That suggests either:
  - config changes add noise beyond repeat noise, or
  - the U-shape is a poor model.
- The fit has 2 dof, so its residual sd is itself uncertain by roughly a factor of 2.
- Identical-config repeats are not exactly deterministic: v1/v1b differ by 2.0 s. The "fixed seed
  sequence" therefore removes the background-seed noise but not system jitter.

Undecided: which noise model applies to a small config change? H3 tests this.
