# experiments/ — the scripts that produce results

Every script here writes one or more files into `results/`, each stamped with the script's hash,
its arguments, its inputs and the environment. Three places describe one experiment, and each does
a different job:

| you want | look in |
|---|---|
| what the experiment asked, the rule it was graded against, and what it found | `docs/experiments/preregs/` |
| the exact command that produced the stored result | `repro/exp/<module>.sh` |
| the numbers | `results/`, never the script and never the prose |

## Which script is which experiment

File names keep the IDs they were written under, because stored results record the script by path.
Those IDs are not consistent: `t52_factorial.py` is experiment E52, but `t39_dread.py` is E44, and
`r6_within_source.py` is E72. [`docs/experiments/REGISTRY.md`](../docs/experiments/REGISTRY.md)
lists every experiment with the scripts that produced its results. The paper's main experiments:

| paper | experiment | script | module |
|---|---|---|---|
| Sec. 4.1, the 8 × 8 factorial | E52 | `t52_factorial.py` (`--rstrip` for the corrected readout) | `e52_factorial.sh` |
| Sec. 4.1, the variance decomposition | E57 | `t57_grid_variance_ci.py` | `e57_variance_ci.sh` |
| Sec. 4.1, within-source resampling | E72 | `r6_within_source.py` | `r6_within_source.sh` |
| Sec. 4.1, type-token-ratio matching | E74 | `r7_matched_pools.py` | `r7_matched_pools.sh` |
| Sec. 4.2, containment and the read | E35, E48 | `t35_containment.py`, `t48b_exposure_growth.py`, `t48c_exposure_vs_read.py`, `t48_crossover.py` | `e48b_exposure.sh`, `e48c_exposure_read.sh`, `e48_crossover.sh` |
| Sec. 4.3, replication at 1B and 2.8B | E75 | `d3_corpus_by_family.py`, `cv6_per_family_ladder.py`, `cv7_1b_rung.py` | `d3_by_family.sh`, `cv6_ladder.sh`, `cv7_rung.sh` |
| Sec. 4.4, the N ladder | E28 | `e28_ladder_410m.py`, `tools/r8_ladder_flatness.py` | `r8_flatness.sh` |
| Sec. 5, answer competence | E79 | `cv4_phase1_capability.py` | `cv4_capability.sh` |

`exploratory/` holds the first round of experiments (E00–E27, run 2026-08-09 to 08-11, write-ups in
`exploratory/descriptions/`) and the later predictor screens E31, E34, E44–E47 and E50
(`t31_`, `t34_`, `t39_`–`t42_`, `t44_`).

## How to run one

Through its module, not directly:

```bash
./lab exp list                              # every module, its tier and cost
bash repro/exp/e52_factorial.sh --dry-run   # what it would run, executing nothing
bash repro/exp/e52_factorial.sh             # the run
```

The module refuses to start without its inputs, checks the real exit status, and afterwards checks
that each output exists and carries a valid provenance block.

## Import rules

- The shared library is `../src`, reached by one `sys.path` entry at the top of each file.
- A sibling script is imported by its bare name, because Python puts a script's own directory on
  `sys.path`. Five scripts are both runnable and imported by others: `t2_fastfit.py` (the fitter, 24
  importers), `t13_transport_controls.py` (8), `t17_reaggregate.py` (5), `t35_containment.py` and
  `t5a_capability_screen.py`. They keep their names because stored provenance points at them.
- `results/` and `corpora/` are one level up: `os.path.join(HERE, "..", "results")`.

## Adding an experiment

See *Adding an experiment* in [`docs/experiments/README.md`](../docs/experiments/README.md#adding-an-experiment).
In short: take the next canonical number from the registry, commit the pre-registration first, name
the script `e<NN>_<name>.py`, store results with `provenance.write_result`, and add a module.
