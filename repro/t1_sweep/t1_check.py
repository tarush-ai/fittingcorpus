#!/usr/bin/env python3
"""T1 sweep checker: payload diff (rung 1-6 ladder) and shared-cause test."""
import json, os, sys, glob, hashlib, subprocess, time
sys.path.insert(0, "src")
from provenance import canonical_payload_sha

SP = os.environ.get("SP") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "_run")
os.makedirs(os.path.join(SP, "before"), exist_ok=True)
os.makedirs(os.path.join(SP, "logs"), exist_ok=True)
FP16_STEP = 9.766e-04


def sha(p):
    if not os.path.isfile(p):
        return None
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def flat(o, pre=""):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from flat(v, f"{pre}.{k}" if pre else str(k))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from flat(v, f"{pre}[{i}]")
    else:
        yield pre, o


def corpora_check():
    """Rung 2: every hashed corpus vs its manifest."""
    bad = []
    n = 0
    for mf in ("corpora/manifest.json", "corpora/manifest_ood.json"):
        if not os.path.isfile(mf):
            continue
        for k, v in json.load(open(mf)).items():
            if not isinstance(v, dict) or "sha256" not in v:
                continue
            n += 1
            p = os.path.join("corpora", v["file"])
            if sha(p) != v["sha256"]:
                bad.append(f"{k}:{v['file']}")
    return n, bad


def pt_state():
    """Preflight state that a SHARED cause would move: .pt input hashes + torch + corpora."""
    tmp = f"{SP}/prov_now.json"
    subprocess.run([".venv/bin/python", "tools/artifact_provenance_diff.py", "--json", tmp],
                   capture_output=True)
    rows = json.load(open(tmp))
    pt_bad, missing, torch_d = set(), set(), set()
    for r in rows:
        for d in r.get("deltas", []):
            if d.startswith(("input CHANGED: ", "input MISSING: ")):
                p = d.split(": ", 1)[1]
                if p.endswith(".pt"):
                    pt_bad.add(p)
                elif d.startswith("input MISSING: "):
                    missing.add(p)
            elif d.startswith("torch "):
                torch_d.add(d)
    n_cor, bad_cor = corpora_check()
    return {"pt_bad": sorted(pt_bad), "missing": sorted(missing),
            "torch": sorted(torch_d), "corpora_bad": bad_cor, "n_corpora": n_cor}


def cmd_baseline():
    st = pt_state()
    json.dump(st, open(f"{SP}/baseline_state.json", "w"), indent=1)
    print(f"  baseline: .pt drifted={len(st['pt_bad'])}  missing={len(st['missing'])} "
          f"{st['missing']}  corpora {st['n_corpora'] - len(st['corpora_bad'])}/{st['n_corpora']} ok  "
          f"torch deltas={st['torch']}")


def cmd_shared():
    base = json.load(open(f"{SP}/baseline_state.json"))
    now = pt_state()
    new = []
    if set(now["pt_bad"]) - set(base["pt_bad"]):
        new.append(f".pt DRIFTED: {sorted(set(now['pt_bad']) - set(base['pt_bad']))}")
    if set(now["missing"]) - set(base["missing"]):
        new.append(f"input MISSING: {sorted(set(now['missing']) - set(base['missing']))}")
    if now["corpora_bad"] != base["corpora_bad"]:
        new.append(f"CORPUS moved: {now['corpora_bad']}")
    if set(now["torch"]) - set(base["torch"]):
        new.append(f"torch: {sorted(set(now['torch']) - set(base['torch']))}")
    if new:
        print("  SHARED CAUSE — new unexplained delta since baseline:")
        for x in new:
            print("     " + x)
        return 1
    print("  preflight re-run clean vs baseline (no .pt drift, no corpus move, no env shift)"
          " -> cause is LOCAL")
    return 0


def ladder(old, new, newpath):
    """Rungs 1-6 for one moved payload."""
    out = []
    fo, fn = dict(flat(old)), dict(flat(new))
    ko, kn = set(fo), set(fn)
    changed = sorted(k for k in ko & kn if fo[k] != fn[k])
    added, removed = sorted(kn - ko), sorted(ko - kn)
    out.append(f"rung1 fields: {len(changed)} changed, {len(added)} added, {len(removed)} removed")
    for k in changed[:8]:
        out.append(f"        {k}: {fo[k]!r} -> {fn[k]!r}")
    if len(changed) > 8:
        out.append(f"        ... and {len(changed)-8} more changed fields")
    for k in (added[:4] + removed[:4]):
        out.append(f"        {'+' if k in kn else '-'} {k}")
    # rung 6 magnitude
    mx, mxk = 0.0, None
    for k in changed:
        a, b = fo[k], fn[k]
        if isinstance(a, (int, float)) and isinstance(b, (int, float)) \
                and not isinstance(a, bool) and not isinstance(b, bool):
            d = abs(float(a) - float(b))
            if d > mx:
                mx, mxk = d, k
    if mxk:
        out.append(f"rung6 max |Δ| numeric = {mx:.6g} at {mxk}  "
                   f"({'INSIDE' if mx <= FP16_STEP else 'ABOVE'} one fp16 step {FP16_STEP:.3e})")
    else:
        out.append("rung6 no numeric field moved (structural/string change only)")
    # rung 2
    n_cor, bad_cor = corpora_check()
    out.append(f"rung2 corpora: {n_cor - len(bad_cor)}/{n_cor} match manifest"
               + (f"  BAD={bad_cor}" if bad_cor else ""))
    # rung 3: inputs recorded by the OLD file, re-hashed now
    op = old.get("provenance") or {}
    ins = op.get("inputs") or []
    bad_in = [i["path"] for i in ins if i.get("path") and i.get("sha256")
              and sha(i["path"]) != i["sha256"]]
    out.append(f"rung3 inputs: {len(ins) - len(bad_in)}/{len(ins)} recorded input hashes match"
               + (f"  CHANGED={bad_in}" if bad_in else ""))
    # rung 4: script
    sc = op.get("script") or {}
    if sc.get("path") and sc.get("sha256"):
        live = sha(sc["path"])
        same = live == sc["sha256"]
        vault = glob.glob(f"repro/scripts_at_run/{sc['sha256'][:12]}__*")
        out.append(f"rung4 script {sc['path']}: {'UNCHANGED' if same else 'CHANGED since the run'}"
                   + ("" if same else
                      (f"; original present in {vault[0]}" if vault
                       else "; original NOT in scripts_at_run")))
    else:
        out.append("rung4 script: OLD FILE HAS NO PROVENANCE (pre-provenance module)")
    # rung 5
    ne = (new.get("provenance") or {}).get("env") or {}
    oe = op.get("env") or {}
    out.append(f"rung5 device/threads: new run torch={ne.get('torch')} "
               f"threads={ne.get('threads')} | recorded torch={oe.get('torch')} "
               f"threads={oe.get('threads')}")
    return out


def cmd_diff(module, rc, secs, outs):
    verdicts, lines = [], []
    for f in outs:
        key = f.replace("/", "_")
        b = f"{SP}/before/{key}"
        if not os.path.isfile(f):
            verdicts.append("DID_NOT_RUN")
            lines.append(f"  {f}: OUTPUT ABSENT after run")
            continue
        if not os.path.isfile(b):
            verdicts.append("NO_BASELINE")
            lines.append(f"  {f}: no pre-run baseline (file did not exist before)")
            continue
        try:
            a, n = json.load(open(b)), json.load(open(f))
        except Exception as e:
            verdicts.append("DID_NOT_RUN")
            lines.append(f"  {f}: unparseable ({e})")
            continue
        # AN UNWRITTEN OUTPUT IS NOT A REPRODUCTION. e48_crossover aborted on its own C0 control
        # after 37s and never wrote its file; comparing the untouched file to its own backup
        # returned BIT-IDENTICAL, a false green. If the file predates this module's run it was
        # never written, whatever the hashes say.
        if secs is not None and os.path.getmtime(f) < (time.time() - float(secs) - 5):
            verdicts.append("DID_NOT_RUN")
            lines.append(f"  {f}: OUTPUT NOT WRITTEN — mtime predates this run "
                         f"(module aborted before writing; hash comparison is meaningless)")
            continue
        ha, hb = canonical_payload_sha(a), canonical_payload_sha(n)
        same = ha == hb
        verdicts.append("BIT_IDENTICAL" if same else "MOVED")
        lines.append(f"  {f}: {ha[:16]} -> {hb[:16]}  "
                     f"{'BIT-IDENTICAL' if same else '*** PAYLOAD MOVED ***'}")
        if not same:
            # Five modules CANNOT come back bit-identical: the repo cleanup rewrote a prereg path
            # string that these scripts write into the payload. For those, the equivalent proof of
            # reproduction is hitting the hash predicted BEFORE the run by
            # repro/t1_sweep/t1_predict_moved.py -- it means every number reproduced exactly and
            # the only delta is the documentation string.
            pred = {}
            try:
                pred = json.load(open("docs/reproducibility/t1_moved_prediction.json"))
            except Exception:
                pass
            p = pred.get(module)
            if p:
                if hb == p["predicted_sha"]:
                    lines.append(f"    PREDICTION CONFIRMED: matches the hash predicted pre-run "
                                 f"({p['predicted_sha'][:16]}). Every number reproduced exactly; "
                                 f"the only delta is {p['fields']}.")
                    verdicts[-1] = "MOVED_AS_PREDICTED"
                else:
                    lines.append(f"    PREDICTION FALSIFIED: expected {p['predicted_sha'][:16]}, "
                                 f"got {hb[:16]}. Something beyond the prereg string moved.")
            lines += ["    " + x for x in ladder(a, n, f)]
    # A non-zero rc does NOT mean the result failed to reproduce. The pre-provenance scripts
    # (t37/t38/t43/t33) write with a bare json.dump, so _lib.sh's verify_outputs rejects them for
    # carrying no provenance block AFTER the science has exited 0 and written the file. Labelling
    # that DID_NOT_RUN hid a payload that was bit-identical, so the exit status is now reported as
    # an _RC1 suffix on the real payload verdict instead of overriding it.
    moved = [v for v in verdicts if v.startswith("MOVED")]
    if "DID_NOT_RUN" in verdicts or "NO_BASELINE" in verdicts:
        v = "DID_NOT_RUN" if "DID_NOT_RUN" in verdicts else "NO_BASELINE"
    elif moved:
        v = "MOVED_AS_PREDICTED" if all(x == "MOVED_AS_PREDICTED" for x in moved) else "MOVED"
        if rc != 0:
            v += "_RC1"
    else:
        v = "BIT_IDENTICAL" + ("_RC1" if rc != 0 else "")
    print(f"\n=== {module}  rc={rc}  {secs}s  ->  {v}")
    for l in lines:
        print(l)
    with open(f"{SP}/verdicts.tsv", "a") as fh:
        fh.write(f"{module}\t{v}\t{rc}\t{secs}\t{';'.join(outs)}\n")
    with open(f"{SP}/detail_{module}.txt", "w") as fh:
        fh.write(f"=== {module} rc={rc} {secs}s -> {v}\n" + "\n".join(lines) + "\n")
    print(f"VERDICT={v}")
    return 0


if __name__ == "__main__":
    m = sys.argv[1]
    if m == "baseline":
        cmd_baseline()
    elif m == "shared":
        raise SystemExit(cmd_shared())
    elif m == "diff":
        raise SystemExit(cmd_diff(sys.argv[2], int(sys.argv[3]), sys.argv[4], sys.argv[5:]))
