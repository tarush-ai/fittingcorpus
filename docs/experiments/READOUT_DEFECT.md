# READOUT_DEFECT — the stripped / unstripped readout, stated mechanically

**ZERO ANALYSIS.** Every statement below is a quotation, a count produced by running a committed
tool or the tokeniser, or a field read out of a stored file. Nothing here interprets what the
difference means, and nothing here adjudicates between two records that disagree.

**Produced 2026-08-20**, local, CPU only, `.venv/bin/python`.

---

## 1. THE ANCHOR'S READOUT RULE, QUOTED

Source: `jacobian-lens/data/evaluations/README.md`
(vendored at `581d398`, gitignored, never modified).

Conventions section, verbatim:

> - **Lens readout** — at each (layer, token position) the Jacobian lens
>   returns a ranked list of vocabulary tokens.
> - **Workspace band** — the contiguous mid-network layer range where
>   workspace content is read; experiments report over this band, not
>   individual layers.
> - **Hit** — a target token is a *hit* if it appears at lens rank 1 at any
>   (layer, position) in the band over the scored span.

Per-set readout position, verbatim from the same file:

| eval set | README sentence, verbatim |
|---|---|
| `lens-eval-multihop` | "`target` defines the readout position only and is not itself scored. Readout is at a single position — **the token immediately preceding `target`** — across all layers." |
| `lens-eval-multilingual` | "`target` defines the readout position only and is not itself scored. Readout is at a single position — **the token immediately preceding `target`** — across all layers." |
| `lens-eval-order-ops` | "`target` defines the readout position only and is not itself scored. Readout is at a single position — **the token immediately preceding `target`** — across all layers." |
| `lens-eval-poetry` | "Readout is at a single position — **the last newline token** (end of line 1 of the couplet) — across all layers." |
| `lens-eval-association` | "Readout is at a single position — **the final prompt token** — the closing period — across all layers." |
| `lens-eval-typo` | "Readout is at a single position — **the final prompt token**, i.e. the last tokenizer fragment of the misspelling — across all layers." |

The metric sentence, common to all six sets: "Metric: pass@k = mean over items of the fraction of
`intermediates` whose min-over-layers lens rank ≤ k."

## 2. THE REPOSITORY'S OWN STATEMENT OF THE SAME RULE

`src/anchor_evals.py`, module docstring lines 26–34, verbatim:

> READOUT POSITION, per set (README):
>   multihop / multilingual / order-ops : the token immediately preceding `target`
>                                         == the final prompt token, after rstrip
>   poetry                              : the last newline token (end of line 1 of the couplet)
>   typo / association                  : the final prompt token
>
> `.rstrip()` IS LOAD-BEARING: the released prompts end in a trailing space (e.g. multihop's
> "... is the "), and an un-stripped trailing space becomes the readout token and destroys the
> baseline.

`src/anchor_evals.py:65-68`, the same rule as code:

```python
# Readout position rule per set (README). "last" == final prompt token after rstrip.
_POSITION_RULE = {
    "multihop": "last", "multilingual": "last", "order-ops": "last",
    "typo": "last", "association": "last", "poetry": "last_newline",
}
```

`src/anchor_evals.py:146-153`, `readout_position` in full:

```python
def readout_position(tok, eval_name: str, prompt: str) -> int:
    """Position index to read at, per the anchor's per-set convention."""
    rule = _POSITION_RULE[eval_name]
    if rule == "last":
        return -1
    ids = tok(prompt, add_special_tokens=True).input_ids
    newlines = [i for i, t in enumerate(ids) if "\\n" in tok.decode([t])]
    return newlines[-1] if newlines else -1
```

`src/anchor_evals.py:228-229`, the application site inside `pass_at_k`:

```python
prompt = item["prompt"].rstrip()          # load-bearing; see module docstring
pos = readout_position(model.tokenizer, eval_name, prompt)
```

Code fact, stated without inference: for the five sets whose rule is `"last"`, `readout_position`
returns `-1` without reading `prompt`. Which token is read is therefore fixed by what the **caller**
passed to the tokeniser, not by `readout_position`.

## 3. THE TOKENISATION, DEMONSTRATED ON REAL EVAL ITEMS

Tokeniser: `EleutherAI/pythia-410m-deduped` (GPT-NeoX BPE), loaded offline from
`$HF_HOME=$HF_HOME`. `add_special_tokens=True`, matching the scoring path.

```
SET multihop  item[0]
  prompt        'Fact: The ocean on the coast of the country where Carnival is most famously celebrated is the '
  target        'Atlantic'
  intermediates ['Brazil']
  tokenise(prompt)          last 5 ids [39316, 19651, 310, 253, 209]  decoded [' famously', ' celebrated', ' is', ' the', ' ']
  tokenise(prompt.rstrip()) last 5 ids [954, 39316, 19651, 310, 253]  decoded [' most', ' famously', ' celebrated', ' is', ' the']
  tokenise(prompt+target)   last 6 ids [954, 39316, 19651, 310, 253, 14847]  decoded [' most', ' famously', ' celebrated', ' is', ' the', ' Atlantic']
  readout_position(prompt)          = -1   -> id 209  ' '
  readout_position(prompt.rstrip()) = -1   -> id 253  ' the'
  is id 209 present anywhere in tokenise(prompt+target)?  False

SET order-ops  item[0]
  prompt        '(2 + 3) * 4 = '
  target        '20'
  intermediates ['5', 'multiplication']
  tokenise(prompt)          last 5 ids [10, 475, 577, 426, 209]  decoded [')', ' *', ' 4', ' =', ' ']
  tokenise(prompt.rstrip()) last 5 ids [495, 10, 475, 577, 426]  decoded [' 3', ')', ' *', ' 4', ' =']
  tokenise(prompt+target)   last 6 ids [495, 10, 475, 577, 426, 1384]  decoded [' 3', ')', ' *', ' 4', ' =', ' 20']
  readout_position(prompt)          = -1   -> id 209  ' '
  readout_position(prompt.rstrip()) = -1   -> id 426  ' ='
  is id 209 present anywhere in tokenise(prompt+target)?  False

SET multilingual  item[2]
  prompt        'Das Gegenteil von laut ist '
  target        'leise'
  intermediates ['German', 'opposite', 'loud', 'quiet']
  tokenise(prompt)          last 5 ids [8449, 826, 307, 10863, 209]  decoded [' von', ' la', 'ut', ' ist', ' ']
  tokenise(prompt.rstrip()) last 5 ids [300, 8449, 826, 307, 10863]  decoded ['il', ' von', ' la', 'ut', ' ist']
  tokenise(prompt+target)   last 6 ids [8449, 826, 307, 10863, 458, 885]  decoded [' von', ' la', 'ut', ' ist', ' le', 'ise']
  readout_position(prompt)          = -1   -> id 209  ' '
  readout_position(prompt.rstrip()) = -1   -> id 10863  ' ist'
  is id 209 present anywhere in tokenise(prompt+target)?  False
```

Facts about the sequences printed above:

- Token id **209** decodes to `' '`, a single space.
- Under the unstripped convention the token read is id **209** in all three items.
- Under the stripped convention the token read is id **253** (`' the'`), **426** (`' ='`) and
  **10863** (`' ist'`) respectively.
- Token id 209 does not occur anywhere in `tokenise(prompt + target)` for any of the three items.
- The same three (unstripped id, stripped id) pairs are stored at
  `results/e52_factorial_410m_rstrip.json -> controls.R1_C2_readout_divergence.examples`:
  multihop `209 -> 253`, multilingual `209 -> 10863`, order-ops `209 -> 426`.

## 4. ITEM COUNTS AFFECTED, RECORDED VS OBSERVED

"Affected" is used here exactly as the stored control defines it: the token id at
`readout_position` differs between `prompt` and `prompt.rstrip()`.

| eval set | released items | RECORDED affected | OBSERVED affected (this run) | agree |
|---|---:|---:|---:|:--:|
| multihop | 93 | 83 | 83 | yes |
| multilingual | 107 | 19 | 19 | yes |
| order-ops | 55 | 55 | 55 | yes |
| poetry | 98 | 0 | 0 | yes |
| typo | 96 | 0 | 0 | yes |
| association | 102 | 0 | 0 | yes |
| **total** | **551** | **157** | **157** | **yes** |

RECORDED source: `results/e52_factorial_410m_rstrip.json -> controls.R1_C2_readout_divergence`,
fields `.required_per_set`, `.observed_per_set`, `.required_total = 157`, `.observed_total = 157`,
`.n_released_items = 551`, `.fires = true`. The same 157-of-551 figure also appears in the
`tools/readout_exposure.py` docstring, in `docs/experiments/preregs/R1_grid_rstrip.md`, and in
`tmp/INDEPENDENT_VERIFICATION_2026-08-19.md` §A1.

OBSERVED source: recomputed for this document by tokenising every released prompt both ways,
calling `src/anchor_evals.readout_position` on each, and comparing the token id actually indexed.
Command in §11.

Two further counts observed in the same pass, recorded because they are different quantities:

- Items whose **prompt string** carries trailing whitespace: multihop 83, multilingual 19,
  order-ops 55, **poetry 97**, typo 0, association 0 — total **254**.
- Items whose **read token** changes: the 157 above. Poetry's 97 trailing-whitespace items do not
  change their read token; poetry's rule is `last_newline`, not `last`.

Three item totals appear in the repository for the same battery, all recorded here:

| total | what it counts | source |
|---:|---|---|
| **551** | released items across all six sets | `results/edata1_item_count_reconciliation.json -> per_set.*.released` (93+107+55+98+96+102) |
| **541** | scorable items | `results/e52_factorial_410m.json -> n_items`; identical in `e36_qladder_410m.json`, `e48_crossover_410m.json`, `d1_min_union_diagnostic_410m.json` |
| **449** items / **801** of 893 pairs | the five admitted sets | `docs/experiments/preregs/R4_corrections.md:45` and `:88` |

## 5. THE COST OF THE DIFFERENCE, AS STORED

| quantity | unstripped | stripped | source |
|---|---|---|---|
| logit-lens constant, `persist`, admitted-5, rung Q0, 410M | `0.0284395` | `0.08317913140635938` | `results/e52_factorial_410m_rstrip.json -> controls.R1_C3_logit_constant_moves.unstripped_reference` / `.observed_logit_Q0_persist` |
| same, absolute difference | — | `0.05473963140635938` | same file, `.abs_diff_vs_unstripped_reference` (`fires: true`) |
| E36 control C1 `logit_here` | `0.028439503419212996`, `abs_diff 2.561e-10`, `fires true` | `0.08317913140635938`, `abs_diff 0.05473962824326009`, `fires false` | `results/e36_qladder_410m.json` / `results/e36_qladder_410m_rstrip.json -> controls.C1_Q0_reproduces_e33` |
| 410M ladder grand-mean admitted read, `persist` | `0.041541330636305086` | `0.11051012409926982` | `results/r8_ladder_flatness.json -> by_aggregation.persist.{unstripped,stripped}.grand_mean_admitted_read` |
| 410M ladder grand-mean admitted read, `min` | `0.13783558227165474` | `0.2542683578322579` | same file, `by_aggregation.min.*` |
| stripped / unstripped grand-mean ratio | — | `persist 2.660245168042099`, `min 1.844722194673436` | `results/r8_ladder_flatness.json -> controls.C2_the_convention_bites_here_too.grand_mean_ratio_stripped_over_unstripped` |
| E52 diagonal excess `D`, `persist` | `0.0010325341964960988` | `0.000845372218579525` | `results/e52_factorial_410m.json` / `results/e52_factorial_410m_rstrip.json -> adjudication.D` |
| E57 `fit_pct` / `read_pct`, `persist` | `91.21993064640641` / `7.133265187892407` | `50.697184677169346` / `48.13211438274321` | `results/e57_grid_variance_ci.json` / `results/e57_grid_variance_ci_rstrip.json -> by_aggregation.persist.point` |
| E54 C2 derangement, `min`, draws where `shuf` beats `J^P` (paired by seed, of 120) | `104` | `84` | `results/e54_aggregation_audit.json` / `results/e54_aggregation_audit_rstrip_v2.json -> C2_derangement.min.shuf_beats_jp_paired_by_seed` |

**UNSTORED.** The per-eval-set cost multipliers stated in the `tools/readout_exposure.py`
docstring and at `docs/experiments/preregs/R1_grid_rstrip.md:48` — *"order-ops 29.8x, multihop 3.13x,
multilingual 1.01x, poetry/typo/association 1.00x exactly"* — were searched for across all
278 non-sidecar `results/**/*.json` at 0.5% relative tolerance and are **not present in any
results file**.

Per-set logit-lens values under both conventions are stored outside `results/`, at
`review/reproducibility/scripts/logit_baseline.json`, keyed `unstripped.<set>.<agg>` and
`rstrip.<set>.<agg>`.

## 6. WHICH SCRIPTS STRIP AND WHICH DO NOT

### 6a. Every `.rstrip()` applied to an eval prompt, by grep

`grep -rn 'prompt"\]\.rstrip()' experiments tools`, complete output:

```
experiments/t8_probe_swap.py:125:        prompt = it["prompt"].rstrip()
experiments/t13_bootstrap_controls.py:51:        prompt = item["prompt"].rstrip()
experiments/t48_crossover.py:234:                p = it["prompt"].rstrip() if a.rstrip else it["prompt"]
experiments/t7_bootstrap_audit.py:57:        prompt = item["prompt"].rstrip()
experiments/t23_pq_ladder.py:93:            prompts.append(it["prompt"].rstrip())
experiments/t20_ablation_kl.py:225:            prompt = item["prompt"].rstrip()
experiments/t2_fastfit.py:56:        out = [i["prompt"].rstrip() for i in items]
experiments/t60_fitter_determinism.py:79:    pool = [it["prompt"].rstrip()
experiments/t22_bootstrap_ci.py:84:        prompt = item["prompt"].rstrip()
experiments/t17_reaggregate.py:66:        prompt = item["prompt"].rstrip()
experiments/t36_qladder.py:312:            p = it["prompt"].rstrip() if a.rstrip else it["prompt"]
experiments/t15_shuffle_diagnostic.py:89:        prompt = item["prompt"].rstrip()
experiments/r6_within_source.py:66:            p = it["prompt"].rstrip() if rstrip else it["prompt"]
experiments/t52_factorial.py:215:            raw, stripped = it["prompt"], it["prompt"].rstrip()
experiments/t52_factorial.py:366:            p = it["prompt"].rstrip() if a.rstrip else it["prompt"]
experiments/e28_ladder_410m.py:102:                p = it["prompt"].rstrip() if rstrip else it["prompt"]
```

### 6b. Classification of every script by `tools/readout_exposure.py:script_class`

The classifier's own definitions, quoted from `tools/readout_exposure.py:108-123`:
`NO_EVAL` = "never calls load_eval; no readout over the battery"; `NO_RSTRIP` = "loads the battery
and does NOT strip the prompt"; `COND_RSTRIP` = "strips only when --rstrip is passed; unstripped by
default"; `RSTRIP` = "loads the battery and applies .rstrip() to the prompt".

| class | n | scripts |
|---|---:|---|
| **RSTRIP** | 10 | `src/anchor_evals.py`, `experiments/t2_fastfit.py`, `experiments/t7_bootstrap_audit.py`, `experiments/t13_bootstrap_controls.py`, `experiments/t15_shuffle_diagnostic.py`, `experiments/t17_reaggregate.py`, `experiments/t20_ablation_kl.py`, `experiments/t22_bootstrap_ci.py`, `experiments/t23_pq_ladder.py`, `experiments/t60_fitter_determinism.py` |
| **COND_RSTRIP** | 5 | `experiments/e28_ladder_410m.py`, `experiments/r6_within_source.py`, `experiments/t36_qladder.py`, `experiments/t48_crossover.py`, `experiments/t52_factorial.py` |
| **NO_RSTRIP** | 23 | `experiments/d1_min_union_diagnostic.py`, `experiments/r7_matched_pools.py`, `experiments/t21_conditioning.py`, `experiments/t31_local_bakeoff.py`, `experiments/t33_logit_baseline.py`, `experiments/t34_dact_vs_floor.py`, `experiments/t34b_jeval_dact.py`, `experiments/t37_rank_ablation.py`, `experiments/t38_jgeometry.py`, `experiments/t39_dread.py`, `experiments/t40_disagreement_geometry.py`, `experiments/t41_disagreement_ablation.py`, `experiments/t42_ablation_pairs.py`, `experiments/t43_derangement_stability.py`, `experiments/t44_concept_energy.py`, `experiments/t58_algebra_audit.py`, `experiments/t59_read_dose.py`, `experiments/t65_ckpt_geometry.py`, `experiments/t65_ckpt_readout.py`, `experiments/t66_fitter_equivalence_cuda.py`, `experiments/trainval.py`, `tools/r4_recomputes.py`, `tools/readout_exposure.py` |
| **NO_EVAL** | 57 | every remaining `.py` under `experiments/`, `tools/` and `src/`; none calls `load_eval` |
| **MISSING** | 0 | — |

Call sites in the `NO_RSTRIP` scripts that reach `readout_position` with an unstripped prompt,
read off the source:

| script | line | code |
|---|---:|---|
| `experiments/trainval.py` | 253, 255 | `p = it["prompt"]` then `pos = readout_position(tok, name, p)` |
| `experiments/t33_logit_baseline.py` | 90, 92 | `p = it["prompt"]` then `pos = readout_position(tok, name, p)` |
| `experiments/d1_min_union_diagnostic.py` | 96, 98 | `p = it["prompt"]` then `pos = readout_position(tok, name, p)` |
| `experiments/t34_dact_vs_floor.py` | 105, 110 | `p = it["prompt"]` then `pos = readout_position(tok, name, p)` |
| `experiments/t37_rank_ablation.py` | 104, 106 | `p = it["prompt"]` then `pos = readout_position(tok, name, p)` |
| `experiments/t59_read_dose.py` | 140, 142 | `p = it["prompt"]` then `"pos": readout_position(tok, name, p)` |
| `experiments/t34b_jeval_dact.py` | 118 | `pos = readout_position(tok, name, it["prompt"])` |
| `experiments/t38_jgeometry.py` | 192 | `pos = readout_position(tok, name, it["prompt"])` |
| `experiments/t39_dread.py` | 108 | `pos = readout_position(tok, name, it["prompt"])` |
| `experiments/t40_disagreement_geometry.py` | 128 | `pos = readout_position(tok, name, it["prompt"])` |
| `experiments/t41_disagreement_ablation.py` | 113 | `pos = readout_position(tok, name, it["prompt"])` |
| `experiments/t42_ablation_pairs.py` | 116 | `pos = readout_position(tok, name, it["prompt"])` |
| `experiments/t43_derangement_stability.py` | 91 | `pos = readout_position(tok, name, it["prompt"])` |
| `experiments/t44_concept_energy.py` | 132 | `pos = readout_position(tok, name, it["prompt"])` |
| `experiments/t58_algebra_audit.py` | 136 | `pos = readout_position(tok, name, it["prompt"])` |
| `experiments/t65_ckpt_readout.py` | 113 | `"pos": readout_position(tok, name, it["prompt"])` |
| `experiments/t66_fitter_equivalence_cuda.py` | 103 | `"pos": readout_position(tok, name, it["prompt"])` |

### 6c. Two `NO_RSTRIP` classifications whose script does strip, by a different code path

Recorded as a code fact, not as a correction of the tool:

- `experiments/r7_matched_pools.py:106` reads
  `items = build_items(tok, load_eval, readout_position, token_ids_of, EVAL_SETS, rstrip=True)`;
  `experiments/r6_within_source.py:58,66` defines `build_items` with
  `p = it["prompt"].rstrip() if rstrip else it["prompt"]`. The classifier's regex at
  `tools/readout_exposure.py:114` matches only a literal `["prompt"].rstrip()` inside the file
  being classified, so `r7_matched_pools.py` classifies `NO_RSTRIP`.
- `experiments/r6_within_source.py:175` likewise calls `build_items(..., rstrip=True)`; the
  classifier returns `COND_RSTRIP`, then resolves it to `EXPOSED` because
  `results/r6_within_source_410m.json` carries no `rstrip_arm` key
  (`tools/readout_exposure.py:187` and `:205`).
- Both `results/r6_within_source_410m.json` and `results/r7_matched_pools_410m.json` carry
  `readout_convention = "STRIPPED — the anchor rule (R1)"`. Both records are given in §8.

## 7. EVERY RESULTS FILE, CLASSIFIED

Source: `tools/readout_exposure.py`, re-run 2026-08-20 on the current working tree. It covers
**278 non-sidecar results files** under `results/`; `*_provenance.json` and `*_reads.json` are
excluded by the tool itself.

Class definitions, quoted verbatim from `tools/readout_exposure.py:16-27`, with the
stripped / unstripped / not-applicable label this document uses for each:

| tool class | definition, verbatim | label used here |
|---|---|---|
| `IMMUNE` | "the producing script never loads the eval battery, and neither does anything it reads. No readout, so the defect cannot reach it." | **not-applicable** |
| `CLEAN` | "the producing script loads the battery AND strips. Already correct." | **stripped** |
| `EXPOSED` | "the producing script loads the battery and does NOT strip." | **unstripped** |
| `INHERITED` | "the script does not load the battery itself but reads results produced by an EXPOSED script. Exposure propagates through provenance.inputs." | **unstripped (inherited)** |
| `RESCORED` | "marks the small set for which a corrected-readout measurement exists." | **unstripped, corrected counterpart exists** |
| `UNKNOWN` | "no provenance, or the script is missing." | **undetermined** |

Totals from this run:

| class | label | count | share |
|---|---|---:|---:|
| `IMMUNE` | not-applicable | 50 | 18.0% |
| `CLEAN` | stripped | 35 | 12.6% |
| `RESCORED` | unstripped, corrected counterpart exists | 22 | 7.9% |
| `EXPOSED` | unstripped | 110 | 39.6% |
| `INHERITED` | unstripped (inherited via provenance.inputs) | 23 | 8.3% |
| `UNKNOWN` | undetermined (no provenance.script) | 38 | 13.7% |
| | **IMMUNE + CLEAN** | **85** | 30.6% |
| | **EXPOSED + INHERITED** | **133** | 47.8% |

### 7a. Full per-file table

| results file | class | label | reason recorded by the tool |
|---|---|---|---|
| `results/e35_containment.json` | `IMMUNE` | not-applicable | t35_containment.py: [producer inferred from path] never calls load_eval; no readout over the battery |
| `results/e35_containment_shard0.json` | `IMMUNE` | not-applicable | t35_containment.py: [producer inferred from path] never calls load_eval; no readout over the battery |
| `results/e35_containment_smoke.json` | `IMMUNE` | not-applicable | t35_containment.py: [producer inferred from path] never calls load_eval; no readout over the battery |
| `results/e35_smoke_box.json` | `IMMUNE` | not-applicable | t35_containment.py: [producer inferred from path] never calls load_eval; no readout over the battery |
| `results/e48_competence_gate_410m.json` | `IMMUNE` | not-applicable | t48_competence_gate.py: never calls load_eval; no readout over the battery |
| `results/e64_instrument_cost.json` | `IMMUNE` | not-applicable | t64_instrument_cost.py: never calls load_eval; no readout over the battery |
| `results/postreview_completion.json` | `IMMUNE` | not-applicable | postreview_completion.py: never calls load_eval; no readout over the battery |
| `results/r8_ladder_flatness.json` | `IMMUNE` | not-applicable | r8_ladder_flatness.py: never calls load_eval; no readout over the battery |
| `results/r9_permutation_calibrated_min.json` | `IMMUNE` | not-applicable | r9_permutation_calibrated_min.py: never calls load_eval; no readout over the battery |
| `results/t0_smoke_160m.json` | `IMMUNE` | not-applicable | t0_smoke.py: [producer inferred from path] never calls load_eval; no readout over the battery |
| `results/t0_smoke_1b.json` | `IMMUNE` | not-applicable | t0_smoke.py: [producer inferred from path] never calls load_eval; no readout over the battery |
| `results/t0_smoke_410m.json` | `IMMUNE` | not-applicable | t0_smoke.py: [producer inferred from path] never calls load_eval; no readout over the battery |
| `results/t0_smoke_70m.json` | `IMMUNE` | not-applicable | t0_smoke.py: [producer inferred from path] never calls load_eval; no readout over the battery |
| `results/t10_target_layer_160m.json` | `IMMUNE` | not-applicable | t10_target_layer.py: [producer inferred from path] never calls load_eval; no readout over the battery |
| `results/t10_target_layer_410m.json` | `IMMUNE` | not-applicable | t10_target_layer.py: [producer inferred from path] never calls load_eval; no readout over the battery |
| `results/t10_target_layer_70m.json` | `IMMUNE` | not-applicable | t10_target_layer.py: [producer inferred from path] never calls load_eval; no readout over the battery |
| `results/t11_fit_distribution_shortskip_70m.json` | `IMMUNE` | not-applicable | t11_fit_distribution.py: [producer inferred from path] never calls load_eval; no readout over the battery |
| `results/t11_multihop_backfill_70m.json` | `IMMUNE` | not-applicable | t11_fit_distribution.py: [producer inferred from path] never calls load_eval; no readout over the battery |
| `results/t11b_refit_feasibility.json` | `IMMUNE` | not-applicable | t11_fit_distribution.py: [producer inferred from path] never calls load_eval; no readout over the battery |
| `results/t12_concept_hessian_410m.json` | `IMMUNE` | not-applicable | t12_concept_hessian.py: [producer inferred from path] never calls load_eval; no readout over the battery |
| `results/t14_dispersion_ladder.json` | `IMMUNE` | not-applicable | t14_dispersion_ladder.py: [producer inferred from path] never calls load_eval; no readout over the battery |
| `results/t14b_dispersion_scaling.json` | `IMMUNE` | not-applicable | t14_dispersion_ladder.py: [producer inferred from path] never calls load_eval; no readout over the battery |
| `results/t16_robust_aggregation_1b.json` | `IMMUNE` | not-applicable | t16_robust_aggregation.py: [producer inferred from path] never calls load_eval; no readout over the battery |
| `results/t16b_reads_mean_1b.json` | `IMMUNE` | not-applicable | t16_robust_aggregation.py: [producer inferred from path] never calls load_eval; no readout over the battery |
| `results/t16b_reads_median_1b.json` | `IMMUNE` | not-applicable | t16_robust_aggregation.py: [producer inferred from path] never calls load_eval; no readout over the battery |
| `results/t18_n_sweep_410m.json` | `IMMUNE` | not-applicable | t18_n_sweep.py: [producer inferred from path] never calls load_eval; no readout over the battery |
| `results/t19_skipfirst_410m.json` | `IMMUNE` | not-applicable | t19_skipfirst_sweep.py: [producer inferred from path] never calls load_eval; no readout over the battery |
| `results/t3_160m_db128.json` | `IMMUNE` | not-applicable | t3_read_audit.py: [producer inferred from path] never calls load_eval; no readout over the battery |
| `results/t3_410m_FIXED.json` | `IMMUNE` | not-applicable | t3_read_audit.py: [producer inferred from path] never calls load_eval; no readout over the battery |
| `results/t3_410m_n200.json` | `IMMUNE` | not-applicable | t3_read_audit.py: [producer inferred from path] never calls load_eval; no readout over the battery |
| `results/t3_70m_db128.json` | `IMMUNE` | not-applicable | t3_read_audit.py: [producer inferred from path] never calls load_eval; no readout over the battery |
| `results/t3_70m_n200.json` | `IMMUNE` | not-applicable | t3_read_audit.py: [producer inferred from path] never calls load_eval; no readout over the battery |
| `results/t3_smoke_70m.json` | `IMMUNE` | not-applicable | t3_read_audit.py: [producer inferred from path] never calls load_eval; no readout over the battery |
| `results/t4_160m_db128.json` | `IMMUNE` | not-applicable | t4_geometry.py: [producer inferred from path] never calls load_eval; no readout over the battery |
| `results/t4_410m_db128.json` | `IMMUNE` | not-applicable | t4_geometry.py: [producer inferred from path] never calls load_eval; no readout over the battery |
| `results/t4_70m_db128.json` | `IMMUNE` | not-applicable | t4_geometry.py: [producer inferred from path] never calls load_eval; no readout over the battery |
| `results/t4_70m_n200.json` | `IMMUNE` | not-applicable | t4_geometry.py: [producer inferred from path] never calls load_eval; no readout over the battery |
| `results/t4_smoke_70m.json` | `IMMUNE` | not-applicable | t4_geometry.py: [producer inferred from path] never calls load_eval; no readout over the battery |
| `results/t5_write_410m.json` | `IMMUNE` | not-applicable | t5_write_battery.py: [producer inferred from path] never calls load_eval; no readout over the battery |
| `results/t5a_capability_160m.json` | `IMMUNE` | not-applicable | t5_write_battery.py: [producer inferred from path] never calls load_eval; no readout over the battery |
| `results/t5a_capability_160m_v2.json` | `IMMUNE` | not-applicable | t5_write_battery.py: [producer inferred from path] never calls load_eval; no readout over the battery |
| `results/t5a_capability_1b.json` | `IMMUNE` | not-applicable | t5_write_battery.py: [producer inferred from path] never calls load_eval; no readout over the battery |
| `results/t5a_capability_410m.json` | `IMMUNE` | not-applicable | t5_write_battery.py: [producer inferred from path] never calls load_eval; no readout over the battery |
| `results/t5a_capability_410m_v2.json` | `IMMUNE` | not-applicable | t5_write_battery.py: [producer inferred from path] never calls load_eval; no readout over the battery |
| `results/t5a_capability_70m.json` | `IMMUNE` | not-applicable | t5_write_battery.py: [producer inferred from path] never calls load_eval; no readout over the battery |
| `results/t5a_capability_70m_v2.json` | `IMMUNE` | not-applicable | t5_write_battery.py: [producer inferred from path] never calls load_eval; no readout over the battery |
| `results/t8_probe_swap_410m.json` | `IMMUNE` | not-applicable | t8_probe_swap.py: [producer inferred from path] never calls load_eval; no readout over the battery |
| `results/t9_n_convergence_160m.json` | `IMMUNE` | not-applicable | t9_n_convergence.py: [producer inferred from path] never calls load_eval; no readout over the battery |
| `results/t9_n_convergence_410m.json` | `IMMUNE` | not-applicable | t9_n_convergence.py: [producer inferred from path] never calls load_eval; no readout over the battery |
| `results/t9_n_convergence_70m.json` | `IMMUNE` | not-applicable | t9_n_convergence.py: [producer inferred from path] never calls load_eval; no readout over the battery |
| `results/e13_rank_target_layer.json` | `CLEAN` | stripped | t13_bootstrap_controls.py: [producer inferred from path] loads the battery and applies .rstrip() to the prompt |
| `results/e48_crossover_410m_rstrip.json` | `CLEAN` | stripped | t48_crossover.py: strips only when --rstrip is passed; unstripped by default; this file records rstrip_arm=true |
| `results/e60_fitter_determinism.json` | `CLEAN` | stripped | t60_fitter_determinism.py: loads the battery and applies .rstrip() to the prompt |
| `results/t13_transport_controls_160m.json` | `CLEAN` | stripped | t13_bootstrap_controls.py: [producer inferred from path] loads the battery and applies .rstrip() to the prompt |
| `results/t13_transport_controls_410m.json` | `CLEAN` | stripped | t13_bootstrap_controls.py: [producer inferred from path] loads the battery and applies .rstrip() to the prompt |
| `results/t13_transport_controls_70m.json` | `CLEAN` | stripped | t13_bootstrap_controls.py: [producer inferred from path] loads the battery and applies .rstrip() to the prompt |
| `results/t13b_bootstrap_controls_160m.json` | `CLEAN` | stripped | t13_bootstrap_controls.py: [producer inferred from path] loads the battery and applies .rstrip() to the prompt |
| `results/t13b_bootstrap_controls_410m.json` | `CLEAN` | stripped | t13_bootstrap_controls.py: [producer inferred from path] loads the battery and applies .rstrip() to the prompt |
| `results/t13b_bootstrap_controls_70m.json` | `CLEAN` | stripped | t13_bootstrap_controls.py: [producer inferred from path] loads the battery and applies .rstrip() to the prompt |
| `results/t15_shuffle_diagnostic_410m.json` | `CLEAN` | stripped | t15_shuffle_diagnostic.py: [producer inferred from path] loads the battery and applies .rstrip() to the prompt |
| `results/t15b_partition_aggregation_dependence.json` | `CLEAN` | stripped | t15_shuffle_diagnostic.py: [producer inferred from path] loads the battery and applies .rstrip() to the prompt |
| `results/t17_reaggregate_160m.json` | `CLEAN` | stripped | t17_reaggregate.py: [producer inferred from path] loads the battery and applies .rstrip() to the prompt |
| `results/t17_reaggregate_410m.json` | `CLEAN` | stripped | t17_reaggregate.py: [producer inferred from path] loads the battery and applies .rstrip() to the prompt |
| `results/t20_ablation_kl_160m.json` | `CLEAN` | stripped | t20_ablation_kl.py: [producer inferred from path] loads the battery and applies .rstrip() to the prompt |
| `results/t20_ablation_kl_410m.json` | `CLEAN` | stripped | t20_ablation_kl.py: [producer inferred from path] loads the battery and applies .rstrip() to the prompt |
| `results/t20_ablation_kl_70m.json` | `CLEAN` | stripped | t20_ablation_kl.py: [producer inferred from path] loads the battery and applies .rstrip() to the prompt |
| `results/t20_ablation_kl_70m_Pcode.json` | `CLEAN` | stripped | t20_ablation_kl.py: [producer inferred from path] loads the battery and applies .rstrip() to the prompt |
| `results/t20_ablation_kl_70m_Ppile.json` | `CLEAN` | stripped | t20_ablation_kl.py: [producer inferred from path] loads the battery and applies .rstrip() to the prompt |
| `results/t20_ablation_kl_70m_Pwikitext.json` | `CLEAN` | stripped | t20_ablation_kl.py: [producer inferred from path] loads the battery and applies .rstrip() to the prompt |
| `results/t22_bootstrap_ci_160m.json` | `CLEAN` | stripped | t22_bootstrap_ci.py: [producer inferred from path] loads the battery and applies .rstrip() to the prompt |
| `results/t22_bootstrap_ci_410m.json` | `CLEAN` | stripped | t22_bootstrap_ci.py: [producer inferred from path] loads the battery and applies .rstrip() to the prompt |
| `results/t22_bootstrap_ci_persist_160m.json` | `CLEAN` | stripped | t22_bootstrap_ci.py: [producer inferred from path] loads the battery and applies .rstrip() to the prompt |
| `results/t22_bootstrap_ci_persist_410m.json` | `CLEAN` | stripped | t22_bootstrap_ci.py: [producer inferred from path] loads the battery and applies .rstrip() to the prompt |
| `results/t23_pq_ladder_410m.json` | `CLEAN` | stripped | t23_pq_ladder.py: [producer inferred from path] loads the battery and applies .rstrip() to the prompt |
| `results/t23_pq_ladder_410m_LENGTHMATCHED.json` | `CLEAN` | stripped | t23_pq_ladder.py: [producer inferred from path] loads the battery and applies .rstrip() to the prompt |
| `results/t23_pq_ladder_70m.json` | `CLEAN` | stripped | t23_pq_ladder.py: [producer inferred from path] loads the battery and applies .rstrip() to the prompt |
| `results/t23_pq_ladder_70m_LENGTHMATCHED.json` | `CLEAN` | stripped | t23_pq_ladder.py: [producer inferred from path] loads the battery and applies .rstrip() to the prompt |
| `results/t23_pq_ladder_70m_wiki_pile.json` | `CLEAN` | stripped | t23_pq_ladder.py: [producer inferred from path] loads the battery and applies .rstrip() to the prompt |
| `results/t7_bootstrap_160m.json` | `CLEAN` | stripped | t7_bootstrap_audit.py: [producer inferred from path] loads the battery and applies .rstrip() to the prompt |
| `results/t7_bootstrap_410m.json` | `CLEAN` | stripped | t7_bootstrap_audit.py: [producer inferred from path] loads the battery and applies .rstrip() to the prompt |
| `results/t7_bootstrap_70m.json` | `CLEAN` | stripped | t7_bootstrap_audit.py: [producer inferred from path] loads the battery and applies .rstrip() to the prompt |
| `results/t7_lens_comparison_160m.json` | `CLEAN` | stripped | t7_bootstrap_audit.py: [producer inferred from path] loads the battery and applies .rstrip() to the prompt |
| `results/t7_lens_comparison_410m.json` | `CLEAN` | stripped | t7_bootstrap_audit.py: [producer inferred from path] loads the battery and applies .rstrip() to the prompt |
| `results/t7_lens_comparison_70m.json` | `CLEAN` | stripped | t7_bootstrap_audit.py: [producer inferred from path] loads the battery and applies .rstrip() to the prompt |
| `results/t7_smoke_410m.json` | `CLEAN` | stripped | t7_bootstrap_audit.py: [producer inferred from path] loads the battery and applies .rstrip() to the prompt |
| `results/e33_logit_baseline_410m_v2.json` | `RESCORED` | unstripped, corrected counterpart exists | t33_logit_baseline.py: [producer inferred from path] loads the battery and does NOT strip the prompt |
| `results/e54_aggregation_audit.json` | `RESCORED` | unstripped, corrected counterpart exists | reads results/e33_logit_baseline_410m_v2.json, which is exposed |
| `results/e54_aggregation_audit_rstrip.json` | `RESCORED` | unstripped, corrected counterpart exists | reads results/e33_logit_baseline_410m_v2.json, which is exposed |
| `results/e54_aggregation_audit_rstrip_v2.json` | `RESCORED` | unstripped, corrected counterpart exists | reads results/e33_logit_baseline_410m_v2.json, which is exposed |
| `results/ladder410/ladder_Github_s0.json` | `RESCORED` | unstripped, corrected counterpart exists | e28_ladder_410m.py: [producer inferred from path] strips only when --rstrip is passed; unstripped by default; this file records rstrip_arm=None |
| `results/ladder410/ladder_Github_s1.json` | `RESCORED` | unstripped, corrected counterpart exists | e28_ladder_410m.py: [producer inferred from path] strips only when --rstrip is passed; unstripped by default; this file records rstrip_arm=None |
| `results/ladder410/ladder_Github_s2.json` | `RESCORED` | unstripped, corrected counterpart exists | e28_ladder_410m.py: [producer inferred from path] strips only when --rstrip is passed; unstripped by default; this file records rstrip_arm=None |
| `results/ladder410/ladder_Pile-CC_s0.json` | `RESCORED` | unstripped, corrected counterpart exists | e28_ladder_410m.py: [producer inferred from path] strips only when --rstrip is passed; unstripped by default; this file records rstrip_arm=None |
| `results/ladder410/ladder_Pile-CC_s1.json` | `RESCORED` | unstripped, corrected counterpart exists | e28_ladder_410m.py: [producer inferred from path] strips only when --rstrip is passed; unstripped by default; this file records rstrip_arm=None |
| `results/ladder410/ladder_Pile-CC_s2.json` | `RESCORED` | unstripped, corrected counterpart exists | e28_ladder_410m.py: [producer inferred from path] strips only when --rstrip is passed; unstripped by default; this file records rstrip_arm=None |
| `results/ladder410/ladder_StackExchange_s0.json` | `RESCORED` | unstripped, corrected counterpart exists | e28_ladder_410m.py: [producer inferred from path] strips only when --rstrip is passed; unstripped by default; this file records rstrip_arm=None |
| `results/ladder410/ladder_StackExchange_s1.json` | `RESCORED` | unstripped, corrected counterpart exists | e28_ladder_410m.py: [producer inferred from path] strips only when --rstrip is passed; unstripped by default; this file records rstrip_arm=None |
| `results/ladder410/ladder_StackExchange_s2.json` | `RESCORED` | unstripped, corrected counterpart exists | e28_ladder_410m.py: [producer inferred from path] strips only when --rstrip is passed; unstripped by default; this file records rstrip_arm=None |
| `results/ladder410/ladder_USPTO_Backgrounds_s0.json` | `RESCORED` | unstripped, corrected counterpart exists | e28_ladder_410m.py: [producer inferred from path] strips only when --rstrip is passed; unstripped by default; this file records rstrip_arm=None |
| `results/ladder410/ladder_USPTO_Backgrounds_s1.json` | `RESCORED` | unstripped, corrected counterpart exists | e28_ladder_410m.py: [producer inferred from path] strips only when --rstrip is passed; unstripped by default; this file records rstrip_arm=None |
| `results/ladder410/ladder_USPTO_Backgrounds_s2.json` | `RESCORED` | unstripped, corrected counterpart exists | e28_ladder_410m.py: [producer inferred from path] strips only when --rstrip is passed; unstripped by default; this file records rstrip_arm=None |
| `results/ladder410/ladder_Wikipedia_en_s0.json` | `RESCORED` | unstripped, corrected counterpart exists | e28_ladder_410m.py: [producer inferred from path] strips only when --rstrip is passed; unstripped by default; this file records rstrip_arm=None |
| `results/ladder410/ladder_Wikipedia_en_s1.json` | `RESCORED` | unstripped, corrected counterpart exists | e28_ladder_410m.py: [producer inferred from path] strips only when --rstrip is passed; unstripped by default; this file records rstrip_arm=None |
| `results/ladder410/ladder_Wikipedia_en_s2.json` | `RESCORED` | unstripped, corrected counterpart exists | e28_ladder_410m.py: [producer inferred from path] strips only when --rstrip is passed; unstripped by default; this file records rstrip_arm=None |
| `results/ladder410_cpu/e51_interaction_cpu.json` | `RESCORED` | unstripped, corrected counterpart exists | reads results/ladder1b/tv_Github_s0.json, which is exposed |
| `results/ladder410_cpu/e53_ladder_summary_cpu.json` | `RESCORED` | unstripped, corrected counterpart exists | reads results/e54_aggregation_audit.json, which is exposed |
| `results/ladder410_cpu_rescore/ladder_Github_s0.json` | `RESCORED` | unstripped, corrected counterpart exists | e28_ladder_410m.py: [producer inferred from path] strips only when --rstrip is passed; unstripped by default; this file records rstrip_arm=None |
| `results/d1_min_union_diagnostic_410m.json` | `EXPOSED` | unstripped | d1_min_union_diagnostic.py: loads the battery and does NOT strip the prompt |
| `results/e31_local_bakeoff_410m.json` | `EXPOSED` | unstripped | t31_local_bakeoff.py: [producer inferred from path] loads the battery and does NOT strip the prompt |
| `results/e33_logit_baseline_410m.json` | `EXPOSED` | unstripped | t33_logit_baseline.py: [producer inferred from path] loads the battery and does NOT strip the prompt |
| `results/e34a_dact_vs_floor_410m.json` | `EXPOSED` | unstripped | t34_dact_vs_floor.py: [producer inferred from path] loads the battery and does NOT strip the prompt |
| `results/e34b_jeval_dact_410m.json` | `EXPOSED` | unstripped | t34_dact_vs_floor.py: [producer inferred from path] loads the battery and does NOT strip the prompt |
| `results/e36_qladder_410m.json` | `EXPOSED` | unstripped | t36_qladder.py: strips only when --rstrip is passed; unstripped by default; this file records rstrip_arm=None |
| `results/e36_qladder_410m_c1arm.json` | `EXPOSED` | unstripped | t36_qladder.py: strips only when --rstrip is passed; unstripped by default; this file records rstrip_arm=None |
| `results/e36_qladder_410m_rstrip.json` | `EXPOSED` | unstripped | t36_qladder.py: strips only when --rstrip is passed; unstripped by default; this file records rstrip_arm=None |
| `results/e37_rank_ablation_160m_wikitext.json` | `EXPOSED` | unstripped | t37_rank_ablation.py: [producer inferred from path] loads the battery and does NOT strip the prompt |
| `results/e37_rank_ablation_410m.json` | `EXPOSED` | unstripped | t37_rank_ablation.py: [producer inferred from path] loads the battery and does NOT strip the prompt |
| `results/e37_rank_ablation_410m_wikitext.json` | `EXPOSED` | unstripped | t37_rank_ablation.py: [producer inferred from path] loads the battery and does NOT strip the prompt |
| `results/e37_rank_ablation_70m_wikitext.json` | `EXPOSED` | unstripped | t37_rank_ablation.py: [producer inferred from path] loads the battery and does NOT strip the prompt |
| `results/e38_jgeometry.json` | `EXPOSED` | unstripped | t38_jgeometry.py: [producer inferred from path] loads the battery and does NOT strip the prompt |
| `results/e44_dread_410m.json` | `EXPOSED` | unstripped | t44_concept_energy.py: [producer inferred from path] loads the battery and does NOT strip the prompt |
| `results/e48/tv_INSTREAM_Github_s0.json` | `EXPOSED` | unstripped | trainval.py: [producer inferred from path] loads the battery and does NOT strip the prompt |
| `results/e48/tv_INSTREAM_Github_s1.json` | `EXPOSED` | unstripped | trainval.py: [producer inferred from path] loads the battery and does NOT strip the prompt |
| `results/e48/tv_INSTREAM_Github_s2.json` | `EXPOSED` | unstripped | trainval.py: [producer inferred from path] loads the battery and does NOT strip the prompt |
| `results/e48/tv_INSTREAM_Pile-CC_s0.json` | `EXPOSED` | unstripped | trainval.py: [producer inferred from path] loads the battery and does NOT strip the prompt |
| `results/e48/tv_INSTREAM_Pile-CC_s1.json` | `EXPOSED` | unstripped | trainval.py: [producer inferred from path] loads the battery and does NOT strip the prompt |
| `results/e48/tv_INSTREAM_Pile-CC_s2.json` | `EXPOSED` | unstripped | trainval.py: [producer inferred from path] loads the battery and does NOT strip the prompt |
| `results/e48/tv_INSTREAM_StackExchange_s0.json` | `EXPOSED` | unstripped | trainval.py: [producer inferred from path] loads the battery and does NOT strip the prompt |
| `results/e48/tv_INSTREAM_StackExchange_s1.json` | `EXPOSED` | unstripped | trainval.py: [producer inferred from path] loads the battery and does NOT strip the prompt |
| `results/e48/tv_INSTREAM_StackExchange_s2.json` | `EXPOSED` | unstripped | trainval.py: [producer inferred from path] loads the battery and does NOT strip the prompt |
| `results/e48/tv_INSTREAM_USPTO_Backgrounds_s0.json` | `EXPOSED` | unstripped | trainval.py: [producer inferred from path] loads the battery and does NOT strip the prompt |
| `results/e48/tv_INSTREAM_USPTO_Backgrounds_s1.json` | `EXPOSED` | unstripped | trainval.py: [producer inferred from path] loads the battery and does NOT strip the prompt |
| `results/e48/tv_INSTREAM_USPTO_Backgrounds_s2.json` | `EXPOSED` | unstripped | trainval.py: [producer inferred from path] loads the battery and does NOT strip the prompt |
| `results/e48/tv_INSTREAM_Wikipedia_en_s0.json` | `EXPOSED` | unstripped | trainval.py: [producer inferred from path] loads the battery and does NOT strip the prompt |
| `results/e48/tv_INSTREAM_Wikipedia_en_s1.json` | `EXPOSED` | unstripped | trainval.py: [producer inferred from path] loads the battery and does NOT strip the prompt |
| `results/e48/tv_INSTREAM_Wikipedia_en_s2.json` | `EXPOSED` | unstripped | trainval.py: [producer inferred from path] loads the battery and does NOT strip the prompt |
| `results/e48/tv_OOD_CommonPile_s0.json` | `EXPOSED` | unstripped | trainval.py: [producer inferred from path] loads the battery and does NOT strip the prompt |
| `results/e48/tv_OOD_CommonPile_s1.json` | `EXPOSED` | unstripped | trainval.py: [producer inferred from path] loads the battery and does NOT strip the prompt |
| `results/e48/tv_OOD_CommonPile_s2.json` | `EXPOSED` | unstripped | trainval.py: [producer inferred from path] loads the battery and does NOT strip the prompt |
| `results/e48/tv_OOD_News_2024_dedup_s0.json` | `EXPOSED` | unstripped | trainval.py: [producer inferred from path] loads the battery and does NOT strip the prompt |
| `results/e48/tv_OOD_News_2024_dedup_s1.json` | `EXPOSED` | unstripped | trainval.py: [producer inferred from path] loads the battery and does NOT strip the prompt |
| `results/e48/tv_OOD_News_2024_dedup_s2.json` | `EXPOSED` | unstripped | trainval.py: [producer inferred from path] loads the battery and does NOT strip the prompt |
| `results/e48/tv_OOD_News_2024_s0.json` | `EXPOSED` | unstripped | trainval.py: [producer inferred from path] loads the battery and does NOT strip the prompt |
| `results/e48/tv_OOD_News_2024_s1.json` | `EXPOSED` | unstripped | trainval.py: [producer inferred from path] loads the battery and does NOT strip the prompt |
| `results/e48/tv_OOD_News_2024_s2.json` | `EXPOSED` | unstripped | trainval.py: [producer inferred from path] loads the battery and does NOT strip the prompt |
| `results/e48/tv_OOD_arXiv_2023_s0.json` | `EXPOSED` | unstripped | trainval.py: [producer inferred from path] loads the battery and does NOT strip the prompt |
| `results/e48/tv_OOD_arXiv_2023_s1.json` | `EXPOSED` | unstripped | trainval.py: [producer inferred from path] loads the battery and does NOT strip the prompt |
| `results/e48/tv_OOD_arXiv_2023_s2.json` | `EXPOSED` | unstripped | trainval.py: [producer inferred from path] loads the battery and does NOT strip the prompt |
| `results/e48_crossover_410m.json` | `EXPOSED` | unstripped | t48_crossover.py: strips only when --rstrip is passed; unstripped by default; this file records rstrip_arm=False |
| `results/e52_factorial_410m.json` | `EXPOSED` | unstripped | t52_factorial.py: strips only when --rstrip is passed; unstripped by default; this file records rstrip_arm=None |
| `results/e52_factorial_410m_pooled.json` | `EXPOSED` | unstripped | t52_factorial.py: strips only when --rstrip is passed; unstripped by default; this file records rstrip_arm=None |
| `results/e52_factorial_410m_rerun.json` | `EXPOSED` | unstripped | t52_factorial.py: strips only when --rstrip is passed; unstripped by default; this file records rstrip_arm=None |
| `results/e52_factorial_410m_rstrip.json` | `EXPOSED` | unstripped | t52_factorial.py: strips only when --rstrip is passed; unstripped by default; this file records rstrip_arm=None |
| `results/e52_factorial_410m_rstrip_w1.json` | `EXPOSED` | unstripped | t52_factorial.py: strips only when --rstrip is passed; unstripped by default; this file records rstrip_arm=None |
| `results/e52_factorial_410m_rstrip_w2.json` | `EXPOSED` | unstripped | t52_factorial.py: strips only when --rstrip is passed; unstripped by default; this file records rstrip_arm=None |
| `results/e52_factorial_410m_rstrip_w8.json` | `EXPOSED` | unstripped | t52_factorial.py: strips only when --rstrip is passed; unstripped by default; this file records rstrip_arm=None |
| `results/e57_factorial_cells_410m.json` | `EXPOSED` | unstripped | t52_factorial.py: strips only when --rstrip is passed; unstripped by default; this file records rstrip_arm=None |
| `results/e57_factorial_cells_410m_pooled.json` | `EXPOSED` | unstripped | t52_factorial.py: strips only when --rstrip is passed; unstripped by default; this file records rstrip_arm=None |
| `results/e57_factorial_cells_410m_rstrip.json` | `EXPOSED` | unstripped | t52_factorial.py: strips only when --rstrip is passed; unstripped by default; this file records rstrip_arm=None |
| `results/e58_algebra_audit.json` | `EXPOSED` | unstripped | t58_algebra_audit.py: loads the battery and does NOT strip the prompt |
| `results/e59_read_dose_410m.json` | `EXPOSED` | unstripped | t59_read_dose.py: loads the battery and does NOT strip the prompt |
| `results/e61/tv_rand_Github_s0.json` | `EXPOSED` | unstripped | trainval.py: [producer inferred from path] loads the battery and does NOT strip the prompt |
| `results/e61/tv_rand_Github_s1.json` | `EXPOSED` | unstripped | trainval.py: [producer inferred from path] loads the battery and does NOT strip the prompt |
| `results/e61/tv_rand_Github_s2.json` | `EXPOSED` | unstripped | trainval.py: [producer inferred from path] loads the battery and does NOT strip the prompt |
| `results/e61/tv_rand_Pile-CC_s0.json` | `EXPOSED` | unstripped | trainval.py: [producer inferred from path] loads the battery and does NOT strip the prompt |
| `results/e61/tv_rand_Pile-CC_s1.json` | `EXPOSED` | unstripped | trainval.py: [producer inferred from path] loads the battery and does NOT strip the prompt |
| `results/e61/tv_rand_Pile-CC_s2.json` | `EXPOSED` | unstripped | trainval.py: [producer inferred from path] loads the battery and does NOT strip the prompt |
| `results/e61/tv_rand_USPTO_Backgrounds_s0.json` | `EXPOSED` | unstripped | trainval.py: [producer inferred from path] loads the battery and does NOT strip the prompt |
| `results/e61/tv_rand_USPTO_Backgrounds_s1.json` | `EXPOSED` | unstripped | trainval.py: [producer inferred from path] loads the battery and does NOT strip the prompt |
| `results/e61/tv_rand_USPTO_Backgrounds_s2.json` | `EXPOSED` | unstripped | trainval.py: [producer inferred from path] loads the battery and does NOT strip the prompt |
| `results/e61/tv_real_USPTO_Backgrounds_s0.json` | `EXPOSED` | unstripped | trainval.py: [producer inferred from path] loads the battery and does NOT strip the prompt |
| `results/e65_ckpt_geometry_410m.json` | `EXPOSED` | unstripped | t65_ckpt_geometry.py: loads the battery and does NOT strip the prompt |
| `results/e65_ckpt_readout_1b.json` | `EXPOSED` | unstripped | t65_ckpt_readout.py: loads the battery and does NOT strip the prompt |
| `results/e65_ckpt_readout_410m.json` | `EXPOSED` | unstripped | t65_ckpt_readout.py: loads the battery and does NOT strip the prompt |
| `results/e65_ckpt_readout_410m_trainval.json` | `EXPOSED` | unstripped | t65_ckpt_readout.py: loads the battery and does NOT strip the prompt |
| `results/e66_fitter_equivalence_cuda.json` | `EXPOSED` | unstripped | t66_fitter_equivalence_cuda.py: loads the battery and does NOT strip the prompt |
| `results/edata1_item_count_reconciliation.json` | `EXPOSED` | unstripped | d1_min_union_diagnostic.py: [producer inferred from path] loads the battery and does NOT strip the prompt |
| `results/en1_operator_error_at_n200.json` | `EXPOSED` | unstripped | d1_min_union_diagnostic.py: [producer inferred from path] loads the battery and does NOT strip the prompt |
| `results/ladder1b/tv_Github_s0.json` | `EXPOSED` | unstripped | e28_ladder_410m.py: [producer inferred from path] strips only when --rstrip is passed; unstripped by default; this file records rstrip_arm=None |
| `results/ladder1b/tv_Github_s1.json` | `EXPOSED` | unstripped | e28_ladder_410m.py: [producer inferred from path] strips only when --rstrip is passed; unstripped by default; this file records rstrip_arm=None |
| `results/ladder1b/tv_Github_s2.json` | `EXPOSED` | unstripped | e28_ladder_410m.py: [producer inferred from path] strips only when --rstrip is passed; unstripped by default; this file records rstrip_arm=None |
| `results/ladder1b/tv_Pile-CC_s0.json` | `EXPOSED` | unstripped | e28_ladder_410m.py: [producer inferred from path] strips only when --rstrip is passed; unstripped by default; this file records rstrip_arm=None |
| `results/ladder1b/tv_Pile-CC_s1.json` | `EXPOSED` | unstripped | e28_ladder_410m.py: [producer inferred from path] strips only when --rstrip is passed; unstripped by default; this file records rstrip_arm=None |
| `results/ladder1b/tv_Pile-CC_s2.json` | `EXPOSED` | unstripped | e28_ladder_410m.py: [producer inferred from path] strips only when --rstrip is passed; unstripped by default; this file records rstrip_arm=None |
| `results/ladder1b/tv_StackExchange_s0.json` | `EXPOSED` | unstripped | e28_ladder_410m.py: [producer inferred from path] strips only when --rstrip is passed; unstripped by default; this file records rstrip_arm=None |
| `results/ladder1b/tv_StackExchange_s1.json` | `EXPOSED` | unstripped | e28_ladder_410m.py: [producer inferred from path] strips only when --rstrip is passed; unstripped by default; this file records rstrip_arm=None |
| `results/ladder1b/tv_StackExchange_s2.json` | `EXPOSED` | unstripped | e28_ladder_410m.py: [producer inferred from path] strips only when --rstrip is passed; unstripped by default; this file records rstrip_arm=None |
| `results/ladder1b/tv_USPTO_Backgrounds_s0.json` | `EXPOSED` | unstripped | e28_ladder_410m.py: [producer inferred from path] strips only when --rstrip is passed; unstripped by default; this file records rstrip_arm=None |
| `results/ladder1b/tv_USPTO_Backgrounds_s1.json` | `EXPOSED` | unstripped | e28_ladder_410m.py: [producer inferred from path] strips only when --rstrip is passed; unstripped by default; this file records rstrip_arm=None |
| `results/ladder1b/tv_USPTO_Backgrounds_s2.json` | `EXPOSED` | unstripped | e28_ladder_410m.py: [producer inferred from path] strips only when --rstrip is passed; unstripped by default; this file records rstrip_arm=None |
| `results/ladder1b/tv_Wikipedia_en_s0.json` | `EXPOSED` | unstripped | e28_ladder_410m.py: [producer inferred from path] strips only when --rstrip is passed; unstripped by default; this file records rstrip_arm=None |
| `results/ladder1b/tv_Wikipedia_en_s1.json` | `EXPOSED` | unstripped | e28_ladder_410m.py: [producer inferred from path] strips only when --rstrip is passed; unstripped by default; this file records rstrip_arm=None |
| `results/ladder1b/tv_Wikipedia_en_s2.json` | `EXPOSED` | unstripped | e28_ladder_410m.py: [producer inferred from path] strips only when --rstrip is passed; unstripped by default; this file records rstrip_arm=None |
| `results/ladder1b_b613/tv_Github_s0.json` | `EXPOSED` | unstripped | e28_ladder_410m.py: [producer inferred from path] strips only when --rstrip is passed; unstripped by default; this file records rstrip_arm=None |
| `results/ladder1b_b613/tv_Github_s1.json` | `EXPOSED` | unstripped | e28_ladder_410m.py: [producer inferred from path] strips only when --rstrip is passed; unstripped by default; this file records rstrip_arm=None |
| `results/ladder1b_b613/tv_Github_s2.json` | `EXPOSED` | unstripped | e28_ladder_410m.py: [producer inferred from path] strips only when --rstrip is passed; unstripped by default; this file records rstrip_arm=None |
| `results/ladder1b_b613/tv_Pile-CC_s0.json` | `EXPOSED` | unstripped | e28_ladder_410m.py: [producer inferred from path] strips only when --rstrip is passed; unstripped by default; this file records rstrip_arm=None |
| `results/ladder1b_b613/tv_Pile-CC_s1.json` | `EXPOSED` | unstripped | e28_ladder_410m.py: [producer inferred from path] strips only when --rstrip is passed; unstripped by default; this file records rstrip_arm=None |
| `results/ladder1b_b613/tv_Pile-CC_s2.json` | `EXPOSED` | unstripped | e28_ladder_410m.py: [producer inferred from path] strips only when --rstrip is passed; unstripped by default; this file records rstrip_arm=None |
| `results/ladder1b_b613/tv_StackExchange_s0.json` | `EXPOSED` | unstripped | e28_ladder_410m.py: [producer inferred from path] strips only when --rstrip is passed; unstripped by default; this file records rstrip_arm=None |
| `results/ladder1b_b613/tv_StackExchange_s1.json` | `EXPOSED` | unstripped | e28_ladder_410m.py: [producer inferred from path] strips only when --rstrip is passed; unstripped by default; this file records rstrip_arm=None |
| `results/ladder1b_b613/tv_StackExchange_s2.json` | `EXPOSED` | unstripped | e28_ladder_410m.py: [producer inferred from path] strips only when --rstrip is passed; unstripped by default; this file records rstrip_arm=None |
| `results/ladder1b_b613/tv_USPTO_Backgrounds_s0.json` | `EXPOSED` | unstripped | e28_ladder_410m.py: [producer inferred from path] strips only when --rstrip is passed; unstripped by default; this file records rstrip_arm=None |
| `results/ladder1b_b613/tv_USPTO_Backgrounds_s1.json` | `EXPOSED` | unstripped | e28_ladder_410m.py: [producer inferred from path] strips only when --rstrip is passed; unstripped by default; this file records rstrip_arm=None |
| `results/ladder1b_b613/tv_USPTO_Backgrounds_s2.json` | `EXPOSED` | unstripped | e28_ladder_410m.py: [producer inferred from path] strips only when --rstrip is passed; unstripped by default; this file records rstrip_arm=None |
| `results/ladder1b_b613/tv_Wikipedia_en_s0.json` | `EXPOSED` | unstripped | e28_ladder_410m.py: [producer inferred from path] strips only when --rstrip is passed; unstripped by default; this file records rstrip_arm=None |
| `results/ladder1b_b613/tv_Wikipedia_en_s1.json` | `EXPOSED` | unstripped | e28_ladder_410m.py: [producer inferred from path] strips only when --rstrip is passed; unstripped by default; this file records rstrip_arm=None |
| `results/ladder1b_b613/tv_Wikipedia_en_s2.json` | `EXPOSED` | unstripped | e28_ladder_410m.py: [producer inferred from path] strips only when --rstrip is passed; unstripped by default; this file records rstrip_arm=None |
| `results/m1/m1_5shard.json` | `EXPOSED` | unstripped | d1_min_union_diagnostic.py: [producer inferred from path] loads the battery and does NOT strip the prompt |
| `results/m1/m1_partial.json` | `EXPOSED` | unstripped | d1_min_union_diagnostic.py: [producer inferred from path] loads the battery and does NOT strip the prompt |
| `results/r4_corrections.json` | `EXPOSED` | unstripped | r4_recomputes.py: loads the battery and does NOT strip the prompt |
| `results/r6_within_source_410m.json` | `EXPOSED` | unstripped | r6_within_source.py: strips only when --rstrip is passed; unstripped by default; this file records rstrip_arm=None |
| `results/r6_within_source_410m_cpu.json` | `EXPOSED` | unstripped | r6_within_source.py: strips only when --rstrip is passed; unstripped by default; this file records rstrip_arm=None |
| `results/r7_matched_pools_410m.json` | `EXPOSED` | unstripped | r7_matched_pools.py: loads the battery and does NOT strip the prompt |
| `results/t21_conditioning_160m.json` | `EXPOSED` | unstripped | t21_conditioning.py: [producer inferred from path] loads the battery and does NOT strip the prompt |
| `results/t21_conditioning_410m.json` | `EXPOSED` | unstripped | t21_conditioning.py: [producer inferred from path] loads the battery and does NOT strip the prompt |
| `results/t21_conditioning_70m.json` | `EXPOSED` | unstripped | t21_conditioning.py: [producer inferred from path] loads the battery and does NOT strip the prompt |
| `results/d2_device_crossvalidation.json` | `INHERITED` | unstripped (inherited via provenance.inputs) | reads results/e48_crossover_410m.json, which is exposed |
| `results/e33b_tstats_410m.json` | `INHERITED` | unstripped (inherited via provenance.inputs) | reads results/e33_logit_baseline_410m_v2.json, which is exposed |
| `results/e48b_exposure_growth.json` | `INHERITED` | unstripped (inherited via provenance.inputs) | reads results/m1/m1_5shard.json, which is exposed |
| `results/e48c_exposure_vs_read.json` | `INHERITED` | unstripped (inherited via provenance.inputs) | reads results/e48_crossover_410m.json, which is exposed |
| `results/e51_interaction_variance.json` | `INHERITED` | unstripped (inherited via provenance.inputs) | reads results/ladder410/ladder_Github_s0.json, which is exposed |
| `results/e53_ladder_summary.json` | `INHERITED` | unstripped (inherited via provenance.inputs) | reads results/e36_qladder_410m.json, which is exposed |
| `results/e55_matrix_robustness.json` | `INHERITED` | unstripped (inherited via provenance.inputs) | reads results/e52_factorial_410m.json, which is exposed |
| `results/e55_matrix_robustness_rstrip.json` | `INHERITED` | unstripped (inherited via provenance.inputs) | reads results/e52_factorial_410m_rstrip.json, which is exposed |
| `results/e56_predictor_registry.json` | `INHERITED` | unstripped (inherited via provenance.inputs) | reads results/e31_local_bakeoff_410m.json, which is exposed |
| `results/e57_grid_variance_ci.json` | `INHERITED` | unstripped (inherited via provenance.inputs) | reads results/e57_factorial_cells_410m.json, which is exposed |
| `results/e57_grid_variance_ci_rstrip.json` | `INHERITED` | unstripped (inherited via provenance.inputs) | reads results/e57_factorial_cells_410m_rstrip.json, which is exposed |
| `results/e61_randomized_null_410m.json` | `INHERITED` | unstripped (inherited via provenance.inputs) | reads results/e61/tv_rand_Github_s0.json, which is exposed |
| `results/e62_band_adjudication.json` | `INHERITED` | unstripped (inherited via provenance.inputs) | reads results/ladder1b_b613/tv_Github_s0.json, which is exposed |
| `results/e62_interaction_b613.json` | `INHERITED` | unstripped (inherited via provenance.inputs) | reads results/ladder410/ladder_Github_s0.json, which is exposed |
| `results/r3_close_d2.json` | `INHERITED` | unstripped (inherited via provenance.inputs) | reads results/ladder410/ladder_Github_s0.json, which is exposed |
| `results/r4b_e36_flatness.json` | `INHERITED` | unstripped (inherited via provenance.inputs) | reads results/e36_qladder_410m.json, which is exposed |
| `results/r4c/e51_interaction_best1L.json` | `INHERITED` | unstripped (inherited via provenance.inputs) | reads results/ladder410/ladder_Github_s0.json, which is exposed |
| `results/r4c/e51_interaction_mean.json` | `INHERITED` | unstripped (inherited via provenance.inputs) | reads results/ladder410/ladder_Github_s0.json, which is exposed |
| `results/r4c/e51_interaction_min.json` | `INHERITED` | unstripped (inherited via provenance.inputs) | reads results/ladder410/ladder_Github_s0.json, which is exposed |
| `results/r4c/e51_interaction_persist.json` | `INHERITED` | unstripped (inherited via provenance.inputs) | reads results/ladder410/ladder_Github_s0.json, which is exposed |
| `results/r4e_control_power.json` | `INHERITED` | unstripped (inherited via provenance.inputs) | reads results/e34a_dact_vs_floor_410m.json, which is exposed |
| `results/r5_corpus_axis_uncertainty.json` | `INHERITED` | unstripped (inherited via provenance.inputs) | reads results/e57_factorial_cells_410m.json, which is exposed |
| `results/r5_corpus_axis_uncertainty_rstrip.json` | `INHERITED` | unstripped (inherited via provenance.inputs) | reads results/e57_factorial_cells_410m_rstrip.json, which is exposed |
| `results/e45_disagreement_geometry.json` | `UNKNOWN` | undetermined (no provenance.script) | no provenance.script |
| `results/e46_disagreement_ablation.json` | `UNKNOWN` | undetermined (no provenance.script) | no provenance.script |
| `results/e47_ablation_pairs.json` | `UNKNOWN` | undetermined (no provenance.script) | no provenance.script |
| `results/e49_derangement_stability.json` | `UNKNOWN` | undetermined (no provenance.script) | no provenance.script |
| `results/e50_concept_energy.json` | `UNKNOWN` | undetermined (no provenance.script) | no provenance.script |
| `results/fit_corpus_manifest_wikitext_n200.json` | `UNKNOWN` | undetermined (no provenance.script) | no provenance.script |
| `results/ladder410_cpu/ladder_Github_s0.json` | `UNKNOWN` | undetermined (no provenance.script) | no provenance.script |
| `results/ladder410_cpu/ladder_Github_s1.json` | `UNKNOWN` | undetermined (no provenance.script) | no provenance.script |
| `results/ladder410_cpu/ladder_Github_s2.json` | `UNKNOWN` | undetermined (no provenance.script) | no provenance.script |
| `results/ladder410_cpu/ladder_Pile-CC_s0.json` | `UNKNOWN` | undetermined (no provenance.script) | no provenance.script |
| `results/ladder410_cpu/ladder_Pile-CC_s1.json` | `UNKNOWN` | undetermined (no provenance.script) | no provenance.script |
| `results/ladder410_cpu/ladder_Pile-CC_s2.json` | `UNKNOWN` | undetermined (no provenance.script) | no provenance.script |
| `results/ladder410_cpu/ladder_StackExchange_s0.json` | `UNKNOWN` | undetermined (no provenance.script) | no provenance.script |
| `results/ladder410_cpu/ladder_StackExchange_s1.json` | `UNKNOWN` | undetermined (no provenance.script) | no provenance.script |
| `results/ladder410_cpu/ladder_StackExchange_s2.json` | `UNKNOWN` | undetermined (no provenance.script) | no provenance.script |
| `results/ladder410_cpu/ladder_USPTO_Backgrounds_s0.json` | `UNKNOWN` | undetermined (no provenance.script) | no provenance.script |
| `results/ladder410_cpu/ladder_USPTO_Backgrounds_s1.json` | `UNKNOWN` | undetermined (no provenance.script) | no provenance.script |
| `results/ladder410_cpu/ladder_USPTO_Backgrounds_s2.json` | `UNKNOWN` | undetermined (no provenance.script) | no provenance.script |
| `results/ladder410_cpu/ladder_Wikipedia_en_s0.json` | `UNKNOWN` | undetermined (no provenance.script) | no provenance.script |
| `results/ladder410_cpu/ladder_Wikipedia_en_s1.json` | `UNKNOWN` | undetermined (no provenance.script) | no provenance.script |
| `results/ladder410_cpu/ladder_Wikipedia_en_s2.json` | `UNKNOWN` | undetermined (no provenance.script) | no provenance.script |
| `results/ladder410_cpu_rstrip/ladder_Github_s0.json` | `UNKNOWN` | undetermined (no provenance.script) | no provenance.script |
| `results/ladder410_cpu_rstrip/ladder_Github_s1.json` | `UNKNOWN` | undetermined (no provenance.script) | no provenance.script |
| `results/ladder410_cpu_rstrip/ladder_Github_s2.json` | `UNKNOWN` | undetermined (no provenance.script) | no provenance.script |
| `results/ladder410_cpu_rstrip/ladder_Pile-CC_s0.json` | `UNKNOWN` | undetermined (no provenance.script) | no provenance.script |
| `results/ladder410_cpu_rstrip/ladder_Pile-CC_s1.json` | `UNKNOWN` | undetermined (no provenance.script) | no provenance.script |
| `results/ladder410_cpu_rstrip/ladder_Pile-CC_s2.json` | `UNKNOWN` | undetermined (no provenance.script) | no provenance.script |
| `results/ladder410_cpu_rstrip/ladder_StackExchange_s0.json` | `UNKNOWN` | undetermined (no provenance.script) | no provenance.script |
| `results/ladder410_cpu_rstrip/ladder_StackExchange_s1.json` | `UNKNOWN` | undetermined (no provenance.script) | no provenance.script |
| `results/ladder410_cpu_rstrip/ladder_StackExchange_s2.json` | `UNKNOWN` | undetermined (no provenance.script) | no provenance.script |
| `results/ladder410_cpu_rstrip/ladder_USPTO_Backgrounds_s0.json` | `UNKNOWN` | undetermined (no provenance.script) | no provenance.script |
| `results/ladder410_cpu_rstrip/ladder_USPTO_Backgrounds_s1.json` | `UNKNOWN` | undetermined (no provenance.script) | no provenance.script |
| `results/ladder410_cpu_rstrip/ladder_USPTO_Backgrounds_s2.json` | `UNKNOWN` | undetermined (no provenance.script) | no provenance.script |
| `results/ladder410_cpu_rstrip/ladder_Wikipedia_en_s0.json` | `UNKNOWN` | undetermined (no provenance.script) | no provenance.script |
| `results/ladder410_cpu_rstrip/ladder_Wikipedia_en_s1.json` | `UNKNOWN` | undetermined (no provenance.script) | no provenance.script |
| `results/ladder410_cpu_rstrip/ladder_Wikipedia_en_s2.json` | `UNKNOWN` | undetermined (no provenance.script) | no provenance.script |
| `results/r7_verified_snapshot/MANIFEST.json` | `UNKNOWN` | undetermined (no provenance.script) | no provenance.script |
| `results/r8_c1_unstripped/ladder_Github_s0.json` | `UNKNOWN` | undetermined (no provenance.script) | no provenance.script |

## 8. FILES WHOSE OWN DECLARED CONVENTION DIFFERS FROM THE TOOL'S CLASSIFICATION

Every results file that carries a `readout_convention`, `rstrip_arm` or `rstrip` field, beside the
class the tool assigned it. Both records are given; no adjudication.

| results file | tool class | `rstrip_arm` | `rstrip` | `readout_convention`, leading clause |
|---|---|---|---|---|
| `results/e36_qladder_410m_c1arm.json` | `EXPOSED` | `None` | `False` | UNSTRIPPED (LEGACY) |
| `results/e36_qladder_410m_rstrip.json` | `EXPOSED` | `None` | `True` | STRIPPED |
| `results/e48_crossover_410m.json` | `EXPOSED` | `False` | `None` | (no readout_convention field) |
| `results/e48_crossover_410m_rstrip.json` | `CLEAN` | `True` | `None` | (no readout_convention field) |
| `results/e52_factorial_410m_pooled.json` | `EXPOSED` | `None` | `False` | UNSTRIPPED (LEGACY) |
| `results/e52_factorial_410m_rstrip.json` | `EXPOSED` | `None` | `True` | STRIPPED |
| `results/e52_factorial_410m_rstrip_w1.json` | `EXPOSED` | `None` | `True` | STRIPPED |
| `results/e52_factorial_410m_rstrip_w2.json` | `EXPOSED` | `None` | `True` | STRIPPED |
| `results/e52_factorial_410m_rstrip_w8.json` | `EXPOSED` | `None` | `True` | STRIPPED |
| `results/e57_grid_variance_ci_rstrip.json` | `INHERITED` | `None` | `None` | STRIPPED (anchor rule) |
| `results/ladder410_cpu_rstrip/ladder_Github_s0.json` | `UNKNOWN` | `None` | `True` | STRIPPED |
| `results/ladder410_cpu_rstrip/ladder_Github_s1.json` | `UNKNOWN` | `None` | `True` | STRIPPED |
| `results/ladder410_cpu_rstrip/ladder_Github_s2.json` | `UNKNOWN` | `None` | `True` | STRIPPED |
| `results/ladder410_cpu_rstrip/ladder_Pile-CC_s0.json` | `UNKNOWN` | `None` | `True` | STRIPPED |
| `results/ladder410_cpu_rstrip/ladder_Pile-CC_s1.json` | `UNKNOWN` | `None` | `True` | STRIPPED |
| `results/ladder410_cpu_rstrip/ladder_Pile-CC_s2.json` | `UNKNOWN` | `None` | `True` | STRIPPED |
| `results/ladder410_cpu_rstrip/ladder_StackExchange_s0.json` | `UNKNOWN` | `None` | `True` | STRIPPED |
| `results/ladder410_cpu_rstrip/ladder_StackExchange_s1.json` | `UNKNOWN` | `None` | `True` | STRIPPED |
| `results/ladder410_cpu_rstrip/ladder_StackExchange_s2.json` | `UNKNOWN` | `None` | `True` | STRIPPED |
| `results/ladder410_cpu_rstrip/ladder_USPTO_Backgrounds_s0.json` | `UNKNOWN` | `None` | `True` | STRIPPED |
| `results/ladder410_cpu_rstrip/ladder_USPTO_Backgrounds_s1.json` | `UNKNOWN` | `None` | `True` | STRIPPED |
| `results/ladder410_cpu_rstrip/ladder_USPTO_Backgrounds_s2.json` | `UNKNOWN` | `None` | `True` | STRIPPED |
| `results/ladder410_cpu_rstrip/ladder_Wikipedia_en_s0.json` | `UNKNOWN` | `None` | `True` | STRIPPED |
| `results/ladder410_cpu_rstrip/ladder_Wikipedia_en_s1.json` | `UNKNOWN` | `None` | `True` | STRIPPED |
| `results/ladder410_cpu_rstrip/ladder_Wikipedia_en_s2.json` | `UNKNOWN` | `None` | `True` | STRIPPED |
| `results/r5_corpus_axis_uncertainty.json` | `INHERITED` | `None` | `None` | UNSTRIPPED (legacy) |
| `results/r5_corpus_axis_uncertainty_rstrip.json` | `INHERITED` | `None` | `None` | STRIPPED (anchor rule) |
| `results/r6_within_source_410m.json` | `EXPOSED` | `None` | `None` | STRIPPED |
| `results/r6_within_source_410m_cpu.json` | `EXPOSED` | `None` | `None` | STRIPPED |
| `results/r7_matched_pools_410m.json` | `EXPOSED` | `None` | `None` | STRIPPED |
| `results/r8_c1_unstripped/ladder_Github_s0.json` | `UNKNOWN` | `None` | `False` | UNSTRIPPED (LEGACY) |
| `results/r9_permutation_calibrated_min.json` | `IMMUNE` | `None` | `None` | STRIPPED |

Mechanical note on the key names, read off the code: the tool reads only `rstrip_arm`
(`tools/readout_exposure.py:187`), which is the field `experiments/t48_crossover.py:560` writes.
`experiments/t36_qladder.py:539` and `experiments/t52_factorial.py:756` write a field named
`rstrip` instead. `results/ladder410_cpu_rstrip/*.json` and `results/r8_c1_unstripped/*.json`
carry no `provenance.script`, which is why the tool classes them `UNKNOWN`.

## 9. THE PAPER-CITED VIEW, AS THE TOOL REPORTS IT

`PAPER_CITED` is a list hard-coded at `tools/readout_exposure.py:56-75`, described there as
"the results files paper/original_paper.tex actually cites, per paper/PAPER_HANDOFF.md section 5".
The tool's output for it, verbatim in content:

| class | the tool's label for the claim | results file |
|---|---|---|
| `EXPOSED` | scale floor, W_U concept-row geometry | `results/e38_jgeometry.json` |
| `CLEAN` | 160M interval, both aggregations | `results/t22_bootstrap_ci_160m.json` |
| `CLEAN` | 160M interval, persist arm | `results/t22_bootstrap_ci_persist_160m.json` |
| `EXPOSED` | the 8x8 grid, margins, LOO, leave-two-out | `results/e52_factorial_410m.json` |
| `RESCORED` | aggregation audit, matrix_loo | `results/e54_aggregation_audit.json` |
| `INHERITED` | bootstrap intervals on the variance split | `results/e57_grid_variance_ci.json` |
| `EXPOSED` | per-draw cells behind E57 | `results/e57_factorial_cells_410m.json` |
| `INHERITED` | independent 5x5 replication at N=400 | `results/e55_matrix_robustness.json` |
| `EXPOSED` | read-dose sweep | `results/e59_read_dose_410m.json` |
| `INHERITED` | per-corpus asymptotes, flatness in N | `results/e53_ladder_summary.json` |
| `INHERITED` | 20 failed predictors | `results/e56_predictor_registry.json` |
| `EXPOSED` | derangement, both aggregations | `results/e48_crossover_410m.json` |
| `EXPOSED` | min-union mechanism and band-width sweep | `results/d1_min_union_diagnostic_410m.json` |
| `INHERITED` | randomised-network null | `results/e61_randomized_null_410m.json` |
| `INHERITED` | containment index | `results/e48c_exposure_vs_read.json` |
| `CLEAN` | fitter and readout fidelity | `results/e60_fitter_determinism.json` |
| `EXPOSED` | context-pool disjointness | `results/e58_algebra_audit.json` |

Tally as printed: `CLEAN 3 of 17`, `RESCORED 1 of 17`, `EXPOSED 7 of 17`, `INHERITED 6 of 17`;
"paper-cited files that are readout-safe : 3 of 17"; "paper-cited files needing a re-score : 13 of 17".

The tool declares two field-level exceptions of its own (`tools/readout_exposure.py:78-90`),
quoted verbatim:

> `results/e38_jgeometry.json` — "the file is EXPOSED (t38 loads the battery), but the fields the
> paper cites are E39/*/mean_cos_I and eff_rank_I, computed from W_U alone with no prompts. The
> scale-floor claim is IMMUNE at field level. E42's gap_by_corpus_410m is not."
>
> `results/e58_algebra_audit.json` — "the file is EXPOSED (t58 loads the battery for the
> concept-token overlap), but the claim the paper cites is context-pool disjointness, a
> corpus-vs-corpus computation with no readout. IMMUNE at field level."

## 10. WHERE THE CORRECTED-READOUT MEASUREMENTS LIVE

`tools/readout_exposure.py:45-53` names three, verbatim:

> `ladder410` — "15 (corpus, seed) cells re-scored under .rstrip() at read-rung Q0
> (review/reproducibility/data/rstrip_rescore/rs_*.json)"
>
> `e33_logit_baseline_410m_v2` — "logit constant re-derived under both conventions
> (review/reproducibility/scripts/logit_baseline.json)"
>
> `e54_aggregation_audit` — "derangement control re-run under both readouts, 5 corpora x
> N in {200,400} x 5 draws (review/reproducibility/scripts/derange.py)"

Files under `results/` carrying `_rstrip` in their path at the time of this run:
`e36_qladder_410m_rstrip.json`, `e48_crossover_410m_rstrip.json`,
`e52_factorial_410m_rstrip.json`, `e52_factorial_410m_rstrip_w1.json`,
`e52_factorial_410m_rstrip_w2.json`, `e52_factorial_410m_rstrip_w8.json`,
`e54_aggregation_audit_rstrip.json`, `e54_aggregation_audit_rstrip_v2.json`,
`e55_matrix_robustness_rstrip.json`, `e57_factorial_cells_410m_rstrip.json`,
`e57_grid_variance_ci_rstrip.json`, `r5_corpus_axis_uncertainty_rstrip.json`, and
`ladder410_cpu_rstrip/ladder_{Github,Pile-CC,StackExchange,USPTO_Backgrounds,Wikipedia_en}_s{0,1,2}.json`
(15 files). `results/r6_within_source_410m.json`, `results/r6_within_source_410m_cpu.json`,
`results/r7_matched_pools_410m.json` and `results/r9_permutation_calibrated_min.json` declare
`readout_convention = "STRIPPED — the anchor rule (R1)"` without `_rstrip` in the filename.
`results/r8_c1_unstripped/ladder_Github_s0.json` declares `"UNSTRIPPED (LEGACY)"`.

## 11. RUN PROVENANCE, AND A DIFFERENCE BETWEEN TWO RUNS OF THE SAME TOOL

Commands executed for this document, from the repository root:

```bash
.venv/bin/python tools/readout_exposure.py                    # table in section 7
.venv/bin/python tools/readout_exposure.py --json <scratchpad>/readout_exposure_fresh.json
shasum -a 256 results/e54_aggregation_audit*.json             # section 5
grep -rn 'prompt"\]\.rstrip()' experiments tools              # section 6a
```

The §4 item counts were recomputed with `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1` and the
`EleutherAI/pythia-410m-deduped` tokeniser: for each of the six sets, tokenise `prompt` and
`prompt.rstrip()` with `add_special_tokens=True`, call
`src.anchor_evals.readout_position(tok, name, <that prompt>)` on each, index both token
sequences at the returned position, and count the items where the two ids differ.

**A difference between two runs of the same tool, recorded without adjudication.**
`tmp/readout_exposure.txt` (file mtime 2026-08-19 20:54) and this run disagree on the file count
and on every class total:

| quantity | `tmp/readout_exposure.txt`, stored 2026-08-19 | this run, 2026-08-20 |
|---|---:|---:|
| non-sidecar results files | 214 | 278 |
| `IMMUNE` | 47 (22.0%) | 50 (18.0%) |
| `CLEAN` | 34 (15.9%) | 35 (12.6%) |
| `RESCORED` | 18 (8.4%) | 22 (7.9%) |
| `EXPOSED` | 97 (45.3%) | 110 (39.6%) |
| `INHERITED` | 12 (5.6%) | 23 (8.3%) |
| `UNKNOWN` | 6 (2.8%) | 38 (13.7%) |
| IMMUNE + CLEAN | 81 (37.9%) | 85 (30.6%) |
| EXPOSED + INHERITED | 109 (50.9%) | 133 (47.8%) |

Two further textual differences between the two outputs, quoted:

- For `e28_ladder_410m.py`, `t36_qladder.py` and `t52_factorial.py` the stored output records
  "loads the battery and does NOT strip the prompt"; this run records "strips only when --rstrip
  is passed; unstripped by default; this file records rstrip_arm=...".
- Files present in this run's listing and absent from the stored one include
  `results/e48_crossover_410m_rstrip.json`, `results/e54_aggregation_audit_rstrip.json`,
  `results/e54_aggregation_audit_rstrip_v2.json`, `results/e36_qladder_410m_rstrip.json`,
  `results/e36_qladder_410m_c1arm.json`, `results/e52_factorial_410m_rstrip*.json`,
  `results/e57_*_rstrip*.json`, `results/r3_close_d2.json`, `results/r4_corrections.json`,
  `results/r4b_e36_flatness.json`, `results/r4c/*.json`, `results/r4e_control_power.json`,
  `results/r5_corpus_axis_uncertainty*.json`, `results/r6_within_source_410m*.json`,
  `results/r7_matched_pools_410m.json`, `results/r8_ladder_flatness.json`,
  `results/r9_permutation_calibrated_min.json`, `results/postreview_completion.json`,
  `results/ladder410_cpu/*.json` and `results/ladder410_cpu_rstrip/*.json`.

This document uses **this run**, per the instruction to run the tool and use its output.
