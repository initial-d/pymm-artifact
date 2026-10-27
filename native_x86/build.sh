#!/bin/bash
# Native x86-64 builds: base (stock), cf (release-store unlock), fix (cf + seq_cst managed stores).
set -e; cd ~/pymm
b(){ n=$1; f=$2; mkdir -p build-$n; cd build-$n
  ../cpython-3.14.9/configure --disable-gil CFLAGS="$f" > cfg.log 2>&1
  nice -n 15 make -j6 > make.log 2>&1; echo "$n done: $(./python -c "import sys;print(sys.version.split()[0], sys._is_gil_enabled())")"; cd ..; }
b base "" & b cf "-DPYMM_RELEASE_UNLOCK" & b fix "-DPYMM_RELEASE_UNLOCK -DPYMM_SC_STORE" & wait
