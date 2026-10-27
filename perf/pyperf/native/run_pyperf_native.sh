#!/bin/bash
# pyperformance on native x86 (dev05, Xeon E5-2620 v3, gcc 11.4), 4 builds x screened benchmarks x 3 rounds.
# Per (round, benchmark) the build order is rotated; each round is one paired sample. pyperf --fast.
cd ~/pymm/pyperf
B=(base sc cf fix); R=${R:-3}
echo "# start $(date '+%F %T') $(grep -m1 'model name' /proc/cpuinfo | cut -d: -f2) load=$(cut -d' ' -f1-3 /proc/loadavg)" > run_native.log
for r in $(seq 1 $R); do
  i=0
  for bm in $(grep ^OK screen_native.txt | awk '{print $2}'); do
    i=$((i+1))
    for k in 0 1 2 3; do
      b=${B[$(( (i + k + r) % 4 ))]}
      mkdir -p out_native/r$r-$b
      env PYTHONPATH=$PWD/lib ../build-$b/python bm/$bm/run_benchmark.py \
        --fast -q --append out_native/r$r-$b/all.json >> run_native.log 2>&1 || echo "FAIL r$r $b $bm" >> run_native.log
    done
  done
  echo "# round $r done $(date '+%F %T') load=$(cut -d' ' -f1-3 /proc/loadavg)" >> run_native.log
done
echo "# done $(date '+%F %T') load=$(cut -d' ' -f1-3 /proc/loadavg)" >> run_native.log
