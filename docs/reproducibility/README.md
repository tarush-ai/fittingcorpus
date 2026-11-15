# docs/reproducibility/ — does the code do what the paper says, and do the results regenerate?

This folder records how the implementation and the stored results were checked. Whether the
experiments are the right experiments is a separate question, in [`../validity/`](../validity/).
To run the checks yourself, start at [`../../repro/README.md`](../../repro/README.md).

## What has been checked

| check | result | record | to re-run |
|---|---|---|---|
| **T0**: every statistic recomputed from the stored results | all 15 modules pass. 14 recompute a payload identical to the stored one; the 15th (E28.3, `r8_ladder_flatness.json`) reproduces every number and differs only in the pre-registration hash it records, because that document's wording changed after the run. The text it ran against is archived in `preregs/as_registered/` | [`T0_RECEIPT.json`](T0_RECEIPT.json) | `tools/t0_receipt.py` |
| **T1**: every read re-scored from the stored maps, on CPU (2026-08-29 to 30) | 16 of 22 modules bit-identical; 22 of 22 reproduce every scientific quantity. The six that moved differ only in a pre-registration path or a wall-clock field. One module's recipe was wrong (the E33 band was one layer short) and was fixed | [`T1_SWEEP_RESULTS.md`](T1_SWEEP_RESULTS.md), [`T1_FINDING_E33_BAND.md`](T1_FINDING_E33_BAND.md) | `bash repro/RUN_ALL.sh --tier T1` |
| **T2**: maps refitted on a GPU, as implementation checks | two refits, chosen to straddle the date the provenance layer was added. A post-provenance map refits to 2.441e-04, inside one fp16 storage step; the older E48 panel refits to 1.1e-03, attributed to unrecorded machine state, and no read changes. This is not a statistical replication | `results/e66c_post_provenance_repro.json`, `results/e66b_determinism_floor.json` | `bash repro/RUN_ALL.sh --tier T2` |
| **the read path** is the released library's, bit for bit | `max\|diff\| = 0` against `JacobianLens.apply`. This does not cover the readout *position*, which is how the readout defect stayed green | `tests/test_anchor_fidelity.py` | `./lab verify` |
| **every producing script is obtainable** | 91 stamped results files: 46 produced by the script on disk now, 44 by an earlier version archived byte for byte in `repro/scripts_at_run/`, 1 by uncommitted code and declared lost | [`SCRIPT_PROVENANCE.md`](SCRIPT_PROVENANCE.md) | `tools/script_provenance.py --verify` (health check H13) |
| **every pinned pre-registration is obtainable** | every pre-registration version a stored result pins by SHA-256 is in `preregs/as_registered/`, byte for byte | [`../experiments/REGISTRATION_LEDGER.md`](../experiments/REGISTRATION_LEDGER.md) | `tools/registration_ledger.py --report` |
| **the mirror holds what was uploaded** | 953 files (16.22 GB) frozen with their hashes before the move to the author's account. Of its 403 large files, 333 also have a hash recorded independently in this repository, and none conflicts. One hand-typed row in `ARTIFACTS.md` was wrong and has been corrected | [`HF_MIRROR_MANIFEST.tsv`](HF_MIRROR_MANIFEST.tsv) | `tools/hf_mirror_manifest.py --verify --repo Tarush-AI/fittingcorpus` and `--cross-check` |
| **a blind reimplementation** (2026-08-20) | an independent implementation written from the methods text alone, without this code, found the readout defect: 157 of 551 items had been scored at a token that does not occur in the sequence | [`../experiments/READOUT_DEFECT.md`](../experiments/READOUT_DEFECT.md) | — |

## What is not reproducible, and why

* **Corpus plaintext is not shipped.** It is third-party text and two sources are CC BY-SA, which the
  mirror's CC BY 4.0 cannot carry. `bash repro/06_data.sh --build` rebuilds it at pinned dataset
  revisions, and the builds are checked against per-file hashes in `corpora/`.
* **Maps fitted before the provenance layer** refit to about 1.1e-03, not bit-identically, because
  the machine and library state of those runs was not recorded. The fitter's own determinism floor
  is about 1e-06. A perturbation of that size moves no read.
* **Reads scored on a GPU** differ from CPU by up to 2.774e-04 (`results/d2_device_crossvalidation.json`),
  so T1 is defined on CPU.
* **One results file's producing script was never committed**, and is declared in
  `repro/scripts_at_run/EXCEPTIONS.json`.

## Files here

| file | holds |
|---|---|
| [`REPRODUCIBILITY.md`](REPRODUCIBILITY.md) | the reference behind `repro/README.md`: the environment, what the local gate asserts, running on a GPU, the standing audit (H1–H13), where new work goes |
| [`COMPUTE.md`](COMPUTE.md) | the measured hardware model, every price paid, provisioning and teardown |
| [`ARTIFACTS.md`](ARTIFACTS.md) | the fitted maps, with their SHA-256 and what produced each |
| [`HF_MIRROR_MANIFEST.tsv`](HF_MIRROR_MANIFEST.tsv) | every file on the mirror, with its size and hash |
| [`SCRIPT_PROVENANCE.md`](SCRIPT_PROVENANCE.md) | results file → producing script → where to get its exact bytes |
| [`T0_RECEIPT.json`](T0_RECEIPT.json) | the latest T0 run, output by output |
| [`T1_SWEEP_SPEC.md`](T1_SWEEP_SPEC.md), [`T1_SWEEP_PREDICTIONS.md`](T1_SWEEP_PREDICTIONS.md), [`T1_SWEEP_RESULTS.md`](T1_SWEEP_RESULTS.md), `t1_evidence/` | the T1 sweep: its plan, its predictions written before it ran, and what happened |
| `readout_exposure.json`, `readout_exposure.txt` | the readout-correction ledger: for every results file, whether it was produced at the corrected readout. Regenerate with `tools/readout_exposure.py` |
| [`PAYLOAD_REDACTIONS.md`](PAYLOAD_REDACTIONS.md) | the filesystem paths removed from three results payloads for the anonymous review, with each payload hash before and after. No numeric value changed |
