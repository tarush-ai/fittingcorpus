#!/usr/bin/env python3
"""build_provenance.py — the provenance index for every experiment document.

For each `docs/experiments/preregs/*.md` this lists every results file the document cites, with that
file's size, SHA-256, producing script and readout exposure class, and writes it all to ONE generated
file, `docs/experiments/INDEX.md`, with each document's canonical ID from
`docs/experiments/registry.json`.

Until 2026-11-14 this tool wrote the same table INTO each pre-registration, between markers. That had
two costs. Every re-stamp of a results file made 45 of 47 documents stale, and a pre-registration
whose exact text a stored result pins by SHA-256 (R5 and R9) could not be regenerated without breaking
the pin. The tables now live only in INDEX.md. The old blocks were stripped once, except from FROZEN
documents: those whose current text a stored result pins. They are detected from the results
themselves and never touched; their embedded blocks are historical, and INDEX.md is current.

    tools/build_provenance.py            # write docs/experiments/INDEX.md (and strip old blocks)
    tools/build_provenance.py --check    # exit 1 if INDEX.md is stale, a cited file is missing,
                                         # or an unfrozen document still carries a block

WHAT THIS DOES NOT COVER: whether a document's prose is right, whether its verdict follows its
registered rule (tools/registration_ledger.py), or files a document mentions only by directory.
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
EXP = os.path.join(REPO, "docs", "experiments", "preregs")

BEGIN = "<!-- BEGIN GENERATED PROVENANCE — tools/build_provenance.py -->"
END = "<!-- END GENERATED PROVENANCE -->"

# readout exposure, reused from the ledger rather than re-derived
# The readout ledger moved to docs/reproducibility/ in the specs/ -> docs/ restructure (d06a39d)
# and this path was not updated. tmp/ is gitignored and absent, load_exposure() swallowed the
# resulting FileNotFoundError, and so EVERY generated provenance block in the repo has been
# printing `UNCLASSIFIED` for the readout column since the restructure -- a column CLAUDE.md 5
# says this tool stamps. The canonical location is checked first; tmp/ stays as a fallback for
# an ad-hoc regeneration.
EXPOSURE = os.path.join(REPO, "docs", "reproducibility", "readout_exposure.json")
EXPOSURE_FALLBACK = os.path.join(REPO, "tmp", "readout_exposure.json")


def sha256_file(p: str) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_exposure() -> dict:
    """The readout class per results file. Absence is REPORTED, not silently defaulted --
    a provenance table whose readout column reads UNCLASSIFIED everywhere looks like a
    measured fact and is actually a missing file."""
    for path in (EXPOSURE, EXPOSURE_FALLBACK):
        try:
            return json.load(open(path))["by_file"]
        except Exception:
            continue
    print(f"WARNING: no readout ledger at {os.path.relpath(EXPOSURE, REPO)} or "
          f"{os.path.relpath(EXPOSURE_FALLBACK, REPO)}; the readout column will read "
          f"UNCLASSIFIED for every file. Regenerate with tools/readout_exposure.py --json",
          file=sys.stderr)
    return {}



def pinned_hashes() -> set:
    """Every pre-registration SHA-256 that a stored result pins in its payload."""
    out = set()
    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k == "prereg_sha256" and isinstance(v, str):
                    out.add(v)
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    for f in glob.glob(os.path.join(REPO, "results", "**", "*.json"), recursive=True):
        try:
            d = json.load(open(f))
        except Exception:
            continue
        if isinstance(d, dict):
            d.pop("provenance", None)
        walk(d)
    return out


def canonical_ids() -> dict:
    """document file name -> canonical experiment ID, from docs/experiments/registry.json."""
    try:
        reg = json.load(open(os.path.join(REPO, "docs", "experiments", "registry.json")))
    except Exception:
        return {}
    norm = lambda s: re.sub(r"[-_ ]", "", s.strip().split(" ")[0]).upper()
    alias = {norm(a): L["id"] for L in reg["lineages"] for a in L["aliases"]}
    out = {}
    for md in glob.glob(os.path.join(EXP, "*.md")):
        name = os.path.basename(md)
        out[name] = alias.get(norm(name[:-3].split("_")[0]), "")
    return out


def first_sentences(s: str, limit: int = 220) -> str:
    """Cut a verdict at a sentence boundary, never mid-sentence: a truncated verdict can invert."""
    s = " ".join(s.split())
    if len(s) <= limit:
        return s
    cut = [m.end() for m in re.finditer(r"[.;:]\s", s) if m.end() <= limit]
    return (s[:cut[-1]].rstrip() if cut else s[:limit].rsplit(" ", 1)[0]) + " …"

def cited_results(text: str) -> list[str]:
    """Results files a document cites, including directory references like results/ladder410/."""
    out, seen = [], set()
    for h in re.findall(r"results/[A-Za-z0-9_/.\-]*\.json", text):
        if h.endswith("_provenance.json") or h in seen:
            continue
        seen.add(h)
        out.append(h)
    # directory citations: results/ladder410/ or results/ladder410/*.json
    for d in re.findall(r"results/([A-Za-z0-9_\-]+)/(?:\*|\s|`|\)|$)", text):
        dp = os.path.join(REPO, "results", d)
        if not os.path.isdir(dp):
            continue
        for f in sorted(glob.glob(os.path.join(dp, "*.json"))):
            rel = os.path.relpath(f, REPO)
            if rel.endswith("_provenance.json") or rel in seen:
                continue
            seen.add(rel)
            out.append(rel)
    return out


def own_result(doc: str, recs: list[dict], text: str = "") -> dict | None:
    """The results file that belongs to THIS document, matched on the shared id.

    Without this the index reports a neighbour's verdict: R9 cites e48's file as an input, and a
    naive first-match prints e48's verdict under R9's row.
    """
    # an explicit "**Output:**" line in the document is authoritative
    decl = re.search(r"\*\*Output:\*\*(.+)", text or "")
    if decl:
        named = re.findall(r"results/[A-Za-z0-9_/.\-]+", decl.group(1))
        for n in named:
            for r in recs:
                if r["path"].startswith(n.rstrip("/")):
                    return r
    m = re.match(r"^([A-Za-z]+\d+[a-z]?)_", doc)
    if not m:
        return None
    stem = m.group(1).lower()
    for r in recs:
        if os.path.basename(r["path"]).lower().startswith(stem + "_"):
            return r
    return None


def describe(rel: str, exposure: dict) -> dict:
    p = os.path.join(REPO, rel)
    if not os.path.exists(p):
        return {"path": rel, "exists": False}
    d = {}
    try:
        d = json.load(open(p))
    except Exception:
        d = {}
    prov = d.get("provenance") or {} if isinstance(d, dict) else {}
    script = (prov.get("script") or {}).get("path")
    payload = prov.get("payload_sha256")
    verdict = ""
    if isinstance(d, dict):
        for k in ("VERDICT", "verdict", "status", "STATUS"):
            if d.get(k):
                verdict = str(d[k])
                break
    return {
        "path": rel,
        "exists": True,
        "bytes": os.path.getsize(p),
        "sha256": sha256_file(p),
        "script": script,
        "payload_sha256": payload,
        "exposure": (exposure.get(rel) or {}).get("class", "UNCLASSIFIED"),
        "verdict": verdict,
    }


def block_for(recs: list[dict]) -> str:
    if not recs:
        return (BEGIN + "\n\n*No results file is cited by this document.*\n\n" + END)
    lines = [BEGIN, "",
             "## PROVENANCE",
             "",
             "Generated by `tools/build_provenance.py`; do not edit by hand. `readout` is the",
             "exposure class from `tools/readout_exposure.py`: **CLEAN** or **IMMUNE** need no",
             "re-score, **EXPOSED** or **INHERITED** were produced at the legacy readout.",
             "",
             "| results file | bytes | sha256 (first 16) | produced by | readout |",
             "|---|---:|---|---|---|"]
    for r in recs:
        if not r["exists"]:
            lines.append(f"| `{r['path']}` | — | **MISSING** | — | — |")
            continue
        sc = os.path.basename(r["script"]) if r.get("script") else "—"
        lines.append(f"| `{r['path']}` | {r['bytes']:,} | `{r['sha256'][:16]}` | `{sc}` | {r['exposure']} |")
    stamped = [r for r in recs if r.get("payload_sha256")]
    if stamped:
        lines += ["", "**Payload checksums** (content only, provenance block excluded):", ""]
        for r in stamped:
            lines.append(f"* `{os.path.basename(r['path'])}` — `{r['payload_sha256'][:32]}`")
    lines += ["", END]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    exposure = load_exposure()
    if not exposure:
        print("NOTE: tmp/readout_exposure.json absent; readout column will read UNCLASSIFIED.",
              file=sys.stderr)

    pins = pinned_hashes()
    ids = canonical_ids()
    stripped, frozen, unstripped, missing, index = [], [], [], [], []
    for md in sorted(glob.glob(os.path.join(EXP, "*.md"))):
        name = os.path.basename(md)
        if name in ("README.md", "INDEX.md"):
            continue
        text = open(md).read()
        is_frozen = sha256_file(md) in pins
        body = re.split(re.escape(BEGIN), text)[0].rstrip()
        # the separator the old in-document block was appended after
        body = re.sub(r"\n-{3,}\s*$", "", body).rstrip()
        # Scan the BODY, never a block written earlier: reading the full text made the generator
        # latch onto citations the prose had already dropped (CV4 phases 2-3 exposed it).
        recs = [describe(r, exposure) for r in cited_results(body)]
        missing += [r["path"] for r in recs if not r["exists"]]
        if BEGIN in text:
            if is_frozen:
                frozen.append(name)
            elif a.check:
                unstripped.append(name)
            else:
                open(md, "w").write(body + "\n")
                stripped.append(name)
        elif is_frozen:
            frozen.append(name)
        mine = own_result(name, recs, text)
        index.append({"doc": name, "id": ids.get(name, ""), "recs": recs, "frozen": is_frozen,
                      "own": os.path.basename(mine["path"]) if mine else "",
                      "verdict": (mine.get("verdict") or "") if mine else ""})

    idx = ["# INDEX: the provenance of every experiment document",
           "",
           "GENERATED by `tools/build_provenance.py`; do not edit by hand. One row per document in",
           "[`preregs/`](preregs/). The canonical ID links each document to its experiment in",
           "[`REGISTRY.md`](REGISTRY.md), which is where to start if a name is unfamiliar.",
           "",
           "\"Its own result\" is the results file this document produced, matched on its ID, not the",
           "first file it cites (R9 cites E48's file as an input). The verdict is that file's stored",
           "verdict, cut at a sentence boundary; the full string is in the file. **readout** is the",
           "exposure class from `tools/readout_exposure.py`: CLEAN or IMMUNE needed no re-score;",
           "EXPOSED or INHERITED were produced at the legacy readout, before the trailing-space fix.",
           "",
           "| ID | document | its own result | readout | verdict as stored |",
           "|---|---|---|---|---|"]
    for r in index:
        ro = ", ".join(sorted({x.get("exposure", "?") for x in r["recs"] if x["exists"]})) or "—"
        v = first_sentences(r["verdict"]).replace("|", "/") or "—"
        own = f"`{r['own']}`" if r["own"] else "none"
        fz = " (frozen)" if r["frozen"] else ""
        idx.append(f"| {r['id'] or '—'} | [`{r['doc']}`](preregs/{r['doc']}){fz} | {own} | {ro} | {v} |")
    idx += ["", f"**{len(index)} documents.** A document marked *frozen* has its exact current text "
            "pinned by a stored result, so it is never edited, not even by this tool. Any provenance "
            "block inside it is historical; the table below is current.", "",
            "## Every cited results file, by document", ""]
    for r in index:
        idx.append(f"### {r['id'] + ': ' if r['id'] else ''}[`{r['doc']}`](preregs/{r['doc']})")
        idx.append("")
        if not r["recs"]:
            idx += ["No results file is cited.", ""]
            continue
        idx += ["| results file | bytes | sha256 (first 16) | payload sha256 (first 16) | produced by | readout |",
                "|---|---:|---|---|---|---|"]
        for x in r["recs"]:
            if not x["exists"]:
                idx.append(f"| `{x['path']}` | — | **MISSING** | — | — | — |")
                continue
            sc = os.path.basename(x["script"]) if x.get("script") else "—"
            ps = f"`{x['payload_sha256'][:16]}`" if x.get("payload_sha256") else "—"
            idx.append(f"| `{x['path']}` | {x['bytes']:,} | `{x['sha256'][:16]}` | {ps} | `{sc}` | {x['exposure']} |")
        idx.append("")
    text_out = "\n".join(idx).rstrip() + "\n"
    dest = os.path.join(EXP, "..", "INDEX.md")

    if a.check:
        stale = not os.path.exists(dest) or open(dest).read() != text_out
        for m in sorted(set(missing)):
            print("MISSING", m)
        for n in unstripped:
            print("UNSTRIPPED block in an unfrozen document:", n)
        if stale:
            print("STALE docs/experiments/INDEX.md: run tools/build_provenance.py")
        print(f"{len(index)} documents ({len(frozen)} frozen); {len(set(missing))} missing files; "
              f"{len(unstripped)} unstripped; INDEX {'stale' if stale else 'current'}")
        return 1 if (missing or unstripped or stale) else 0
    open(dest, "w").write(text_out)
    print(f"wrote docs/experiments/INDEX.md ({len(index)} documents); stripped {len(stripped)} old "
          f"block(s); frozen, left untouched: {', '.join(frozen) or 'none'}")
    if missing:
        print("WARNING, missing results files:", *sorted(set(missing)), sep="\n  ")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
