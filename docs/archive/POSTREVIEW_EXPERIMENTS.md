# POSTREVIEW — THE EXPERIMENT SLATE

**Written 2026-08-19.** Derived from `review/`, which holds two independent external reviews of
this programme. One of three post-review specs; the others are
[`POSTREVIEW_PAPER.md`](POSTREVIEW_PAPER.md) and [`POSTREVIEW_RELEASE.md`](POSTREVIEW_RELEASE.md).

**Deadline: 28 August 2026 AoE. Nine days.** Every item below is priced against that.

---

## -1. IF YOU ARE THE AGENT EXECUTING THIS SPEC, READ THIS SECTION FIRST

This spec is self-contained. You do not need the conversation that produced it.

**The programme has one defect that governs everything else, and it is not a wrong number. It is a
wrong readout position.** Sections 2a and 2b tell you exactly what it is, what it costs, and which
results it reaches. Read them before touching anything.

**Ground truth is mechanical and already computed.** Run:

```bash
.venv/bin/python tools/readout_exposure.py
```

It walks every results file, resolves its producing script, checks whether that script strips the
eval prompt, and propagates exposure through `provenance.inputs` to a fixpoint. Output is also
stored at `tmp/readout_exposure.txt` and `tmp/readout_exposure.json`. **Do not re-derive this by
hand and do not ask an agent to classify claims by reading them — the tool is exhaustive,
deterministic, and cannot hallucinate.** Its headline:

> **13 of the 17 results files `paper_5pp.tex` cites need a re-score. 3 are readout-safe.**

Two file-level classifications are coarser than the truth and the tool says so: `e38_jgeometry` and
`e58_algebra_audit` are EXPOSED as files, but the fields the paper cites from them are readout-free.

**One item is not yours: R0**, the retraction of the corpus-axis crossover, is operator-only.
Report it as outstanding; do not edit the canonical documents it names.

**The three rules that bind you** (`CLAUDE.md` §2.9, §6.2, §6.11): never reinterpret a
pre-registered decision rule; never report a number that is not in a results file; verify every
finding numerically before acting on it. If a rule fires REJECT or UNCLEAR, stop and report. Do not
adjust the experiment to make it fire differently.

---

## 0. VERDICT FIRST

**Mixed for the programme, and the mix is unusually clean.** The reproducibility review reproduced
essentially every number it checked, by re-implementing the estimands rather than tracing them, and
it found the repository's most transferable result — the metric audit — **robust to the one
convention that moves everything else**. That is a strong outcome and it should be said before the
bad news.

The bad news is one thing, and it is not a wrong number. **The readout position is wrong on 35% of
the admitted eval items**, in about twenty scripts, and it was declared nowhere. §2a gives the
mechanism; §2b gives the measured cost; `tools/readout_exposure.py` gives the exhaustive ledger.
**13 of the 17 results files the paper cites need a re-score.**

The damage is real but it is **concentrated and directional**, and two things make it survivable:

* **The operators are fine.** Fitting never touches eval prompts, so every fix is a free CPU
  re-score. No refit, no GPU.
* **The corpus effect largely survives and the interaction gets stronger.** Absolutely, the corpus
  effect fell 13%, the ordering is 4/5 unchanged, and the corpus x eval-set interaction is **37%
  larger**. What collapsed is a *share*, because the denominator grew 4.9x.

What actually dies is **§3.4, the corpus-axis crossover** — the one S3 claim `CONTEXT.md` said
survived. Under the correct readout all five corpora beat the logit lens. Retract it first (R0).

S1 is untouched, S2 survives, S3 is a reshuffle. §2c has the per-subthesis account.

---

## 1. CALIBRATION — read this before reacting to the reviews

Four alphaXiv reviews are in `review/ALPHAXIV_REVIEW.md`. Their verdicts are **not four independent
votes**, and treating them as such would badly mis-set the agenda.

| review | prompt | verdict | novelty |
|---|---|---|---|
| Incredibly Brutal | *"UNBELIEVABLY BRUTAL AND COLD, aggressive and adversarial reviewer"* | Reject (conf 82) | 68 |
| Intermediate | *"aggressive and adversarial reviewer"* | Reject (conf 82) | 76 |
| **No Steering** | *"score the paper's novelty and give an accept/reject verdict"* | **Accept** | **84** |
| Related Work | citation coverage only | 63/100 coverage | — |

**The two rejects were commissioned to reject.** The one review that was not steered accepts, at
novelty 84 and confidence 87. The correct inference is not "three reviewers rejected"; it is "under
maximal adversarial pressure the paper's substantive criticisms are X, and an unsteered reader finds
the contribution sufficient". Both facts matter. Act on the substantive criticisms; do not rewrite
the paper as though its reception were three-to-one against.

Three further observations that shape what is worth running:

1. **Several "required experiments" are already in the paper.** The Brutal review demands
   leave-one-out sensitivity and a Github-dropped column; `paper_5pp.tex` Table `tab:split` prints
   exactly that, and the review then cites those very numbers against the paper. It demands the
   dose asymmetry be addressed; §Analysis sweeps it. It demands the limitations be moved forward;
   they are a numbered section with the fixed task battery as item 1. **The gap here is
   presentation, not measurement** — see `POSTREVIEW_PAPER.md`.
2. **Both adversarial reviews make reproducibility their largest single deduction (30/100), and
   both say the reason is that no repository was provided.** That is not an experiment. It is
   `POSTREVIEW_RELEASE.md`, and it is the highest-value work in the whole post-review programme
   per unit of effort.
3. **The two reviews' strongest shared technical point is real and cheap to answer badly, expensive
   to answer well:** the variance shares are a *panel-specific descriptive decomposition* over eight
   deliberately-chosen corpora, not a population estimate, and the bootstrap resamples seeds rather
   than corpora. The honest fix is wording plus a corpus-axis uncertainty statement, both of which
   the repository already has the data for (leave-one-out and leave-two-out).

---

## 2. WHAT WAS VERIFIED BEFORE THIS SLATE WAS WRITTEN

`CLAUDE.md` §6.11: *"Verify every agent/reviewer finding numerically before acting. In this
programme two accepted findings were wrong and one dismissed finding was right."*

Every finding this slate acts on was recomputed locally first. The record, with commands, is
[`tmp/INDEPENDENT_VERIFICATION_2026-08-19.md`](../tmp/INDEPENDENT_VERIFICATION_2026-08-19.md).
Headlines:

* **Confirmed exactly:** the 157/551 readout divergence (and resolved per set: multihop 83/93,
  order-ops **55/55**, multilingual 19/107, the other three sets 0); `rstrip` absent from every spec
  document while `RESULTS_TAXONOMY.md:263` asserts the readout position matches the anchor; the F-5
  four-arm interval table; the F-8 containment column mix; the M-2 integer-key hash defect
  (re-keying to int reproduces the stored hash exactly); 166/166 E28 sidecars carrying
  `"corpus": "wikitext"` and `anchor_agreement_gate: null`; 0 of 166 E28 operators named in
  `ARTIFACTS.md`.
* **Escalated:** the unstripped readout is not a convention, it is a **bug**. The token it reads
  (id 209, a bare space) **does not occur** in the tokenisation of prompt+target, while the stripped
  one is exactly "the token immediately preceding `target`" as the anchor's data README specifies.
  Verified directly on multihop items. This removes the "two defensible conventions" reading and is
  why R1 is a correction, not a sensitivity arm.
* **Corrected:** F-1/F-2's *numbers* do **not** touch the paper's headline, because the paper's 91/7
  is E57's fit x read grid decomposition and the reviewer re-scored E51's ladder corpus x eval-set
  decomposition. Two different designs; both round to 91%;
  `e54.matrix_structure.persist.note_on_interaction` states the distinction verbatim, and E51's
  numbers appear nowhere in `paper_5pp.tex`. **But F-1 lands on the paper anyway**, through the
  ladder-derived numbers the paper does print: `tab:asym`'s whole "vs logit" column and
  `paper_5pp.tex:266-269`, where Github moves from -1.2% to **+21.1%** and "the only one at or below
  the free baseline" becomes false, 0 of 5 rather than 1 of 5.
* **Corrected:** S-5 is refuted. `results/m1/merged/*.npz` are the primary stored inputs to the
  entire containment analysis (`t48b_exposure_growth.py:75`), not debris.
* **Corrected:** M-22b is refuted. "~25%" appears in **two** live places: `CONTEXT.md:226` and
  `docs/context/RESULTS_TAXONOMY.md:66`, the canonical claims ledger.
* **Corrected:** M-16's "mislabelled" is too strong. `PREREG_E52_FACTORIAL.md:69` defines `D`
  exactly as implemented, and the permutation p is computed on `D` itself so the 8/7 factor cancels.
* **Corrected:** F-5's one-sentence framing is wrong at 160M, where **neither** aggregation beats the
  logit lens. The eight intervals themselves all reproduce exactly.
* **Corrected:** M-6 overstates. The paper's two figures *are* regenerated, by `paper/build.sh`,
  not by the `make_figures.py` `main()` that `REPRODUCIBILITY.md` documents.
* **Test suite 6/6 green** before this slate was written.

---

## 2a. THE DEFECT, COMPLETELY

**What the anchor specifies.** `jacobian-lens/data/evaluations/README.md`, for multihop,
multilingual and order-ops: *"`target` defines the readout position only and is not itself scored.
Readout is at a single position, **the token immediately preceding `target`**, across all layers."*

**What the data looks like.** `prompt` is the text before the target and carries a trailing space so
that `prompt + target` concatenates:

```
prompt  "...the country where Carnival is most famously celebrated is the "
target  "Brazil"
```

**Why the trailing space is a trap.** GPT-NeoX BPE encodes words with their leading space. In the
joined text the trailing space is absorbed into `' Brazil'` and never survives as a token:

```
tokens of prompt+target, last four :   ' celebrated'   ' is'   ' the'   ' Brazil'
stripped   readout token           :   ' the'   (id 253)   == the anchor's rule
unstripped readout token           :   ' '      (id 209)   <- occurs nowhere in that sequence
```

**This is not a defensible alternative convention. The unstripped path reads a token that does not
exist in the sequence the rule refers to.** Treat every corrected number as *the* number and every
unstripped number as legacy.

**Whose bug.** Ours. The released library ships **no evaluation code at all** (`jlens/` is lens,
fitting, hooks, hf, protocol, vis, examples; grep for `pass_at_k|readout_position` returns nothing),
so there is no upstream implementation to have inherited this from. Our own
`src/anchor_evals.py:65` states the rule (`"last" == final prompt token after rstrip`) and `:228`
applies it. The trap is that `readout_position(tok, name, prompt)` **ignores `prompt` entirely for
the five "last" sets and returns `-1`** — so it looks like it handles the prompt and does not. The
caller must strip before tokenizing.

**Scope.** 157 of 551 released items; 157 of the 449 items in the five admitted sets, i.e. **35%**.

## 2b. WHAT IT COSTS, MEASURED

From the 15 re-scored 410M ladder cells (`persist`, N >= 75, admitted-5). **The three unaffected
sets are bit-identical, which is the internal control proving the re-score is the same computation
and the readout token is the only difference.**

| eval set | items affected | unstripped | corrected | ratio |
|---|---|---|---|---|
| **order-ops** | 55/55 | 0.01098 | 0.32686 | **29.8x** |
| **multihop** | 83/93 | 0.01412 | 0.04420 | **3.13x** |
| multilingual | 19/107 | 0.03393 | 0.03439 | 1.01x |
| poetry | 0/98 | 0.00304 | 0.00304 | **1.00x** |
| typo | 0/96 | 0.14097 | 0.14097 | **1.00x** |
| association | 0/102 | 0.00005 | 0.00005 | **1.00x** |
| admitted-5 mean | | 0.04061 | 0.10989 | 2.71x |

**order-ops was being read at 1/30th of its true value.**

### 2b.1 The recovery is ~90% uniform across corpora, and that governs the variance results

| corpus | gain from the fix |
|---|---|
| Github | +0.0726 |
| StackExchange | +0.0708 |
| USPTO | +0.0701 |
| Wikipedia | +0.0660 |
| Pile-CC | +0.0655 |

Range 0.0071 on a mean gain of 0.0690 — **10.3% non-uniform**. Variance decompositions are
**translation-invariant**, so a uniform shift changes nothing. Consequences, all measured:

| quantity | unstripped | corrected | |
|---|---|---|---|
| between-corpus spread (absolute) | 0.02165 | 0.01917 | **-11.5% only** |
| corpus ordering | USPTO > Pile-CC > StackEx > Wiki > Github | USPTO > StackEx > Pile-CC > Wiki > Github | **4 of 5 unchanged**; the swap was a tie (0.04572 vs 0.04568) |
| spread / seed SD | 71.5x | 52.8x | still decisive |
| best/worst ratio | 1.77x | 1.19x | **genuinely smaller** |

### 2b.2 The ladder ANOVA in ABSOLUTE terms, which is the number that matters

Shares move when the denominator moves. This decomposition reproduces the stored shares to three
decimals (1.903 / 91.324 / 6.773 against the stored 1.906 / 91.278 / 6.781), so it is the same
estimand:

| | unstripped | corrected | |
|---|---|---|---|
| SS_corpus | 1.455e-03 | 1.272e-03 | **0.87x** |
| SS_set | 6.980e-02 | 3.429e-01 | **4.91x** |
| **SS_interaction** | 5.176e-03 | **7.091e-03** | **1.37x, it GREW** |
| interaction / corpus main | 3.56 | **5.58** | stronger |

> **"The corpus main effect fell 5.3x" is a share statement and it is misleading. Absolutely it fell
> 13%. The corpus x eval-set interaction — the programme's most novel result — is 37% LARGER under
> the correct readout.** Do not restate the share collapse as a loss of effect anywhere.

**The operators are unaffected.** Fitting draws its pool from `corpora/*.jsonl`
(`experiments/trainval.py:241-244`), never from eval prompts. **Every correction on this slate is a
free CPU re-score. No refit, no GPU, no re-fetch.**

## 2c. WHAT THIS DOES TO S1, S2 AND S3

| | status | why |
|---|---|---|
| **S1 — small models** | **untouched** | the cited numbers are `E39/*/mean_cos_I` and `eff_rank_I`, computed from `W_U` alone; the 160M consequence interval comes from `t22_bootstrap_ci.py:84`, which strips; the P-ladder R comes from `t23_pq_ladder.py:93`, which strips |
| **S2 — the N ladder** | **survives, measured** | re-derived under both conventions across the 16-rung grid: range over N is 1.5-5.8 seed SD unstripped, 1.9-7.1 corrected. "Reads are flat in N" holds either way. §2.4's sampling law is an operator-norm quantity, immune |
| **S3 §3.4 the crossover** | **DEAD** | Github 0.02808 vs logit 0.02844 becomes **0.10069 vs 0.08318, +21.1%**. All five corpora beat the logit lens. The one S3 claim `CONTEXT.md` said survived is gone. **Retract it before anything else** |
| **S3 §3.9 the interaction** | **STRONGER** | see 2b.2 |
| **S3 §3.1 the READ-axis REJECT** | **now unverified** | E36's "the fitted operator is flatter across shift than the unfitted one, 5/5" is a logit-lens comparison from `t36_qladder.py` (no strip, never re-scored), and the logit lens is what moved most. R5 re-runs it |
| **S3 §3.5 the 91/7 grid** | **unmeasured, least exposed** | the grid averages eval sets *inside* each cell, so the order-ops explosion never enters the fit x read decomposition, and a ~90%-uniform shift is translation-invariant. R1 settles it |
| **S3 §3.3 twenty failed predictors** | exposed, but a null | can only move toward a discovery |

---

## 2d. WALLCLOCK FOR THE 13 OF 17 — costed from a measured baseline

**Calibration, measured not guessed.** The 15 re-scored ladder cells record their own runtimes:
**17,561 s serial across ~205 score passes = ~86 s per score pass** on a laptop, where one pass is
541 items x 13 layers unembedded against a 50,304 vocabulary. Every estimate below is that
constant times a pass count read off the stored config.

| what | passes | serial | note |
|---|---:|---:|---|
| **R1 — E52 grid + E57 cells** | 30 caches + 30 x 26 arms = **780** | **~19 h** | plus ~1.8 h of activation caching (30 distinct prefixes). The single biggest item |
| **R4b — E36 qladder** | 13 rungs x ~7 arms = **~91** | ~2.2 h | |
| **R2 — E48 crossover rstrip arm** | comparable to one ladder pass set | ~1-2 h | already scripted behind `RUN_RSTRIP_ARM=1` |
| **R3 — ladder410 CPU re-score** | 15 cells | ~1 h | `PAPER_HANDOFF.md` §3.1's own estimate; parallel already |
| E59 read-dose | 3 dose rungs | <1 h | |
| E61 randomised null | 10 cells | ~1 h | |
| D1 min-union | recompute off E48's arms | minutes | reproduces the stored arms bit-exactly |
| **The seven pure recomputes** (E51, E53, E54, E55, E56, E57 stats, E48c) | none | **seconds to minutes each** | they read JSON, they do not score |

**Serial total: roughly 25-30 h. Call it a day and a half of laptop.**

### The single change that makes this an overnight job

**`experiments/t52_factorial.py` is serial** (a plain `for rung: for ps:` double loop, no pool),
while `experiments/e28_ladder_410m.py:175` already does exactly the right thing:

```python
with mp.Pool(a.workers) as pool:
    for corpus, seed, nN, msg in pool.imap_unordered(cell, cells):
```

The grid's 30 (rung, prefix-seed) cells are embarrassingly parallel — each has its own activation
cache and shares only the read-only operators. **Porting that pool into `t52` is about fifteen lines
copied from a script in this repository**, and it takes R1 from ~19 h to **~2.5-3 h** on eight
workers. Do that before running R1, not after.

**With the pool ported: the whole 13-of-17 re-score is ~4-6 h wallclock. One overnight run.**

### Should it go on a GPU instead?

The arithmetic says yes and the discipline says no. 562 TFLOP at even 10% of an L40S's 91.6 TFLOPS
fp32 is ~10 minutes, so **under $1**. But `results/d2_device_crossvalidation.json` fired **DIVERGENT**
on the CUDA-vs-CPU comparison, and the paper's scoring is CPU throughout. Moving the corrected
headline onto a device whose agreement is an open question, in the same pass that corrects a
different measurement defect, is how two problems become one confounded problem.

**Recommendation: port the pool, run on CPU overnight.** If a GPU is used anyway, the D2 protocol
applies: cross-validate at least one cell on CPU and store the comparison.

### Before committing to any of this

`CLAUDE.md` §6.6, tiny-first. The 86 s/pass constant is from the reviewer's machine, not
necessarily this one. **Smoke one cell, measure it, and re-derive the table above from the observed
constant** before starting a multi-hour run. If the observed per-pass cost is more than ~2x the
calibration, stop and report rather than starting a two-day job.

---

## 3. THE SLATE

Ordered by *decisiveness per dollar*. Every entry carries the seven fields `CLAUDE.md` §3 mandates.
**Nothing here may run before its `docs/experiments/preregs/` document exists and is committed** — the
pre-registration must carry a git timestamp strictly earlier than the result (§C-1 of the review
found 25 of 45 registration claims are in-file docstrings that carry no independent timestamp; do
not add a 26th).

### Tier A — free, CPU, and one of them decides how much of the paper stands

---

#### R0. Retract the corpus-axis crossover — **OPERATOR ONLY. DO NOT EXECUTE.**

> **If you are an agent, this item is not yours.** Read it so you know what is blocked, then stop.
> Do not edit `paper/CONTEXT.md`, `docs/context/RESULTS_TAXONOMY.md`, `docs/archive/HANDOFF.md`,
> `docs/archive/DISTRIBUTION_RESULTS.md` or `repro/lib/banned_claims.py` under this item. A retraction
> rewrites the canonical record of what the programme believes, and that judgement stays with the
> operator. Report that R0 is outstanding and move to R1, which is unblocked by it in practice even
> though §4's gate lists it first.

**WHY.** `CLAUDE.md` §2.5: *"After every result, ask: what did this just invalidate? Then go check
those claims."* §3.4 of `paper/CONTEXT.md` is titled *"WHAT S3 GOT RIGHT — the crossover exists, on
the corpus-identity axis"* and rests on Github reading 0.02808 against a logit constant of 0.02844,
i.e. indistinguishable from not fitting at all. Under the correct readout Github reads **0.10069**
against a logit constant of **0.08318**, or **+21.1%**, and **all five corpora beat the logit lens**.
There is no crossover.

This is not an experiment. It is a retraction, and under §2.5 it blocks everything downstream: no
new claim may be written while a falsified one is still standing in the canonical documents.

**WHAT TO DO.**
1. Add a Tier D entry to `docs/context/RESULTS_TAXONOMY.md` naming the retraction, the corrected numbers,
   and the readout defect as the cause.
2. Rewrite `paper/CONTEXT.md` §3.4 in place, keeping the retraction where the claim was, per the
   repository's existing practice (all six prior retractions sit inline).
3. Check every document that restates it. At minimum: `docs/archive/HANDOFF.md`,
   `docs/archive/DISTRIBUTION_RESULTS.md`, `docs/context/RESULTS_TAXONOMY.md`. Grep for `0.02808`, `0.02844`,
   `crossover`, and `at or below`.
4. `paper/paper_5pp.tex:298-300` prints *"the only one at or below the free baseline"*. That clause
   is now false and comes out. See `POSTREVIEW_PAPER.md` §3.0.

**DECISION RULE.** None. A retraction has no branches.

**CONTROLS.** `./lab health` H11 enforces one banned claim already; add the crossover to
`repro/lib/banned_claims.py` so it cannot reappear, and confirm H11 fails when it does.

**COST.** $0, under an hour of operator time.

**WHY OPERATOR-ONLY.** Three reasons, in descending weight. (1) A retraction is a statement about
what the programme now believes, and `CLAUDE.md` §2.5 makes retracting a *precondition* for
continuing — delegating it delegates the belief. (2) It edits the four documents that are canonical
for state, and a wrong edit there propagates silently into everything downstream. (3) The prior
retractions in this repository were all written by the operator and sit inline in a house style that
an agent will not reproduce. **The measurement behind it is settled** (§2c): Github 0.10069 against
a logit constant of 0.08318, all five corpora above the baseline. Only the writing is reserved.

---

#### P0. Port the process pool into `t52_factorial.py` — prerequisite for R1

**WHY.** R1 is ~19 h serial and ~2.5-3 h on eight workers (§2d). `experiments/t52_factorial.py`
scores its 30 (read-rung, prefix-seed) cells in a plain nested loop with no pool, while
`experiments/e28_ladder_410m.py:175` in the same repository already runs the identical shape of work
through `mp.Pool(...).imap_unordered`. The cells are embarrassingly parallel: each builds its own
activation cache and the operators are read-only and shared. **This is not an optimisation, it is
the difference between an overnight run and a two-day one**, and it is fifteen lines copied from a
sibling script.

**DESIGN.** Mirror `e28_ladder_410m.py`:
* add `--workers` (default `min(8, os.cpu_count())`, matching the ladder);
* hoist the per-cell body into a module-level `cell((rung, prefix_seed))` function so it pickles;
* keep the operators loaded once in the parent and let fork share them copy-on-write; do **not**
  re-`torch.load` per worker, which would multiply memory by `workers`;
* `torch.set_num_threads(1)` inside each worker. Without it, eight workers each spawn eight BLAS
  threads and the run gets *slower*, and `CLAUDE.md` §8b records that fits are not bit-reproducible
  above 8 CPU threads, so thread count is not a free parameter here;
* collect with `imap_unordered` and assemble `CELL` by key, not by arrival order.

**PRIMARY.** Wallclock for the full 30-cell grid, pooled vs serial.

**DECISION RULE — and it is a gate, not a target.**
* **ACCEPT:** the pooled run reproduces the serial run's stored matrix at **`max_abs_diff = 0.0`
  across all 128 cell values**, and wallclock falls by at least 3x.
* **REJECT:** any non-zero difference. **STOP.** A parallelisation that changes a number is a bug,
  and shipping it would put a scheduling artifact inside the paper's headline. Do not "investigate
  the tolerance" — there is no tolerance. The same computation in a different order over the same
  fp32 inputs must give the same bits here, because nothing is reduced across cells.

**CONTROLS.**
* **C1 — bit-identity.** Run pooled **without** `--rstrip` and compare to
  `results/e52_factorial_410m.json`. Required: `max_abs_diff = 0.0` on all 128 stored cell values.
  This is the same self-test E57 already implements (`measurement_side_C1`, tolerance 1e-12,
  currently fires at 0.0), so the machinery exists.
* **C2 — worker-count invariance.** `--workers 1`, `--workers 2` and `--workers 8` must all give
  byte-identical output. If they do not, there is shared mutable state and the port is wrong.
* **C3 — no thread oversubscription.** Assert `torch.get_num_threads() == 1` inside a worker.

**DECLARED BIAS.** None: this changes scheduling only. That is exactly what C1 and C2 verify, and
it is why they are pass/fail rather than tolerance-based.

**COST.** $0. An hour to write, minutes to gate. **Do this before R1, not after.** Consider the same
port for `t36_qladder.py` (R4b, ~2.2 h serial) if it is also a plain loop.

---

#### R1. Re-score the 8x8 grid at the correct readout token

> **This is the experiment. If only one thing on this slate runs, it is this one.**

**WHY.** The readout position used by the ladder, the grid, and most of the programme **is not a
defensible alternative convention. It is a bug**, and that was established here rather than
assumed.

The anchor's data spec (`jacobian-lens/data/evaluations/README.md`, vendored at `581d398`) says the
readout position for multihop, multilingual and order-ops is *"the token immediately preceding
`target`"*. The released prompts end in a trailing space. Tokenised, that space is absorbed into the
target's leading space, so it never survives as a token of its own. Verified directly on three
multihop items:

```
prompt tail  ' famously celebrated is the '        target 'Brazil'
  tokens of prompt+target, last 4   ' celebrated'  ' is'  ' the'  ' Brazil'
  stripped   readout token          ' the'   (id 253)   <- "the token immediately preceding target"
  unstripped readout token          ' '      (id 209)   <- DOES NOT OCCUR in prompt+target at all
```

`src/anchor_evals.py:32-34` already says so in the repository's own words: *"`.rstrip()` IS
LOAD-BEARING ... an un-stripped trailing space becomes the readout token and **destroys the
baseline**."* `src/anchor_evals.py:228` applies it. `experiments/t52_factorial.py:192` does not, and
neither do `e28_ladder_410m.py:99`, `trainval.py:253`, `t33_logit_baseline.py:90`,
`t36_qladder.py:196`, `t59_read_dose.py:140` or `d1_min_union_diagnostic.py:96`.

**So R1 is not a sensitivity arm and must not be written as one.** It is the correction of a
readout defect on **157 of 551 items, which is 157 of the 449 admitted-set items, 35%** — including
**all 55 order-ops items** and **83 of 93 multihop items**. The stripped arm is the estimate; the
unstripped arm is the legacy.

**What is already known, and it is not reassuring.** The reviewer re-scored the 15 ladder cells and
those numbers are **printed in the paper**: under the anchor readout the logit-lens constant moves
0.02844 -> 0.08318 (`persist`) and Github moves **-1.2% -> +21.1%**. So `tab:asym`'s entire "vs
logit" column and `paper_5pp.tex:266-269` are wrong as printed, independently of R1 (see
`POSTREVIEW_PAPER.md` §3.0). What R1 settles is the *grid*, which nobody has re-scored.

**A grounded prediction, so the run is not a surprise.** The grid is the *least* exposed of the
readout-dependent quantities, for a structural reason: it decomposes cell means in which the eval
sets are **averaged inside every cell**, so the order-ops explosion (§2b) never enters the fit x read
factorisation the way it entered the ladder's corpus x set one. And the recovery is ~90% uniform
across corpora (§2b.1), while variance is translation-invariant. **My prediction is that 91/7 moves
little.** The measured analogue on the ladder is that the absolute corpus effect fell 13% while its
*share* fell 5.3x purely because the denominator grew; the grid has no comparable denominator
growth. ACCEPT and QUALIFIED are both far more likely than REJECT. Record this prediction before
running so that being wrong about it is visible.

**DESIGN.** `experiments/t52_factorial.py` gains a `--rstrip` flag, implemented exactly as
`t48_crossover.py:234` implements it: `p = it["prompt"].rstrip() if a.rstrip else it["prompt"]`,
with `readout_position(tok, name, p)` then called on the same `p`. Nothing else changes: same 24
operators (`results/e48/lens_{INSTREAM_,OOD_}*_410m_n200_s{0,1,2}.pt`, **all on local disk**), same
band [9,21], same `K=[1,2,5,10,20,50,100]`, same five admitted sets, same 10 read rungs, same 3
prefix seeds, same `--n-boot 4000 --n-perm 2000`, `--device cpu`. Then `t57_grid_variance_ci.py`
re-runs on the new cells. Output `results/e52_factorial_410m_rstrip.json` and
`results/e57_grid_variance_ci_rstrip.json`; the unstripped files are **not** overwritten.

**PRIMARY.** `fit_pct` and `read_pct` under `persist` from E57, stripped vs unstripped. Published:
fit 91.220% [87.609, 92.171], read 7.133% [6.311, 9.752].

**DECISION RULE — fixed before running.** Note the asymmetry: because the stripped readout is the
**correct** one, the stripped numbers become the paper's numbers under every branch. What the
branches decide is what the paper can *say*.

* **ACCEPT (headline robust):** stripped `fit_pct` exceeds stripped `read_pct` under **both**
  aggregations, and stripped `fit_pct` lies inside the published bootstrap interval [87.609, 92.171]
  under `persist`. The headline survives with its magnitude. The unstripped arm is reported once, in
  the deviations table, as a corrected defect.
* **QUALIFIED (ordering survives, magnitude does not):** stripped `fit_pct` still exceeds
  `read_pct` under both aggregations but falls outside the published interval. **The paper's
  ordering claim stands and its magnitude claim is restated at the corrected value.** The abstract,
  Table `tab:split`, Figure 1 and the Conclusion all move to the stripped numbers. This is the
  branch the bracket above makes most likely, and it is a rewrite, not a retraction.
* **REJECT (ordering does not survive):** stripped `fit_pct` does not exceed `read_pct` under both
  aggregations. **STOP. Alert the operator.** Under `CLAUDE.md` §2.9 nothing is re-thresholded; the
  paper's central claim is false as stated and the submission is re-planned around the metric audit
  and the scale floor (`POSTREVIEW_PAPER.md` §2, Plan C).

**In every branch, the published unstripped numbers stop being the paper's headline.** There is no
branch in which the paper keeps printing a number computed at a token that does not exist in the
sequence its own rule refers to.

**CONTROLS.** Each must produce the stated number to count as firing.
* **C1 — recovery of the published run.** Running the new code **without** `--rstrip` must reproduce
  `results/e52_factorial_410m.json` to `max_abs_diff = 0.0` across all 128 stored cell values (the
  8x8 grid under both aggregations). This is the
  same self-test E57 already implements (`measurement_side_C1`, tolerance 1e-12, currently fires at
  0.0). If it does not fire at exactly 0.0 the flag has changed something it should not have and the
  arm is void.
* **C2 — the convention actually bites.** The count of items whose readout token changes must be
  **157 of 551**, distributed 83/93 multihop, 19/107 multilingual, 55/55 order-ops, 0 on
  poetry/typo/association. Verified locally already; re-assert inside the run and store it. If it is
  not 157 the two arms are not the two arms.
* **C3 — the logit-lens constant moves.** The identity-transport arm must differ between the two
  conventions. Under the unstripped path it is 0.0284395 (E33/E36 agree to 2.6e-10). A stripped
  identity arm equal to the unstripped one means the flag did not reach the scoring path.
* **C4 — derangement floor holds.** The `shuf` arm must remain below every real operator under
  `persist` in the stripped arm, as it does unstripped. The review's own re-run found the metric
  audit convention-independent (0/50 both ways); this re-asserts it inside the factorial.

**DECLARED BIAS.** The 24 operators were **fitted** on unstripped prompts (`trainval.py:253`), and
R1 changes only the **scoring** readout. A fully anchor-faithful arm would refit. That is deliberate
and it is the cheap half: it isolates the readout convention from the fitting convention, and the
fitting-side question is R13. State this in the results file and in the paper.

Second bias: the operators are E48's matched-provenance refits, not the E28 ladder fits. That is
already true of the published E52 and is why the two families' numbers are not interchangeable.

**COST.** $0. CPU only. **Run P0 first** — serial this is ~19 h, pooled ~2.5-3 h. Smoke first
(`--smoke`) per §6.6, then time one cell before committing to 30. Expect single-digit hours; if the smoke projects more than 12 h, move it to an L40S at
roughly $0.55/h rather than tying up the laptop, and disclose the device with a CPU cross-check of
one cell (the D2 protocol).

**WHAT ELSE RE-DERIVES FOR FREE ONCE R1's MATRIX EXISTS.** All of these are pure recomputes off the
new 8x8 matrix and must be redone in the same pass, or the paper will mix conventions:
Table `tab:split` (body), `tab:loo` and the 28 leave-two-out splits (`e54.matrix_loo`, `e55`), the
66/31 four-corpus restriction (`e55.e36_5x5_independent.persist.E52_same_five_minus_github`),
Figure 1 (`fig0_grid_single`), the grid tables `tab:grid-persist` / `tab:grid-min`, and E52's
diagonal excess `D`.

---

#### R2. The declared-but-never-run `--rstrip` sensitivity arm on E48

**WHY.** `repro/exp/e48_crossover.sh:5-7` declares the unstripped path PRIMARY and `--rstrip` "the
disclosed sensitivity arm", and `results/e48_crossover_410m.json` contains the prose *"The stripped
path is run separately via `--rstrip`."* **It was not run.**
`results/e48_crossover_410m_rstrip.json` does not exist and the stored `rstrip_arm` is `false`
(F-3). A results file asserting an execution that never happened is the single most corrosive kind
of defect this repository can carry, because the whole provenance argument rests on results-file
prose being true.

**DESIGN.** Run it. `RUN_RSTRIP_ARM=1 bash repro/exp/e48_crossover.sh`, unchanged. It is already
implemented and already gated behind the flag.

**PRIMARY.** The derangement control under both conventions, and the per-corpus asymptotes against
the logit constant.

**DECISION RULE.** This is a **disclosure**, not a test: it has no accept/reject branch and must not
be given one. It runs, it is stored, and both arms are reported. The one thing it can do is
contradict C4 of R1, in which case R1's metric-audit control has failed and both stop.

**CONTROLS.** C0 (reproduces E33's numbers) fires on the unstripped arm only, by construction; that
is why the unstripped path is PRIMARY. Record that the stripped arm cannot fire C0 and why.

**DECLARED BIAS.** None beyond the fitting-side bias in R1.

**COST.** $0, CPU, hours. Already scripted.

**Also required, and non-negotiable:** the false sentence in
`results/e48_crossover_410m.json` must be corrected. Results files are append-only in this
repository's practice, so the correction is a new field in the *new* file plus a retraction line in
`RESULTS_TAXONOMY.md` §Tier D naming the defect. Do not silently edit the old file.

---

#### R3. Close D2 — re-score `ladder410` on CPU and re-derive

**WHY.** `paper/PAPER_HANDOFF.md` §3.1 records that D2 fired **DIVERGENT**
(max |CUDA − CPU| = 2.774e-4 against a 1e-6 tolerance) and that under the pre-registered rule
**ladder-derived numbers are not cleared for citation**. The paper cites three: the per-corpus
asymptotes against the logit lens, the flatness in N, and the 1B replication. The handoff offers
three ways to close it and recommends (b), re-scoring on CPU. `CLAUDE.md` §2.9 forbids the operator
of this spec from choosing (a) or (c) unsigned. **Choose (b): it is free and it converts a standing
caveat into a closed one.**

Note that a partial artifact already exists: `results/ladder410_cpu_rescore/` was produced on
2026-08-19 (`docs/validity/AUDIT_READINESS.md` §3) and the reproducibility review independently re-scored a
CUDA cell on CPU to max 3.6e-4 with code sharing nothing with this repo. R3 finishes the job for all
15 cells.

**DESIGN.** Re-score all 15 (corpus, seed) 410M ladder cells on CPU from the 83 stored operators,
same band, K grid and admitted sets. Re-derive E33's asymptotes, E51's decomposition and E53's
summary from the CPU cells. Store under `results/ladder410_cpu/`.

**PRIMARY.** Every ladder-derived number the paper cites, CPU vs CUDA.

**DECISION RULE — fixed before running.** CLEARED if every paper-cited ladder number moves by less
than one pooled seed SD (3.5e-3) **and** no reported ordering changes. Otherwise **STOP and alert**:
the CUDA ladder is not citable and the affected paper claims come out.

**CONTROLS.** C1 — the CPU re-score of the one cell already done must agree with the new run
bit-identically. C2 — `persist` cells must agree with CUDA to better than 3.4e-9 (D2's measured
`persist` agreement), which is the positive control that the re-score is the same computation.

**DECLARED BIAS.** Re-scoring does not test the *fits*, only the reads. The fits are
`TRACED-NOT-RERUN` and need a GPU (U-1).

**COST.** $0, CPU, roughly one hour per the handoff's own estimate.

---

#### R4. Corrections that are pure recomputation

Grouped because each is minutes of work, each closes a named finding, and none has a losing branch.
Each still gets a results file and a line in `RESULTS_TAXONOMY.md`; none may be reported from
memory (§6.2).

| id | what | finding | what to produce |
|---|---|---|---|
| **R4a** | Containment at the coverage the text claims | F-8 | Recompute the k=32 row at **20/20 shards** for every corpus. Confirmed values: post-cutoff Wikipedia **0.26958** (not 0.24), PubMed control **0.79273** (not 0.67); in-stream 0.918-0.934 and OOD 0.0001-0.0013 are already 20/20 and correct. Store a single table keyed by shard count so the two columns can never be mixed again. |
| **R4b** | The four-arm `t22` table | F-5 | One results file holding all four hierarchical intervals (410M/160M x `min`/`persist`, J-minus-logit and J-minus-shuffled). The pattern — the aggregation that beats the free baseline is the one that fails the derangement control, at both scales — is currently invisible because each file reports only itself. **This is unfavourable and it must be published.** |
| **R4c** | All four aggregation arms | F-5 second half | `best1L` and `mean` exist in every ladder cell and in `e51`/`e54`/`e55` and are never reported; the reported interaction share is the argmax of the four. Publish all four. |
| **R4d** | E36's `shuf` arm is Pile-CC's derangement | F-7 | `t36_qladder.py:217` builds `JSHUF` from Pile-CC, so "a derangement beats Github's operator" is not the like-for-like comparison the prose describes. Recompute with Github's own derangement. The like-for-like evidence already in the tree goes the other way decisively (`e33..._v2`: Github 0.027926 vs its own `jshuf` 0.018142; `e54` C2: 0 of 15 and 0 of 120). Also surface E36's `C2_shuf_below_everything`, `fires: false` — **a failed pre-registered control that is discussed nowhere.** |
| **R4e** | Control-power audit | JUSTIFIABILITY | 27 of 97 control fields could not have failed: 8 compare a quantity to itself, 6 are recorders with no gate, 4 are declared in a docstring and never coded, 9 are arithmetic identities. Produce the enumeration as a results file, mark each in place, and add the power question to the experiment-spec template. Include E47's bottom-k control, which was computed, stored, never gated, and **would have failed 3 of 5**. |
| **R4f** | `payload_sha256` integer keys | M-2 | One-line fix in `src/provenance.canonical_payload_sha` (coerce keys to `str` before hashing) plus a regression test. Verified locally: re-keying `e58_algebra_audit`'s payload to int reproduces the stored hash exactly, so the defect is understood and the fix is safe. Only **29 of 214** non-sidecar results files carry a `payload_sha256` at all (measured 2026-08-19), so the check has never been exercised on most of the tree. Extend the stamp to every results file the post-review work produces. |
| **R4g** | E28 provenance and manifest repair | M-3, M-4, F-11 | 166 of 166 sidecars record `"corpus": "wikitext"` (the `--corpus` default leaking) and `anchor_agreement_gate: null`. Backfill the true corpus from `corpus_file`, record the gate where recoverable or mark it explicitly unrecorded, hash all 166 into `ARTIFACTS.md`, and delete the stale line 211. Then fix `./lab health` H3 to compare a hash instead of a basename string. |
| **R4i** | **The 1B replication ran on a band the paper's own rule does not produce** | new, found 2026-08-19 | `e53_ladder_summary.bands_declared_vs_used` records for 1B: `declared_by_the_papers_own_rule [6,13]`, `used_in_the_ladder [5,13]`, **`matches: False`**. `paper_5pp.tex:189-191` states the band rule and `:277-280` cites the 1B replication (9 of 10 pairs at 35x seed SD) without disclosing that the 1B arm is one layer below the rule. **The corrected-band recompute already exists** as E62 (`results/ladder1b_b613/`, `e62_interaction_b613.json`). Re-derive the 1B claim from it, or state the deviation. Do not leave a paper that prescribes a band rule and silently violates it at the second scale |
| **R4j** | **The single leave-two-out failure reverses the ordering, and the paper does not say by how much** | new | `e54.matrix_loo.min.drop_both_extremes_github_and_uspto` = fit 42.011 / read **47.613** / residual 10.375, `fit_dominates_read: false`. The paper says at `:295` "27/28 under `min`, the exception being the drop-both-extremes case" without printing that in that case **the read axis beats the fit axis by 5.6 percentage points**. Publish the number. Also: the abstract's "28/28 leave-two-out splits" carries no aggregation qualifier and is `persist`-only |
| **R4k** | **"541 items" is the six-set count; only five sets are scored** | new | `t52_factorial.py` builds `items` by looping `EVAL_SETS`, not `ADMITTED`, so `n_items = 541` is 551 released minus 10 unscorable association items. The admitted five hold **449** released items and **801** of the 893 pairs. `paper_5pp.tex:206-207` and `tab:config` both call 541 "the readout task". Relabel, or report the admitted-five counts |
| **R4l** | **Three of the "twenty pre-registered" predictors have no locatable registering text** | C-1 | The review's git audit found 6 of 45 registration claims `UNVERIFIABLE`, and three of those are rows of `tab:predictors` (E45, E47, E50 family). `paper_5pp.tex:113` says "Twenty **pre-registered** candidate predictors". Either drop the qualifier, qualify the count, or locate the registration. The conclusion is unchanged either way, because none of the twenty passes |
| **R4h** | Small numeric corrections, each verified here | M-7, M-16, M-20..M-25 | Effective rank minimum is **725.888** at `step143000`, the only checkpoint below 726, so "never falls below 726" is false. "Random better on one pair" is **2 of 5**, both Github pairs. `\|rho\| <= 0.28` is **0.2818**. "Two sets exactly zero" are **-1.29e-5** and **-2.89e-6**, small and negative. "the repo previously asserted ~25%" should be **~17%**, the measurement was **0.1704**, so the guess was vindicated to 0.04pp rather than corrected — and **the reviewer's claim that this appears only in `CONTEXT.md` is wrong: it is also at `docs/context/RESULTS_TAXONOMY.md:66`, the canonical claims ledger. Two places to fix.** On E52's `D`: the reviewer calls it "mislabelled", which is **partly refuted** — `docs/archive/prereg/PREREG_E52_FACTORIAL.md:69` defines it verbatim as implemented, so it is not an implementation-vs-prereg break. It is a redundant estimand (`D = 8/7 x` the diagonal mean identically) plus a misleading English gloss, it inflates the reported figure by 14.3%, and **the C4 permutation p = 0.0055 is computed on `D` itself so the factor cancels and the inference is untouched.** Fix the gloss, not the number. |

**COST for all of R4.** $0, CPU, one working day in total.

---

### Tier B — answers the external reviewers, still free or nearly so

---

#### R4b. Re-score E36 — S3's READ-axis rejection is a logit-lens comparison and is now unverified

**WHY.** `CONTEXT.md` §3.1 records S3's first half as REJECTED on the read axis: the fitted operator
is *flatter* across the shift axis than the unfitted logit lens, 5 of 5. That is a **comparison
against the logit lens**, produced by `t36_qladder.py` (no strip, never re-scored), and the logit
lens is the single quantity the defect moved most — its constant goes 0.02844 to 0.08318, a 2.9x
change, while the fitted operators move 2.2-2.7x. A comparison between two quantities that move by
different factors can reverse. **Until this re-runs, S3's headline rejection is unverified.**

E36 is separately implicated: `t36_qladder.py:217` builds its `shuf` arm from **Pile-CC's** operator,
not Github's (R4d), and its control `C2_shuf_below_everything` records `fires: false`. Fix all three
in one pass.

**DESIGN.** Add `--rstrip` to `t36_qladder.py:196` exactly as `t48_crossover.py:234` does it.
Re-run the Q-ladder over the same operators, same band, same rungs. Rebuild `JSHUF` from each
corpus's own operator rather than Pile-CC's. Output `results/e36_qladder_410m_rstrip.json`.

**PRIMARY.** The number of read rungs on which the fitted operator is flatter than the logit lens,
stripped vs unstripped (published: 5 of 5).

**DECISION RULE — fixed before running.**
* **REJECT STANDS:** the fitted operator is flatter on >= 4 of 5 rungs. §3.1 is unchanged.
* **REJECT OVERTURNED:** flatter on <= 1 of 5. **STOP and alert.** S3's first half is no longer
  rejected on the read axis, which reopens the subthesis and changes the paper's framing.
* **UNCLEAR:** 2 or 3 of 5. Report and stop. Do not re-cut.

**CONTROLS.** C1 — running without `--rstrip` must reproduce the stored E36 arms bit-exactly.
C2 — the corrected `shuf` arm, built from each corpus's own operator, must lose to that operator
under `persist`, as the like-for-like evidence already on disk does (`e33_v2`: Github 0.027926 vs
its own `jshuf` 0.018142; `e54` C2: 0 of 15 and 0 of 120). C3 — record
`C2_shuf_below_everything` and report it whichever way it fires.

**DECLARED BIAS.** Scoring-side only; the operators are unchanged (§2b).

**COST.** $0, CPU, hours.

---

#### R5. Corpus-axis uncertainty, stated as such

**WHY.** Both adversarial reviews make the same correct point: the bootstrap resamples **seed
factors**, holds the eight corpora fixed, and is then written next to language that invites a
population reading. The Brutal review calls the 91% "a descriptive decomposition of one 8x8 grid,
not a robust scientific estimate". The reproducibility review reaches the same place independently
(C-3 row 6: *"the interval resamples seeds and holds the eight corpora fixed; the leave-k-out
numbers are the honest corpus-axis uncertainty"*). **Two independent reviewers converging is the
strongest signal in the whole review package.**

**DESIGN.** No new measurement. From `e57_factorial_cells_410m.json` and `e55_matrix_robustness`,
produce: the full leave-one-corpus-out and leave-two-corpus-out distributions of `fit_pct` and
`read_pct` (not just the count of splits preserving the ordering), the min-max range over those
splits, and a corpus-as-random-effect variance component with its degrees of freedom printed next to
it so its weakness at n=8 is visible.

**PRIMARY.** The range of `fit_pct` over all 28 leave-two-out splits, reported beside the seed
bootstrap interval, with both units named in the caption.

**DECISION RULE.** Descriptive; no branch. The deliverable is that the paper stops printing one
interval whose unit is not the unit the claim is about.

**CONTROLS.** C1 — the full-panel value must be recovered when no corpus is dropped. C2 — the
leave-one-out counts must reproduce the stored 8/8 and 28/28 (27/28 under `min`).

**DECLARED BIAS.** n=8 corpora, chosen not sampled. A random-effect variance component on eight
non-random units is a description dressed as an inference and must be captioned as such.

**COST.** $0, CPU, hours.

---

#### R6. Within-source resampling — is "corpus" a factor or a bundle?

**WHY.** The single best experimental idea in either adversarial review, and the one the paper's own
Limitations item 3 already concedes: *"A corpus bundles formatting, boundaries, token-frequency
profile, syntax and surprisal; we control prompt length and nothing else."* If the fit-axis effect
survives when the *source* is held fixed and only the sample varies, the effect is not a bundle
artifact. If it collapses, the paper's factor is confounded and must be renamed.

**DESIGN.** Pick the two largest in-stream sources (Pile-CC and Wikipedia, which have the deepest
document pools). Draw **four disjoint sub-corpora per source** at N=200 from disjoint document
blocks, fit an operator on each, and read all eight against the fixed battery at a fixed read
context. Decompose variance into between-source and within-source.

**PRIMARY.** `between_source_SS / (between_source_SS + within_source_SS)` under `persist`.

**DECISION RULE — fixed before running.**
* **ACCEPT (corpus identity is a real factor):** between-source share >= 0.70.
* **REJECT (the effect is sample noise, not source identity):** between-source share <= 0.30.
  **STOP and alert** — the paper's factor is not what it is called.
* **UNCLEAR:** anything between. Report the number and stop; do not re-cut it.

**CONTROLS.** C1 — the four within-source draws must be verified document-disjoint (`e58`'s
disjointness machinery already exists and reports 24-26% overlap without the step, so it has power).
C2 — a shuffled-assignment null: relabel the eight operators' source at random and confirm the
between-source share falls to its chance level (~1/7 of total). C3 — each new operator must clear
the derangement floor under `persist`, as all published 410M operators do on 120/120 draws.

**DECLARED BIAS.** Two sources, not eight. This tests whether *source identity* beats *sampling*,
not whether it beats formatting, which needs R7. And the fitting pools must be drawn from the same
`require_full_window` filter, whose selectivity differs by corpus — the very confound `SUSPICIONS.md`
S-3 raises.

**COST.** 8 fits at 410M, N=200. `./lab cost 410m 200 L40S` ~ 0.17 GPU-h ~ $0.14 each, so
**~$1.20 plus the read**, call it **under $5**. This is the best value on the entire slate after R1.

---

#### R7. Length- and format-matched fitting pools

**WHY.** `SUSPICIONS.md` S-3, unresolved: Github is the outlier in at least nine analyses and is
also the corpus whose token distribution differs most from the English-prose battery. The P-ladder
already shows length matters — R moves from 2.60 raw to 3.46 length-matched at 410M, and
`CONTEXT.md` §1.2 instructs the reader to cite the length-matched column. **Nothing in `results/`
matches the fitting corpora on length, type-token ratio or tokens-per-document before comparing
their reads.**

**DESIGN.** Refit the five in-stream corpora at N=200 on pools matched on median tokens-per-document
and type-token ratio, and re-run the ladder read.

**PRIMARY.** The between-corpus spread in units of the pooled seed SD, matched vs unmatched
(published: 58x under `persist`, 43x under the anchor readout per the review's re-score).

**DECISION RULE.** ACCEPT if the matched spread stays above 20 seed SDs. UNCLEAR between 5 and 20.
REJECT below 5, in which case the corpus effect is substantially a length effect and the paper says
so.

**CONTROLS.** C1 — matched pools must actually be matched: report the post-matching spread in the
matched statistics and require it below 10% of the pre-matching spread. C2 — reproduce the unmatched
spread from the same code path.

**DECLARED BIAS.** Matching on two statistics leaves markup, code-ness and surprisal free. Github
may not be matchable at all against English prose without discarding most of it; if the matched pool
falls below N=200, report the shortfall rather than padding.

**COST.** 5 fits ~ **$1**, plus CPU read. `SUSPICIONS.md` prices the grid at ~$2.

---

### Tier C — the external asks that are real, expensive, and out of scope for 28 August

These are listed so the paper can say honestly what it did not do, and so a follow-up has a plan.
**Do not start any of them before the deadline.** Each names the cheapest defensible substitute,
which is what actually goes in the paper.

| ask | who asked | why it is out of scope | cheapest defensible substitute, for this submission |
|---|---|---|---|
| **Move the task battery** (three-factor design P x Q x T) | Brutal #1 "Essential", Intermediate #4, Related-work #3 | Requires building concept batteries in new domains with verified target tokens, then re-running the whole grid per battery. Weeks, not days. **It is also the paper's own Limitation 1**, already stated first. | State it as the decisive limitation in the abstract, not only in §Limitations. Report the **per-eval-set** decomposition already stored in `e52_factorial_410m.per_set_D` and `e51`'s corpus x set interaction, which is direct evidence that *which concepts are legible* moves with the corpus even though the battery is fixed. |
| **Canonical protocol arm** (N=1000, the anchor's `min`, its log-k trapezoid over ks=(1,2,5,10,25,100), final target layer) | Brutal #6, Intermediate #4, Related-work #1 | 8 corpora x 3 seeds at N=1000 is 5x the fitting cost of the whole 410M grid; ~$60 and a day of GPU. Over the §10 budget gate and over the deadline. | The paper already reports **both** aggregations everywhere and both agree on every ordering. Add a table enumerating each deviation from the published recipe with its measured effect where one exists (`E17` for `skip_first`, `t14b`/`e13` for target layer, `M-15` for the two AUC definitions) and mark the rest **unmeasured**. Honesty beats a partial replication. |
| **External validation of `persist`** against causal interventions or behavioural criteria | Brutal #5, Intermediate #5, No-Steering, Related-work #2 | The write side has never produced a clean number (`CONTEXT.md` §4.1 parks S4) and building an interventional criterion from scratch is a paper of its own. | **Stop calling `persist` the adjudicator.** The paper already concedes the circularity, citing Kriegeskorte. Reframe as: `min` fails a structural control on a wide band, `persist` does not, both agree on every ordering the paper reports, and neither is validated against an external criterion. That is exactly what the data support and it costs one paragraph. |
| **A second model family / instruction-tuned models** | Brutal #4, Intermediate #3, Related-work #4 | Pythia is chosen *because* its stream is published, which is what makes the containment label a measurement. Another family loses that and needs a new corpus pipeline. | Retitle and rescope. The No-Steering reviewer accepts without this; both adversarial reviewers propose the same fix, which is to narrow the claim rather than broaden the evidence. See `POSTREVIEW_PAPER.md` §2. |
| **Corpus-resampling / hierarchical random-effects design over many sub-corpora** | Brutal #3 | The full version needs dozens of fits. | R6 is the two-source version, at ~$5, and R5 states the corpus-axis uncertainty from data already on disk. |
| **E66's fitter discrepancy resolved by refit** | F-4, U-1 | Needs a GPU refit; the operator asked for it to be held. | **Correct the claim instead.** `CONTEXT.md` §6.2 dismisses E66's C1 failure as an fp16 artifact; the fp16 bound is 2^-11 = 4.883e-4 and the observation is 2.535e-3, short by **5.19x**. The reads from all three arms are byte-identical, so *"no fitter confound for the read"* is directly supported and is what should be claimed. The operator-level discrepancy stands unexplained and the file's own VERDICT stays. |
| **Re-score E36/E48/E52/E59 and the 1B ladder under `.rstrip()`** beyond R1 | S-1 | R1 covers the paper's headline. The rest is ~3-5 h CPU plus fetching the 1B operators. | Do it **after** the deadline, or during it if R1 lands early. If R1 returns QUALIFIED or REJECT this becomes Tier A immediately. |

---

## 4. THE GATE — what must hold before any number reaches the paper

0. **R0 has landed** — **operator-only**; an agent reports it outstanding rather than doing it. No
   new claim is written while a falsified one stands (§2.5).
1. **R1 has run and been adjudicated**, and the paper's headline is written to whichever of the
   three branches fired. No branch may be softened (§2.9).
2. **R3 has cleared D2**, or every ladder-derived claim is removed from the paper. Three claims are
   affected: the per-corpus asymptotes against the logit lens, the flatness in N, and the 1B
   replication.
3. **R4a-R4h are landed**, because each is a number currently wrong or missing in a document the
   reviewers will read.
4. **Every new result file carries a `payload_sha256` that verifies** — which requires R4f first.
5. **`./lab verify` and `./lab health` are green**, and the test suite passes. It does today (6/6).
6. **Every retraction is in `RESULTS_TAXONOMY.md` before the claim it replaces is cited anywhere**
   (§2.5).
7. **No new claim is written from an unstored number** (§6.2). The verifications in
   `tmp/INDEPENDENT_VERIFICATION_2026-08-19.md` are recomputations, not results files; anything from
   there that the paper wants must be re-run into `results/` first.

---

## 5. WHAT NOT TO RUN, AND WHY

* **Anything that re-thresholds a fired rule.** D2 fired DIVERGENT. R1 has three branches written
  before it runs. Neither may be re-cut afterwards.
* **A partial canonical replication.** Running N=1000 on two corpora and calling it a canonical arm
  is worse than not running it, because it invites the reader to generalise from a sample chosen by
  budget.
* **A `persist` validation built from another structural null.** The reviewers' objection is that
  `persist` is validated on the control it was designed to pass; a second control of the same family
  does not answer it and spends the paper's credibility.
* **Anything above 410M before R1 adjudicates.** The 1B arm inherits whatever R1 finds.
* **The write side (S4) and the Hessian (S5).** Parked, correctly, and nothing in either review
  changes that.

---

## 6. BUDGET AND SCHEDULE

**Committed spend: under $10.** Everything decisive is $0.

| day | work |
|---|---|
| 1 | **R0 (operator).** In parallel, an agent does **P0** (the pool port, gated on bit-identity), writes the `docs/experiments/preregs/` documents for R1, R2, R3, R4b, R6, commits them, and smoke-times one R1 cell. |
| 1-2 | **R1** runs. R4f and R4g land in parallel (they touch no result R1 depends on). |
| 2 | **R1 adjudicated.** This is the fork: ACCEPT keeps `POSTREVIEW_PAPER.md` on plan A, QUALIFIED moves it to plan B, REJECT triggers a stop-and-report. |
| 2-3 | R2 and R3 run. R4a-R4e, R4h land. |
| 3-4 | R5 from data on disk. R6 and R7 fits if the budget gate is signed. |
| 4-9 | `POSTREVIEW_PAPER.md` and `POSTREVIEW_RELEASE.md`. **Release work is not a tail task**; both adversarial reviews scored reproducibility 30/100 and both named the missing repository as the cause. |

**Budget gate (§10):** nothing here approaches $40 or 6 h of GPU. If R1's smoke projects a CPU run
longer than 12 h, that is the one decision worth a rental, and it needs a signed note in the results
file recording that the device changed and that one cell was cross-validated on CPU.

---

## 7. PRE-REGISTRATION REQUIREMENTS

The review verified registration claims against **git timestamps rather than prose** and found no
back-dating, but did find that **25 of 45 registration claims are in-file docstrings** — the file
that states the rule is the file that computes the result, so the rule carries no independent
timestamp, and in 10 cases both first appear in the same commit.

Therefore, for everything on this slate:

1. The `docs/experiments/preregs/` document is written and **committed in its own commit**, before the
   script that computes the result is committed and before any run.
2. The commit message names the experiment id and says `PREREG`.
3. The results file records the prereg path **and its SHA-256 at the time of the run**.
4. The decision rule is quoted **verbatim** in the `docs/experiments/preregs/` document, and the results
   file quotes the same string. If the two differ the result is void.
5. Every control names the number it must produce **before** the run, and the results file records
   observed-versus-required for each. A control that cannot fail is not a control (R4e); state its
   power in the spec.
