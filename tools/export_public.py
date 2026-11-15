#!/usr/bin/env python3
"""export_public.py — build the public tree for github.com/tarush-ai/fittingcorpus, and check it.

This repository is the private working copy: it tracks the agents' instructions, handoffs, review
prompts and superseded maps alongside the code. The public repository is a single initial commit
with no history. This tool decides what goes into it and proves the result stands on its own.

    .venv/bin/python tools/export_public.py --list            # what would ship, and what would not
    .venv/bin/python tools/export_public.py --check           # run every check, write nothing
    .venv/bin/python tools/export_public.py --out ../fittingcorpus-public    # build the tree

THE PUBLIC TREE is every git-tracked file, minus the patterns in release/private.txt, minus any
tracked figure that nothing public references, plus the paper source copied from the gitignored
paper/ directory (PAPER_FILES below). It never includes results/, corpora plaintext or the vendored
jacobian-lens/: those are fetched, rebuilt and cloned by the repro scripts.

THE CHECKS, each with a planted failure that must make it fire (--check runs the plants first):
  links     every relative link in a public .md resolves inside the public tree. Files in
            preregs/as_registered/ and docs/archive/ are byte-exact archives and are exempt: their
            links were written for where they used to live, and their READMEs say so.
  identity  no machine identifier (hostname, home path, agent-tooling slug), using the patterns in
            the gitignored tools/deanon_patterns.json. The author's name and email ARE allowed now.
  secrets   no API token or private key (Hugging Face, GitHub, OpenAI and Anthropic, AWS, PEM).
  required  README.md, LICENSE, CITATION.cff and the paper source are present.
  size      no file over 10 MB (the maps live on Hugging Face, not in git).

WHAT THIS DOES NOT COVER. Whether the public README reads well, whether the paper source is the
camera-ready version (it copies whatever is in paper/ now), and anything about the Hugging Face
mirror (tools/hf_mirror_manifest.py --verify covers that). It also cannot catch an identifier that
matches none of the patterns. The patterns are the record of what leaked before, not a proof that
nothing else can.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PRIVATE = os.path.join(ROOT, "release", "private.txt")
PATTERNS = os.path.join(ROOT, "tools", "deanon_patterns.json")
PAPER_FILES = ["paper/audit_paper_5pp.tex", "paper/audit_paper_extended.tex", "paper/refs.bib", "paper/neurips_2026.sty",
               "paper/tables_audit.tex", "paper/build_audit.sh", "paper/tools/make_audit_tables.py",
               "paper/tools/prose_lint.py"]
PAPER_OPTIONAL = ["paper/audit_paper_5pp.pdf", "paper/audit_paper_extended.pdf"]
REQUIRED = ["README.md", "LICENSE", "CITATION.cff", "paper/audit_paper_5pp.tex"]
MAX_BYTES = 10 * 1024 * 1024
SECRETS = [("huggingface token", r"\bhf_[A-Za-z0-9]{30,}\b"),
           ("github token", r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
           ("openai/anthropic key", r"\bsk-(?:ant-)?[A-Za-z0-9_\-]{30,}\b"),
           ("aws access key", r"\bAKIA[0-9A-Z]{16}\b"),
           ("private key", r"-----BEGIN [A-Z ]*PRIVATE KEY-----")]
LINK = re.compile(r"\]\(([^)\s#]+)(?:#[^)]*)?\)")


def private_patterns() -> list[str]:
    return [l.strip() for l in open(PRIVATE) if l.strip() and not l.lstrip().startswith("#")]


def is_private(path: str, pats: list[str]) -> bool:
    for p in pats:
        if p.endswith("/") and path.startswith(p):
            return True
        if fnmatch.fnmatch(path, p):
            return True
    return False


def public_files() -> tuple[list[str], list[str], list[str]]:
    tracked = subprocess.run(["git", "-C", ROOT, "ls-files"], capture_output=True,
                             text=True).stdout.split()
    pats = private_patterns()
    excluded = [f for f in tracked if is_private(f, pats)]
    keep = [f for f in tracked if not is_private(f, pats)]
    paper = [f for f in PAPER_FILES + PAPER_OPTIONAL if os.path.exists(os.path.join(ROOT, f))]
    # A tracked figure ships only if the paper or a public document references it.
    figs = [f for f in keep if f.startswith("figures/") and f.endswith((".png", ".pdf"))]
    texts = "".join(open(os.path.join(ROOT, f), errors="ignore").read()
                    for f in keep + paper if f.endswith((".md", ".tex")))
    unref = [f for f in figs if os.path.basename(f) not in texts]
    keep = [f for f in keep if f not in unref]
    return sorted(set(keep + paper)), sorted(excluded), sorted(unref)   # paper files may also be tracked


def identity_rx() -> list[tuple[str, re.Pattern]] | None:
    if not os.path.exists(PATTERNS):
        return None
    pat = json.load(open(PATTERNS))["patterns"]
    return [(p[0], re.compile(p[1], re.I)) for p in pat if p[0] in ("hostname", "home_path", "agent_slug")]


def check_links(files: list[str], read) -> list[str]:
    fs = set(files)
    dirs = {os.path.dirname(f) for f in files}
    while True:                                          # every ancestor directory exists too
        more = {os.path.dirname(d) for d in dirs} - dirs
        if not more:
            break
        dirs |= more
    bad = []
    for f in files:
        archived = ("/as_registered/" in f or f.startswith("docs/archive/")) and not f.endswith("README.md")
        if not f.endswith(".md") or archived:
            continue
        for u in LINK.findall(read(f)):
            if re.match(r"^[a-z]+:", u):
                continue
            t = os.path.normpath(os.path.join(os.path.dirname(f), u)).rstrip("/")
            if t not in fs and t not in dirs:
                bad.append(f"{f} -> {u}")
    return bad


def scan(files: list[str], read, rx) -> list[str]:
    out = []
    for f in files:
        if f.endswith((".png", ".pdf", ".pt", ".npz")):
            continue
        t = read(f)
        for name, r in rx:
            if r.search(t):
                out.append(f"{f}: {name}")
    return out


def run_checks(files: list[str], read, size) -> dict[str, list[str]]:
    rx_id = identity_rx()
    res = {"links": check_links(files, read),
           "identity": scan(files, read, rx_id) if rx_id else ["tools/deanon_patterns.json is absent: cannot scan"],
           "secrets": scan(files, read, [(n, re.compile(p)) for n, p in SECRETS]),
           "required": [f"missing {r}" for r in REQUIRED if r not in files],
           "size": [f"{f}: {size(f)/1e6:.1f} MB" for f in files if size(f) > MAX_BYTES]}
    return res


def self_test() -> list[str]:
    """Each check must fire on a planted failure. A check that cannot fail is not a check."""
    planted = {
        "a.md": "[x](missing.md)",
        "README.md": "ok", "LICENSE": "ok", "CITATION.cff": "ok", "paper/audit_paper_5pp.tex": "ok",
        "s.txt": "token hf_" + "A" * 34,
    }
    rx = identity_rx()
    if rx:
        leaks = json.load(open(PATTERNS)).get("planted_leaks_for_self_test") or {}
        sample = next((v for k, v in (leaks.items() if isinstance(leaks, dict) else [])
                       if "host" in k.lower()), None)
        if sample is None and isinstance(leaks, list) and leaks:
            sample = leaks[0] if isinstance(leaks[0], str) else None
        planted["i.txt"] = sample or ""
    read = lambda f: planted[f]
    res = run_checks(list(planted), read, lambda f: 11 * 1024 * 1024 if f == "s.txt" else 1)
    fails = []
    for k in ("links", "secrets", "size"):
        if not res[k]:
            fails.append(f"self-test: the {k} check did not fire on its planted failure")
    if rx and not res["identity"]:
        fails.append("self-test: the identity check did not fire on a planted hostname")
    res2 = run_checks(["README.md"], lambda f: "ok", lambda f: 1)
    if not res2["required"]:
        fails.append("self-test: the required-files check did not fire with LICENSE missing")
    return fails


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--list", action="store_true")
    g.add_argument("--check", action="store_true")
    g.add_argument("--out")
    a = ap.parse_args()
    files, excluded, unref = public_files()
    if a.list:
        print(f"public: {len(files)} files   private: {len(excluded)} tracked files   "
              f"unreferenced figures left out: {len(unref)}")
        top = {}
        for f in files:
            top[f.split("/")[0]] = top.get(f.split("/")[0], 0) + 1
        print("  public by top level:", ", ".join(f"{k} {v}" for k, v in sorted(top.items())))
        for f in excluded:
            print("  private ", f)
        for f in unref:
            print("  unreferenced figure ", f)
        return 0
    st = self_test()
    for s in st:
        print("FAIL", s)
    read = lambda f: open(os.path.join(ROOT, f), errors="ignore").read()
    size = lambda f: os.path.getsize(os.path.join(ROOT, f))
    res = run_checks(files, read, size)
    n_bad = sum(len(v) for v in res.values()) + len(st)
    for k, v in res.items():
        print(f"{k:9s} {'ok' if not v else f'{len(v)} problem(s)'}")
        for x in v[:25]:
            print("   ", x)
    print(f"{len(files)} public files; self-test {'passed' if not st else 'FAILED'}; "
          f"{n_bad} problem(s)")
    if a.check or n_bad:
        return 1 if n_bad else 0
    out = os.path.abspath(a.out)
    if os.path.exists(out) and os.listdir(out):
        print(f"REFUSING: {out} exists and is not empty")
        return 1
    for f in files:
        dst = os.path.join(out, f)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(os.path.join(ROOT, f), dst)
    print(f"wrote {len(files)} files to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
