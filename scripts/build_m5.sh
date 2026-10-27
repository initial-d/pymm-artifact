#!/bin/zsh
# Build the four free-threaded CPython 3.14.9 configurations used on the Apple M5, for arm64 and
# (under Rosetta 2) x86_64, out of tree next to a patched source tree.
#   1. tar xf Python-3.14.9.tar.xz && cd Python-3.14.9 && git apply ../model/pymm_patch.diff && cd ..
#   2. CPY=Python-3.14.9 scripts/build_m5.sh
# base = stock; sc = seq_cst managed accesses; cf = release-store unlock; fix = cf + sc.
set -e
CPY=${CPY:?set CPY to the patched CPython 3.14.9 source tree}
typeset -A F; F=(base "" sc "-DPYMM_SC_STORE" cf "-DPYMM_RELEASE_UNLOCK" fix "-DPYMM_RELEASE_UNLOCK -DPYMM_SC_STORE")
for a in arm x86; do
  [ $a = arm ] && A=arm64 || A=x86_64
  for b in base sc cf fix; do
    mkdir -p build-$a-$b; (cd build-$a-$b &&
      arch -$A ../$CPY/configure --disable-gil CFLAGS="${F[$b]}" > cfg.log 2>&1 &&
      arch -$A make -j8 > make.log 2>&1)
    echo "$a-$b: $(arch -$A build-$a-$b/python.exe -c 'import sys; print(sys.version.split()[0], sys._is_gil_enabled())')"
  done
done
