# REPRODUCIBILITY.md — the reference behind `repro/README.md`

**To reproduce the paper, start at [`repro/README.md`](../../repro/README.md):** four commands, the
three tiers (T0, T1, T2) and what each one needs. What has been checked, with the record of each
check, is in [`README.md`](README.md) in this folder. This page holds the rest: the environment,
what the local gate asserts, how a GPU run is done safely, the standing audit, and where new work
goes.

## 1. Environment

`./lab doctor` checks each of these and prints the fix for whichever is missing.

| # | what | needed for | how |
|---|---|---|---|
| 1 | Python ≥ 3.10 and `uv` | everything | `uv sync` builds `.venv` from `pyproject.toml` and `uv.lock` |
| 2 | `jacobian-lens` at `581d398` | everything | `bash repro/01_setup_local.sh` (or `./lab setup`) clones it into `jacobian-lens/`, gitignored and never modified |
| 3 | network access to Hugging Face | Pythia weights, the results and the maps | the models and the mirror are public; no login is needed to download |
| 4 | a Hugging Face **write** token | uploading to a mirror (optional) | on your own machine only, never on a rented box |
| 5 | the `vastai` CLI and an API key | GPU runs only (T2) | `pip install vastai`, then `./lab doctor` |
| 6 | an SSH key registered with vast.ai | reaching a rented box | `ssh-keygen -t ed25519` |
| 7 | `tmux` | `./lab watch` | `brew install tmux` |

**The single point of failure is the reference implementation.** Every fit and every read goes
through the released `jlens` package: 28 files import it, through four entry points
(`jlens.hf.from_hf` and `Layout`, `jlens.lens.JacobianLens`, `jlens.fitting.fit` and
`SKIP_FIRST_N_POSITIONS`, `jlens.hooks.ActivationRecorder`). It is cloned from
`github.com/anthropics/jacobian-lens` at `581d398` and not mirrored by this work. If that repository
disappears, nothing here runs.

## 2. The local gate

`./lab verify` (`repro/02_verify_local.sh`) runs ten test files from `tests/`, 197 assertions on
2026-11-14, and prints the environment it ran in. If it fails, stop: nothing downstream can be
trusted, and no GPU time is justified. It needs the 70M map
`results/lenses/ladder/lens_70m_n200_db128.pt` from the mirror (`./lab fetch`); without it,
`test_anchor_fidelity` reports a missing artifact rather than a broken repository.

What the anchor-fidelity test asserts:

* the transported activation equals `jlens.lens.JacobianLens.apply` to `max|diff| = 0`;
* the released readout reproduces the model's own logits to 2.3e-3;
* fitting honours `skip_first`: the released code drops the first 16 positions
  (`jlens/fitting.py:42`) while the source paper's text says 0. This work uses 16 and says so;
* there is no centering anywhere: the mean activation never enters a lens vector or a write.

What it does not assert: the **position** the readout is taken at. That is how the readout defect
(157 of 551 items scored at a token that does not occur in the sequence) passed this gate. See
[`../experiments/READOUT_DEFECT.md`](../experiments/READOUT_DEFECT.md).

Three more test files sit outside this gate: `test_provenance_hash.py` and `test_band_rule.py`
(run them directly with `.venv/bin/python tests/<file>`), and `test_e28_eval_compliance.py`, which
checks an E28 evaluation run's output against its pre-registration.

## 3. Running on a GPU

Only T2 and new fits need a GPU. Price the run before renting anything.

```bash
./lab cost 410m 200 L40S       # price it first
./lab offers L40S              # live offers, ranked by fp32 TFLOPS per dollar-hour
./lab up 4 L40S 1.20           # rent the 4 cheapest L40S offers under $1.20/h
./lab push                     # rsync the code (maps and corpora are excluded on purpose)
./lab preflight                # on the box: torch, CUDA, TF32 off, anchor fidelity
./lab shard jobs.txt           # one job per line, round-robin across the boxes
./lab watch                    # tmux: a dashboard and one window per box
./lab pull                     # rsync back, then verify every file's hash
./lab down --all               # destroy; refuses any box without a verified pull receipt
```

Choose GPUs by fp32 throughput, not by name (L40S 91.6 TFLOPS > RTX 4090 82.6 > H100 67 > A100
19.5): every fit here runs in fp32, and **TF32 must be off**, because its 10-bit mantissa breaks the
bit-identity gate. Remote jobs run in a named tmux session, so they survive a dropped connection.

**The teardown order is fixed: run → pull → hash-verify → mirror → destroy.** `./lab down` reads the
receipt `./lab pull` writes and refuses without it; two maps were lost with their boxes before
that guard existed. `ALLOW_UNVERIFIED=1` overrides it and records a typed reason in
`logs/teardown.log`. Before destroying, the script checks that the id is one of the account's live
instances, and refuses otherwise; after, it re-lists them and exits non-zero if the box is still
there, so `./lab down` keeps it in `.fleet`. Both checks were added on 2026-11-14, after `./lab up` was
found to record offer ids rather than instance ids: a teardown then targeted a number that was not
an instance while the real box kept billing.

Measured prices, the hardware model behind `./lab cost`, and the record of every rental are in
[`COMPUTE.md`](COMPUTE.md).

## 4. The standing audit

`./lab health` (`repro/30_repo_health.sh`) runs these checks. Each exists because of something
that went wrong here. A **FAIL** blocks; a **warn** records a known gap.

| check | catches |
|---|---|
| H1 | the reference implementation missing, off its pinned commit, or modified in place |
| H2 | large binaries committed to git |
| H3 | a map on disk with no SHA-256 in `ARTIFACTS.md` or no provenance sidecar |
| H4 | a claim in a write-up that names no results file |
| H5 | the test suite failing |
| H6 | a module that four or more others import, with no test |
| H7 | a GPU still billing |
| H8 | uncommitted work |
| H9 | corpus plaintext tracked in git |
| H10 | a document pointing at a file that does not exist |
| H11 | a disproved claim restated as a finding (with a self-test that the gate still fires) |
| H12 | retired: checked that no identity string reached the tree during the double-blind review |
| H13 | a results file whose producing script cannot be obtained from the tree |

## 5. Where new work goes

| adding | goes in | and you must also |
|---|---|---|
| an experiment | `experiments/eNN_<name>.py` | follow [`../experiments/README.md`](../experiments/README.md#adding-an-experiment): the pre-registration is committed first, alone, then the script, the `repro/exp/` module and the registry entry |
| a shared routine or metric | `src/<name>.py` | add `tests/test_<name>.py`; H6 flags a heavily imported module without one |
| a result | `results/<name>.json`, written with `provenance.write_result` | cite the file in its pre-registration (H4) |
| a fitted map | the Hugging Face mirror | record its SHA-256 in `ARTIFACTS.md` (H3) |
| a reproduction step | `repro/NN_<name>.sh` | give it a `./lab` verb and a row in `repro/README.md` |
| a health check | `repro/30_repo_health.sh` | use `ok` / `warn` / `bad` from `repro/lib/common.sh`, and name the failure it would have caught |

The code references nothing outside this repository except the cloned `jacobian-lens/`. A new
external dependency is a design regression.
