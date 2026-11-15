# docs/ — the written record behind the paper

The paper states the findings. This folder holds the evidence for each one: the pre-registrations,
what each experiment did and found, how the experiments were checked for validity, and how the
results were checked for reproducibility. Code is in `src/`, `experiments/`, `tools/` and `repro/`.
Results are in `results/`, fetched from the Hugging Face mirror.

## Where to look

| question | file |
|---|---|
| What does an experiment ID mean (E52, R1, CV6, T14, …)? | [`experiments/REGISTRY.md`](experiments/REGISTRY.md) |
| Which experiments stand behind each claim in the paper? | [`experiments/README.md`](experiments/README.md) |
| What exactly was registered before an experiment ran, and what came out? | [`experiments/preregs/`](experiments/preregs/), one document per experiment |
| Which results file does each document cite, and is it on the corrected readout? | [`experiments/INDEX.md`](experiments/INDEX.md) (generated) |
| The whole programme in one narrative, every verdict with its file | [`context/CONTEXT.md`](context/CONTEXT.md) |
| Every claim, graded by how well it is supported | [`context/RESULTS_TAXONOMY.md`](context/RESULTS_TAXONOMY.md) |
| Why `min` is the primary band summary | [`context/AGGREGATION_POLICY.md`](context/AGGREGATION_POLICY.md) |
| Which configuration produced each cited number | [`context/CONFIG_MATRIX.md`](context/CONFIG_MATRIX.md) |
| The readout correction, mechanically | [`experiments/READOUT_DEFECT.md`](experiments/READOUT_DEFECT.md) |
| The two layer-permutation nulls, adjudicated | [`experiments/DA1_OUTCOME.md`](experiments/DA1_OUTCOME.md) |
| Are the experiments the right experiments? | [`validity/`](validity/) |
| Does the code do what the paper says, and do the results regenerate? | [`reproducibility/`](reproducibility/) |

## Glossary

The paper's terms were settled late. Code, file names and older documents often use earlier ones.

| paper term | in code and older documents | meaning |
|---|---|---|
| **Jacobian map**, *J* | operator, lens, `J^P` | the model's derivative of its final hidden state with respect to a layer, averaged over the fitting corpus |
| **fitting corpus** | fit corpus, *P*, fit axis | the text whose prompts the map is averaged over |
| **read context** | read rung, *Q*, read axis, prefix | the 128 tokens of text placed in front of each test prompt when the lens is read |
| **logit lens** | free lens, `J = I`, `logit_I`, identity transport | the unfitted baseline: the model's own unembedding applied to the hidden state |
| **evaluation battery** | anchor evals, eval sets, the 551 items | the 551 test prompts released with the lens, in six families. One family sits at the floor for every lens, including the logit lens, so comparisons use the other five (the "admitted sets") |
| **readout score** | read AUC, pass@k AUC, read | the share of prompts whose annotated concept is in the lens's top *k* at any band layer, averaged over *k* = 1, 2, 5, 10, 20, 50, 100. Results files store it on a 0–1 scale; the paper multiplies by 100 |
| **band** | L38–L92, `[9,21]` | the middle layers the readout looks at: the source's band (38% to 92% of depth), scaled to each model. At 410M that is layers 9–21 of 24 |
| **`min`** (any layer) | min-over-layers | the source's published band summary: recovered if *any* band layer has the concept in its top *k*. Primary in the paper |
| **`persist`** (half the band) | persistence | recovered only if at least half the band layers do. A sensitivity analysis |
| **corrected readout** | `--rstrip`, stripped, `_rstrip` | the readout after the trailing-space fix (see `experiments/READOUT_DEFECT.md`). *Legacy* or *unstripped* means before it |
| **32-gram containment** | containment, exposure, membership | the share of a corpus's 32-token windows that occur verbatim in Pythia's training stream |
| **layer-permutation null** | derangement, `J^shuf`, shuffled map | the map with each band layer given another layer's Jacobian; a control for whether layer-specific structure matters |
| **seed** | seed block, `s0`–`s2` | a disjoint block of fitting documents. Three per corpus, so sampling noise can be measured |
| — | S1, S2, S3 | the programme's starting intuitions: S1, the effect is larger in small models; S2, a justifiable *N* exists; S3, the lens degrades under distribution shift faster than the logit lens. They told us what to measure and are not claims |
| — | T0, T1, T2 | reproduction tiers: recompute from stored JSON, re-score stored maps on CPU, refit on a GPU. See [`../repro/README.md`](../repro/README.md) |
| — | tiers A, B, D | a different thing: how well a *claim* is supported, in `context/RESULTS_TAXONOMY.md` |

## Two kinds of check

Rigor here is checked along two independent lines, because each catches what the other cannot.

* **Validity** ([`validity/`](validity/)): assuming the code is right, are these the right
  experiments, with the right replication unit, enough power, and controls that could have failed?
* **Reproducibility** ([`reproducibility/`](reproducibility/)): is the code right, and do the stored
  results regenerate?

The readout defect was found by the second. A design check could never have found it, because the
design was right and the code was not. The second could never have found that an apparent null had
too little power to detect the effect it was compared with, because the code faithfully implemented
that design.

## Traps that have cost time

1. **A results file's top-level `inputs` field is a hand-written declaration and does not track
   command-line overrides.** `e54_aggregation_audit_rstrip.json` declares `e36_qladder_410m.json`
   while its `provenance.argv` passes the corrected file. Read `provenance.argv` and
   `provenance.inputs`.
2. **`_rstrip` in a file name does not guarantee a corrected readout throughout.**
   `e54_aggregation_audit_rstrip.json` reads a corrected E36 but a pre-correction E48, which is why its
   derangement count is 104 of 120 where `_rstrip_v2` gives 84 of 120.
3. **The pooling convention moves headline ratios by about 37%; the choice of N grid moves them by
   about 0.1%.** The sample SD pooled by root mean square is the defensible estimator. Name the
   convention whenever you print a "× seed SD" figure.
4. **At 70M, `persist` is `min` by construction.** The band is two layers, so "at least half" means
   "at least one". A 70M result reported as surviving "both aggregations" has the weight of one.
5. **Results file names follow the script, not the experiment.** `e62_interaction_b613.json` was
   written by E51's script and belongs to E62. The registry resolves every file to its owner.

## What this repository cites but does not contain

The code, the harness and most of these documents were written by LLM coding agents working under
Tarush Gupta's direction and review (see the paper's *Use of AI assistance* section). Three kinds of
thing they cite are not in the public repository.

**The agents' working files.** `CLAUDE.md` (the agents' standing rules), `instructions/`, `STATE.md`,
`HANDOFF.md`, session handoffs, review and audit prompts, and the 2026-08-22 validity audit's working
files stayed in the private working repository. Script comments and older documents cite them, for
example "`CLAUDE.md` §2.9" or "`HANDOFF.md` §0.3". The scripts cannot be edited to remove these
citations, because each stored result pins its producing script's exact bytes. `CLAUDE.md` was
revised many times and its section numbers moved, so match a citation by its wording, not its
number. The rules cited are these:

| the rule | in plain words |
|---|---|
| **a null is a finding** | a measured null with a stated bound ranks with a positive result. An underpowered miss is not a null: state the effect the design could have detected |
| **never reinterpret a pre-registered rule** | if a result contradicts its prediction, report it and stop. No threshold is re-cut afterwards, even one judged mis-specified; a new rule is registered first (as E65T, E66b and OS1c were) |
| **never report an unstored number** | a number that is not in a results file is re-run and stored before it is cited |
| **never accept a proxy** | assert on observed state (the file's contents, the instance list), never on "the command returned"; never swallow an exception |
| **name the control and its number** | every control states the value it produced and the value that would have made it fail. A control that cannot fail is labelled a recorder |
| **a surprising result is a bug report** | enumerate the artifacts that could produce it, and test them, before reporting it |
| **ask what each result invalidated** | then check those claims |
| **one experiment at a time** | each is adjudicated before the next starts |
| **no centering** | the mean activation never enters a lens vector or a write |
| **tiny-first** | the exact script path is run on CPU at small size before any paid GPU run |
| **TF32 off** | every fit is fp32, with TF32 disabled in torch |
| **the reference implementation is never modified** | `jacobian-lens/` is cloned at `581d398` and used as released |
| **artifacts before teardown** | a GPU box's outputs are pulled and hash-verified before it is destroyed |

In those documents, *the operator* means Tarush, directing the agents. Everywhere else in this
repository, *operator* means the Jacobian map.

**The development history.** The public repository is a single commit. Commit hashes in documents and
in each results file's `provenance.git` block (`1340e76`, `271454e`, …) refer to the private
development history and cannot be checked out here. The evidence that depended on that history was
computed while it existed and is stored in the tree:
[`experiments/REGISTRATION_LEDGER.md`](experiments/REGISTRATION_LEDGER.md) (whether each
pre-registration was committed before its code), [`experiments/preregs/as_registered/`](experiments/preregs/as_registered/)
(every registration text a stored result pins by hash), and `repro/scripts_at_run/` (the exact bytes of
every script version that produced a stored result).

**Earlier research lines.** Before this programme, the repository and its first artifact mirror hosted
two of Tarush's unrelated research lines. Their code and maps were removed on 2026-08-12 and are
not used here.

`archive/` holds one restored file that pre-registrations link to.
