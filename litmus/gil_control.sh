#!/bin/zsh
# GIL control: same binaries, GIL forced on with -X gil=1 (PYTHON_GIL is ignored under -I).
# Switch interval lowered so the spin-synchronised bodies make progress.
export PYMM_SWITCH=1e-6
for B in arm-base arm-cf; do P=../build-$B/python.exe; echo "## build-$B"
  for T in SB MP; do $P -I -X gil=1 litmus.py $T array 1000000 3; done
  $P -I -X gil=1 litmus.py SB list 1000000 3
  $P -I -X gil=1 litmus.py SB attrb 1000000 3
done
