# R1 — re-score the 8x8 fit x read grid at the correct readout token

**PRE-REGISTERED 2026-08-19, before the `--rstrip` flag was added to `t52_factorial.py` and before
any run.** Source: [`../POSTREVIEW_EXPERIMENTS.md`](../POSTREVIEW_EXPERIMENTS.md) §3 Tier A, item
R1. Supersedes nothing; it corrects [`E52_factorial.md`](E52_factorial.md) and
[`E57_grid_variance_ci.md`](E57_grid_variance_ci.md) on the scoring side only.

---

## QUESTION

The paper's headline is a variance decomposition of an 8x8 `fit corpus x read rung` grid:
**fit 91.2% / read 7.1%**. Every cell in that grid was read at a token that **does not occur in the
sequence the anchor's rule refers to**. Does the headline survive the correction?

## WHY IT IS A CORRECTION AND NOT A SENSITIVITY ARM

`jacobian-lens/data/evaluations/README.md` (vendored at `581d398`) specifies, for multihop,
multilingual and order-ops, that readout is at *"the token immediately preceding `target`"*. The
released prompts end in a trailing space. GPT-NeoX BPE absorbs that space into the target's leading
space, so it never survives as a token:

```
prompt tail  ' famously celebrated is the '        target 'Brazil'
  tokens of prompt+target, last 4   ' celebrated'  ' is'  ' the'  ' Brazil'
  stripped   readout token          ' the'   (id 253)   <- "the token immediately preceding target"
  unstripped readout token          ' '      (id 209)   <- DOES NOT OCCUR in prompt+target at all
```

`src/anchor_evals.py:32-34` already says so in the repository's own words — *"`.rstrip()` IS
LOAD-BEARING ... an un-stripped trailing space becomes the readout token and destroys the
baseline"* — and `:228` applies it. `experiments/t52_factorial.py:192` does not. The trap is that
`readout_position(tok, name, prompt)` **ignores `prompt` entirely** for the five "last" sets and
returns `-1`, so it looks as though it handles the prompt and does not; the caller must strip
before tokenising.

Scope: **157 of 551 released items = 157 of the 449 admitted-set items = 35%**, being 55/55
order-ops, 83/93 multihop, 19/107 multilingual, 0 on poetry/typo/association.

**Therefore the stripped arm is the estimate and the unstripped arm is legacy.** There is no branch
of this experiment in which the paper keeps printing a number computed at a token that does not
exist in the sequence its own rule refers to.

## RECORDED PREDICTION — logged before the run so that being wrong about it is visible

The grid is the **least** exposed of the readout-dependent quantities, for a structural reason: it
decomposes cell means in which the five eval sets are **averaged inside every cell**, so the
order-ops explosion (29.8x) never enters the `fit x read` factorisation the way it entered the
ladder's `corpus x set` one; and the recovery is ~90% uniform across corpora while a variance
decomposition is translation-invariant. **Prediction: 91/7 moves little; ACCEPT or QUALIFIED, not
REJECT.**

## DESIGN

`experiments/t52_factorial.py` gains `--rstrip`, implemented exactly as `t48_crossover.py:234`
implements it — `p = it["prompt"].rstrip() if a.rstrip else it["prompt"]`, with
`readout_position(tok, name, p)` then called on the same `p`.

Everything else is held: the same 24 matched-provenance operators
(`results/e48/lens_{INSTREAM_,OOD_}*_410m_n200_s{0,1,2}.pt`, all on local disk), band [9,21],
`K = [1,2,5,10,20,50,100]`, five admitted sets, 10 read rungs, 3 prefix seeds,
`--n-boot 4000 --n-perm 2000`, `--device cpu`. `t57_grid_variance_ci.py` then re-runs on the new
cells.

Outputs `results/e52_factorial_410m_rstrip.json`, `results/e57_factorial_cells_410m_rstrip.json`
and `results/e57_grid_variance_ci_rstrip.json`. **The unstripped files are not overwritten.**

## PRIMARY

`fit_pct` and `read_pct` under `persist` from E57, stripped versus unstripped.
Published (unstripped): fit **91.220%** [87.609, 92.171], read **7.133%** [6.311, 9.752].

## DECISION RULE — fixed before running, quoted verbatim

Quoted from `specs/POSTREVIEW_EXPERIMENTS.md` §3, item R1:

> * **ACCEPT (headline robust):** stripped `fit_pct` exceeds stripped `read_pct` under **both**
>   aggregations, and stripped `fit_pct` lies inside the published bootstrap interval [87.609, 92.171]
>   under `persist`. The headline survives with its magnitude. The unstripped arm is reported once, in
>   the deviations table, as a corrected defect.
> * **QUALIFIED (ordering survives, magnitude does not):** stripped `fit_pct` still exceeds
>   `read_pct` under both aggregations but falls outside the published interval. **The paper's
>   ordering claim stands and its magnitude claim is restated at the corrected value.** The abstract,
>   Table `tab:split`, Figure 1 and the Conclusion all move to the stripped numbers. This is the
>   branch the bracket above makes most likely, and it is a rewrite, not a retraction.
> * **REJECT (ordering does not survive):** stripped `fit_pct` does not exceed `read_pct` under both
>   aggregations. **STOP. Alert the operator.** Under `CLAUDE.md` §2.9 nothing is re-thresholded; the
>   paper's central claim is false as stated and the submission is re-planned around the metric audit
>   and the scale floor (`POSTREVIEW_PAPER.md` §2, Plan C).

**This rule is not to be reinterpreted, and none of the three branches may be softened.**

## CONTROLS — each with the number it must produce

* **C1 — recovery of the published run.** The new code run **without** `--rstrip` must reproduce
  `results/e52_factorial_410m.json` to `max_abs_diff = 0.0` across all 128 stored cell values.
  *Required:* exactly 0.0. If it does not fire at exactly 0.0 the flag has changed something it
  should not have and the arm is void. (Shared with P0/C1.)
* **C2 — the convention actually bites.** The count of items whose readout token changes must be
  **157 of 551**, distributed 83/93 multihop, 19/107 multilingual, 55/55 order-ops, 0 on
  poetry/typo/association. *Required:* exactly those six counts, asserted inside the run and stored.
  If it is not 157 the two arms are not the two arms.
* **C3 — the logit-lens constant moves.** The identity-transport arm must differ between the two
  conventions. *Required:* under the unstripped path it is **0.0284395** (E33/E36 agree to 2.6e-10)
  on the `Q0` rung under `persist`; the stripped identity arm must differ from it. A stripped
  identity arm equal to the unstripped one means the flag did not reach the scoring path.
* **C4 — derangement floor holds.** The `shuf` arm must remain below every non-degenerate operator
  under `persist` in the stripped arm, as it does unstripped. *Required:* `C2_shuf_floor_excl_degenerate`
  fires, i.e. an empty `below_floor` list on every rung.

## DECLARED BIAS

1. The 24 operators were **fitted** on unstripped prompts (`trainval.py:253`) and R1 changes only
   the **scoring** readout. A fully anchor-faithful arm would refit. That is deliberate and it is
   the cheap half: it isolates the readout convention from the fitting convention. The fitting-side
   question is out of scope here and is recorded as open.
2. The operators are E48's matched-provenance refits, not the E28 ladder fits. That is already true
   of the published E52 and is why the two families' numbers are not interchangeable.

## COST

$0, CPU only. Runs after P0. Serial ~19 h; pooled, on the wallclock actually measured on this
machine at gate time (recorded in the results file), single-digit hours. Per `CLAUDE.md` §6.6 one
cell is timed before the full 30 are committed; if the observed per-pass cost exceeds ~2x the
slate's 86 s/pass calibration, stop and report rather than starting a two-day job.

## WHAT RE-DERIVES FROM THE NEW MATRIX, IN THE SAME PASS

Table `tab:split` (body), `tab:loo` and the 28 leave-two-out splits (`e54.matrix_loo`, `e55`), the
66/31 four-corpus restriction, Figure 1 (`fig0_grid_single`), the grid tables `tab:grid-persist` /
`tab:grid-min`, and E52's diagonal excess `D`. Mixing conventions across these is the failure mode.

## RESULT

*(unrun at time of writing)*

## VERDICT

*(pending)*
