# How free-threaded CPython 3.14.9 implements Python-visible shared accesses (source-derived)

Notation: L(m) = PyMutex lock = seq_cst CAS on per-object mutex m (succeeds when uncontended);
U(m) = PyMutex unlock = seq_cst CAS (base) | release store (CF); W^o / R^o = store/load with
C11 order o; RC(o) = refcount RMW (seq_cst) on owner object o (absent if owner borrowed/immortal).

| Python op | C11 sequence | source |
|---|---|---|
| `l[i] = v`  (STORE_SUBSCR_LIST_INT) | L(l); W^rel l[i]; U(l) | bytecodes.c `_STORE_SUBSCR_LIST_INT` |
| `l[i]`      (BINARY_OP_SUBSCR_LIST_INT) | R^sc l.ob_item; R^sc l[i]; TryIncref(v) | listobject.c `list_get_item_ref` |
| `o.a = v`   (STORE_ATTR_INSTANCE_VALUE) | L(o); W^rel o.a; U(o) | `_STORE_ATTR_INSTANCE_VALUE` |
| `o.a`       (LOAD_ATTR_INSTANCE_VALUE) | R^acq o.a; TryIncref(v) | `_LOAD_ATTR_INSTANCE_VALUE` |
| `o.s = v`   (STORE_ATTR_SLOT) | L(o); W^rel o.s; U(o) | `_STORE_ATTR_SLOT` |
| `o.s`       (LOAD_ATTR_SLOT) | R^sc o.s; TryIncref(v) | `_LOAD_ATTR_SLOT` |
| `d[k] = v`  (STORE_SUBSCR_DICT) | CS(d){...; W^rel entry.value}; | dictobject.c STORE_VALUE |
| `d[k]`      (BINARY_OP_SUBSCR_DICT) | R^acq keys...; R^sc entry.value; TryIncref | `_Py_TryXGetRef` |
| `c = v` nonlocal (STORE_DEREF) | CS(cell){W^rel cell.ref} | pycore_cell.h PyCell_SwapTakeRef |
| `c` nonlocal (LOAD_DEREF) | R^sc cell.ref; TryIncref | `_PyCell_GetStackRef` |
| `a[i] = v`, `a[i]` array.array | plain (non-atomic) W / R  — a C data race | arraymodule.c i_setitem/i_getitem |
| (PR #130771 planned) array | W^rlx / R^rlx | colesbury, 2025-03 |

TryIncref(v): immortal v (small ints, None, ...) or deferred -> nothing; else possibly
CAS on v's shared refcount + R^sc re-check of the slot. Owner refcount: `X[i].a = v` increfs X[i]
(TryIncRefShared CAS) and decrefs it after the store (atomic add) unless the reference is borrowed.

Compiled (clang 23, -O3, from disassembly):
| C11 | x86-64 | AArch64 (apple-m1 baseline) |
|---|---|---|
| W^rel | mov | stlr |
| W^sc  | xchg | stlr |
| R^acq | mov | ldapr |
| R^sc  | mov | ldar |
| CAS^sc | lock cmpxchg | casal |
| W^rel unlock (CF) | mov | stlrb |
