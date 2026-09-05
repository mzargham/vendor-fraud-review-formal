#!/usr/bin/env bash
# Run every check and write one JSON report. The final CHECKS: line is the
# only summary; each step's full output is in checks/out/last.log.
set -uo pipefail
cd "$(dirname "$0")/.."
mkdir -p checks/out
LOG=checks/out/last.log
: > "$LOG"
SHA=$(git rev-parse --short HEAD 2>/dev/null || echo none)
DIRTY=$(test -n "$(git status --porcelain 2>/dev/null)" && echo true || echo false)
declare -a STEPS=()
FAIL=0

step() { # step <name> <expected-exit> <cmd...>
  local name="$1" expect="$2"; shift 2
  echo "== $name ==" | tee -a "$LOG"
  "$@" >> "$LOG" 2>&1
  local got=$?
  if [ "$got" -eq "$expect" ]; then
    STEPS+=("\"$name\": \"pass\""); echo "   pass"
  else
    STEPS+=("\"$name\": \"FAIL\""); echo "   FAIL (exit $got, expected $expect; see checks/out/last.log)"; FAIL=1
  fi
}

step "toolchain: pinned sysml, checksum-verified" 0 bash toolchain/get-sysml.sh
step "model: validate -strict" 0 toolchain/bin/sysml model/vendor-fraud-review.sysml -validate -strict
step "model: satisfy RunConfigurations" 0 toolchain/bin/sysml model/vendor-fraud-review.sysml -satisfy=RunConfigurations
step "counterexample: unattended run must fail satisfy" 1 toolchain/bin/sysml counterexamples/run-unattended.sysml -satisfy=RunConfigurations

regen() {
  toolchain/bin/sysml model/vendor-fraud-review.sysml -convert ttl > generated/vendor-fraud-review.ttl \
    && uv run python checks/render_queries.py \
    && git diff --quiet -- generated/
}
step "generated/ regenerates byte-identically" 0 regen
step "site: myst build --html" 0 uv run myst build --html
step "tests: full suite (verbatim, model, shapes, queries, gaps, walkthrough)" 0 uv run pytest -q

RESULT=$([ "$FAIL" -eq 0 ] && echo PASS || echo FAIL)
printf '{"sha":"%s","dirty":%s,"time":"%s","steps":{%s},"result":"%s"}\n' \
  "$SHA" "$DIRTY" "$(date -u +%FT%TZ)" "$(IFS=,; echo "${STEPS[*]}")" "$RESULT" > checks/out/report.json
echo "CHECKS: $RESULT (sha=$SHA dirty=$DIRTY)"
exit "$FAIL"
