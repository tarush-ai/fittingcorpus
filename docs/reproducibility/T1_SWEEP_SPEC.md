# T1 SWEEP — specification for the executing agent

**Written 2026-08-29 for a fresh-context agent.** Self-contained: you do not need this conversation.
Read this file, then `CLAUDE.md` §2–3, then start. Kickoff prompt: see §8.

---

## 0. THE JOB, IN ONE LINE

Run all 22 `repro/exp/` modules of tier **T1**, and for each one report whether the stored results
payload comes back **bit-identical**. Nothing else.

T1 re-scores the stored `.pt` operators against the evaluation battery. It is the tier that answers
*"do the released operators still produce the numbers in the paper?"* T0 (statistics from stored
JSON) is already verified 13/13. T2 (refitting operators) is out of scope.

## 0.5 PREFLIGHT — run this first, it takes seconds

```bash
.venv/bin/python tools/artifact_provenance_diff.py
```

It diffs every recorded script hash, input hash and library version against what is on disk. As of
2026-08-29 it returns:

* **385 of 385 `.pt` input hashes match. No operator has changed.**
* 43 `.json` files have a moved *file* hash: 38 rewritten by the anonymisation scrub (hostname
  redacted, `0 payload hashes moved`), 5 re-run on 2026-08-29. **0 unexplained.**

So you begin from a tree where nothing has drifted. **If this preflight reports anything
unexplained, stop and tell the operator before running a single module** — a drifted input makes
every downstream "does not reproduce" uninterpretable.

## 1. HARD CONSTRAINTS — read before running anything

### 1.1 CPU ONLY. Never `--device cuda`. This is measured, not stylistic.

`results/d2_device_crossvalidation.json` cross-checked CUDA-scored against CPU-scored reads over 30
cells and returned **DIVERGENT**:

```
max |CUDA - CPU| = 2.774e-04   (worst: USPTO_Backgrounds s2, min, 0.18% relative)
tolerance derivation: one (item,intermediate) pair flipping at one k moves a set mean by
                      >= 1/(893*7) = 1.6e-4, so 1e-6 separates fp accumulation from a
                      single changed decision
```

`2.774e-04 > 1.6e-4`, so the device change flips actual scoring decisions. The stored numbers are
CPU numbers. **A GPU sweep would return "does not reproduce" by construction** and would be a
manufactured false negative. D2's own verdict already requires CPU sourcing.

Do not "save time" on a GPU. The correct run costs **$0 and 6-7 hours of CPU**.

### 1.1b T1 IS NOT T2. You are not refitting anything.

T1 **reads** the `.pt` operators and re-scores them. It never rewrites one. Regenerating operators
is T2, it needs a GPU, and it is **out of scope for you**.

If a module appears to want to fit an operator, you have the wrong module. Stop.

Why this is not a gap: `tools/artifact_provenance_diff.py` shows all 385 recorded `.pt` input hashes
still match, so the operators on disk *are* the operators that produced the stored results. T2 was
sampled separately at n=2, deliberately straddling the provenance boundary — `r6` (post-provenance)
refit to `2.441e-04`, inside one fp16 step; `e48` (pre-provenance) to `1.0986e-03`. Reads were
bit-identical in both cases.

### 1.1c DO NOT CHANGE THE THREAD COUNT

Leave `torch.get_num_threads()` at its default. Do **not** set `OMP_NUM_THREADS`, do not call
`torch.set_num_threads`, and do not "use all the cores".

`cv3_margins` reproduced **bit-identically at the default of 10** on this machine. `e60` measured the
fitters agreeing exactly at 1, 4 and 8 threads and diverging by `1.09e-04` above that, so thread
count changes results. If you raise it to 14 and something fails, nobody can tell whether the
failure is real or something you introduced — a confound deliberately added to the one experiment
whose entire purpose is bit-identity.

Quitting other applications is good: it gives those 10 threads full cores. Changing the number is
not. Record `torch.get_num_threads()` in your report.

### 1.2 Do not touch `results/` after the sweep without re-scrubbing

`src/provenance.py` stamps the hostname into every results file it writes. The tree was scrubbed
once already. **Every module you run re-introduces the identity leak.** That is expected. When the
sweep is finished, tell the operator; the scrub is re-run at release time, not by you.

### 1.3 Never re-cut a decision rule, and never edit a results file by hand

If a module fails to reproduce, report it. Do not adjust tolerances, re-run with different flags to
get a friendlier number, or hand-edit JSON. Everything in `results/` is hash-stamped.

## 2. THE PRE-HOC MAP — what to expect, decided BEFORE running

This is the point of the exercise: the difficulty of diagnosing a failure is **predictable from the
provenance already in the file**. Classify before you run, not after.

| class | n | modules | expectation |
|---|---|---|---|
| **FULL** — argv + env + commit + hashed inputs | 25 of 30 cited | most of the sweep | **must be bit-identical.** A failure here is a real finding |
| **PARTIAL** — argv + env, no commit | 2 | `r6_within_source`, `r7_matched_pools` | bit-identical expected. Commit absence is **expected and benign**: they ran on a box with no `.git`. `provenance.git_state()` now says so explicitly |
| **NONE** — no provenance block | 3 | `e33_logit_v2`, `e38_geometry`, `e49_stability` | **these are the risk.** They predate the provenance layer (committed `1a6f5df`, 2026-08-14 20:05 PDT). Their repro modules were hand-written from the scripts' own defaults, not from a recorded `argv` |

Note the three NONE modules are exactly the three that needed hand-written modules, because there
was no `argv` to generate one from. If anything fails, look there first.

## 3. PROCEDURE — per module, in order

Run modules **one at a time**. Start with the fast ones so failures surface early.

```bash
M=cv5_sensitivity                      # the module id
OUT=$(grep -o 'OUTPUTS=([^)]*)' repro/exp/$M.sh | sed 's/OUTPUTS=(//;s/)//')

# 1. BACK UP every declared output BEFORE running
for f in $OUT; do cp "$f" "/tmp/t1_before_$(basename $f)"; done

# 2. RUN
bash repro/exp/$M.sh

# 3. DIFF THE PAYLOAD — this is the actual test
.venv/bin/python - <<'PY'
import json, sys, os, glob
sys.path.insert(0, "src")
from provenance import canonical_payload_sha
for new in sys.argv[1:]:
    old = f"/tmp/t1_before_{os.path.basename(new)}"
    a, b = json.load(open(old)), json.load(open(new))
    ha, hb = canonical_payload_sha(a), canonical_payload_sha(b)
    print(f"{os.path.basename(new)}: {ha[:16]} -> {hb[:16]}  "
          f"{'BIT-IDENTICAL' if ha == hb else '*** PAYLOAD MOVED ***'}")
PY
```

`canonical_payload_sha` excludes the provenance block by construction, so a timestamp or hostname
change does **not** move it. If it moves, a **number** moved.

### Suggested order (fast first)

```
cv5_sensitivity  cv2_position  e58_algebra  e59_read_dose  d1_union  e38_geometry
e37_rank_70m  e37_rank_160m  e49_stability  e33_logit_v2  cv3_margins  cv4_capability
cv7_rung  d3_by_family  cv6_ladder  e65_ckpt_geometry  cv1_competence  e48b_exposure
e48_crossover  e48_gate  e52_factorial  e36_qladder
```

The last four are the long ones (15 min, 25 min, 40 min, 1.3-2 h, 1.5-2 h). `cv3_margins` is already
verified **BIT-IDENTICAL** (6 min) — re-running it is a useful sanity check that your harness works.

### Running in the background

Each module writes to stdout; run detached and be woken when it exits, rather than polling:

```bash
nohup bash repro/exp/$M.sh > /tmp/t1_$M.log 2>&1 &
```

Then check the payload diff when it completes. **Do not run modules in parallel**: several are
multi-threaded, and `e60_fitter_determinism` established that fits are not bit-reproducible above 8
threads on this machine. Oversubscribing the CPU risks changing reduction order.

## 3.5 THE LOOP, CONCRETELY — and the ONE condition that stops it

You are not being stewarded. Run to completion unattended unless the stop condition below fires.

```
preflight()                              # tools/artifact_provenance_diff.py
if preflight reports ANY unexplained delta:
    STOP before running anything. Alert the operator.

for M in MODULES:                        # 22 of them, STRICTLY SEQUENTIAL, one at a time
    backup(outputs of M)                 # cp each declared OUTPUT to /tmp/t1_before_<name>
    run(M)                               # nohup, detached; wake when it exits
    verdict = payload_sha(before) == payload_sha(after)

    if BIT-IDENTICAL:
        record; continue                                     # the expected case

    if DID NOT RUN (missing input / crash):
        record WHICH input, exactly; continue                # not a reproduction failure

    if MOVED:                            # a number changed
        record which field moved
        rung = walk the ladder in section 4                  # ~10 min, CPU, no GPU
        rerun preflight()                                    # seconds

        if preflight now reports a NEW unexplained delta:
            -> SHARED CAUSE. STOP THE SWEEP. Alert the operator.
        elif M in {e33_logit_v2, e38_geometry, e49_stability}:
            -> EXPECTED. These are the pre-provenance three (section 2). Record and CONTINUE.
        else:
            -> LOCAL CAUSE. Record the rung and the field. CONTINUE.

report the section 5 table
```

### The stop condition, stated plainly

**Stop only when the cause is SHARED.** That is the whole rule, and the reason is mechanical: a
shared cause — a drifted corpus, a changed common input, an environment shift — is inherited by
every module that has not run yet, so their results become uninterpretable and the remaining hours
are wasted. A local cause is confined to one module and costs nothing to carry.

The test for "shared" is not a judgement call. Re-run the preflight: it hashes every recorded input
in the tree in seconds. If it comes back clean, the cause was local. If a new unexplained delta
appeared, it is shared.

### What MOVED is, and is not

A MOVED payload is **a finding, not your failure**. Three of these modules are *expected* to be at
risk, and that expectation was written down before the sweep started (section 2). Recording
"`e49_stability` MOVED, rung 4: script changed since the run, original present in
`repro/scripts_at_run/`" is a complete and successful outcome for that module.

What is NOT acceptable is stopping the sweep because a number changed, or continuing past a shared
cause because the sweep "should" finish.

## 4. WHEN SOMETHING DOES NOT REPRODUCE

Do not speculate. Walk this ladder, which is the one that diagnosed E66:

1. **What moved?** Diff the payload key-by-key. A single changed field is a different problem from a
   whole table moving.
2. **Corpus.** `sha256` the relevant `corpora/*.jsonl` against `corpora/manifest.json` /
   `manifest_ood.json`. All 11 hashed corpora were byte-identical on 2026-08-29.
   **`OOD_News_2024_dedup.jsonl` is in neither manifest and has no recorded hash** — if a failing
   module consumes it, that is your first suspect and it should be hashed into the manifest.
3. **Inputs.** The provenance block lists every input with its SHA-256. Re-hash them. A changed
   upstream file is the most common cause and is detectable, not mysterious.
4. **Script.** `provenance.script.sha256` versus the file on disk. If they differ, the code changed
   since the result was written; `repro/scripts_at_run/` carries the original by content address,
   and `repro/scripts_at_run/EXCEPTIONS.json` lists the ones that are declared unobtainable.
5. **Device / threads.** Confirm CPU. Then check thread count: E60 measured exact agreement at 1, 4
   and 8 threads and `1.09e-04` divergence above that.
6. **Storage dtype.** Operators are stored `float16`. One fp16 step in the `[1,2)` binade is
   `9.766e-04`. A difference at that scale is storage, not science. E66c's target reproduced to
   `2.441e-04`, inside one step.

Report the rung at which you found it. **"It does not reproduce" without a rung is not a result.**

## 5. WHAT TO REPORT

One table, and nothing else:

| module | outputs | payload before → after | verdict | if moved: rung from §4, and what field |
|---|---|---|---|---|

Then one line: `N of 22 bit-identical`.

**Verdicts are three-way**, matching this repository's protocol:
* **BIT-IDENTICAL** — payload hash unchanged.
* **MOVED** — payload hash changed. Say which field and which §4 rung explains it. This is a
  finding, not a failure of yours; report it plainly.
* **DID NOT RUN** — missing input, crash, missing `.pt`. Say which input, exactly. Do not
  substitute a different input to make it run.

## 6. WHAT NOT TO DO

* Do not run on GPU (§1.1).
* Do not run modules in parallel (§3).
* Do not adjust any tolerance, threshold or flag to make something pass.
* Do not edit `results/*.json`.
* Do not delete or regenerate any `.pt`.
* Do not run the anonymisation scrub. Tell the operator the sweep is done; ordering is theirs.
* If a module wants to *fit* an operator (tier T2), stop. That is not this job.

## 7. CONTEXT YOU MAY NEED

* `CLAUDE.md` — the working rules and the three tiers.
* `docs/reproducibility/REVIEWER_REPRO.md` — what is verified and what is not, with numbers.
* `repro/exp/_lib.sh` — the harness every module sources; it already asserts that outputs exist and
  carry a provenance block whose script hash matches.
* Already verified, do not redo: T0 13/13; corpora 11/11 byte-identical; `cv3_margins`
  bit-identical; `e48c`, `e33b`, `r9`, `cv1` payloads bit-identical on re-run.

## 8. KICKOFF

Paste this into a fresh conversation:

> Read `docs/reproducibility/T1_SWEEP_SPEC.md` and execute it. You are running the T1
> reproducibility sweep: 22 modules in `repro/exp/` that re-score the stored `.pt` operators against
> the evaluation battery. For each, report whether the stored payload comes back bit-identical.
>
> Run the §0.5 preflight first. Then: CPU only, one module at a time, never in parallel, never
> change the thread count, never adjust a tolerance to make something pass, never edit
> `results/*.json`. You are not refitting operators — that is T2 and it is out of scope.
>
> Run each module detached and wake on completion rather than polling. After each, diff the payload
> with `canonical_payload_sha` (§3) and classify BIT-IDENTICAL / MOVED / DID NOT RUN. On a MOVED
> payload, follow §3.5: walk the six-rung ladder in §4, re-run the preflight, and **stop only if the
> cause is shared** — otherwise record the rung and keep going. "It does not reproduce" without a
> rung is not a result. Run to completion unattended; the operator is not watching.
>
> Report the §5 table and nothing else. Do not run the anonymisation scrub; tell the operator the
> sweep is done.
