# R4b — re-score E36: S3's READ-axis rejection is a logit-lens comparison and is now unverified

**PRE-REGISTERED 2026-08-19, before `--rstrip` was added to `t36_qladder.py` and before any run.**
Source: [`../POSTREVIEW_EXPERIMENTS.md`](../POSTREVIEW_EXPERIMENTS.md) §3 Tier B, item R4b.
Amends [`E36_qladder.md`](E36_qladder.md).

---

## QUESTION

`paper/CONTEXT.md` §3.1 records S3's first half as REJECTED on the read axis: the fitted operator is
*flatter* across the shift axis than the unfitted logit lens, **5 of 5**. That is a comparison
**against the logit lens**, produced by `t36_qladder.py`, which does not strip and has never been
re-scored — and the logit lens is the single quantity the readout defect moved most. Its constant
goes 0.02844 to 0.08318, a 2.9x change, while the fitted operators move 2.2-2.7x. **A comparison
between two quantities that move by different factors can reverse.** Until this re-runs, S3's
headline rejection is unverified.

E36 is separately implicated twice, and all three are fixed in one pass:

* `t36_qladder.py:217` builds its `shuf` arm from **Pile-CC's** operator, not from each corpus's
  own, so "a derangement beats Github's operator" is not the like-for-like comparison the prose
  describes;
* its control `C2_shuf_below_everything` records `fires: false` — **a failed pre-registered control
  that is discussed nowhere.**

## DESIGN

Add `--rstrip` to `t36_qladder.py:196` exactly as `t48_crossover.py:234` does it. Re-run the
Q-ladder over the same operators, same band, same rungs. Rebuild `JSHUF` **from each corpus's own
operator** rather than Pile-CC's. Output `results/e36_qladder_410m_rstrip.json`; the stored
unstripped file is not overwritten.

## PRIMARY

The number of read rungs on which the fitted operator is flatter than the logit lens, stripped
versus unstripped. Published: **5 of 5**.

## DECISION RULE — fixed before running, quoted verbatim

Quoted from `specs/POSTREVIEW_EXPERIMENTS.md` §3, item R4b (Tier B):

> * **REJECT STANDS:** the fitted operator is flatter on >= 4 of 5 rungs. §3.1 is unchanged.
> * **REJECT OVERTURNED:** flatter on <= 1 of 5. **STOP and alert.** S3's first half is no longer
>   rejected on the read axis, which reopens the subthesis and changes the paper's framing.
> * **UNCLEAR:** 2 or 3 of 5. Report and stop. Do not re-cut.

## CONTROLS — each with the number it must produce

* **C1 — recovery of the published run.** Running without `--rstrip` and with the original
  Pile-CC-sourced `shuf` must reproduce the stored E36 arms **bit-exactly**. *Required:*
  `max_abs_diff = 0.0`.
* **C2 — the corrected `shuf` arm must lose to its own operator.** Built from each corpus's own
  operator, the derangement must sit **below** that corpus's real operator under `persist`, as the
  like-for-like evidence already on disk does: `e33_logit_baseline_410m_v2` gives Github 0.027926
  against its own `jshuf` 0.018142, and `e54`'s C2 fires at 0 of 15 and 0 of 120.
  *Required:* 0 corpora below their own derangement floor.
* **C3 — report `C2_shuf_below_everything` whichever way it fires.** A recorder, not a gate; its
  power is nil by construction and that is stated here rather than discovered later.

## DECLARED BIAS

Scoring-side only; the operators are unchanged. The fitting corpus for each operator is still the
unstripped pool, as in R1.

## COST

$0, CPU, hours.

## RESULT

*(unrun at time of writing)*

## VERDICT

*(pending)*
