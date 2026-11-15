#!/usr/bin/env bash
# build_audit.sh - regenerate the audit papers from results/ and gate them.
#
# One source, two builds:
#   audit_paper_extended  the public extended version: the same source with \EXTENDED defined, which adds
#                         CV3's score-unit result to App. E (see that file's header). Same gates.
#   audit_paper_5pp   the camera-ready. Body gated at 5 pages, as in the submission, by Tarush's choice: the
#                     workshop FAQ allows 6 for the camera-ready. References and appendices ride free.
#
# ONE DOCUMENT, ON PURPOSE. A 7-page variant and a variant B both existed and both were deleted, on
# 2026-08-24 and 2026-08-29. Two documents claiming the same numbers is a currency hazard and the
# 7pp had already drifted once. Its stale PDF nonetheless sat in this directory for five days after
# the .tex was removed, which is the same failure in a quieter form: delete the ARTIFACTS, not just
# the source.
#
# The 7-page variant was deleted 2026-08-24. Two documents claiming the same numbers is a currency
# hazard, and it had already drifted once: a claim-level fix landed in the 5pp first.
#
# Figures are drawn from results/*.json at build time; nothing in them is typed in. The prose gate
# enforces the house rules (no em dashes, no bold in the abstract, no hedging boilerplate, no
# sentence over 45 words).
#
#   ./build_audit.sh            regenerate figures, compile both, gate
#   ./build_audit.sh --fast     compile only, for prose edits
#
# Exits non-zero if a prose gate fails, if LaTeX or BibTeX errors, if the body exceeds 5 pages, or if the
# PDF Author field does not name the author (the camera-ready is de-anonymised; under double-blind
# review this gate required the field to be EMPTY).
set -uo pipefail
set -e

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
export ROOT
PY="$ROOT/.venv/bin/python"

FAST=0
DOCS=(audit_paper_5pp audit_paper_extended)
for a in "$@"; do
  case "$a" in
    --fast) FAST=1 ;;
    audit_paper_*) DOCS=("$a") ;;
    *) echo "unknown argument: $a" >&2; exit 2 ;;
  esac
done

# Both submission variants are gated at 5 body pages. A variant that is not gated is a variant that
# silently stops being submittable, which is how the deleted 7pp drifted.
limit_for() { case "$1" in audit_paper_5pp*|audit_paper_extended*) echo 5 ;; *) echo 99 ;; esac; }

cd "$HERE"

if [[ "$FAST" -eq 0 ]]; then
  echo "==> regenerating figures from results/"
  "$PY" "$ROOT/figures/make_audit_figures.py"
  echo "==> regenerating appendix tables from results/"
  "$PY" "$ROOT/paper/tools/make_audit_tables.py"
fi

FAIL=0
for DOC in "${DOCS[@]}"; do
  LIMIT=$(limit_for "$DOC")
  echo
  echo "==================== $DOC (body limit $LIMIT) ===================="

  echo "==> prose gate"
  "$PY" "$ROOT/paper/tools/prose_lint.py" "$DOC.tex" --check

  echo "==> latex"
  pdflatex -interaction=nonstopmode "$DOC.tex" >/dev/null 2>&1 || true
  # BibTeX errors were once swallowed here (`|| true`), which hid an @ inside a % comment in refs.bib
  # that BibTeX parses as an entry. A failing bibtex now fails the build, with its log.
  if ! bibtex "$DOC" > "$DOC.bibtex.out" 2>&1; then
    echo "FAIL: bibtex"; tail -20 "$DOC.bibtex.out"; FAIL=1
  fi
  pdflatex -interaction=nonstopmode "$DOC.tex" >/dev/null 2>&1 || true
  pdflatex -interaction=nonstopmode "$DOC.tex" >/dev/null 2>&1 || true

  # This block runs without -e/pipefail on purpose: `grep -c` exits 1 on zero matches and
  # `pdftotext | awk ... exit` SIGPIPEs pdftotext, either of which would kill the script silently
  # AFTER the assignment, which is how a gate like this first appears to "pass" while printing
  # nothing.
  set +e
  # '^!' and not '^! ': a fatal "!pdfTeX error" (an unreadable figure) has no space and once passed
  # this gate as 0 errors while no PDF was written. A missing PDF is itself an error.
  ERRORS=$(grep -cE '^!' "$DOC.log" || true)
  [[ -s "$DOC.pdf" ]] || ERRORS=$((ERRORS+1))
  OVERFULL=$(grep -c 'Overfull \\hbox' "$DOC.log" || true)
  UNDEF=$(grep -ciE 'warning.*(undefined|citation)' "$DOC.log" || true)
  # BODY is the number of pages the body occupies, which is NOT the page the References heading
  # lands on: those differ by one exactly when the body fills its last page and References starts
  # at the top of the next. Margin line numbers are digit-only lines and are skipped first.
  BODY=$("$PY" -c '
import re, subprocess, sys
pages = subprocess.run(["pdftotext", sys.argv[1], "-"],
                       capture_output=True, text=True).stdout.split("\f")
for i, pg in enumerate(pages, 1):
    lines = [l.strip() for l in pg.splitlines()
             if l.strip() and not re.fullmatch(r"[0-9]+", l.strip())]
    if "References" in lines:
        # the camera-ready opens the references page with the acknowledgments
        print(i - 1 if lines[0] in ("References", "Acknowledgments and Disclosure of Funding") else i)
        break
else:
    print(len(pages))
' "$DOC.pdf")
  TOTAL=$(pdfinfo "$DOC.pdf" | awk '/^Pages/{print $2}')
  AUTHOR=$(pdfinfo "$DOC.pdf" | sed -n 's/^Author: *//p')
  set -e

  echo
  echo "    latex errors      $ERRORS"
  echo "    overfull boxes    $OVERFULL"
  echo "    undefined refs    $UNDEF"
  echo "    body pages        $BODY   (limit $LIMIT; references and appendices ride free)"
  echo "    total pages       $TOTAL"
  echo "    pdf Author field  '${AUTHOR}'   (must name the author: the camera-ready is de-anonymised)"

  [[ "$ERRORS" -eq 0 ]] || { echo "FAIL: $DOC latex errors"; FAIL=1; }
  [[ "$BODY" -le "$LIMIT" ]] || { echo "FAIL: $DOC body is $BODY pages, limit $LIMIT"; FAIL=1; }
  [[ "$AUTHOR" == "Tarush Gupta" ]] || { echo "FAIL: $DOC pdf Author field is '$AUTHOR', expected 'Tarush Gupta'"; FAIL=1; }
  [[ "$OVERFULL" -eq 0 ]] || echo "warn: $OVERFULL overfull box(es)"
  [[ "$UNDEF" -eq 0 ]] || echo "warn: $UNDEF undefined reference(s)"
done

exit $FAIL
