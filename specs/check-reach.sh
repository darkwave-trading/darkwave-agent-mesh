#!/usr/bin/env bash
# Each reachability check must be VIOLATED: it shows a path of the model is reachable,
# so no property passes because the model never gets there.
# Usage: specs/check-reach.sh path/to/tla2tools.jar   (run from the directory holding specs/)
set -u
jar="$1"; fail=0
check() { # spec, its configuration, then its reachability invariants
  local spec="$1" conf="$2"; shift 2
  for inv in "$@"; do
    cfg=$(mktemp --suffix=.cfg)
    sed -e '/^INVARIANTS/d' -e '/^PROPERTIES/d' "specs/$conf.cfg" > "$cfg"
    echo "INVARIANT $inv" >> "$cfg"
    if java -cp "$jar" tlc2.TLC -workers auto -metadir "$(mktemp -d)" -config "$cfg" "specs/$spec.tla" 2>&1 | grep -q "Invariant $inv is violated"; then
      echo "ok   $conf: $inv is violated (path reachable)"
    else
      echo "FAIL $conf: $inv holds: the path is not reachable"; fail=1
    fi
    rm -f "$cfg"
  done
}
check MessagePath MessagePath NotActedAndClosed NotApprovedActed NotStatedClosed NotEndedByOperator NotBudgetRefused NotDupRefused
check MessagePath MessagePath-person NotPersonActed NotAskExpiredClosed
check Exceptions Exceptions NotDiverged NotLateRefused NotRaceRefused
exit $fail
