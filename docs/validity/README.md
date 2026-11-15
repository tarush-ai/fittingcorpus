# docs/validity/ — are these the right experiments?

This folder asks one question: assuming the code is right and every result reproduces, do the
experiments measure what the paper says they measure? Whether the code is right is checked
separately, in [`../reproducibility/`](../reproducibility/). Keeping the two apart matters because
each catches errors the other cannot.

| file | what it holds |
|---|---|
| [`DIAGNOSIS.md`](DIAGNOSIS.md) | **start here.** Why the absolute readout numbers are low (Pythia answers 3–6% of the battery at top-1), which candidate causes were measured, and what each finding must therefore be called. This is the reasoning behind the paper's Limitations section |
| [`CONSTRUCT_VALIDITY.md`](CONSTRUCT_VALIDITY.md) | where the ground truth comes from (concepts annotated for much larger models than Pythia), and the routes out of that problem |

## What a design check catches

Design errors survive perfect code and perfect reproduction. Every row below was found in this
programme, on numbers that recompute exactly. Values are on the 0–1 scale the results files use (the
paper multiplies by 100).

| failure | the case found here |
|---|---|
| **wrong replication unit** | the fit/read variance decomposition's bootstrap resampled seeds while holding the eight corpora fixed, but the claim is about corpora |
| **an underpowered null reported as an absence** | the containment contrast has a minimum detectable effect of 0.0268 at 80% power, more than the whole between-corpus spread of 0.0246. The honest statement is a bound of about ±0.02, not "exposure does not matter". The paper says only that raw containment does not account for the ordering |
| **a decision statistic with a degenerate denominator** | E37's ratio divides by +0.0055 at 70M (inside the noise) and −0.0358 at 160M (negative), so neither its REJECT nor its ACCEPT means anything. E37 is silent about the mechanism at small scale |
| **a result that exists under only one free choice** | on the independent 5 × 5 grid, the fit-over-read ordering holds under `min` and reverses under `persist`. The paper reports the share split as aggregation-dependent for this reason |
| **an aggregation that collapses** | at 70M the band is two layers, so `persist` is `min`. A 70M result that "survives both aggregations" survives one |
| **a control that could not have fired** | E33's first derangement shifted each layer by one; adjacent layers have the most similar Jacobians, so the control was near-vacuous. The amended random derangement flipped the sign of one result |
| **a statistic that does not measure the intended quantity** | unembedding geometry computed on uncentred rows is dominated by a direction shared by every row, which cancels out of the rank comparison the readout makes. The paper therefore does not use it as a cause of the small-model floor |
| **a stale transcription** | a number computed before a correction and still printed. It is fixed by recomputing, never by editing the number |

## How to check a claim

1. **Name the replication unit.** How many independent maps, corpora and seeds? Bootstrapping over
   items does not create independent corpora.
2. **For every null, state the effect the design could have detected.** If it could not detect an
   effect the size of what it is compared with, it is a bound, not an absence.
3. **Check every ratio's denominator.** A rule whose denominator can be near zero or change sign is
   not a rule.
4. **Vary the free choices**: the band summary (`min`, `persist`, best single layer, band mean), the
   readout (corrected or legacy), the band, *N*, the evaluation families and the corpus panel. A claim
   that holds under one setting is a claim about that setting.
5. **After every result, ask what it invalidated**, then check those claims.

The 2026-08-22 audit that found most of the rows above was run by independent reviewers against an
extracted digest of the results. Its working files stay in the private working repository;
`DIAGNOSIS.md` is the public synthesis.
