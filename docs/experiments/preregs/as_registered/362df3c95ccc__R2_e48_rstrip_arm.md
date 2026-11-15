# R2 — the declared-but-never-run `--rstrip` sensitivity arm on E48

**PRE-REGISTERED 2026-08-19, before the run.** Source:
[`../POSTREVIEW_EXPERIMENTS.md`](../POSTREVIEW_EXPERIMENTS.md) §3 Tier A, item R2. Amends
[`E48_crossover.md`](E48_crossover.md).

---

## QUESTION

`repro/exp/e48_crossover.sh:5-7` declares the unstripped path PRIMARY and `--rstrip` *"the
disclosed sensitivity arm"*, and `results/e48_crossover_410m.json` contains the prose *"The
stripped path is run separately via `--rstrip`."* **It was not run.**
`results/e48_crossover_410m_rstrip.json` does not exist and the stored `rstrip_arm` is `false`.

A results file asserting an execution that never happened is the most corrosive defect this
repository can carry, because the whole provenance argument rests on results-file prose being true.
R2 makes the sentence true and stores the arm.

## DESIGN

Run it, unchanged: `RUN_RSTRIP_ARM=1 bash repro/exp/e48_crossover.sh`. The flag is already
implemented (`t48_crossover.py:171-172, 234`) and already gated. Nothing about the experiment is
modified — that is the point.

## PRIMARY

The derangement control under both conventions, and the per-corpus asymptotes against the logit
constant.

## DECISION RULE — fixed before running, quoted verbatim

Quoted from `specs/POSTREVIEW_EXPERIMENTS.md` §3, item R2:

> **DECISION RULE.** This is a **disclosure**, not a test: it has no accept/reject branch and must not
> be given one. It runs, it is stored, and both arms are reported. The one thing it can do is
> contradict C4 of R1, in which case R1's metric-audit control has failed and both stop.

## CONTROLS

* **C0 — reproduction of E33.** Fires on the **unstripped** arm only, by construction; that is why
  the unstripped path is PRIMARY. The stripped arm **cannot** fire C0, and the reason is recorded
  in the results file rather than left as a silent skip. *Number:* the stored file already records
  `skipped: true` with `why_skipped` naming the 157/551 divergence.
* **C-cross — consistency with R1/C4.** The stripped derangement result must agree in direction
  with R1's C4. *Required:* the real operators clear their own layer-deranged floor under `persist`
  in the stripped arm, as they do on 120/120 draws unstripped. A contradiction stops both.

**Power.** C0 is a recorder on this arm, not a gate — stated explicitly per R4e's control-power
audit. C-cross can fail.

## DECLARED BIAS

None beyond R1's fitting-side bias: the operators were fitted on unstripped prompts and only the
scoring readout changes.

## ALSO REQUIRED, AND NON-NEGOTIABLE

The false sentence in `results/e48_crossover_410m.json` must be corrected. Results files are
append-only in this repository's practice, so the correction is a new field in the **new** file
plus a retraction line in `RESULTS_TAXONOMY.md` §Tier D naming the defect. **The old file is not
silently edited.**

## COST

$0, CPU, hours. Already scripted.

## RESULT

*(unrun at time of writing)*

## VERDICT

**DISCLOSED AND STORED — no branch, as registered.**

The arm ran unmodified via `RUN_RSTRIP_ARM=1 bash repro/exp/e48_crossover.sh` and
`results/e48_crossover_410m_rstrip.json` now exists, so the sentence in
`results/e48_crossover_410m.json` asserting it had been run is true for the first time.

Both arms are reported. At the corrected readout the logit constant moves **0.028440 -> 0.083179**
and Github moves **-1.9% -> +21.1%** against it; **all eight corpora sit above the free baseline**,
from +17.7% to +44.3%. C0 fires on the unstripped arm only, by construction, and the stripped arm
records why it cannot.

**C-cross holds:** the stripped derangement result agrees in direction with R4b's C2 — no corpus's
own derangement beats its own operator — so R1/C4 is not contradicted and nothing stops.

**Incidental, and favourable:** re-running the unstripped primary reproduced the stored file
**exactly, 0 of 2496 numeric fields differing** (the only change is a prereg path string updated for
the repo restructure). E48 is bit-reproducible on this machine.

**The retraction this measurement supports — `paper/CONTEXT.md` §3.4, the corpus-axis crossover —
is R0, remains OPERATOR-ONLY, and was deliberately not performed.**
