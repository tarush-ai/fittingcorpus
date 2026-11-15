# repro/ — reproducing the results

There are three tiers of reproduction. Each needs more than the one before, and each answers a
different question.

| tier | the question | what it does | what you need | cost |
|---|---|---|---|---|
| **T0** | do the paper's statistics follow from the stored results? | recomputes every statistic from the stored results JSON. No model, no GPU | this repository and the results JSON | free, about a minute |
| **T1** | do the stored reads follow from the stored maps? | re-scores every read from the stored fitted maps, on CPU | the maps from the mirror (16 GB) | free, minutes to hours |
| **T2** | does the fitting step still produce those maps? | refits a few maps from scratch and compares them with the stored ones | a GPU, fp32, TF32 off | rented GPU time |

Today there are 15 T0 modules, 31 T1 and 7 T2.

## Start here

```bash
uv sync                               # the Python environment
bash repro/01_setup_local.sh          # clones github.com/anthropics/jacobian-lens at 581d398
bash repro/04_fetch_results.sh        # the results JSON from the mirror, about 8 MB, no login
bash repro/RUN_ALL.sh --tier T0       # recompute every statistic
```

`jacobian-lens/` and `results/` are both gitignored, so a fresh clone has neither until lines 2 and 3
have run. For T1, add `bash repro/03_fetch_artifacts.sh --all` (the maps, hash-verified on download)
and run `RUN_ALL.sh --tier T1`. T2 needs a GPU box and prints its cost before it starts.

**T1 runs on CPU on purpose.** Scored on CUDA, the same reads differ from CPU by up to 2.774e-04
(`results/d2_device_crossvalidation.json`, verdict DIVERGENT). T1's test is bit-identity with the
stored payload, so on a GPU it would report "does not reproduce" by construction.

**T2 is a spot-check on the fitting step, not a rebuild.** No module writes a `.pt`; every T2 module
writes a JSON comparison. A refit is not bit-identical to a stored map. Maps fitted after the
provenance layer existed refit to 2.441e-04, inside one fp16 storage step
(`results/e66c_post_provenance_repro.json`). The older E48 panel refits to 1.1e-03
(`results/e66b_determinism_floor.json`) because machine and library state was not recorded then.
That gap changes no read. So you cannot replace the mirror's maps with your own refits and expect
T1 to pass. To rebuild a map from scratch, run `experiments/trainval.py --save-lens` yourself.
That validates the recipe, not the stored artifact.

## Where the record lives

| place | holds |
|---|---|
| this repository | code, pre-registrations, experiment documents, the harness, and `scripts_at_run/` (the exact bytes of every script that produced a stored result) |
| [the Hugging Face mirror](https://huggingface.co/Tarush-AI/fittingcorpus) | the results JSON and every fitted map. No corpus plaintext, which is third-party text: rebuild it with `06_data.sh --build` |

`docs/reproducibility/HF_MIRROR_MANIFEST.tsv` lists every file on the mirror with its hash.
`tools/hf_mirror_manifest.py --verify --repo <repo>` checks a mirror against it.

## The scripts

Every script runs on its own (`bash repro/NN_name.sh`). Most are also reachable through `./lab <verb>`.

| script | `./lab` | what it does | cost |
|---|---|---|---|
| `00_check_config.sh` | `doctor` | every dependency, present or missing, with the exact fix | free |
| `01_setup_local.sh` | `setup` | builds `.venv`, clones and pins `jacobian-lens`, installs it | free |
| `02_verify_local.sh` | `verify` | the local gate: the unit tests, plus bit-identity of the read path to the released library | free |
| `03_fetch_artifacts.sh` | `fetch` | downloads the fitted maps from the mirror and verifies each hash | free |
| `04_fetch_results.sh` | `results` | downloads the results JSON; `--check` compares local against the mirror without writing | free |
| `05_mirror_results.sh` | — | uploads results to the mirror, then re-lists and verifies rather than trusting the upload | free |
| `06_data.sh` | — | rebuilds the corpus pools at their pinned dataset revisions (`--build`) | free |
| `10`–`15_vast_*.sh` | `up`, `preflight`, `pull`, `down` | rent a GPU box, check it, pull results back with hash verification, destroy it. `down` refuses without a verified pull receipt | **paid** |
| `20_cost_estimate.sh` | `cost` | prices any run before anything is rented | free |
| `30_repo_health.sh` | `health` | the standing audit (H1–H13) | free |
| `RUN_ALL.sh` | — | runs every module of one tier and reports which reproduced | by tier |
| `exp/*.sh` | `exp list`, `exp run` | one module per experiment (below) | by tier |
| `t1_sweep/` | — | the harness of the full T1 sweep, whose results are in `docs/reproducibility/T1_SWEEP_RESULTS.md` | free |

`./lab doctor` also prints **cost levels** 0 to 3 (local CPU, one GPU-hour, one experiment, a full
ladder). They price what a step spends and are not the T0/T1/T2 tiers: cost level 1 rents a GPU,
while tier T1 is CPU-only.

## Experiment modules (`exp/`)

Each module is the one canonical invocation of one experiment: the flags that produced the stored
result, in a file, next to the reason for them. Every module:

1. declares its inputs and outputs, and refuses to start if an input is missing;
2. checks the real exit status of the Python process;
3. afterwards checks that each output exists **and** carries a provenance block whose recorded script
   hash still matches (a truncated map once passed a presence check);
4. prints its cost and, above the budget gate, refuses without `--yes`.

```bash
./lab exp list                              # every module, its tier and cost
bash repro/exp/e52_factorial.sh --dry-run   # what it would run, executing nothing
```

Module names keep the historical ID of the results they produce (`r6_within_source.sh` writes R6's
results). [`docs/experiments/REGISTRY.md`](../docs/experiments/REGISTRY.md) lists each module under
its experiment's canonical ID. `exp/cv7_1b.sh` declares no tier on purpose: it is a detached
launcher, not a module, and `RUN_ALL.sh` names it when it skips it.

## Why the guards exist

Each one is the residue of a real failure.

- **the pull-receipt guard**: two maps were destroyed with the box they were on.
- **the verified toolchain install**: a pip install that failed into `/dev/null` left torch at 2.4.0 on
  four boxes, and 180 fits failed silently.
- **the TF32 assertion**: TF32's 10-bit mantissa breaks the bit-identity gate, silently.
- **the torch, torchvision and torchaudio pin**: the image's torchvision and torchaudio break the
  GPT-NeoX import.
- **the budget gate**: a cost estimate was once wrong by a factor of five, because it priced the largest
  *N* instead of the sum over the *N* grid.

## Conventions

- `set -euo pipefail` everywhere. A script that cannot do its job stops.
- Anything that spends money or destroys something asks first. `FORCE=1` skips the prompt for
  automation; it never skips the pull-receipt guard.
- `doctor`, `cost`, `offers`, `health` and `status` change nothing.
- To add a health check, put it in `30_repo_health.sh` and use `ok` / `warn` / `bad` from
  `lib/common.sh`: `bad` blocks, `warn` records a known gap. State which real failure it would have
  caught.
