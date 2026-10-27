#!/bin/bash
# Re-run cells that timed out at 25 min, with -speedcheck fast (stops at first witness; forbid still needs full search).
H=${HERD7:-herd7}
run(){ m=$1; f=$2; s=$(date +%s); out=$($H -speedcheck fast -model $m $f 2>&1); r=$(echo "$out" | grep -E '^Observation' ); echo "$f | $m | ${r:-ERR $(echo "$out"|tail -1)} | $(( $(date +%s)-s ))s"; }
export -f run; export H
printf '%s\n' \
 "rc11.cat c11/R_attr-base.litmus" "rc11.cat c11/2+2W_list-base.litmus" "rc11.cat c11/2+2W_attr-base.litmus" \
 "rc11.cat c11/2+2W_attr-cf.litmus" "rc11.cat c11/2+2W_attrb-base.litmus" "rc11.cat c11/IRIW_attr-base.litmus" \
 "x86tso.cat x86/2+2W_list-base.litmus" "x86tso.cat x86/2+2W_attr-base.litmus" "x86tso.cat x86/2+2W_attrb-base.litmus" \
 "aarch64.cat aarch64/R_attr-base.litmus" \
 | xargs -P 6 -L1 bash -c 'run "$0" "$1"'
