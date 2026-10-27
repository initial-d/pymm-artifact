#!/bin/bash
# Interleaved 2x2 cost study, native x86-64 (gcc 11.4). Output: bench2_native.tsv
cd ~/pymm; out=bench2_native.tsv; : > $out
echo "# $(date "+%F %T") host=$(hostname -s) $(grep -m1 "model name" /proc/cpuinfo | cut -d: -f2) load=$(cut -d" " -f1-3 /proc/loadavg)" >> $out
B=(base sc cf fix)
for r in $(seq 1 15); do for k in 0 1 2 3; do b=${B[$(( (r + k) % 4 ))]}
  build-$b/python -I bench2.py x86n-$b $r >> $out; done; done
echo "# done $(date "+%F %T") load=$(cut -d" " -f1-3 /proc/loadavg)" >> $out
