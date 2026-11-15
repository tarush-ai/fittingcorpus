#!/usr/bin/env python3
"""t0_receipt.py — run every T0 module in a throwaway copy, and store what happened.

T0 modules write their outputs back into results/, re-stamping provenance. Running them in place
would make the local results differ from the mirror even when every number is identical. So this
copies the tracked tree and results/ into a temporary directory, links .venv and jacobian-lens/,
runs `repro/RUN_ALL.sh --tier T0` there, and compares each output's payload hash (the content,
provenance excluded) with the stored file's. Nothing in this repository's results/ is touched.

    .venv/bin/python tools/t0_receipt.py          # writes docs/reproducibility/T0_RECEIPT.json

The receipt records the commit, the date, RUN_ALL's exit status, and for every output whether
its recomputed payload is identical to the stored one. For any that are not, it lists the payload
fields that differ, so a difference in a pre-registration hash is distinguishable from a moved
number.

WHAT THIS DOES NOT COVER: T1 (re-scoring the stored maps) and T2 (refitting). A T0 pass shows that
the statistics follow from the stored results, not that the stored results follow from the maps.
"""
from __future__ import annotations

import datetime as dt
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "docs", "reproducibility", "T0_RECEIPT.json")


def flat(o, pre=""):
    out = {}
    if isinstance(o, dict):
        for k, v in o.items():
            out.update(flat(v, f"{pre}.{k}"))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            out.update(flat(v, f"{pre}[{i}]"))
    else:
        out[pre] = o
    return out


def main() -> int:
    commit = subprocess.run(["git", "-C", ROOT, "rev-parse", "--short=12", "HEAD"],
                            capture_output=True, text=True).stdout.strip()
    dirty = bool(subprocess.run(["git", "-C", ROOT, "status", "--porcelain", "--untracked-files=no"],
                                capture_output=True, text=True).stdout.strip())
    tracked = subprocess.run(["git", "-C", ROOT, "ls-files"], capture_output=True, text=True).stdout.split()
    modules = []
    for m in sorted(glob.glob(os.path.join(ROOT, "repro", "exp", "*.sh"))):
        t = open(m).read()
        if 'MODULE_TIER="T0"' in t:
            outs = re.search(r"OUTPUTS=\((.*?)\)", t, re.S).group(1).split()
            modules.append((os.path.basename(m)[:-3], outs))
    with tempfile.TemporaryDirectory(prefix="t0_receipt_") as tmp:
        for f in tracked:
            dst = os.path.join(tmp, f)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(os.path.join(ROOT, f), dst)
        shutil.copytree(os.path.join(ROOT, "results"), os.path.join(tmp, "results"))
        for link in (".venv", "jacobian-lens"):
            os.symlink(os.path.join(ROOT, link), os.path.join(tmp, link))
        run = subprocess.run(["bash", "repro/RUN_ALL.sh", "--tier", "T0"], cwd=tmp,
                             capture_output=True, text=True)
        summary = re.sub(r"\x1b\[[0-9;]*m", "", run.stdout).strip().splitlines()[-3:]
        rows = []
        for name, outs in modules:
            for o in outs:
                a = json.load(open(os.path.join(ROOT, o)))
                p = os.path.join(tmp, o)
                if not os.path.exists(p):
                    rows.append({"module": name, "output": o, "identical": False, "why": "no output"})
                    continue
                b = json.load(open(p))
                same = a["provenance"]["payload_sha256"] == b["provenance"]["payload_sha256"]
                row = {"module": name, "output": o, "identical": same}
                if not same:
                    a.pop("provenance"); b.pop("provenance")
                    fa, fb = flat(a), flat(b)
                    row["fields_that_differ"] = sorted(k for k in set(fa) | set(fb) if fa.get(k) != fb.get(k))
                rows.append(row)
    n_same = sum(r["identical"] for r in rows)
    receipt = {
        "what": "every T0 module run in a temporary copy; each output's payload compared with the stored file",
        "written_by": "tools/t0_receipt.py",
        "utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "commit": commit, "working_tree_dirty": dirty,
        "run_all_exit_status": run.returncode, "run_all_summary": summary,
        "n_modules": len(modules), "n_outputs": len(rows), "n_payload_identical": n_same,
        "outputs": rows,
    }
    json.dump(receipt, open(OUT, "w"), indent=1)
    print(f"RUN_ALL exit {run.returncode}; {len(modules)} modules; {n_same} of {len(rows)} outputs "
          f"payload-identical; wrote {os.path.relpath(OUT, ROOT)}")
    for r in rows:
        if not r["identical"]:
            print(f"  differs: {r['output']}: {r.get('fields_that_differ') or r.get('why')}")
    return 0 if run.returncode == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
