#!/bin/zsh
# Interleaved 2x2 cost study on the M5: each round runs all 4 builds (order rotated per round)
# for arm (native) and x86 (Rosetta 2). Output: perf/bench2_m5.tsv
cd ${0:A:h}/..
out=perf/bench2_m5.tsv; : > $out
echo "# $(date '+%F %T') host=$(hostname -s) $(sysctl -n machdep.cpu.brand_string); herd7 jobs running: $(pgrep -c herd7)" >> $out
B=(base sc cf fix)
for r in $(seq 1 15); do
  for k in 0 1 2 3; do
    b=${B[$(( (r + k) % 4 + 1 ))]}
    arch -arm64  build-arm-$b/python.exe -I perf/bench2.py arm-$b $r >> $out
    arch -x86_64 build-x86-$b/python.exe -I perf/bench2.py x86-$b $r >> $out
  done
done
echo "# done $(date '+%F %T') herd7 jobs: $(pgrep -c herd7)" >> $out
