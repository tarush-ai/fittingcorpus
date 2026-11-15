# T1 SWEEP — RESULTS

**Run 2026-08-29 17:17 → 2026-08-30 00:59 PDT. CPU only, one module at a time, thread count never
changed. $0.** Harness: `repro/t1_sweep/`. Spec: `T1_SWEEP_SPEC.md`.

## The §5 table

| module | outputs | payload before → after | verdict | if moved: §4 rung, and what field |
|---|---|---|---|---|
| `cv5_sensitivity` | `cv5_metric_sensitivity_410m` | `cde8769ac592` → `cde8769ac592` | **BIT-IDENTICAL** | — |
| `cv2_position` | `cv2_position_support` | `1eb1ab9b76e7` → `1eb1ab9b76e7` | **BIT-IDENTICAL** | — |
| `e58_algebra` | `e58_algebra_audit` | `d635e656a85c` → `d635e656a85c` | **BIT-IDENTICAL** | — |
| `e59_read_dose` | `e59_read_dose_410m` | `06272f749e1f` → `7c1c6b762d47` | **MOVED (as predicted)** | rung 4 — script changed; only `prereg` string. **0 numeric.** Hit the hash predicted pre-run |
| `d1_union` | `d1_min_union_diagnostic_410m` | `c0cdf93b343e` → `c0cdf93b343e` | **BIT-IDENTICAL** | — |
| `e38_geometry` | `e38_jgeometry` | `16ffc7b0b928` → `75bef4cf9e27` | **MOVED** | rung 4 — pre-provenance; only `prereg` string. **0 numeric** |
| `e37_rank_70m` | `e37_rank_ablation_70m_wikitext` | `5bd9d6dfaa40` → `5bd9d6dfaa40` | **BIT-IDENTICAL** (harness rc=1) | — |
| `e37_rank_160m` | `e37_rank_ablation_160m_wikitext` | `94c65b4aa024` → `94c65b4aa024` | **BIT-IDENTICAL** (harness rc=1) | — |
| `e49_stability` | `e49_derangement_stability` | `6082b49722ab` → `6082b49722ab` | **BIT-IDENTICAL** (harness rc=1) | — |
| `e33_logit_v2` **as shipped** | `e33_logit_baseline_410m_v2` | `73b90a8b5d58` → `69faeffafcdd` | **DOES NOT REPRODUCE** | recipe undershot the band one layer; 86 numeric fields moved, VERDICT flipped |
| `e33_logit_v2` **recipe fixed** | same | `73b90a8b5d58` → `73b90a8b5d58` | **BIT-IDENTICAL** | fix verified: the band was the only defect |
| `cv3_margins` | `cv3_margins_410m` | `38efe87c84be` → `38efe87c84be` | **BIT-IDENTICAL** | — |
| `cv4_capability` | `cv4_phase1_capability` | `43b21658bcc6` → `43b21658bcc6` | **BIT-IDENTICAL** | — |
| `cv7_rung` | `cv7_1b_rung` | `a073b38c6bce` → `a073b38c6bce` | **BIT-IDENTICAL** | — |
| `d3_by_family` | `d3_corpus_by_family_410m` | `fc353bf005b4` → `fc353bf005b4` | **BIT-IDENTICAL** | — |
| `cv6_ladder` | `cv6_per_family_ladder` | `37c137de5d77` → `37c137de5d77` | **BIT-IDENTICAL** | — |
| `e65_ckpt_geometry` | `e65_ckpt_geometry_410m` | `cea1549bbfef` → `bbe32c177ad9` | **MOVED (as predicted)** | rung 4 — only `prereg` string. **0 numeric.** Hit the predicted hash |
| `cv1_competence` | `cv1_answer_competence` | `8809019f865f` → `8809019f865f` | **BIT-IDENTICAL** | — |
| `e48b_exposure` | `e48b_exposure_growth` | `a3904599356a` → `a3904599356a` | **BIT-IDENTICAL** | — |
| `e48_crossover` | `e48_crossover_410m` | `364c5f3be616` → `e479cd0c039e` | **MOVED (as predicted)** | rung 4 — only `prereg` string. **0 numeric.** Hit the predicted hash |
| `e48_gate` | `e48_competence_gate_410m` | `682a6cbd921d` → `682a6cbd921d` | **BIT-IDENTICAL** | — |
| `e52_factorial` | `e52_factorial_410m_rstrip` | `44d43319a7ec` → `2a992ddc89b7` | **MOVED** | 31 wall-clock fields + 6 `prereg` paths. **0 scientific quantities** |
| | `e57_factorial_cells_410m_rstrip` | `8bd3566ee0a9` → `8bd3566ee0a9` | **BIT-IDENTICAL** | the per-cell science file |
| `e36_qladder` | `e36_qladder_410m_rstrip` | `2b970c1743f8` → `1318d73053a6` | **MOVED (as predicted)** | rung 4 — `prereg`, `prereg_r4b`. **0 numeric.** Hit the predicted hash |

**16 of 22 bit-identical. 22 of 22 reproduce every scientific quantity** — 6 payloads moved, and
in every case the movement was a pre-registration path string or a wall-clock timing, never a
measured number. One module (`e33_logit_v2`) required a recipe fix, verified.

## The one real defect

`--band`'s help says "lo,hi inclusive"; the parser is `range(lo,hi)`, exclusive
(`t33_logit_baseline.py:81`). `e33` has no `provenance.argv`, so its module was hand-written from
that help and passed `--band 9,21` — **12 layers instead of 13**. 86 numeric fields moved and the
verdict flipped. The band itself was never in question: `[9,21]` is `int(0.38L)..int(0.92L)` at
L=24, the rule `tests/test_band_rule.py` asserts. The shipped code was never wrong; git holds two
versions of that script with a byte-identical parsing line. Fixed by correcting the recipe to
`--band 9,22`, which reproduced the stored payload exactly. Full diagnosis:
`T1_FINDING_E33_BAND.md`.

That wrong-band run also overwrote its own stored result, which is an input to `e48_crossover`'s C0
control — so `e48_crossover` correctly aborted (`max|diff| = 2.083e-02 → DOES NOT FIRE`). With the
stored file restored (verified byte-identical to HF snapshot `ffdac38e5e95`), C0 reads
`max|diff| = 1.916e-08 → FIRES` and the module reproduces.

## Pre-registered predictions, scored

| prediction | result |
|---|---|
| 5 modules MOVE to a specific pre-computed hash | **4 of 5 confirmed** (`e59`, `e65`, `e48_crossover`, `e36`). `e52` falsified — it records wall-clock in its payload, which the predictor did not model |
| the pre-provenance scripts exit rc=1 on the harness provenance check | **4 of 4 confirmed** |
| the remaining modules are bit-identical | held, with `e33` the single documented exception |
| thread count | **14 of 14** after `cv4_capability` falsified the first hypothesis and sharpened it |

## Two harness defects this sweep exposed in itself

1. **False green.** When `e48_crossover` aborted before writing, comparing the untouched file to
   its own backup returned BIT-IDENTICAL. `t1_check.py` now treats an output whose mtime predates
   its own run as `DID_NOT_RUN`.
2. **Missed shared-cause test.** Adding an `_RC1` suffix broke the driver's `[ "$V" = "MOVED" ]`
   match, so `e33`'s MOVED skipped the §3.5 test; it was run by hand (result: LOCAL). Fixed to
   match any `MOVED*`.

## Resolved along the way

* **`torch_num_threads` is 8, not the default 10.** `experiments/t2_fastfit.py:14` pins it at
  import; seven scripts import it transitively for `PYTHIA_LAYOUT_T5`. 8 is inside the regime
  `e60_fitter_determinism.json` measured as agreeing EXACTLY; 10 is not.
* **SPEC §2's pre-provenance set is five, not three** — `e37_rank_70m` and `e37_rank_160m` also
  lack a provenance block.
* **`e48b_exposure`'s argv difference is benign** — `--exclude OOD_News_2024_dedup` is the parser
  default, and the payload came back bit-identical, proving it.

## What this does not cover

Bit-identity of a re-scored read says nothing about whether the operator is correct, whether the
band is the right band, or whether the eval battery measures what it claims. T2 (refitting
operators) was out of scope and remains sampled at n=2.
