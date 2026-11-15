# E51 — is the corpus effect a level or an interaction?

**Verdict: an INTERACTION. Good for the thesis, and the most structurally novel result the
programme has.**

---

## QUESTION

E33 established that the fitting corpus moves the read by 58× the seed noise. That is compatible
with two very different stories:

- **a level** — some corpora simply make better operators, and one could in principle rank them;
- **an interaction** — the corpus changes *which concepts* are legible, with no consistent
  ranking.

The two have opposite consequences. A level invites a scalar "corpus quality" predictor. An
interaction says no such scalar can exist, because the thing to predict is a matrix.

## PRE-REGISTRATION

**None.** This is a *recomputation*, not a measurement: it re-derives from stored ladder artifacts
a decomposition that had been quoted in six documents and computed by no script in any commit. The
file records this as `"recomputes_not_remeasures"`.

That history is why the experiment exists at all, and it is the honest framing: E51 does not add
evidence, it makes existing evidence checkable. Its own decision content is the **F test**, which
was specified as part of the recomputation.

## DESIGN

Two scales. `pythia-410m-deduped` (band [9,21]) and `pythia-1b-deduped` (band [5,13], see deltas).
`persist`, `N ≥ 75`, five corpora × five admitted concept sets × three disjoint seed blocks.

Variance decomposition of read AUC over (corpus, set) with seed blocks as replication:

```
y[c,s,r] = μ + a_c + b_s + (ab)_{cs} + ε_r
```

Reported both for the five admitted sets and for all six (`association` is floored — 196 of 205
scored cells are exactly zero).

## CONTROLS, and the number each produced

| control | required | produced | fires |
|---|---|---|---|
| **reproduces the prose** | within 0.1 pp | 410M interaction claimed 6.8 / recomputed **6.780626**; corpus main claimed 1.9 / recomputed **1.906450**; set main claimed 91.3 / recomputed **91.278294**. 1B likewise | **yes, all six** |
| **C3** permutation null | — | **MIS-SPECIFIED — DO NOT CITE.** It destroys the corpus main effect along with the interaction, so it cannot separate them | **no** |
| **C4** F test with seed blocks as the error term | F > F_crit(0.001) = 3.3 | **F(16,50) = 611.89** (410M), **567.29** (1B) | **yes** |
| **4614× audit** | reproduce the quoted multiplier | **does not reproduce under any of six natural denominators**: 196× / 235× / 612× / 2548× / 2768× (seed×set) / 10268× (seed main) | **fails — see deltas** |

## RESULT

| | 410M | 1B |
|---|---|---|
| eval-set main effect (task difficulty) | **91.278%** | **88.580%** |
| **corpus × set interaction** | **6.781%** | **9.158%** |
| corpus main effect | 1.906% | 2.212% |
| seed residual | 0.035% | 0.050% |

The interaction is **3.56×** the corpus main effect at 410M and **4.14×** at 1B, and
**F(16,50) = 612 / 567** against a 0.1% critical value of 3.3.

Concretely: Github is **+1.3** on order-ops and **−1.9** on multihop in within-set z-scores. The
sign reverses.

`results/e51_interaction_variance.json`

## VERDICT

**REPRODUCES.** The six variance fractions match the prose to within 0.1 percentage points at both
scales, and the interaction is larger than the seed-level scatter by a factor of 612.

> The fitting corpus does not make the Jacobian lens better or worse. It changes which concepts
> the lens can read.

## FLAGGED DELTAS

1. **"4614× the seed×set noise floor" is RETRACTED.** The variance fractions reproduce exactly;
   the multiplier does not follow from that decomposition under any natural denominator, and **no
   script in any commit ever computed it**. It was in six live citations and is dropped from all of
   them, replaced by the F test — which is what the sentence was reaching for. The file's own
   VERDICT says it "must not be restated until the operator names the intended denominator."
2. **C3 is mis-specified and marked so in the file.** Cite C4, never C3.
3. **The 1B band is off by one layer.** `ladder1b` is scored on **[5,13]** where the anchor's
   normalized L38–L92 rule gives **[6,13]**, and its ceiling reaches 81% of depth rather than 92%
   because the penultimate target sits inside the band at 16 layers. **Disclosed, not corrected**:
   the 1B ladder lenses were never retained, so the fix is a refit rather than a rescore. It
   affects the 1B column here.
4. **Absolute AUCs are not comparable across scales** (13 band layers at 410M, 9 at 1B, so the
   `persist` threshold differs). Orderings and variance decompositions are.
5. **No pre-registration.** Strength comes from the recomputation matching independently-quoted
   numbers, not from a rule fixed in advance.

## MEANING FOR THE PAPER

Supports §"The corpus effect is an interaction, not a level" and — importantly — supplies the
*reason* two other results came out as they did:

- it explains **why E48's registered CI had no power**: between-set heterogeneity at 91.3% swamps
  a 1.9% corpus main effect across five sets;
- it explains **why E31's twenty-one predictors all fail**: a scalar summary of "corpus quality"
  is predicting the 1.9%, and the effect lives in the 6.8%.

That makes E51 the hinge of the paper rather than a supporting table.

## PROVENANCE

| | |
|---|---|
| result | `results/e51_interaction_variance.json` |
| script | `experiments/t51_interaction_variance.py` |
| module | `bash repro/exp/e51_interaction.sh` |
| inputs | `results/ladder410/*.json`, `results/ladder1b/*.json` (30 files hashed) |
| tier | **A** |
| cost | free, seconds on CPU |
