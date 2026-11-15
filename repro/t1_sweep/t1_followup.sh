#!/usr/bin/env bash
# t1_followup.sh — the fix-verification pass, run AFTER the main T1 sweep driver exits.
#
# WHY THIS IS SEPARATE FROM THE SWEEP. The sweep's verdict for e33_logit_v2 is
# "DOES NOT REPRODUCE as shipped" and that verdict is final -- SPEC §1.3 forbids re-running with
# changed flags until something passes. This pass is not part of that verdict. It answers a
# different, clearly labelled question: does the CORRECTED recipe (--band 9,22, the only invocation
# of the never-changed parser that yields the stored band [9..21]) reproduce the stored result?
#
# It also re-runs e48_crossover, which never completed: it aborted on its own C0 control after 37s
# because e33's wrong-band output had overwritten the file C0 checks against. That input has been
# restored (verified byte-identical to the HF mirror snapshot ffdac38e5e95).
#
# THE GUARD. If the corrected e33 re-run does NOT land on the stored payload, this script RESTORES
# the stored file before touching e48_crossover, so a second bad e33 cannot poison it twice. That
# is the failure mode that cost us e48_crossover the first time; it does not get to happen again.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
cd "$REPO"
SP="${SP:-$HERE/_run}"
export SP
PY="$REPO/.venv/bin/python"

E33_JSON="results/e33_logit_baseline_410m_v2.json"
E33_STORED_SHA="73b90a8b5d582481"          # verified against HF snapshot ffdac38e5e95
E33_BACKUP="$SP/before/results_e33_logit_baseline_410m_v2.json"
WAIT_PID="${WAIT_PID:-}"

payload_sha() {
  "$PY" - "$1" <<'PY'
import json, sys, os
sys.path.insert(0, "src")
from provenance import canonical_payload_sha
print(canonical_payload_sha(json.load(open(sys.argv[1]))))
PY
}

restore_e33() {
  if [ -f "$E33_BACKUP" ]; then
    cp "$E33_BACKUP" "$E33_JSON"
    echo "### RESTORED $E33_JSON from pre-run backup -> $(payload_sha "$E33_JSON" | cut -c1-16)"
  else
    echo "### !! no backup at $E33_BACKUP — recover from HF before running e48_crossover"
    return 1
  fi
}

echo "############################################################"
echo "### T1 FIX-VERIFICATION PASS   $(date '+%Y-%m-%d %H:%M:%S')"

if [ -n "$WAIT_PID" ]; then
  echo "### waiting for the main sweep driver (pid $WAIT_PID) to exit..."
  while kill -0 "$WAIT_PID" 2>/dev/null; do sleep 30; done
  echo "### main driver exited at $(date '+%H:%M:%S'); starting fix verification"
fi

echo "" >> "$SP/verdicts.tsv"
echo "# --- FIX-VERIFICATION PASS (not part of the sweep verdict) ---" >> "$SP/verdicts.tsv"

# ---------------------------------------------------------------- 1. e33 with the corrected band
echo "### [1/2] e33_logit_v2 with the CORRECTED recipe (--band 9,22)"
bash "$HERE/t1_sweep.sh" e33_logit_v2
got="$(payload_sha "$E33_JSON" | cut -c1-16)"
if [ "$got" = "$E33_STORED_SHA" ]; then
  echo "### FIX VERIFIED: e33 payload $got == stored $E33_STORED_SHA."
  echo "###   The recipe was the only defect. The stored result is reproduced exactly."
  echo "e33_logit_v2_FIXED	BIT_IDENTICAL	0	-	$E33_JSON" >> "$SP/verdicts.tsv"
else
  echo "### FIX DID NOT VERIFY: e33 payload $got != stored $E33_STORED_SHA."
  echo "###   The band was NOT the only cause. Do not draw a conclusion; see the ladder in"
  echo "###   $SP/detail_e33_logit_v2.txt"
  echo "e33_logit_v2_FIXED	MOVED	-	-	$E33_JSON" >> "$SP/verdicts.tsv"
  restore_e33 || exit 3
fi

# ---------------------------------------------------------------- 2. e48_crossover, unblocked
echo "### [2/2] e48_crossover (its C0 input is now the stored e33: $(payload_sha "$E33_JSON" | cut -c1-16))"
bash "$HERE/t1_sweep.sh" e48_crossover

echo "############################################################"
echo "### FIX-VERIFICATION PASS COMPLETE  $(date '+%Y-%m-%d %H:%M:%S')"
tail -6 "$SP/verdicts.tsv"
