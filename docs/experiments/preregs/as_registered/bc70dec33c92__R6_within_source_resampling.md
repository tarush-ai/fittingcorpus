# R6 — within-source resampling: is "corpus" a factor, or a bundle?

**PRE-REGISTERED 2026-08-20, before any fit.** Source:
[`../POSTREVIEW_EXPERIMENTS.md`](../POSTREVIEW_EXPERIMENTS.md) §3 Tier B, item R6.

---

## QUESTION

The single best experimental idea in either external review, and the one the paper's own
Limitations item 3 already concedes: *"A corpus bundles formatting, boundaries, token-frequency
profile, syntax and surprisal; we control prompt length and nothing else."*

If the fit-axis effect survives when the **source is held fixed** and only the **sample** varies,
the effect is not a bundle artifact. If it collapses, the paper's factor is confounded and must be
renamed.

**Why this matters more after R1, not less.** R1 cut the fit axis's *share* from 91.2% to 50.7%,
but in absolute terms the fit axis barely moved (SS ×0.85) — what grew was the read axis (×10.27).
So the fit effect is still the larger of the two and still needs to be shown to be a *source*
effect rather than a *sampling* effect. R6 is the experiment that decides that.

## DESIGN

The two largest in-stream sources by document pool: **Pile-CC** and **Wikipedia_en**. Four
**disjoint** sub-corpora per source at N=200, drawn from disjoint document blocks. Fit one operator
on each — 8 operators — and read all eight against the fixed battery at a fixed read context.
Decompose the read variance into between-source and within-source.

## PRIMARY

`between_source_SS / (between_source_SS + within_source_SS)` under `persist`.

## DECISION RULE — fixed before running, quoted verbatim

Quoted from `specs/POSTREVIEW_EXPERIMENTS.md` §3, item R6:

> * **ACCEPT (corpus identity is a real factor):** between-source share >= 0.70.
> * **REJECT (the effect is sample noise, not source identity):** between-source share <= 0.30.
>   **STOP and alert** — the paper's factor is not what it is called.
> * **UNCLEAR:** anything between. Report the number and stop; do not re-cut it.

## CONTROLS — each with the number it must produce

* **C1 — document disjointness.** The four within-source draws must be verified document-disjoint.
  *Required:* **0** shared documents between any pair. `e58`'s disjointness machinery already
  exists and reports 24–26% overlap *without* the exclusion step, so it has demonstrated power.
* **C2 — shuffled-assignment null.** Relabel the eight operators' source at random and recompute.
  *Required:* the between-source share falls to its chance level, ~1/7 of total (0.143), and the
  observed share must exceed the null's 95th percentile.
* **C3 — derangement floor.** Each new operator must clear its own layer-deranged floor under
  `persist`, as all published 410M operators do on 120/120 draws. *Required:* 8 of 8.

**Power.** All three can fail. C2 in particular is a real null, not an identity: with 8 operators
in 2 groups a random relabelling has a well-defined non-zero expected between-group share, and the
test is whether the observed value exceeds it.

## DECLARED BIAS

1. **Two sources, not eight.** This tests whether *source identity* beats *sampling*; it does not
   test whether it beats *formatting*, which is R7.
2. The fitting pools are drawn under the same `require_full_window` filter, **whose selectivity
   differs by corpus** — the confound `SUSPICIONS.md` S-3 raises. Stated, not solved.
3. **Scored at the corrected (stripped) readout**, per R1. The published operators were scored
   unstripped, so R6's numbers are not comparable to pre-R1 figures and must not be placed beside
   them.

## COST

8 fits at 410M, N=200. `./lab cost 410m 200 L40S` ~ 0.17 GPU-h ~ $0.14 each, so **~$1.20 plus the
read** — call it **under $5**. Requires a rented GPU box: a 410M fit at N=200 is hours on this
laptop's CPU, so 8 of them is not a local job. **Needs the operator's sign-off before any spend.**

## RESULT

*(unrun — awaiting budget sign-off)*

## VERDICT

*(pending)*
