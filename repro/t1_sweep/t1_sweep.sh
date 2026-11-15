#!/usr/bin/env bash
# T1 sweep driver — strictly sequential, CPU only, no thread-count changes.
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export SP="${SP:-$HERE/_run}"
mkdir -p "$SP/before" "$SP/logs"
cd "$(cd "$HERE/../.." && pwd)"
# The results files carrying NO provenance block at all. SPEC §2 names three; auditing every
# payload (repro/t1_sweep/t1_classify.py) finds FIVE -- e37_rank_70m and e37_rank_160m are also
# provenance-less and the spec's pre-hoc map omits them. Label only: both branches CONTINUE, so
# this never changes control flow, and the 2026-08-29 run was driven with the spec's three.
PRE_PROV=" e33_logit_v2 e38_geometry e49_stability e37_rank_70m e37_rank_160m "

for M in "$@"; do
  echo "############################################################"
  echo "### $M   start $(date '+%H:%M:%S')"
  OUT=$(grep -o 'OUTPUTS=([^)]*)' repro/exp/$M.sh | sed 's/OUTPUTS=(//;s/)//')
  echo "### outputs: $OUT"
  for f in $OUT; do
    key=$(echo "$f" | tr '/' '_')
    if [ -f "$f" ]; then cp "$f" "$SP/before/$key"; echo "### backed up $f"
    else echo "### NO BASELINE (absent before run): $f"; fi
  done
  s=$(date +%s)
  bash repro/exp/$M.sh > "$SP/logs/$M.log" 2>&1
  rc=$?
  e=$(date +%s)
  echo "### $M exited rc=$rc after $((e-s))s"
  [ "$rc" -ne 0 ] && { echo "### last 25 log lines:"; tail -25 "$SP/logs/$M.log"; }
  V=$(SP="$SP" .venv/bin/python "$HERE/t1_check.py" diff "$M" "$rc" "$((e-s))" $OUT | tee -a "$SP/sweep_detail.log" | grep '^VERDICT=' | cut -d= -f2)
  echo "### $M VERDICT=$V"
  # Match any MOVED* verdict. The 2026-08-29 run used `= "MOVED"`, and when the _RC1 suffix was
  # added for harness-rejected outputs, e33_logit_v2 came back MOVED_RC1 and skipped this test --
  # it had to be run by hand. MOVED_AS_PREDICTED is excluded deliberately: hitting a pre-computed
  # hash proves every number reproduced, which rules out a shared cause more strongly than the
  # preflight re-run does.
  if [ "${V#MOVED}" != "$V" ] && [ "$V" != "MOVED_AS_PREDICTED" ]; then
    echo "### MOVED -> re-running preflight to test whether the cause is SHARED"
    if ! SP="$SP" .venv/bin/python "$HERE/t1_check.py" shared | tee -a "$SP/sweep_detail.log"; then
      echo "### *** SHARED CAUSE. STOPPING THE SWEEP at $M. ***" | tee -a "$SP/sweep_detail.log"
      echo "HALTED_SHARED $M" >> "$SP/verdicts.tsv"
      exit 9
    fi
    case "$PRE_PROV" in *" $M "*) echo "### EXPECTED: $M is one of the pre-provenance three. CONTINUE." ;;
                       *) echo "### LOCAL CAUSE recorded. CONTINUE." ;; esac
  fi
done
echo "############################################################"
echo "### SWEEP SEGMENT COMPLETE $(date '+%H:%M:%S')"
