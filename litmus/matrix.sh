#!/bin/zsh
for P in ${PY314T:?set PY314T to python3.14t} ${PY315T:?set PY315T to python3.15t}; do
  for T in SB MP LB R 2+2W; do for K in list attr slot dict; do
    $P -I litmus.py $T $K 1000000 3
  done; done
done
echo "=== GIL control (3.14t with PYTHON_GIL=1) ==="
for T in SB MP; do for K in list attr; do
  PYTHON_GIL=1 ${PY314T:?set PY314T to python3.14t} -I litmus.py $T $K 1000000 1
done; done
