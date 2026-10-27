#!/bin/bash
# Native x86 litmus: SB on key kinds per build (10M x 3 = 30M), MP sanity.
cd ~/pymm
for b in base cf fix; do P=build-$b/python
  for k in list attr attrb slotb dict; do echo "[$b] $(nice -n 10 $P -I litmus.py SB $k 10000000 3)"; done
  echo "[$b] $(nice -n 10 $P -I litmus.py SB array 2000000 3)"
  for k in list attr array; do echo "[$b] $(nice -n 10 $P -I litmus.py MP $k 2000000 3)"; done
done
