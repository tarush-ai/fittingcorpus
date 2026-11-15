#!/usr/bin/env python3
"""
t1_classify.py — first-principles audit of what the 22 T1 modules actually re-run.

WHY THIS EXISTS. A T1 sweep is only worth its runtime if each module re-derives the stored
number the way the stored number was derived. Two things can silently break that and neither is
visible from a green verdict:

  1. the module's invocation drifts from `provenance.argv` of the file it claims to reproduce;
  2. the script on disk is no longer the script that produced the file (rung 4 of the SPEC §4
     ladder), so the module reproduces *current* code, not the recorded run.

It also settles what each module physically touches, because "22 modules reproduced" invites the
reading that 22 operators were re-scored. They were not. This classifies on EVIDENCE FROM THE
SCRIPT SOURCE, not on whether the results file happens to record a .pt input -- that proxy
undercounts, because pre-provenance scripts load operators without recording them.

  TYPE_1_OPERATOR  the script loads fitted .pt operators off disk and re-derives reads through them
  TYPE_2_MODEL     the script runs a model forward (AutoModelForCausalLM); no operator in the quantity
  TYPE_2_CORPUS    no model forward -- tokenizer plus corpora/eval battery only; still primary data
  TYPE_3_REAGG     no model and no operator; arithmetic over already-stored JSON

TYPE_2_CORPUS exists because `from_pretrained` is NOT evidence of a model: cv2_position_support
and t48b_exposure_growth call it on an AutoTokenizer and never instantiate a network. Counting
those as "model measurements" overstates what they re-derive. They are still first-principles --
they read the battery and the corpora -- but no forward pass happens.

Usage:
  .venv/bin/python repro/t1_sweep/t1_classify.py            # table
  .venv/bin/python repro/t1_sweep/t1_classify.py --json out.json
"""
import argparse, ast, json, os, re, subprocess, sys, hashlib

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "src"))

# The 22, in the SPEC §3 suggested order.
MODULES = [
    "cv5_sensitivity", "cv2_position", "e58_algebra", "e59_read_dose", "d1_union",
    "e38_geometry", "e37_rank_70m", "e37_rank_160m", "e49_stability", "e33_logit_v2",
    "cv3_margins", "cv4_capability", "cv7_rung", "d3_by_family", "cv6_ladder",
    "e65_ckpt_geometry", "cv1_competence", "e48b_exposure", "e48_crossover", "e48_gate",
    "e52_factorial", "e36_qladder",
]


def sha(path):
    if not os.path.isfile(path):
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def bash_array(text, name):
    """Extract a bash array assignment NAME=(a b c) as a list."""
    m = re.search(rf"^{name}=\(([^)]*)\)", text, re.M)
    return m.group(1).split() if m else []


def module_invocations(text):
    """Every `run_py <script> <args...>` in the module, with line continuations joined.

    Two shapes must both parse, and an earlier version of this got both wrong:
      main() { run_py experiments/x.py; }              -- trailing ';' and '}' are shell, not args
      if [ "${1:-}" = "--legacy" ]; then A else B fi   -- B is the DEFAULT, A is opt-in
    So we strip shell punctuation and return every invocation; the caller matches all of them
    against the recorded argv rather than assuming the first is canonical.
    """
    joined = re.sub(r"\\\n\s*", " ", text)
    out = []
    for m in re.finditer(r"run_py\s+([^\s;)}]+)((?:[^\n;&|]*)?)", joined):
        script = m.group(1).strip()
        args = [a for a in m.group(2).replace("}", " ").split() if a and a not in (";", "}")]
        out.append((script, args))
    return out


def script_evidence(path):
    """What does this script physically do? Parsed from source, not guessed."""
    if not os.path.isfile(path):
        return {"exists": False}
    src = open(path).read()
    try:
        tree = ast.parse(src)
    except SyntaxError:
        tree = None
    ev = {
        "exists": True,
        # operator loading: torch.load of a .pt, or the repo's lens loaders
        "torch_load": len(re.findall(r"torch\.load\s*\(", src)),
        "pt_literal": len(re.findall(r"\.pt[\"']", src)),
        "lens_tokens": len(re.findall(r"\blens\w*\b", src, re.I)),
        "load_operator": len(re.findall(r"load_operator|load_lens|JOperator|JacobianLens", src)),
        # model loading
        "from_pretrained": len(re.findall(r"from_pretrained\s*\(", src)),
        "automodel": len(re.findall(r"AutoModelForCausalLM", src)),
        # re-aggregation signature: reads results/*.json
        "reads_results_json": len(re.findall(r"results/[\w./{}-]*\.json|RESULTS_DIR|results\", ", src)),
    }
    # which top-level functions exist (adjudicate-style short circuits)
    ev["funcs"] = sorted({n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}) if tree else []
    return ev


def classify(ev, argv, inputs_pt):
    """TYPE_1 / TYPE_2 / TYPE_3 from source evidence + the argv actually used."""
    if not ev.get("exists"):
        return "SCRIPT_MISSING", "script not on disk"
    adjudicate_only = "--adjudicate" in argv and "adjudicate" in ev["funcs"]
    loads_operator = (ev["torch_load"] > 0 and (ev["pt_literal"] > 0 or ev["lens_tokens"] > 0)) \
        or ev["load_operator"] > 0
    runs_model = ev["automodel"] > 0 or ev["from_pretrained"] > 0
    if adjudicate_only:
        return "TYPE_3_REAGG", "--adjudicate branch returns before any model/operator work"
    if loads_operator:
        why = f"torch.load x{ev['torch_load']}"
        if ev["load_operator"]:
            why += f", operator API x{ev['load_operator']}"
        if inputs_pt:
            why += f", {inputs_pt} .pt recorded"
        else:
            why += ", .pt NOT recorded in provenance (pre-provenance script)"
        return "TYPE_1_OPERATOR", why
    if ev["automodel"] > 0:
        return "TYPE_2_MODEL", f"AutoModelForCausalLM x{ev['automodel']}, no operator load"
    if runs_model:
        return "TYPE_2_CORPUS", ("tokenizer-only from_pretrained "
                                 f"x{ev['from_pretrained']}, no model forward, no operator")
    return "TYPE_3_REAGG", "no model, no operator"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=None)
    a = ap.parse_args()
    os.chdir(ROOT)

    rows = []
    for mid in MODULES:
        mpath = f"repro/exp/{mid}.sh"
        text = open(mpath).read()
        outs = bash_array(text, "OUTPUTS")
        ins = bash_array(text, "INPUTS")
        invs = module_invocations(text)
        # Which invocation is canonical is decided by the RECORDED argv, not by source order:
        # e52/e36 put the opt-in --legacy arm first and the default arm in the else branch.
        script, args = invs[0] if invs else (None, [])

        primary = outs[0] if outs else None
        stored, argv_rec, script_rec = {}, None, {}
        if primary and os.path.isfile(primary):
            try:
                stored = json.load(open(primary))
            except Exception:
                stored = {}
        prov = (stored.get("provenance") or {}) if isinstance(stored, dict) else {}
        argv_rec = prov.get("argv")
        script_rec = prov.get("script") or {}
        inputs_rec = prov.get("inputs") or []
        pt_rec = sum(1 for i in inputs_rec if (i.get("path") or "").endswith(".pt"))
        pt_declared = sum(1 for i in ins if i.endswith(".pt"))

        # --- 1. ARGV MATCH: module invocation vs recorded argv -------------------
        mod_argv = ([script] + args) if script else []
        if argv_rec is None:
            argv_verdict, argv_detail = "NO_RECORD", "results file has no provenance.argv"
        else:
            rec = list(argv_rec)

            def matches(cand):
                return (len(rec) == len(cand)
                        and os.path.basename(rec[0]) == os.path.basename(cand[0])
                        and rec[1:] == cand[1:])

            hit = next((([s] + ar) for (s, ar) in invs if matches([s] + ar)), None)
            if hit:
                argv_verdict, argv_detail = "EXACT", ""
                script, args = hit[0], hit[1:]
            else:
                argv_verdict = "DIFFERS"
                argv_detail = ("recorded=" + " ".join(rec) + "  |  module offers: "
                               + " ;; ".join(" ".join([s] + ar) for s, ar in invs))
            mod_argv = ([script] + args) if script else []

        # --- 2. SCRIPT IDENTITY: rung 4 ------------------------------------------
        if script_rec.get("sha256") and script_rec.get("path"):
            live = sha(script_rec["path"])
            if live == script_rec["sha256"]:
                sc_verdict, sc_detail = "SAME_CODE", ""
            else:
                vault = [f for f in os.listdir("repro/scripts_at_run")
                         if f.startswith(script_rec["sha256"][:12])]
                sc_verdict = "CODE_CHANGED"
                sc_detail = (f"original at repro/scripts_at_run/{vault[0]}" if vault
                             else "ORIGINAL NOT VAULTED")
        else:
            sc_verdict, sc_detail = "NO_RECORD", "no provenance.script"

        ev = script_evidence(script) if script else {"exists": False}
        typ, why = classify(ev, args, pt_rec or pt_declared)

        rows.append({
            "module": mid, "script": script, "args": args, "outputs": outs,
            "type": typ, "type_why": why,
            "argv_match": argv_verdict, "argv_detail": argv_detail,
            "script_identity": sc_verdict, "script_detail": sc_detail,
            "pt_recorded": pt_rec, "pt_declared": pt_declared,
            "n_invocations": len(invs),
        })

    w = max(len(r["module"]) for r in rows) + 1
    print(f"{'module':<{w}} {'type':<16} {'argv':<9} {'code':<13} .pt  why")
    print("-" * 118)
    for r in rows:
        print(f"{r['module']:<{w}} {r['type']:<16} {r['argv_match']:<9} "
              f"{r['script_identity']:<13} {r['pt_recorded']:<3}  {r['type_why']}")
    from collections import Counter
    c = Counter(r["type"] for r in rows)
    print("\n  " + "  ".join(f"{k}={v}" for k, v in sorted(c.items())))
    bad_argv = [r["module"] for r in rows if r["argv_match"] == "DIFFERS"]
    no_argv = [r["module"] for r in rows if r["argv_match"] == "NO_RECORD"]
    changed = [r["module"] for r in rows if r["script_identity"] == "CODE_CHANGED"]
    print(f"  argv EXACT   : {sum(1 for r in rows if r['argv_match']=='EXACT')}/22")
    print(f"  argv DIFFERS : {bad_argv or 'none'}")
    print(f"  argv NO_RECORD: {no_argv or 'none'}")
    print(f"  code CHANGED since the recorded run: {changed or 'none'}")
    for r in rows:
        if r["argv_detail"]:
            print(f"     ! {r['module']}: {r['argv_detail']}")
        if r["script_detail"] and r["script_identity"] == "CODE_CHANGED":
            print(f"     ~ {r['module']}: {r['script_detail']}")
    if a.json:
        json.dump(rows, open(a.json, "w"), indent=1)
        print(f"  wrote {a.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
