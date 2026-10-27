#!/bin/zsh
# pyperformance subset (benchmarks with no third-party deps that run on our builds; see screen.txt)
# on the 4 builds x 2 arches of the M5. Per benchmark, build order is rotated. pyperf --fast.
cd ${0:A:h}
B=(base sc cf fix); i=0
echo "# start $(date '+%F %T') $(sysctl -n machdep.cpu.brand_string) herd7=$(pgrep -c herd7)" > run.log
for bm in $(grep ^OK screen.txt | awk '{print $2}'); do
  i=$((i+1))
  for k in 0 1 2 3; do
    b=${B[$(( (i + k) % 4 + 1 ))]}
    for a in arm x86; do
      [ $a = arm ] && A=arm64 || A=x86_64
      mkdir -p out/$a-$b
      arch -$A env PYTHONPATH=$PWD/lib ../../build-$a-$b/python.exe bm/$bm/run_benchmark.py \
        --fast -q --append out/$a-$b/all.json >> run.log 2>&1 || echo "FAIL $a-$b $bm" >> run.log
    done
  done
done
echo "# done $(date '+%F %T') herd7=$(pgrep -c herd7)" >> run.log
