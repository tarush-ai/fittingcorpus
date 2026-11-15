#!/usr/bin/env python3
"""
t1_predict_moved.py — prove, before the modules run, WHY five payloads must move.

`repro/t1_sweep/t1_classify.py` finds five T1 modules whose script on disk differs from the script
recorded in the result it reproduces, and diffing each against its vaulted original in
`repro/scripts_at_run/` shows every changed line is a pre-registration PATH STRING, rewritten when
`specs/...` became `docs/experiments/preregs/...`. Those strings are written into the payload, and
`canonical_payload_sha` hashes everything except the `provenance` block. So the payload must move.

This script does not wait to find out. It takes the STORED payload, applies the exact string
rewrite the current script would apply, and recomputes the hash. That establishes the conditional:

    IF the numbers reproduce bit-identically, THEN the payload differs ONLY in prereg-family keys.

which is precisely the prediction in docs/reproducibility/T1_SWEEP_PREDICTIONS.md. When the module
actually lands, the observed field diff is compared against the prediction and either confirms it
or falsifies it -- a numeric field moving falsifies "documentation only" outright.

WHAT THIS DOES NOT DO. It cannot prove the numbers reproduce; only the sweep can. It proves the
path-string mechanism is SUFFICIENT to move the hash, not that it is the only thing that moved.

  .venv/bin/python repro/t1_sweep/t1_predict_moved.py
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "src"))
from provenance import canonical_payload_sha  # noqa: E402

# module -> (stored result, vaulted original script, current script)
TARGETS = {
    "e59_read_dose": ("results/e59_read_dose_410m.json",
                      "repro/scripts_at_run/808803674ad1__t59_read_dose.py",
                      "experiments/t59_read_dose.py"),
    "e65_ckpt_geometry": ("results/e65_ckpt_geometry_410m.json",
                          "repro/scripts_at_run/8388d47ba755__t65_ckpt_geometry.py",
                          "experiments/t65_ckpt_geometry.py"),
    "e48_crossover": ("results/e48_crossover_410m.json",
                      "repro/scripts_at_run/a76a103f93a2__t48_crossover.py",
                      "experiments/t48_crossover.py"),
    "e52_factorial": ("results/e52_factorial_410m_rstrip.json",
                      "repro/scripts_at_run/6d74ea7f4ef2__t52_factorial.py",
                      "experiments/t52_factorial.py"),
    "e36_qladder": ("results/e36_qladder_410m_rstrip.json",
                    "repro/scripts_at_run/ef457ce679e6__t36_qladder.py",
                    "experiments/t36_qladder.py"),
}

# the cleanup rewrite, applied to any string value in the payload
REWRITES = [
    ("specs/experiments/", "docs/experiments/preregs/"),
    ("specs/archive/prereg/", "docs/experiments/preregs/superseded/"),
]


def rewrite(o):
    if isinstance(o, str):
        for a, b in REWRITES:
            o = o.replace(a, b)
        return o
    if isinstance(o, dict):
        return {k: rewrite(v) for k, v in o.items()}
    if isinstance(o, list):
        return [rewrite(v) for v in o]
    return o


def flat(o, pre=""):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from flat(v, f"{pre}.{k}" if pre else str(k))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from flat(v, f"{pre}[{i}]")
    else:
        yield pre, o


def main():
    os.chdir(ROOT)
    allpred = {}
    for mid, (res, vault, cur) in TARGETS.items():
        if not os.path.isfile(res):
            print(f"  {mid}: stored result missing ({res})")
            continue
        stored = json.load(open(res))
        predicted = rewrite(stored)
        h0, h1 = canonical_payload_sha(stored), canonical_payload_sha(predicted)

        fo, fn = dict(flat({k: v for k, v in stored.items() if k != "provenance"})), \
            dict(flat({k: v for k, v in predicted.items() if k != "provenance"}))
        changed = sorted(k for k in fo if k in fn and fo[k] != fn[k])
        numeric = [k for k in changed
                   if isinstance(fo[k], (int, float)) and not isinstance(fo[k], bool)]

        # is the code difference really nothing but these strings?
        codediff = "n/a"
        if os.path.isfile(vault) and os.path.isfile(cur):
            a, b = open(vault).read().splitlines(), open(cur).read().splitlines()
            import difflib
            hunks = [l for l in difflib.unified_diff(a, b, n=0)
                     if l.startswith(("+", "-")) and not l.startswith(("+++", "---"))]
            nonpath = [l for l in hunks
                       if "specs/" not in l and "docs/experiments/preregs/" not in l]
            codediff = f"{len(hunks)} changed lines, {len(nonpath)} NOT a prereg path"

        verdict = ("MOVED (prereg strings only)" if h0 != h1 and not numeric
                   else "MOVED with NUMERIC change" if numeric
                   else "would NOT move")
        print(f"\n  {mid}")
        print(f"    stored payload sha : {h0[:16]}")
        print(f"    predicted after    : {h1[:16]}   -> {verdict}")
        print(f"    fields changed     : {len(changed)}  {changed}")
        print(f"    numeric changed    : {len(numeric)}  {numeric if numeric else '(none)'}")
        print(f"    script diff        : {codediff}")
        allpred[mid] = {"stored_sha": h0, "predicted_sha": h1, "fields": changed,
                        "numeric": numeric, "script_diff": codediff}

    out = "docs/reproducibility/t1_moved_prediction.json"
    json.dump(allpred, open(out, "w"), indent=1)
    print(f"\n  wrote {out}")
    bad = [m for m, v in allpred.items() if v["numeric"]]
    print("  PREDICTION: these five report MOVED, prereg-family string keys only, zero numeric "
          "movement." if not bad else f"  WARNING: numeric movement predicted for {bad}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
