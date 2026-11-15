#!/usr/bin/env python3
"""hf_mirror_manifest.py — record the artifact mirror's exact contents, and check a mirror against it.

WHY. The mirror moves from the anonymous review account to the author's account. A transfer is a
WRITE to the record of record (16.2 GB of fitted maps plus every results JSON), and "the page loads"
is not evidence that the bytes came across. This tool freezes what the mirror holds before the move,
then proves the destination holds the same thing.

    .venv/bin/python tools/hf_mirror_manifest.py --write  --repo AnonymousInterpScience/pythia-jlens-artifacts
    .venv/bin/python tools/hf_mirror_manifest.py --verify --repo Tarush-AI/fittingcorpus
    .venv/bin/python tools/hf_mirror_manifest.py --cross-check     # the repo's own records vs the manifest

--write   lists the repo tree (recursive, with LFS metadata) and writes
          docs/reproducibility/HF_MIRROR_MANIFEST.tsv: one row per file with its path, size, and
          hash. For an LFS file the hash is the SHA-256 of the content; otherwise it is the git
          blob id the Hub reports.
--verify  lists another repo and compares it row by row. Exit 1 unless every file under results/ and
          corpora/ is present with the same size and hash and none is added. The model card
          (README.md, LICENSE, ATTRIBUTION.md, .gitattributes) may differ: it is reported, not failed.
--cross-check  compares every hash this repository records independently against the manifest: the
          fitter sidecars (results/**/*_provenance.json), provenance input blocks in results JSON,
          and the sha256 column of docs/reproducibility/ARTIFACTS.md. Exit 1 on any conflict.

WHAT THIS DOES NOT COVER.
  * It compares the hashes the Hub REPORTS. It does not download content, so a server-side
    inconsistency between the LFS pointer and the stored object would pass. Downloading a file and
    hashing it locally (repro/03_fetch_artifacts.sh verifies on fetch) is the check for that.
  * --write records what the mirror holds, not whether it is right. 256 of the 382 maps have no
    hash recorded anywhere in this repository, so the manifest is the only record of them, and
    --cross-check can say nothing about them.
  * It does not check git history, the model card's prose, or whether a results file's numbers
    are correct. tools/script_provenance.py and the T0 modules cover those.
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
MANIFEST = os.path.join(REPO, "docs", "reproducibility", "HF_MIRROR_MANIFEST.tsv")


def list_tree(repo: str) -> tuple[str, dict[str, tuple[int, str, str]]]:
    from huggingface_hub import HfApi
    api = HfApi()
    info = api.model_info(repo)
    out = {}
    for e in api.list_repo_tree(repo, repo_type="model", recursive=True, expand=True):
        if getattr(e, "lfs", None) is None and not hasattr(e, "size"):
            continue                                   # a folder
        if e.__class__.__name__ != "RepoFile":
            continue
        if e.lfs:
            out[e.path] = (e.size, "sha256", e.lfs.sha256)
        else:
            out[e.path] = (e.size, "gitoid", e.blob_id)
    return info.sha, out


def read_manifest() -> tuple[dict, dict[str, tuple[int, str, str]]]:
    meta, rows = {}, {}
    for line in open(MANIFEST):
        if line.startswith("#"):
            k, _, v = line[1:].strip().partition(": ")
            if v:
                meta[k] = v
            continue
        if line.startswith("path\t"):
            continue
        path, size, kind, h = line.rstrip("\n").split("\t")
        rows[path] = (int(size), kind, h)
    return meta, rows


def cmd_write(repo: str) -> int:
    sha, tree = list_tree(repo)
    n_lfs = sum(1 for v in tree.values() if v[1] == "sha256")
    tot = sum(v[0] for v in tree.values())
    with open(MANIFEST, "w") as f:
        f.write(f"# source repo: {repo}\n# source commit: {sha}\n"
                f"# listed (UTC): {dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')}\n"
                f"# files: {len(tree)} ({n_lfs} LFS)\n# bytes: {tot}\n"
                f"# written by: tools/hf_mirror_manifest.py --write. Do not edit by hand.\n")
        f.write("path\tsize\thash_kind\thash\n")
        for p in sorted(tree):
            s, k, h = tree[p]
            f.write(f"{p}\t{s}\t{k}\t{h}\n")
    print(f"wrote {os.path.relpath(MANIFEST, REPO)}: {len(tree)} files, {n_lfs} LFS, "
          f"{tot/1e9:.2f} GB, from {repo}@{sha[:12]}")
    return 0


def cmd_verify(repo: str) -> int:
    meta, want = read_manifest()
    sha, have = list_tree(repo)
    missing = [p for p in want if p not in have]
    extra = [p for p in have if p not in want]
    changed = [p for p in want if p in have and have[p] != want[p]]
    same = len(want) - len(missing) - len(changed)
    print(f"manifest: {len(want)} files from {meta.get('source repo')}@{meta.get('source commit', '')[:12]}")
    print(f"{repo}@{sha[:12]}: identical {same}, changed {len(changed)}, missing {len(missing)}, "
          f"extra {len(extra)}")
    for tag, lst in (("CHANGED", changed), ("MISSING", missing), ("EXTRA", extra)):
        for p in lst[:20]:
            print(f"  {tag} {p}")
        if len(lst) > 20:
            print(f"  ... {len(lst) - 20} more {tag}")
    # The record is results/ and corpora/: those must be identical, present, and not added to. The
    # model card (README.md, LICENSE, ATTRIBUTION.md, .gitattributes) is expected to be rewritten
    # after a move, so a change there is reported and does not fail the check.
    record = lambda p: p.startswith(("results/", "corpora/"))
    bad = [p for p in missing + changed + extra if record(p)]
    card = [p for p in changed + extra + missing if not record(p)]
    if card:
        print(f"  model-card files that differ (allowed): {', '.join(sorted(card))}")
    print(f"  the record (results/, corpora/): {'IDENTICAL' if not bad else f'{len(bad)} file(s) differ'}")
    return 0 if not bad else 1


def _norm(p: str) -> str:
    return "results/" + p.split("results/", 1)[1] if "results/" in p else p


def cmd_cross_check() -> int:
    _, rows = read_manifest()
    lfs = {p: h for p, (_, k, h) in rows.items() if k == "sha256"}
    agree, conflict = {}, []

    def note(src: str, path: str, h: str) -> None:
        p = _norm(path)
        if p not in lfs:
            return
        if lfs[p] == h:
            agree.setdefault(src, set()).add(p)
        else:
            conflict.append((src, p, h, lfs[p]))

    for f in glob.glob(os.path.join(REPO, "results", "**", "*_provenance.json"), recursive=True):
        try:
            j = json.load(open(f))
        except Exception:
            continue
        if j.get("artifact") and j.get("sha256"):
            # Sidecars written before the specs/ -> docs/ restructure name the map by its old path
            # (pythia/results/lens_*.pt). The map is the sidecar's sibling, so resolve it there.
            sib = os.path.join(os.path.dirname(f), os.path.basename(j["artifact"]))
            note("fitter sidecar", os.path.relpath(sib, REPO), j["sha256"])

    def walk(o):
        if isinstance(o, dict):
            if isinstance(o.get("path"), str) and isinstance(o.get("sha256"), str):
                note("provenance input", o["path"], o["sha256"])
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    for f in glob.glob(os.path.join(REPO, "results", "**", "*.json"), recursive=True):
        try:
            walk(json.load(open(f)).get("provenance", {}))
        except Exception:
            continue
    art = open(os.path.join(REPO, "docs", "reproducibility", "ARTIFACTS.md")).read()
    for p, h in re.findall(r"`(results/[^\s`|]+\.pt)`\s*\|[^\n]*?`([0-9a-f]{64})`", art):
        note("ARTIFACTS.md", p, h)
    covered = set().union(*agree.values()) if agree else set()
    for src in sorted(agree):
        print(f"{src:18s} agrees with the manifest on {len(agree[src])} map(s)")
    print(f"maps with at least one independent record: {len(covered | {c[1] for c in conflict})} "
          f"of {len(lfs)}; conflicts: {len(conflict)}")
    for src, p, h, m in conflict:
        print(f"  CONFLICT [{src}] {p}: recorded {h[:20]}… manifest {m[:20]}…")
    return 1 if conflict else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--verify", action="store_true")
    g.add_argument("--cross-check", action="store_true")
    ap.add_argument("--repo")
    a = ap.parse_args()
    if (a.write or a.verify) and not a.repo:
        ap.error("--repo is required with --write and --verify")
    if a.write:
        return cmd_write(a.repo)
    if a.verify:
        return cmd_verify(a.repo)
    return cmd_cross_check()


if __name__ == "__main__":
    sys.exit(main())
