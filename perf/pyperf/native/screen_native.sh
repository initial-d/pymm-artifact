#!/bin/bash
# screen the M5-passing pyperformance benchmarks on the native Xeon base build (one --debug-single-value run each)
cd ~/pymm/pyperf
: > screen_native.txt
for bm in $(cat ok_m5.txt); do
  if timeout 600 env PYTHONPATH=$PWD/lib ../build-base/python bm/$bm/run_benchmark.py --debug-single-value -q -o /tmp/scr_$$.json > /tmp/scr_$$.log 2>&1; then
    echo "OK $bm" >> screen_native.txt
  else
    echo "FAIL $bm: $(tail -1 /tmp/scr_$$.log)" >> screen_native.txt
  fi
  rm -f /tmp/scr_$$.json
done
echo "# done $(date '+%F %T')" >> screen_native.txt
