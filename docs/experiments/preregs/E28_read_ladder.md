# E28 — the read ladder: does corpus choice or sample size govern the read?

**Output:** `results/ladder410/`, `results/ladder1b/`

**Verdict: corpus, decisively. `N` barely moves it. Good for the thesis, and it is the ladder
every later 410M result is scored against.**

---

## QUESTION

The estimator decomposition has two error terms — sampling, `O(N^-1/2)` and buyable, and corpus
bias, `O(1)` in `N` and unbuyable. The method's own convergence analysis addresses the first. This
measures which one actually moves a read.

## PRE-REGISTRATION

`docs/experiments/preregs/superseded/PREREG_PYTHIA_T7_v2.md` governs the confirmatory cells; E28's own primary
("do the per-corpus asymptotes separate?") was fixed with amendments A1/A2 before scoring.

**Guard that still binds:** models named in that pre-registration must not be scored without
`--prereg`; the runner refuses. **1.4B and 2.8B are the last clean confirmatory cells.** Fitting
there is safe; *scoring reads there consumes the confirmatory test*. 1B is already burned and free.

## DESIGN

`pythia-410m-deduped` (band [9,21]) and `pythia-1b-deduped` (band [5,13] — see deltas).
Five Pile components — Pile-CC, StackExchange, Wikipedia (en), Github, USPTO Backgrounds — 2400
windows each in **three disjoint seed blocks**, **16 values of `N` ∈ [25, 800]**, `persist`, five
admitted sets.

**Every prompt contributes exactly 128 tokens**, so prompt length is controlled by construction and
cannot drive any between-corpus comparison. All 83 fitting runs share identical hyperparameters.

**Replication unit:** the three disjoint seed blocks, never residual scatter across `N`. The `N`
grid is nested, so errors along it are correlated and an interval computed from them is too narrow.

## CONTROLS, and the number each produced

| control | required | produced | fires |
|---|---|---|---|
| **asymptote separation** | pairs separate at p<0.05 | **9 of 10** pairs; between-corpus spread **58×** the seed SD | **yes** |
| **1B replication** | ordering holds | 9/10 pairs separate at **36×** seed SD; **Github worst at both scales** | **partially** — Spearman only **+0.700** |
| **seed-block disjointness** | no shared prompts | index ranges recorded in `corpora/manifest.json` | **yes** |

## RESULT

Read AUC by corpus and `N` (`persist`, five admitted sets, seeds averaged):

| corpus | N=25 | 75 | 200 | 400 | 800 | range / seedSD |
|---|---|---|---|---|---|---|
| Github | 0.0263 | **0.0292** | 0.0279 | 0.0278 | 0.0280 | 2.5 |
| Wikipedia (en) | **0.0397** | 0.0376 | 0.0382 | 0.0393 | 0.0389 | 3.9 |
| StackExchange | 0.0444 | 0.0453 | 0.0456 | **0.0458** | 0.0456 | 3.7 |
| Pile-CC | 0.0454 | **0.0459** | 0.0456 | 0.0458 | — | 1.2 |
| USPTO Backgrounds | 0.0480 | 0.0495 | 0.0494 | **0.0504** | — | 3.1 |

Total movement in read AUC over a **32×** change in `N` is at most **0.00283** — 1.2 to 3.9 seed
SDs — and **Wikipedia peaks at N=25**, so more data makes it worse there.

`results/ladder410/*.json`, `results/ladder1b/*.json`

**Operator convergence and task accuracy decouple.** The operator is still measurably moving at
`N=800`; the read stopped before `N=75`. The method's `N=1000` recipe buys nothing measurable.

## VERDICT

**ASYMPTOTES SEPARATE.** Corpus identity sets a floor that more data cannot fix.

## FLAGGED DELTAS

1. **"Reads plateau at N≈75" is RETRACTED.** Only 3 of 5 corpora show that shape and Wikipedia
   peaks at N=25. Reads are **flat** in `N`, which is the stronger and simpler statement.
2. **The −0.511 sample-size law is RETRACTED as a finding.** `ε = √(disp/N)` recovering an exponent
   of −1/2 is true *by construction*: `Ĵ_N` is a sample mean, its standard error is σ/√N by the
   CLT, and dispersion is *defined* as σ²/μ². It is retained only prescriptively — at ε=5% it asks
   for `N* = 946` at 410M — and then shown not to transfer to reading a model.
3. **The 1B band is off by one layer**: [5,13] where the anchor's rule gives [6,13]. Disclosed, not
   corrected — the 1B ladder lenses were never retained, so the fix is a refit rather than a
   rescore. Absolute AUCs are therefore not comparable across the two scales; orderings and
   variance decompositions are.
4. **Scale-stability is only partial.** Spearman +0.700 between the two scales: StackExchange moves
   third → first, USPTO first → fourth. *Which* corpus is best is itself a function of scale. The
   paper must not claim a stable ranking.
5. **`association` is excluded throughout** — 196 of 205 scored cells are exactly zero, so it is
   floored, not measured.
6. **Tier B.** The ladder predates `src/provenance.py`. Its consumers (E51, E33b) are Tier A.

## MEANING FOR THE PAPER

Supplies §"Sample size is close to the wrong question" and Figure 1. Its role in the argument is
to close off the buyable error term: *over a 32× range in fitting sample size the read barely
moves; over five fitting corpora it moves by 58× the seed noise.* That contrast is the paper's
opening move.

## PROVENANCE

| | |
|---|---|
| results | `results/ladder410/*.json` (15), `results/ladder1b/*.json` (15), `results/e28_*.pt` (240 lenses) |
| script | `experiments/e28_ladder_410m.py`; eval driver `e28_eval_410m.sh` |
| tier | **B** |
| cost | GPU — this is the one expensive experiment in the programme |
