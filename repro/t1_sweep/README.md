# `repro/t1_sweep/` — the harness that runs the T1 sweep, so the sweep itself can be reproduced

`docs/reproducibility/T1_SWEEP_SPEC.md` tells an agent to run 22 T1 modules and diff each payload.
It gives the diff as a shell heredoc. **A heredoc is not reproducible**: it exists only in the
transcript of whoever ran it, it is not hash-stamped, and a reviewer who wants to check the
checker has nothing to read. Everything the 2026-08-29 sweep executed is therefore a file here.

The rule this enforces: *a reviewer must be able to reproduce the reproduction, not just the
science.* If the tool that decides BIT-IDENTICAL vs MOVED is untracked, its verdicts are
unauditable, and "22 of 22 reproduced" is a claim about a script nobody can see.

## The four scripts

| file | what it does |
|---|---|
| `t1_preflight_audit.py` | the SPEC §0.5 gate, **computed** rather than asserted: `.pt` drift, moved `.json`, corpora vs manifest, and a git-history payload test that separates a scrub rewrite from a genuine re-run |
| `t1_sweep.sh` | the driver. Strictly sequential, backs up each declared OUTPUT, runs the module detached, diffs, and implements the SPEC §3.5 halt rule |
| `t1_check.py` | the payload diff and the SPEC §4 six-rung ladder; also the shared-cause test the driver halts on |
| `t1_classify.py` | first-principles audit of what each module actually re-runs: argv vs `provenance.argv`, script identity vs the recorded run, and operator/model/re-aggregation type |

## Running it

```bash
.venv/bin/python repro/t1_sweep/t1_preflight_audit.py     # gate. must PASS before anything runs
.venv/bin/python repro/t1_sweep/t1_classify.py            # what the 22 modules actually do
bash repro/t1_sweep/t1_sweep.sh cv5_sensitivity           # one module
bash repro/t1_sweep/t1_sweep.sh cv5_sensitivity cv2_position ...   # sequentially, never parallel
```

State lands in `$SP` (default `repro/t1_sweep/_run/`, gitignored): `before/` holds the pre-run
backup of every declared output, `logs/` the per-module stdout, `verdicts.tsv` the table, and
`detail_<module>.txt` the ladder for anything that moved.

## Three constraints that are measured, not stylistic

* **CPU only.** `results/d2_device_crossvalidation.json` returned DIVERGENT at
  `max |CUDA − CPU| = 2.774e-04`, above the `1.6e-4` threshold at which one scoring decision
  flips. A GPU sweep returns "does not reproduce" by construction.
* **Never change the thread count.** `results/e60_fitter_determinism.json` measured exact
  agreement at 1, 4 and 8 threads and `1.09e-04` divergence at 10 and 12. The stored numbers are
  10-thread numbers on this machine; the driver never sets `OMP_NUM_THREADS` or calls
  `torch.set_num_threads`.
* **Never in parallel.** Oversubscribing the CPU risks changing reduction order, which is the
  same failure as changing the thread count.

## What these scripts do NOT cover

* `t1_classify.py` reads source statically. It proves a script *contains* a `torch.load` of an
  operator on the path the recorded argv selects; it does not instrument the run to prove the load
  executed. For the four modules where the distinction could matter the loads were also read by
  hand (`t38_jgeometry.py:125,149`, `t43_derangement_stability.py:121`).
* `t1_preflight_audit.py` establishes that inputs are unchanged. Provenance identity is
  **necessary, not sufficient** — it never claims a result is correct.
* `t1_check.py` compares payload hashes. A payload that is bit-identical for the wrong reason —
  because a module silently no-opped and rewrote the same file — would pass. The driver's `rc`
  check and `_lib.sh`'s `verify_outputs` are what guard that.
* Nothing here re-fits an operator. That is T2 and out of scope.

## Counting note

`t1_preflight_audit.py` prints two counts for moved `.json` inputs, because both are defensible
and they differ. **strict** counts a path if any consumer's recorded hash misses — this is what
`tools/artifact_provenance_diff.py` flags, and it is the 43 quoted in SPEC §0.5. **union** counts
it only if no consumer recorded the current content. The gap is files re-run mid-programme, which
some consumers recorded before and others after.
