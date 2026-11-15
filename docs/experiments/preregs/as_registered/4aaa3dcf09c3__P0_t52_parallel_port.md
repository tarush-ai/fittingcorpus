# P0 — port a process pool into `t52_factorial.py`

**PRE-REGISTERED 2026-08-19, before the port was written and before any run.**
Source: [`../POSTREVIEW_EXPERIMENTS.md`](../POSTREVIEW_EXPERIMENTS.md) §3 Tier A, item P0.

---

## QUESTION

Can E52's 30 `(read rung, prefix seed)` cells be scored in parallel **without changing a single
number**, so that R1 is an overnight job rather than a two-day one?

This is infrastructure, not science. It is pre-registered anyway because it sits directly upstream
of the paper's headline: a parallelisation that changes a number would put a scheduling artifact
inside `fit_pct`, and the only way that is caught is by fixing the acceptance condition before the
port exists.

## PRE-REGISTRATION — the rule, verbatim

Quoted from `specs/POSTREVIEW_EXPERIMENTS.md` §3, item P0, "DECISION RULE — and it is a gate, not
a target":

> * **ACCEPT:** the pooled run reproduces the serial run's stored matrix at **`max_abs_diff = 0.0`
>   across all 128 cell values**, and wallclock falls by at least 3x.
> * **REJECT:** any non-zero difference. **STOP.** A parallelisation that changes a number is a bug,
>   and shipping it would put a scheduling artifact inside the paper's headline. Do not "investigate
>   the tolerance" — there is no tolerance. The same computation in a different order over the same
>   fp32 inputs must give the same bits here, because nothing is reduced across cells.

## DESIGN

`experiments/t52_factorial.py` gains `--workers`. The per-cell body (`cache` + the 26 `score`
arms) is hoisted to a module-level function so it pickles; the parent keeps ownership of
everything that defines *what* a cell is, and the worker owns only *how* it is computed.

**Deviation from the slate's design note, declared, with its reason.** §3/P0 says "keep the
operators loaded once in the parent and let fork share them copy-on-write". **That is not available
here**: this laptop is `darwin`, where Python's default (and, with PyTorch loaded, only safe) start
method is `spawn`, not `fork` — measured, `multiprocessing.get_start_method()` returns `spawn`.
Forcing `fork` with an already-initialised PyTorch is the documented deadlock case. The port
therefore follows the pattern **`e28_ladder_410m.py` actually uses**, which is the same file the
slate points at: a top-level `cell()` that takes picklable arguments and loads the model and the
operators itself, once per worker, via a `Pool(initializer=...)`. Cost of the deviation: peak RSS
grows with `--workers` instead of staying flat. That is measured below and is what caps the worker
count, and it changes no number.

What the parent still computes, so that determinism is structural rather than hoped for:

* every cell's prefix construction — `build(rung, ps)` runs in the parent, so the
  `torch.Generator` sequence is identical to the serial run's regardless of scheduling;
* the item table, the pair table, `SET_IDX`, `ITEM_PAIRS`;
* all aggregation, bootstrap, permutation and adjudication, unchanged.

The worker returns the same per-pair score vectors the serial loop put into `CELL`, so every
downstream statistic reads an object of identical type and content.

`torch.set_num_threads(1)` is set inside each worker. Without it, `--workers 8` spawns 8x8 BLAS
threads on 14 cores and the run gets slower.

## PRIMARY

Wallclock for the full 30-cell grid, pooled versus serial.

## CONTROLS — each with the number it must produce

* **C1 — bit-identity.** Pooled, **without** `--rstrip`, against `results/e52_factorial_410m.json`.
  *Required:* `max_abs_diff = 0.0` on all 128 stored cell values (64 cells x 2 aggregations).
  This is the check `t52` already implements as E57's `control_C1_reproduces_stored_e52_matrix`
  (tolerance 1e-12, last fired at exactly 0.0).
* **C2 — worker-count invariance.** `--workers 1`, `2` and `8` must give identical output.
  *Required:* `max_abs_diff = 0.0` between every pair, on the same 128 values. A difference means
  shared mutable state and the port is wrong.
* **C3 — no thread oversubscription.** *Required:* `torch.get_num_threads() == 1` observed inside a
  worker and recorded in the results file, not asserted in a comment.

**Power.** C1 and C2 can fail: the scoring path was measured thread-count-invariant on this machine
before the port (smoke matrix at `OMP_NUM_THREADS=1` vs the default 10 threads,
`max|diff| = 0.0` over 18 cells), so an exact-zero requirement is a real constraint rather than a
tolerance chosen to be met. Had that pre-test come back non-zero, this gate would have been
impossible and the port abandoned — which is what makes it a gate.

## DECLARED BIAS

None on the numbers: this changes scheduling only, which is exactly what C1 and C2 verify and why
they are pass/fail rather than tolerance-based. One operational bias: with `spawn`, peak memory is
`workers x (model + operators)`, so `--workers` is bounded by RAM, not by cores, on this machine.

## COST

$0, CPU. An hour to write, minutes to gate.

## RESULT

*(unrun at time of writing)*

## VERDICT

*(pending)*
