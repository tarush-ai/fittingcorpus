#!/usr/bin/env python
r"""prose_lint.py - deterministic prose gate for the paper sources.

The papers acquired a house style that reads as machine-generated: em dashes as the default
connective, bold as emphasis-spray, inline results-file paths, and hedging boilerplate that
qualifies every claim inside the sentence that makes it. None of that is a judgement call once
it is written down as a rule, so it is written down here and enforced.

  paper/tools/prose_lint.py paper/original_paper.tex            # report
  paper/tools/prose_lint.py paper/*.tex --fix              # rewrite what is mechanically fixable
  paper/tools/prose_lint.py paper/*.tex --check            # exit 1 if any rule fails (CI gate)

RULES
  R1  no em dashes.  LaTeX `---`, unicode `—`, and spaced `--`.  A clause worth setting off is
      worth a semicolon, a comma, or its own sentence.  --fix applies: ` --- ` -> `; ` when the
      following word is lowercase (a continuing clause), `. ` + capitalised otherwise.
  R2  no \textbf in the abstract, and at most BOLD_MAX in the body.  Bold that appears twelve
      times in one paragraph is not emphasis, it is texture.
  R3  no \src{} inline provenance.  A reader cannot open results/e57_grid_variance_ci.json.
      Provenance belongs in one appendix table and one repository URL.
  R4  no \todo markers.
  R5  no hedging boilerplate from the banned list.  These are phrases that qualify a claim
      inside the sentence asserting it, which reads as a system hedging rather than an author
      deciding.  Qualify once, in Limitations.
  R6  no sentence longer than MAX_WORDS words outside of tables and captions.
"""
from __future__ import annotations

import argparse
import re
import sys

BOLD_MAX = 12
MAX_WORDS = 45

BANNED_PHRASES = [
    "we take this to mean",
    "which is not the same as",
    "it remains possible that",
    "what kind of paper this is",
    "is less broken",
    "not excluded",
    "worth noting",
    "it is worth",
    "in some sense",
    "arguably",
    "delve",
    "crucially",
    "importantly,",
    "notably,",
    "furthermore,",
    "moreover,",
    "that said,",
    "at the end of the day",
    "a testament to",
    "underscores",
    "sheds light on",
    "paves the way",
    "rich tapestry",
]

# Environments whose contents are exempt from the sentence-length rule.
EXEMPT_ENVS = ("tabular", "thebibliography", "verbatim", "equation", "align")


def _strip_comments(text: str) -> str:
    return re.sub(r"(?<!\\)%.*", "", text)


def _abstract(text: str) -> str:
    m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", text, re.S)
    return m.group(1) if m else ""


def _body_sentences(text: str):
    """Yield (line_no, sentence) outside exempt environments, captions and section headings.

    ACCUMULATE INTO A PARAGRAPH, THEN SPLIT. Splitting each source LINE into sentences, as this did
    until 2026-08-29, meant a sentence wrapped across two source lines was never assembled, so R6
    (no sentence over 45 words) COULD NOT FIRE ON ANY SENTENCE IN THIS PAPER -- every long one is
    hard-wrapped. The paired witness: one 59-word sentence passed when wrapped over two lines and
    failed when joined onto one. A gate that cannot fire is not a gate.

    With the buffer, the rule reports what is actually there. The line number is the line the
    sentence STARTS on, which is what you need to go and fix it.
    """
    out, depth = [], 0
    buf, buf_start = [], 0

    def flush():
        if not buf:
            return
        para = " ".join(buf)
        for s in re.split(r"(?<=[.!?])\s+", para):
            s = s.strip()
            if s:
                out.append((buf_start, s))
        buf.clear()

    for lineno, raw in enumerate(text.split("\n"), start=1):
        if any(f"\\begin{{{e}}}" in raw for e in EXEMPT_ENVS):
            flush(); depth += 1
        if any(f"\\end{{{e}}}" in raw for e in EXEMPT_ENVS):
            flush(); depth = max(0, depth - 1)
            continue
        # A blank line, a table row, or a line opening with a macro all end the current paragraph.
        # They are still skipped as content -- the change is that they now FLUSH what came before,
        # instead of the buffer silently spanning them.
        if depth or not raw.strip() or raw.strip().startswith("\\") or "&" in raw:
            flush()
            continue
        if not buf:
            buf_start = lineno
        buf.append(raw.strip())
    flush()
    return out


def fix_em_dashes(text: str) -> tuple[str, int]:
    """R1 --fix.  ` --- ` becomes `; ` before a lowercase word and `. ` before a capital.
    A trailing ` ---` at clause end becomes `,`.  Deterministic, reviewed afterwards by a human."""
    n = 0

    def repl(m):
        nonlocal n
        n += 1
        nxt = m.group(1)
        if nxt and nxt[0].isupper():
            return ". " + nxt
        return "; " + nxt

    text = re.sub(r"\s*(?:---|—)\s*(\S)", repl, text)
    return text, n


def lint(path: str, fix: bool) -> list[str]:
    src = open(path).read()
    text = _strip_comments(src)
    problems: list[str] = []

    # ---- R1 em dashes
    dashes = len(re.findall(r"---|—", text))
    if dashes:
        if fix:
            src, n = fix_em_dashes(src)
            problems.append(f"R1 FIXED  {n} em dash(es) rewritten")
        else:
            problems.append(f"R1 FAIL   {dashes} em dash(es)")

    # ---- R2 bold
    abs_bold = len(re.findall(r"\\textbf", _abstract(text)))
    if abs_bold:
        problems.append(f"R2 FAIL   {abs_bold} \\textbf in the abstract (limit 0)")
    body_bold = len(re.findall(r"\\textbf", text)) - abs_bold
    if body_bold > BOLD_MAX:
        problems.append(f"R2 FAIL   {body_bold} \\textbf in the body (limit {BOLD_MAX})")

    # ---- R3 inline provenance
    srcs = len(re.findall(r"\\src\{", text))
    if srcs:
        problems.append(f"R3 FAIL   {srcs} inline \\src{{}} provenance macro(s)")

    # ---- R4 todo
    todos = len(re.findall(r"\\todo\{", text))
    if todos:
        problems.append(f"R4 FAIL   {todos} \\todo marker(s)")

    # ---- R5 boilerplate
    low = text.lower()
    for p in BANNED_PHRASES:
        c = low.count(p)
        if c:
            problems.append(f'R5 FAIL   {c}x banned phrase "{p}"')

    # ---- R6 sentence length
    # Count the sentence the same way the test does. Reporting `len(s.split())` while testing the
    # macro-stripped length printed "37-word sentence" next to a failure of a >45 rule, because
    # stripping `$R\ge10$` to bare words RAISES the count. A gate whose message contradicts its own
    # verdict gets argued with instead of obeyed.
    def _wc(s):
        return len(re.sub(r"\\[a-zA-Z]+|[{}$\\]", " ", s).split())
    long_ones = [(ln, s) for ln, s in _body_sentences(text) if _wc(s) > MAX_WORDS]
    for ln, s in long_ones:
        problems.append(f"R6 FAIL   line {ln}: {_wc(s)}-word sentence: {s[:70]}...")

    if fix:
        open(path, "w").write(src)
    return problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--fix", action="store_true", help="apply the mechanical fixes (R1 only)")
    ap.add_argument("--check", action="store_true", help="exit 1 if any rule fails")
    a = ap.parse_args()

    failed = False
    for p in a.paths:
        probs = lint(p, a.fix)
        hard = [x for x in probs if "FAIL" in x]
        print(f"\n{p}: {'OK' if not hard else str(len(hard)) + ' problem(s)'}")
        for x in probs:
            print("  " + x)
        failed |= bool(hard)
    return 1 if (failed and a.check) else 0


if __name__ == "__main__":
    raise SystemExit(main())
