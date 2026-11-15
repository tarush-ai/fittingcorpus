# T1 SWEEP — pre-hoc predictions, written 2026-08-29 while the sweep was running

Written after module 3 of 22 had been adjudicated and while `e59_read_dose` was still executing,
so every prediction below about modules 4–22 was made **before its verdict existed**. That is the
point: SPEC §2 asks for the risk to be classified before running, not explained afterwards.

Evidence: `repro/t1_sweep/t1_classify.py`, output stored at `docs/reproducibility/t1_module_audit.json`.

---

## PREDICTION 1 — five modules will report MOVED, and the cause is a documentation path, not a number

`repro/t1_sweep/t1_classify.py` finds five modules whose script on disk differs from the script
recorded in the result they reproduce (SPEC §4 rung 4):

| module | vaulted original | changed lines |
|---|---|---|
| `e59_read_dose` | `repro/scripts_at_run/808803674ad1__t59_read_dose.py` | 4 |
| `e65_ckpt_geometry` | `repro/scripts_at_run/8388d47ba755__t65_ckpt_geometry.py` | 4 |
| `e48_crossover` | `repro/scripts_at_run/a76a103f93a2__t48_crossover.py` | 4 |
| `e52_factorial` | `repro/scripts_at_run/6d74ea7f4ef2__t52_factorial.py` | 12 |
| `e36_qladder` | `repro/scripts_at_run/ef457ce679e6__t36_qladder.py` | 6 |

**Every changed line is a pre-registration path string**, rewritten by the repo cleanup that moved
`specs/…` to `docs/experiments/preregs/…`. No computational line differs — diff them and see.

The consequence is not cosmetic. These scripts write the prereg path *into the result payload*:

```
results/e59_read_dose_410m.json   payload key: prereg
results/e65_ckpt_geometry_410m.json                prereg
results/e48_crossover_410m.json                    prereg
results/e52_factorial_410m_rstrip.json             prereg, prereg_files
results/e36_qladder_410m_rstrip.json               prereg, prereg_r4b
```

`canonical_payload_sha` excludes only the `provenance` block (`src/provenance.py:213`), so these
keys are hashed. **Therefore these five must report MOVED**, with:

* rung 1 — only `prereg`-family keys changed, all string-valued;
* rung 6 — **no numeric field moved at all**;
* rung 4 — script changed since the run, original present in `repro/scripts_at_run/`.

**A MOVED verdict here is not a reproduction failure.** It is the payload hash correctly detecting
that a documentation string was rewritten. If any of the five moves a *numeric* field, that
prediction is wrong and the result is a genuine finding that needs the full ladder.

**Falsifier:** any of the five returning BIT-IDENTICAL falsifies the mechanism above, and any of
them moving a numeric field falsifies the "documentation only" claim.

## PREDICTION 2 — the remaining seventeen should be BIT-IDENTICAL

They run the byte-identical script recorded in the result, on the same machine, same torch
(2.13.0), same device (CPU), same untouched thread count (10). `cv5_sensitivity`, `cv2_position`
and `e58_algebra` have already returned BIT-IDENTICAL, consistent with this.

---

## CORRECTION TO SPEC §2 — the pre-provenance set is FIVE, not three

SPEC §2 lists three results with no provenance block: `e33_logit_v2`, `e38_geometry`,
`e49_stability`. Auditing every payload finds **five**. `e37_rank_70m` and `e37_rank_160m` also
have `provenance: ABSENT`, and the spec's pre-hoc map omits them.

This does not change control flow — SPEC §3.5 routes both EXPECTED and LOCAL to CONTINUE, and the
halt test is the preflight re-run, which is unaffected. It changes only which modules are
*labelled* expected-to-be-risky. The 2026-08-29 run was driven with the spec's three; the
corrected set is recorded in `repro/t1_sweep/t1_sweep.sh`.

## `e48b_exposure` — the one argv difference, and why it is benign

Recorded `provenance.argv` is `['pythia/t48b_exposure_growth.py']`, with no flags. The module runs
`experiments/t48b_exposure_growth.py --exclude OOD_News_2024_dedup`. Two differences, both benign:

1. `pythia/` → `experiments/` is the repo-cleanup path rewrite the module header documents.
2. `--exclude OOD_News_2024_dedup` is **the parser default**
   (`experiments/t48b_exposure_growth.py:77`), so passing it explicitly is semantically identical
   to the recorded run that passed nothing.

It is an explicit restatement of a default, not a changed setting. Worth noting because
`OOD_News_2024_dedup.jsonl` is the corpus SPEC §4 rung 2 flags as being in neither manifest and
carrying no recorded hash — this module excludes it, so it never reads it.

---

## The prediction, made exact (added 2026-08-29 19:50, still before any of the five ran)

`repro/t1_sweep/t1_predict_moved.py` applies the cleanup's string rewrite to each STORED payload
and recomputes the hash, so the prediction is a specific target rather than a direction:

| module | stored payload sha | MUST become | fields that move | numeric |
|---|---|---|---|---|
| `e59_read_dose` | `06272f749e1fbef8` | `7c1c6b762d47c819` | `prereg` | 0 |
| `e65_ckpt_geometry` | `cea1549bbfefad0b` | `bbe32c177ad9c0f8` | `prereg` | 0 |
| `e48_crossover` | `364c5f3be616f008` | `e479cd0c039e8384` | `prereg` | 0 |
| `e52_factorial` | `44d43319a7ec0b61` | `56ec5e422daa5fab` | `prereg`, 3x `prereg_files[].path` | 0 |
| `e36_qladder` | `2b970c1743f835d8` | `1318d73053a6a271` | `prereg`, `prereg_r4b` | 0 |

Full record: `docs/reproducibility/t1_moved_prediction.json`.

**Why this is the strongest available proof for these five.** BIT-IDENTICAL is impossible for them
by construction. But the predicted hash is computed from the stored payload by changing NOTHING
except the path string. So if the observed hash equals it, every numeric field reproduced
bit-identically -- a single flipped scoring decision anywhere would change a number and miss the
target. `repro/t1_sweep/t1_check.py` performs this comparison automatically and records
`MOVED_AS_PREDICTED` on a match, `PREDICTION FALSIFIED` otherwise.

It also subsumes the SPEC §3.5 shared-cause test for these five: a drifted corpus or operator would
move a number, which would break the match. A hash match therefore rules out a shared cause.

---

## PREDICTION 3 — the pre-provenance five will exit rc=1, and it is the HARNESS, not the science
(added 2026-08-29 20:05, after `e38_geometry` exited 1 and before the other four ran)

`e38_geometry` returned `rc=1`. Its log shows the science completed:

```
wrote results/e38_jgeometry.json
   ✓ experiments/t38_jgeometry.py exited 0
   ! results/e38_jgeometry.json: NO PROVENANCE BLOCK (module predates provenance.py?)
   ✗ output verification FAILED — the result is not trustworthy
```

The script exited 0. `_lib.sh`'s `verify_outputs` then refused the result because it carries no
provenance block, and the module died. **This is a harness contract failure, not a computation
failure**, and it is structural: these scripts write with a bare `json.dump`, never
`provenance.write_result`, so they CANNOT satisfy `verify_outputs`.

| script | `write_result` calls | `json.dump` calls |
|---|---|---|
| `t38_jgeometry.py` | 0 | 2 |
| `t37_rank_ablation.py` | 0 | 2 |
| `t43_derangement_stability.py` | 0 | 2 |
| `t33_logit_baseline.py` | 0 | 1 |

**Prediction:** `e37_rank_70m`, `e37_rank_160m`, `e49_stability` and `e33_logit_v2` will also exit
`rc=1` with the identical `NO PROVENANCE BLOCK` message. Their payloads contain no stale `specs/`
path, so unlike `e38` they should come back **BIT-IDENTICAL** despite the non-zero exit.

`e38` itself moved by exactly one field — `prereg`,
`pythia/specs/PREREG_E38_JGEOMETRY.md` → `docs/experiments/preregs/superseded/...` — with **zero
numeric fields moved**. So `e38`'s numbers reproduced exactly. It was not in Prediction 1 only
because, having no recorded script hash, the rung-4 comparison that identified the other five was
unavailable for it.

Remaining payloads still carrying a stale path, and so still expected to MOVE:
`e65_ckpt_geometry` (1), `e48_crossover` (1), `e52_factorial` (4), `e36_qladder` (2).

## OPEN QUESTION — the recorded thread count is 8, not the default 10

Every compute module in this sweep recorded `torch_num_threads: 8`; `cv2_position`, which runs a
tokenizer and no parallel op, recorded 10. A fresh interpreter on this machine reports 10
consistently, including under `nohup`, after a BLAS matmul, and after an `at::parallel_for`
elementwise op, and `provenance.env_state()` called directly also reports 10. **The mechanism is
not yet explained and is recorded here rather than guessed at.**

It does not threaten the sweep: nothing set the value (no `OMP_NUM_THREADS`, no
`torch.set_num_threads` in any of the 22 scripts or their imports), so SPEC §1.1c was respected,
and 8 is inside the regime `results/e60_fitter_determinism.json` measured as EXACTLY agreeing
(`cross_implementation_abs = 0.0` at 1, 4 and 8 threads; divergence appears at 10 and 12). The
bit-identical results observed so far are consistent with running in that regime.

### The 8-vs-10 investigation: what is FALSIFIED, and the natural experiment that will settle it

`repro/t1_sweep/t1_thread_probe.py` tests each candidate in its own fresh subprocess. **Every one
returned 10 -> 10.** None reproduces the 8 the sweep records:

| candidate | result |
|---|---|
| `import torch` / `transformers` / `provenance` / `anchor_evals` / `jlens` | 10 -> 10 |
| `AutoTokenizer.from_pretrained`, `AutoModelForCausalLM.from_pretrained` | 10 -> 10 |
| three real forward passes through pythia-410m | 10 -> 10 |
| `torch.load` of a stored operator, and `.float()` of its `J` dict | 10 -> 10 |
| BLAS matmul, `at::parallel_for` elementwise | 10 -> 10 |
| `torch.linalg.svd` / `eigh` / `qr` (LAPACK) | 10 -> 10 |
| spawn chain: nohup, stdout piped to grep, double-nested bash, setsid, caffeinate, closed stdin | 10 -> 10 |
| 150s sustained matmul soak, sampling on every change | never left 10 |
| environment diff, running module vs interactive shell | no thread variable differs |

`provenance.env_state()` is a plain `torch.get_num_threads()` call (`src/provenance.py:169`), so the
recorded 8 is genuinely what those processes returned. **The mechanism is unexplained. Do not
assert one in the write-up.**

The surviving correlation is workload shape, not time: `cv2_position` (tokenizer only, no tensor
work) recorded 10, while `cv5`, `e58`, `e59` and `d1` (all of which score operators) recorded 8 --
and `cv2` and `e58` ran six seconds apart in the same driver, which rules out drift over time.

**The sweep will test this for free.** Remaining provenance-stamping modules split cleanly:

* `cv7_rung`, `cv6_ladder` — `--adjudicate`, pure JSON re-aggregation, no torch tensor work.
  **Predicted: 10**, matching `cv2`.
* `cv3_margins`, `cv4_capability`, `d3_by_family`, `e65_ckpt_geometry`, `cv1_competence`,
  `e48b_exposure`, `e48_gate`, `e48_crossover` — real tensor work. **Predicted: 8.**
* `e52_factorial` sets `torch.set_num_threads(1)` (`t52_factorial.py:147`) and `e36_qladder` sets
  `OMP_NUM_THREADS=1` (`t36_qladder.py:154`). **Predicted: 1**, and these are the only two of the
  22 that pin threads deliberately.

If that split holds, the cause is something in the tensor-execution path that no isolated probe
reproduces. If it does not hold, this correlation is wrong too and the question stays open.

**Either way the sweep's validity is unaffected:** nothing overrode the default (SPEC §1.1c holds --
no `OMP_NUM_THREADS` in the environment, no `set_num_threads` in 20 of the 22 scripts), and both 8
and 1 sit inside the regime `e60_fitter_determinism.json` measured as agreeing EXACTLY
(`cross_implementation_abs = 0.0` at 1, 4, 8). Only 10 and 12 diverge, and the modules recording 10
are the ones doing no tensor arithmetic at all.

### THREAD PREDICTION FALSIFIED, then sharpened (2026-08-29 23:30, 13 of 22 landed)

The prediction above said "real tensor work -> 8". **`cv4_capability` falsified it**: it runs six
models up to 2.8B with full forward passes and recorded **10**. The corrected discriminator is
narrower and fits every observation exactly:

| module | type | threads |
|---|---|---|
| `cv5`, `e58`, `e59`, `d1`, `cv3` | TYPE_1_OPERATOR (loads a fitted `.pt`) | 8, 8, 8, 8, 8 |
| `cv2_position` | TYPE_2_CORPUS (tokenizer only) | 10 |
| `cv4_capability` | TYPE_2_MODEL (six models, 2.8B forwards) | 10 |
| `cv7_rung` | TYPE_3_REAGG (JSON only) | 10 |

**Loading and scoring through a stored operator is what coincides with 8. Running a model is not.**
That is why `repro/t1_sweep/t1_thread_probe.py` missed it: it tested `torch.load` of a lens and
`.float()` of its `J` dict in isolation, but not the scoring path that follows.

This remains a CORRELATION over 8 observations, not a mechanism. It is recorded as such.

**Remaining tests, predicted before the modules run:**

| module | type | predicted threads |
|---|---|---|
| `d3_by_family`, `e48_crossover` | TYPE_1_OPERATOR | **8** |
| `cv6_ladder` | TYPE_3_REAGG | **10** |
| `e65_ckpt_geometry`, `cv1_competence`, `e48_gate` | TYPE_2_MODEL | **10** |
| `e48b_exposure` | TYPE_2_CORPUS | **10** |
| `e52_factorial`, `e36_qladder` | TYPE_1 but pin threads explicitly | **1** |

Nine tests, a four-way split. If `d3` or `e48_crossover` returns 10, or any TYPE_2 returns 8, the
correlation is dead and the question returns to open.

Validity is untouched either way: 8 and 1 are inside the regime `e60_fitter_determinism.json`
measured as agreeing EXACTLY, and the modules recording 10 are exactly those that never transport
an activation through a fitted operator.
