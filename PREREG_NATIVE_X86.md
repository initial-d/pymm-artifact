# Prereg: native x86-64 replication (dev05, Xeon E5-2620 v3 Haswell, gcc, written 2026-10-25 before running)
Builds: base / cf (-DPYMM_RELEASE_UNLOCK) / fix (+ -DPYMM_SC_STORE), same 3.14.9 tree.
Predictions (herd x86tso column of Table herd):
 P1 base: SB list/attrb/slotb = 0; array SB > 0.
 P2 cf:   SB list > 0, attrb > 0, slotb > 0; attr (X[i].v, owner refcount RMW) = 0.
 P3 fix:  SB list/attrb/slotb = 0.
 P4 all builds: MP list/attr = 0. array MP = 0 (TSO forbids MP).
Kill: any P1/P3/P4 managed-cell nonzero refutes the herd x86 model of the implementation.
P2 cell = 0 at >=30M is "not detected" (Rosetta rates may not transfer), not a refutation.
Note: compiler differs (gcc vs clang); check disassembly of _PyMutex_TryUnlock and store sites first.
