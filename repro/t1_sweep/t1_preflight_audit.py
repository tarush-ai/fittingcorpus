#!/usr/bin/env python3
"""
t1_preflight_audit.py — the §0.5 gate, computed rather than asserted.

WHY THIS EXISTS. `tools/artifact_provenance_diff.py` prints DELTA / STAMP_ONLY / NO_PROVENANCE
and a total input-hash count. It does NOT print the two numbers T1_SWEEP_SPEC.md §0.5 actually
gates on:

    "385 of 385 .pt input hashes match. No operator has changed."
    "43 .json files have a moved file hash ... 0 unexplained."

Those were a human reading of the tool's output. A gate you have to re-derive by hand is a gate
that silently rots, so this recomputes both, plus the thing the spec's prose asserts but the tool
never checks: whether a moved .json actually moved a NUMBER, or only a hostname/timestamp stamp.

THE PAYLOAD TEST. For each .json input whose recorded hash no longer matches, we walk git history
for the blob whose file hash IS the recorded one, then compare `canonical_payload_sha` of that
blob against the file on disk. Equal payload => the file hash moved but no number did (the
anonymisation scrub). Different payload => the file was genuinely re-run since the consumer
recorded it. Not found in git => the recorded version was never committed (it lived on disk
between a run and a scrub).

WHAT THIS DOES NOT COVER. It says nothing about whether a result is CORRECT, only whether the
inputs to it are unchanged. Provenance identity is necessary, not sufficient -- the same caveat
`tools/artifact_provenance_diff.py` carries in its own docstring.

  .venv/bin/python repro/t1_sweep/t1_preflight_audit.py
  .venv/bin/python repro/t1_sweep/t1_preflight_audit.py --skip-git    # fast, no payload test
"""
import argparse, collections, glob, hashlib, json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "src"))
from provenance import canonical_payload_sha  # noqa: E402


def fsha(b):
    return hashlib.sha256(b).hexdigest()


def sha(p):
    if not os.path.isfile(p):
        return None
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-git", action="store_true",
                    help="skip the payload test (which walks git history and is the slow part)")
    a = ap.parse_args()
    os.chdir(ROOT)

    recorded = collections.defaultdict(set)   # path -> {recorded sha256}
    pt_refs = pt_ok = 0
    for p in sorted(glob.glob("results/**/*.json", recursive=True)):
        try:
            o = json.load(open(p))
        except Exception:
            continue
        if not isinstance(o, dict):
            continue
        for i in ((o.get("provenance") or {}).get("inputs") or []):
            ip, ish = i.get("path"), i.get("sha256")
            if not ip or not ish:
                continue
            recorded[ip].add(ish)
            if ip.endswith(".pt"):
                pt_refs += 1
                if sha(ip) == ish:
                    pt_ok += 1

    moved_pt, moved_json, missing = [], [], []
    for path, shas in sorted(recorded.items()):
        live = sha(path)
        if live is None:
            missing.append(path)
        elif live not in shas:
            (moved_pt if path.endswith(".pt") else moved_json).append(path)

    # TWO DEFENSIBLE COUNTS, and they differ, so both are printed rather than one being picked.
    # A file can be consumed by several results that recorded DIFFERENT hashes for it, because it
    # was re-run between them. `strict` counts a path as moved if ANY consumer's record misses
    # (this is what tools/artifact_provenance_diff.py flags, and is the spec's 43). `union`
    # counts it moved only if NO consumer recorded the current content (38). The gap is exactly
    # the files re-run mid-programme.
    strict = sorted({p for p, shas in recorded.items()
                     if not p.endswith(".pt") and os.path.isfile(p) and sha(p) not in shas
                     or (not p.endswith(".pt") and os.path.isfile(p)
                         and any(sha(p) != s for s in shas))})
    print(f"  .pt  input-hash references : {pt_ok}/{pt_refs} match     "
          f"({len(moved_pt)} operator(s) drifted)")
    print(f"  .json moved (strict/union) : {len(strict)} / {len(moved_json)}"
          "   [strict = any consumer's record misses; union = no consumer's record matches]")
    print(f"  unique inputs MISSING      : {len(missing)}  {missing if missing else ''}")

    # corpora, rung 2 of SPEC §4
    n_cor, bad_cor = 0, []
    for mf in ("corpora/manifest.json", "corpora/manifest_ood.json"):
        if not os.path.isfile(mf):
            continue
        for k, v in json.load(open(mf)).items():
            if isinstance(v, dict) and "sha256" in v:
                n_cor += 1
                if sha(os.path.join("corpora", v["file"])) != v["sha256"]:
                    bad_cor.append(v["file"])
    print(f"  corpora vs manifest        : {n_cor - len(bad_cor)}/{n_cor} byte-identical"
          + (f"  BAD={bad_cor}" if bad_cor else ""))

    if not a.skip_git and moved_json:
        same, diff, notfound = [], [], []
        for f in moved_json:
            cur = open(f, "rb").read()
            revs = subprocess.run(["git", "rev-list", "--all", "--", f],
                                  capture_output=True, text=True).stdout.split()
            hit = None
            for r in revs:
                b = subprocess.run(["git", "show", f"{r}:{f}"], capture_output=True).stdout
                if b and fsha(b) in recorded[f]:
                    hit = b
                    break
            if hit is None:
                notfound.append(f)
                continue
            try:
                if canonical_payload_sha(json.loads(hit)) == canonical_payload_sha(json.loads(cur)):
                    same.append(f)
                else:
                    diff.append(f)
            except Exception:
                notfound.append(f)
        print(f"\n  payload test on the {len(moved_json)} moved .json:")
        print(f"    payload IDENTICAL (stamp/scrub only) : {len(same)}")
        print(f"    payload MOVED (genuinely re-run)     : {len(diff)}")
        for f in diff:
            print(f"       * {f}")
        print(f"    recorded version not in git history  : {len(notfound)}")
        for f in notfound:
            print(f"       ? {f}")

    gate_ok = not moved_pt and not bad_cor
    print(f"\n  §0.5 GATE: {'PASS — no operator drift, no corpus drift' if gate_ok else 'FAIL'}")
    return 0 if gate_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
