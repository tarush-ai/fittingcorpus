#!/usr/bin/env python3
"""build_registry.py — one canonical ID per experiment, derived from the record, and the gate that keeps it whole.

WHY. The programme accumulated fifteen naming families (T0-T23, E13-E66, R0-R10, CV1-CV8, D1-D3, DA1,
DN1, EN1, EDATA1, OS1/b/c, EFFRANK1, CTRLBF1, P0, PAPER_CLUSTERED_T, POSTREVIEW) and suffixes with no
fixed meaning (E48b is a different question from E48; E66b is a run of E66). Worse, one experiment
carried several names (t52_factorial.py writes e52_*.json, its corrected re-score was filed as R1 and its
parallel port as P0), and script numbers drifted from experiment numbers (E44's script is t39_dread.py).

docs/experiments/registry.json holds the only curated decisions: which lineage each old ID belongs to,
the plain-language question, and the family. Everything else is DERIVED from the record here:

  results    every results/**/*.json (sidecars excepted) resolved to the run that owns it, through, in
             order: registry.json file_overrides, dir_overrides, the provenance `experiment` label, then
             the filename prefix
  dates      the earlier of the git commit that first added a results file and its provenance timestamp
  runs       E##.n, numbered within a lineage in order of first stored result
  documents  every pre-registration (live, superseded, as-registered) and description, by file name
  scripts    the producing script recorded in provenance, plus each module's invocation
  modules    every repro/exp/*.sh, by the lineage its OUTPUTS resolve to
  paper      which table and figure macros read which results files, parsed from
             paper/tools/make_audit_tables.py and figures/make_audit_figures.py, kept only if
             paper/audit_paper_5pp.tex uses them (paper/ is gitignored; absent, the column says so)

    .venv/bin/python tools/build_registry.py           # write docs/experiments/REGISTRY.md
    .venv/bin/python tools/build_registry.py --check   # exit 1 on any violation, or if REGISTRY.md is stale

THE GATE fails when: a results file, document or module output resolves to no lineage; an old ID is
claimed by two lineages; a canonical ID repeats; a lineage below E67 does not carry the number of one of
its own old E- or T-IDs (rule 2); the lineages from E67 up are not in order of first stored result
(rule 3); or REGISTRY.md differs from what this run would write.

WHAT THIS DOES NOT COVER.
  * Whether a lineage assignment is RIGHT. The gate proves every file is assigned exactly once and the
    numbering rules hold; whether R5 belongs with E55 is a judgement recorded in registry.json.
  * Whether a results file's numbers are correct (T0 modules, tools/script_provenance.py), or whether
    a pre-registration was followed (tools/registration_ledger.py).
  * Dates for results created after results/ left git (2026-08-22): those carry only the provenance
    timestamp, which a later re-stamp can move forward. A first date is the earliest evidence on
    record, not necessarily the day the experiment first ran.
  * The paper column covers tables and figures only. Numbers the paper states in prose are traced in
    the experiment documents, not here.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import subprocess
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
REG = os.path.join(ROOT, "docs", "experiments", "registry.json")
OUT = os.path.join(ROOT, "docs", "experiments", "REGISTRY.md")
PAPER_TEX = os.path.join(ROOT, "paper", "audit_paper_5pp.tex")
TABLES_PY = os.path.join(ROOT, "paper", "tools", "make_audit_tables.py")
FIGS_PY = os.path.join(ROOT, "figures", "make_audit_figures.py")


def norm(s: str) -> str:
    """Old-ID normal form: the first token, upper case, separators dropped. 'E48-gate' -> 'E48GATE'."""
    s = s.strip().split(" ")[0]
    return re.sub(r"[-_ ]", "", s).upper()


PREFIX = re.compile(r"^(t|e|cv|d|r|da|dn|en|os|edata|ctrlbf|effrank)(\d+)([a-z]?)_")


def old_id_from_name(base: str) -> str | None:
    if base.startswith("paper_clustered"):
        return "PAPERCLUSTEREDT"
    if base.startswith("postreview"):
        return "POSTREVIEW"
    m = PREFIX.match(base)
    return (m.group(1) + m.group(2) + m.group(3)).upper() if m else None


def git_first_adds() -> dict[str, str]:
    out = subprocess.run(["git", "-C", ROOT, "log", "--all", "--diff-filter=A", "--name-only",
                          "--format=@@%aI"], capture_output=True, text=True).stdout
    adds, cur = {}, None
    for line in out.splitlines():
        if line.startswith("@@"):
            cur = line[2:]
            continue
        p = line[len("pythia/"):] if line.startswith("pythia/") else line
        if p.startswith("results/") and cur and (p not in adds or cur < adds[p]):
            adds[p] = cur
    return adds


def natural(s: str):
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", s)]


def build():
    reg = json.load(open(REG))
    errors: list[str] = []
    lineages = {L["id"]: L for L in reg["lineages"]}
    if len(lineages) != len(reg["lineages"]):
        seen = set()
        for L in reg["lineages"]:
            if L["id"] in seen:
                errors.append(f"canonical ID {L['id']} is used twice")
            seen.add(L["id"])
    alias_of: dict[str, str] = {}
    disp: dict[str, str] = {}             # normal form -> the spelling the registry gives
    for L in reg["lineages"]:
        for a in L["aliases"]:
            k = norm(a)
            disp[k] = a
            if k in alias_of and alias_of[k] != L["id"]:
                errors.append(f"old ID {a} is claimed by both {alias_of[k]} and {L['id']}")
            alias_of[k] = L["id"]

    # ---- results -------------------------------------------------------------------------------
    adds = git_first_adds()
    fo = {k: norm(v) for k, v in reg["file_overrides"].items() if not k.startswith("_")}
    do = sorted(((k, norm(v)) for k, v in reg["dir_overrides"].items()), key=lambda kv: -len(kv[0]))
    results = {}          # path -> dict(old, lineage, date, script, stamped)
    for f in sorted(glob.glob(os.path.join(ROOT, "results", "**", "*.json"), recursive=True)):
        rel = os.path.relpath(f, ROOT)
        if rel.endswith("_provenance.json"):
            continue
        try:
            d = json.load(open(f))
        except Exception:
            errors.append(f"unreadable results file {rel}")
            continue
        p = d.get("provenance") if isinstance(d, dict) else None
        label = (p or {}).get("experiment")
        old = fo.get(rel)
        if old is None:
            old = next((v for k, v in do if rel.startswith(k)), None)
        if old is None and label:
            old = norm(label)
        if old is None:
            old = old_id_from_name(os.path.basename(rel))
        lin = alias_of.get(old) if old else None
        if lin is None:
            errors.append(f"results file {rel} resolves to no lineage (old ID {old!r})")
            continue
        dates = [x[:16] for x in (adds.get(rel), (p or {}).get("utc")) if x]
        sc = (p or {}).get("script")
        ins = [i.get("path") for i in (p or {}).get("inputs", []) if isinstance(i, dict)]
        results[rel] = dict(old=old, lineage=lin, date=min(dates) if dates else None,
                            script=sc.get("path") if isinstance(sc, dict) else None, stamped=bool(p),
                            inputs=[i for i in ins if i and i.startswith("results/") and i.endswith(".json")])

    # ---- runs ----------------------------------------------------------------------------------
    by_old = defaultdict(list)
    for rel, r in results.items():
        by_old[(r["lineage"], r["old"])].append(rel)
    runs = defaultdict(list)    # lineage -> [(run_id, old, first_date, files)]
    for (lin, old), files in by_old.items():
        first = min((results[f]["date"] for f in files if results[f]["date"]), default="9999")
        runs[lin].append([None, old, first, sorted(files)])
    run_of_old = {}
    owner = {(results[f]["lineage"], f): results[f]["old"] for f in results}
    for lin, rs in runs.items():
        # Order by what the provenance record says was consumed: a run whose stored inputs include
        # another run's results comes after it. Dates only break ties, because a re-stamp (a T0
        # recompute rewrites provenance.utc) can move a producer's date past its consumer's.
        after = {r[1]: set() for r in rs}
        for r in rs:
            for f in r[3]:
                for i in results[f]["inputs"]:
                    dep = owner.get((lin, i))
                    if dep and dep != r[1]:
                        after[r[1]].add(dep)
        key = {r[1]: (r[2], natural(r[1])) for r in rs}
        order, done = [], set()
        while len(order) < len(rs):
            ready = [o for o in after if o not in done and after[o] <= done]
            if not ready:                        # a cycle: fall back to dates for what is left
                ready = [o for o in after if o not in done]
            nxt = min(ready, key=lambda o: key[o])
            order.append(nxt); done.add(nxt)
        rs.sort(key=lambda r: order.index(r[1]))
        for i, r in enumerate(rs, 1):
            r[0] = f"{lin}.{i}"
            run_of_old[(lin, r[1])] = r[0]
    first_of = {lin: min(r[2] for r in rs) for lin, rs in runs.items()}

    # ---- rules 2 and 3 -------------------------------------------------------------------------
    for L in reg["lineages"]:
        n = int(L["id"][1:])
        nums = {int(m.group(2)) for a in L["aliases"] for m in [re.match(r"^(E|T)(\d+)", norm(a))] if m}
        if n < 67 and n not in nums:
            errors.append(f"rule 2: {L['id']} carries no number from its own old IDs {L['aliases']}")
        if L["id"] not in runs:
            errors.append(f"{L['id']} has no stored result")
    new = [L["id"] for L in reg["lineages"] if int(L["id"][1:]) >= 67]
    by_date = sorted(new, key=lambda i: first_of.get(i, "9999"))
    if new != sorted(new, key=natural) or by_date != sorted(new, key=natural):
        errors.append(f"rule 3: lineages from E67 up must be numbered in order of first stored result; "
                      f"by date they run {by_date}")

    # ---- findings and the README ---------------------------------------------------------------
    for L in reg["lineages"]:
        if L.get("finding") not in reg.get("findings", {}):
            errors.append(f"{L['id']} has no valid finding (got {L.get('finding')!r})")
    for fid, F in reg.get("findings", {}).items():
        if F.get("lead") and lineages.get(F["lead"], {}).get("finding") != fid:
            errors.append(f"finding {fid}'s lead {F['lead']} is not assigned to {fid}")
    readme = os.path.join(ROOT, "README.md")
    if os.path.exists(readme):
        rt = open(readme).read()
        absent = [i for i in lineages if not re.search(rf"\b{i}(\.\d+)?\b", rt)]
        if absent:
            errors.append(f"README.md does not name {len(absent)} experiment(s): {', '.join(absent)}")

    # ---- documents -----------------------------------------------------------------------------
    docs = defaultdict(list)
    dov = reg.get("doc_overrides", {})
    patterns = ["docs/experiments/preregs/*.md", "docs/experiments/preregs/superseded/*.md",
                "docs/experiments/preregs/as_registered/*.md", "docs/experiments/descriptions/*.md",
                "experiments/exploratory/descriptions/*.md"]
    for pat in patterns:
        for f in sorted(glob.glob(os.path.join(ROOT, pat))):
            rel = os.path.relpath(f, ROOT)
            base = os.path.basename(rel)
            if base == "README.md":
                continue
            stem = re.sub(r"^[0-9a-f]{12}__", "", base[:-3])
            old = norm(dov[rel]) if rel in dov else norm(stem.split("_")[0] if "/preregs/" in rel else stem)
            lin = alias_of.get(old)
            if lin is None:
                errors.append(f"document {rel} resolves to no lineage (old ID {old!r})")
                continue
            kind = ("as registered" if "/as_registered/" in rel else "superseded" if "/superseded/" in rel
                    else "pre-registration" if "/preregs/" in rel else "description")
            docs[lin].append((kind, rel))

    # ---- modules -------------------------------------------------------------------------------
    modules = defaultdict(list)
    scripts = defaultdict(set)
    for rel, r in results.items():
        if r["script"]:
            scripts[r["lineage"]].add(r["script"])
    for f in sorted(glob.glob(os.path.join(ROOT, "repro", "exp", "*.sh"))):
        if os.path.basename(f) == "_lib.sh":
            continue
        t = open(f).read()
        tier = (re.search(r'MODULE_TIER="(T\d)"', t) or [None, "untiered"])[1]
        blk = re.search(r"OUTPUTS=\((.*?)\)", t, re.S)
        outs = [o for o in (blk.group(1).split() if blk else []) if o.startswith("results/")]
        hit = {results[o]["lineage"] for o in outs if o in results}
        rel = os.path.relpath(f, ROOT)
        if outs and not hit:
            errors.append(f"module {rel}: none of its OUTPUTS resolves to a stored result")
        for lin in sorted(hit):
            modules[lin].append((os.path.basename(f)[:-3], tier))
        for s in re.findall(r"run_py\s+((?:experiments|tools)/[\w/]+\.py)", t):
            for lin in hit:
                scripts[lin].add(s)
    for lin in lineages:            # lineages with no stamped script: fall back to their own docs
        if not scripts[lin]:
            for kind, rel in docs[lin]:
                if kind == "description":
                    scripts[lin] |= set(re.findall(r"((?:experiments|tools)/[\w/]+\.py)",
                                                   open(os.path.join(ROOT, rel)).read()))

    # ---- paper ---------------------------------------------------------------------------------
    paper = defaultdict(set)
    paper_note = None
    if os.path.exists(PAPER_TEX) and os.path.exists(TABLES_PY) and os.path.exists(FIGS_PY):
        tex = open(PAPER_TEX).read()
        tp = open(TABLES_PY).read()
        var = dict(re.findall(r"(\w+)\s*=\s*load\(\"([^\"]+)\"\)", tp))
        for fn, args in re.findall(r"tbl_(\w+)\(([^)]*)\)\)", tp):
            macro = "\\tbl" + fn.replace("_", "")
            if macro not in tex:
                continue
            for a in [x.strip() for x in args.split(",") if x.strip()]:
                f = "results/" + var.get(a, "")
                if f in results:
                    paper[results[f]["lineage"]].add(f"table {macro}")
        fp = open(FIGS_PY).read()
        for name, body in re.findall(r"\ndef (f[A-Z]\w*)\(.*?\n(.*?)(?=\ndef |\Z)", fp, re.S):
            if f"{name}.png" not in tex:
                continue
            for f in set(re.findall(r"(?:load|_load)\(\"([^\"]+)\"\)", body)) | set(re.findall(r"results/([\w.\-]+\.json)", body)):
                rel = "results/" + f if not f.startswith("results/") else f
                if rel in results:
                    paper[results[rel]["lineage"]].add(f"figure {name}")
    else:
        paper_note = "paper/ is not present in this checkout, so the paper column is empty"

    return dict(reg=reg, lineages=lineages, results=results, runs=runs, run_of_old=run_of_old,
                first_of=first_of, docs=docs, modules=modules, scripts=scripts, paper=paper,
                paper_note=paper_note, alias_of=alias_of, disp=disp, errors=errors)


def render(b) -> str:
    reg, runs = b["reg"], b["runs"]
    L = []
    w = L.append
    w("# Experiment registry: one canonical ID per experiment\n")
    w("GENERATED by `tools/build_registry.py` from `docs/experiments/registry.json` and the record. "
      "Do not edit by hand: change `registry.json`, then run the tool. `--check` is the gate.\n")
    w("**If you have an old ID, use the lookup table below.** Every experiment, re-score, port, control "
      "and adjudication in this repository has exactly one canonical ID of the form `E##`, and every "
      "stored result belongs to exactly one run of it, `E##.n`. The old names (T14, R1, CV3, DA1b, …) "
      "still appear in file names, commit messages and older documents. They are kept as aliases, "
      "because files are pinned by path in the provenance record and cannot be renamed.\n")
    w("## The rules\n")
    for i, r in enumerate(reg["rules"], 1):
        w(f"{i}. {r}")
    w("")
    n_res = len(b["results"])
    n_docs = sum(len(v) for v in b["docs"].values())
    n_mod = len({m for v in b["modules"].values() for m, _ in v})
    n_runs = sum(len(v) for v in runs.values())
    w(f"**{len(b['lineages'])} experiments, {n_runs} runs, {n_res} results files, {n_docs} documents, "
      f"{n_mod} reproduction modules.** Every one of them resolves to exactly one experiment. "
      "`tools/build_registry.py --check` fails otherwise.\n")
    # lookup
    w("## Old ID → canonical ID\n")
    w("| old ID | canonical | the experiment |")
    w("|---|---|---|")
    rows = []
    for lin, Ld in b["lineages"].items():
        for a in Ld["aliases"]:
            rid = b["run_of_old"].get((lin, norm(a)))
            rows.append((a, rid or lin, Ld["question"]))
    for a, c, q in sorted(rows, key=lambda r: natural(norm(r[0]))):
        short = q if len(q) <= 90 else q[:87].rsplit(" ", 1)[0] + " …"
        w(f"| `{a}` | **{c}** | {short} |")
    w("")
    # by family
    w("## The experiments, by finding\n")
    w("Every experiment belongs to exactly one finding: the claim in the paper it bears on, or, for the "
      "last two groups, the instrument checks and the work that did not enter the paper. The README's "
      "findings table names every experiment; `--check` fails if one is missing there.\n")
    w("Runs are listed with the old ID each one was known by, and the date of its first stored result. "
      "Documents link to the pre-registration and the description. Modules are the `repro/exp/` "
      "invocations that reproduce the run, with their tier (T0 recomputes from stored JSON, T1 "
      "re-scores stored maps on CPU, T2 refits on a GPU).\n")
    if b["paper_note"]:
        w(f"> {b['paper_note']}.\n")
    fam_of = defaultdict(list)
    for lin, Ld in b["lineages"].items():
        fam_of[Ld["finding"]].append(lin)
    for fid, F in reg["findings"].items():
        lead = F.get("lead")
        ids = sorted(fam_of.get(fid, []), key=lambda i: (i != lead, natural(i)))
        if not ids:
            continue
        w(f"### {fid}: {F['title']}\n")
        w(f"*{F['paper']}*" + (f" · lead experiment **{lead}**" if lead else "") + "\n")
        for lin in ids:
            Ld = b["lineages"][lin]
            w(f"#### {lin}: {Ld['question']}\n")
            rs = runs.get(lin, [])
            w("- **runs**: " + " · ".join(f"`{r[0]}` = {b['disp'].get(r[1], r[1])} ({r[2][:10]}, {len(r[3])} file{'s' if len(r[3]) != 1 else ''})" for r in rs))
            no_res = [a for a in Ld["aliases"] if (lin, norm(a)) not in b["run_of_old"]]
            if no_res:
                w(f"- **also known as**, with no stored result of its own: {', '.join('`' + a + '`' for a in no_res)}")
            ds = sorted(b["docs"].get(lin, []), key=lambda d: (["pre-registration", "description", "superseded", "as registered"].index(d[0]), d[1]))
            live = [f"[`{os.path.basename(p)}`](../../{p})" for k, p in ds if k in ("pre-registration", "description")]
            arch = [p for k, p in ds if k in ("superseded", "as registered")]
            if live:
                w("- **documents**: " + ", ".join(live))
            if arch:
                w(f"- **archived pre-registration versions**: {len(arch)}")
            sc = sorted(b["scripts"].get(lin, []))
            if sc:
                w("- **scripts**: " + ", ".join(f"`{s}`" for s in sc))
            md = sorted(set(b["modules"].get(lin, [])))
            if md:
                w("- **modules**: " + ", ".join(f"`{m}` ({t})" for m, t in md))
            pp = sorted(b["paper"].get(lin, []))
            if Ld.get("paper") or pp:
                w("- **in the paper**: " + "; ".join(([Ld["paper"]] if Ld.get("paper") else []) + pp))
            w("")
    return "\n".join(L).rstrip() + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    b = build()
    text = render(b)
    if a.check:
        errs = list(b["errors"])
        if not os.path.exists(OUT) or open(OUT).read() != text:
            errs.append("docs/experiments/REGISTRY.md is stale: run tools/build_registry.py")
        for e in errs:
            print("FAIL", e)
        n_runs = sum(len(v) for v in b["runs"].values())
        print(f"{len(b['lineages'])} experiments, {n_runs} runs, {len(b['results'])} results files; "
              f"{len(errs)} violation(s)")
        return 1 if errs else 0
    for e in b["errors"]:
        print("WARNING", e)
    open(OUT, "w").write(text)
    print(f"wrote {os.path.relpath(OUT, ROOT)}; {len(b['errors'])} violation(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
