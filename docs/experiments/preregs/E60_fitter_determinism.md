# E60 — the fitter equivalence, measured rather than asserted

**Run 2026-08-16.**

## WHY
`paper.tex` asserted "our fitter equals `jlens.fitting.fit` at 2e−05" and cited
`tests/test_anchor_fidelity.py`. **That test did not contain the claim.** 2e−05 is the `atol`
**default** of `fastfit.verify_against_anchor()`, nothing in the repo ever called it, and no results
file stored its output. A tolerance is not a measurement.

## OUTPUT
`results/e60_fitter_determinism.json`

## DESIGN
`experiments/t60_fitter_determinism.py`. pythia-70m, 8 prompts of ≥128 tokens, `target_layer=-2`,
`skip_first=16`, thread counts {1,4,8,10,12}. Reports cross-implementation disagreement **and**
each implementation's disagreement with *itself* across thread counts.

## PRIMARY
Whether the cross-implementation gap is the same order as each fitter's own nondeterminism.

## CONTROLS
| control | required | produced | fires |
|---|---|---|---|
| **C1** repeated runs at a fixed thread count are bit-identical | 0.0 | anchor **0.0e+00**, fast **0.0e+00** | ✓ |
| **C2** prompts exceed `skip_first`+1 | all | 140–153 tokens, 8/8 | ✓ |

## RESULT
**Exact (0.00e+00) at 1, 4 and 8 threads; 1.1e-04 at 10 and 12.** The released fitter disagrees with
**itself** across thread counts by **1.3e-04** — the same order. So the two fitters are equal up to
fp32 reduction order, and `atol=2e-05` is a gate that passes or fails by machine.

**Corollary, and it is the more important half: fits are not bit-reproducible above 8 threads on
this machine**, which every stored lens SHA depends on.

C2 exists because the first attempt used a 6-prompt eval sample; `skip_first=16` discarded four of
them and the 2-prompt fit disagreed at 1.4e-04 for that reason alone — not the regime any real fit
runs in.

## VERDICT
The paper's fidelity sentence now reads "0.00e+00 up to 8 CPU threads and 1.1×10⁻⁴ above that,
the same order as the released fitter's disagreement with itself — equality up to fp32 reduction
order." `tests/test_anchor_fidelity.py` A6 asserts the **envelope across thread counts**, not a
number that happens to hold at one of them.

## FLAGGED DELTAS
- Measured on 70M only. Whether the crossover thread count differs at 410M/1B is untested.
- The A5 assertion (`top-1 disagreements == 0`) is knife-edge by construction and flipped on the
  L40S box; see `E62_ladder1b_corrected_band.md` for that adjudication.
