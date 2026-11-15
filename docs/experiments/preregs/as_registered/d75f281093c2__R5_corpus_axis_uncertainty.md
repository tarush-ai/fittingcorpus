# R5 — corpus-axis uncertainty, stated as such

**PRE-REGISTERED 2026-08-19, before the run.** Source:
[`../POSTREVIEW_EXPERIMENTS.md`](../POSTREVIEW_EXPERIMENTS.md) §3 Tier B, item R5.

---

## QUESTION

The paper prints one interval on its headline variance split. That interval **resamples seed
factors and holds the eight corpora fixed**, and it is then written next to language that invites a
population reading. Two independent reviewers converged on this — the adversarial review calls the
91% *"a descriptive decomposition of one 8x8 grid, not a robust scientific estimate"*, and the
reproducibility review reaches the same place independently (C-3 row 6: *"the interval resamples
seeds and holds the eight corpora fixed; the leave-k-out numbers are the honest corpus-axis
uncertainty"*). **Two independent reviewers converging is the strongest signal in the review
package.**

## DESIGN

**No new measurement.** From `e57_factorial_cells_410m*.json` and `e55_matrix_robustness`, produce:

* the full leave-one-corpus-out and leave-two-corpus-out **distributions** of `fit_pct` and
  `read_pct` — not merely the count of splits preserving the ordering;
* the min-max range over those splits;
* a corpus-as-random-effect variance component **with its degrees of freedom printed next to it**,
  so its weakness at n=8 is visible rather than implied.

Run against R1's corrected cells once they exist, and against the unstripped cells, so the two
conventions are never mixed.

## PRIMARY

The range of `fit_pct` over all 28 leave-two-out splits, reported beside the seed bootstrap
interval, **with both units named in the caption**.

## DECISION RULE — fixed before running, quoted verbatim

Quoted from `specs/POSTREVIEW_EXPERIMENTS.md` §3, item R5:

> **DECISION RULE.** Descriptive; no branch. The deliverable is that the paper stops printing one
> interval whose unit is not the unit the claim is about.

## CONTROLS — each with the number it must produce

* **C1 — full-panel recovery.** With no corpus dropped, the decomposition must recover the stored
  full-panel value. *Required:* `fit_pct` equal to the E57 point estimate to <= 1e-9.
* **C2 — leave-k-out counts reproduce.** *Required:* 8 of 8 leave-one-out and 28 of 28
  leave-two-out under `persist`; **27 of 28** under `min`, the exception being the
  drop-both-extremes split.

**Power.** C1 can fail (a wrong axis or a wrong denominator breaks it). C2 can fail. Neither is an
identity.

## DECLARED BIAS

n = 8 corpora, **chosen not sampled**. A random-effect variance component on eight non-random units
is a description dressed as an inference and is captioned as such wherever it appears.

## COST

$0, CPU, hours.

## RESULT

*(unrun at time of writing)*

## VERDICT

*(pending)*
