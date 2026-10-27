# Pre-registered predictions: counterfactual release-store unlock (written before any CF run)

Patch (cpython-3.14.9, #ifdef PYMM_RELEASE_UNLOCK): PyMutex unlock = one release store;
lock slow path spins (with thread-state detach) and never parks. This is a correct C11 mutex
(textbook spinlock). Baseline = same tree, same compiler, macro undefined.

Mechanism, from source (3.14.9):
- writer: LOCK (seq_cst CAS) ; release store of slot ; UNLOCK (baseline: seq_cst CAS / CF: release store)
- reader: list/slot: seq_cst load ; attr: acquire load ; small ints are immortal -> no RMW, no re-check.
SB (x=1; r0=y || y=1; r1=x) needs a later load to overtake an earlier store.

| platform | location | baseline | CF prediction | why |
|---|---|---|---|---|
| ARM | list | 0 | 0 | store stlr, load ldar: RCsc forbids SB |
| ARM | slot | 0 | 0 | same (seq_cst load) |
| ARM | attr | 0 | >0 IF acquire load compiles to ldapr | RCpc ldapr may pass stlr; unlock CAS removed |
| x86 | list/slot/attr/dict | 0 | >0 | release store = MOV, loads = MOV; only the unlock lock-cmpxchg fenced |
| any | MP | 0 | 0 | release store + acquire/seq_cst load forbids MP regardless |
| any | array | >0 | >0 | no locks at all |

Kill conditions for the "SC is accidental" claim:
- x86 CF shows 0 SB on list/attr after >=10M iterations while array still shows SB in the same
  harness -> SB-freedom does not hinge on the unlock RMW; claim dies.
- MP appears on list/attr in CF -> my reading of the source is wrong somewhere; stop and re-read.
