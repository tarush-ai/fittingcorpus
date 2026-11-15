# R7 — length- and format-matched fitting pools

**PRE-REGISTERED 2026-08-20, before any fit.** Source:
[`../POSTREVIEW_EXPERIMENTS.md`](../POSTREVIEW_EXPERIMENTS.md) §3 Tier B, item R7.

---

## QUESTION

`SUSPICIONS.md` S-3, unresolved: **Github is the outlier in at least nine analyses**, and it is also
the corpus whose token distribution differs most from the English-prose battery. The P-ladder
already shows length matters — R moves from 2.60 raw to **3.46 length-matched** at 410M, and
`CONTEXT.md` §1.2 instructs the reader to cite the length-matched column. **Nothing in `results/`
matches the fitting corpora on length, type-token ratio or tokens-per-document before comparing
their reads.**

## DESIGN

Refit the five in-stream corpora at N=200 on pools matched on **median tokens-per-document** and
**type-token ratio**, then re-run the ladder read.

## PRIMARY

The between-corpus spread in units of the pooled seed SD, matched versus unmatched.
Published: **58×** under `persist` unstripped; **43×** under the anchor readout per the review's
re-score.

## DECISION RULE — fixed before running, quoted verbatim

Quoted from `specs/POSTREVIEW_EXPERIMENTS.md` §3, item R7:

> **DECISION RULE.** ACCEPT if the matched spread stays above 20 seed SDs. UNCLEAR between 5 and 20.
> REJECT below 5, in which case the corpus effect is substantially a length effect and the paper
> says so.

## CONTROLS — each with the number it must produce

* **C1 — the pools must actually be matched.** Report the post-matching spread in the matched
  statistics. *Required:* below **10%** of the pre-matching spread.
* **C2 — reproduce the unmatched spread from the same code path.** *Required:* the unmatched arm
  recovers the published spread for its readout convention, so that any movement is attributable to
  matching and not to the pipeline.

**Power.** C1 can fail outright — Github may not be matchable against English prose at all. C2 is a
reproduction check with a real threshold.

## DECLARED BIAS

Matching on two statistics leaves **markup, code-ness and surprisal free**. Github may not be
matchable against English prose without discarding most of it; **if the matched pool falls below
N=200, report the shortfall rather than padding.** Scored at the corrected (stripped) readout per
R1, so the comparison baseline is the re-scored spread, not the published 58×.

## COST

5 fits ~ **$1**, plus CPU read. `SUSPICIONS.md` prices the grid at ~$2. GPU required for the same
reason as R6. **Needs the operator's sign-off before any spend.**

## RESULT

*(unrun — awaiting budget sign-off)*

## VERDICT

*(pending)*
