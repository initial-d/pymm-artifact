# Module-global schemes (audit, see AUDIT.md). STORE_GLOBAL -> PyDict_SetItem: dict lock,
# STORE_VALUE (release; seq_cst under PYMM_SC_STORE), PyMutex unlock. LOAD_GLOBAL_MODULE reads
# me_value with a RELAXED load and, for immortal/deferred values, never re-reads it
# (bytecodes.c:1814, _Py_TryIncrefCompareStackRef). No owner refcount (globals dict is borrowed).
import os, gen_litmus as G, gen_hw as H
G.SCHEMES.update({
 'global-base':  dict(st=G.REL, ld=G.RLX, unlock='rmw', rc=False),
 'global-fix':   dict(st=G.SC,  ld=G.RLX, unlock='rmw', rc=False),
 'global-fixcf': dict(st=G.SC,  ld=G.RLX, unlock='rel', rc=False),
 'global-fix2':  dict(st=G.SC,  ld=G.SC,  unlock='rmw', rc=False),
 'global-fix2cf': dict(st=G.SC, ld=G.SC,  unlock='rel', rc=False),  # extended patch, CF unlock
})
H.HW.clear(); H.HW.update({
 'global-base':  ('rel', 'rlx', 'rmw', False),
 'global-fix':   ('sc',  'rlx', 'rmw', False),
 'global-fixcf': ('sc',  'rlx', 'rel', False),
 'global-fix2':  ('sc',  'sc',  'rmw', False),
 'global-fix2cf': ('sc', 'sc',  'rel', False),
})
H.SHAPES = {k: G.SHAPES[k] for k in ('SB', 'MP', 'R')}
if __name__ == '__main__':
    os.makedirs('global/c11', exist_ok=True); os.chdir('global')
    for sh in H.SHAPES:
        for s in [k for k in G.SCHEMES if k.startswith('global')]:
            open(f'c11/{sh}_{s}.litmus', 'w').write(G.litmus(sh, s))
    for a in ('aarch64', 'x86'): H.gen(a)
