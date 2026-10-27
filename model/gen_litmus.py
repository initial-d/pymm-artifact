# Generate C11 litmus tests (herd7 C syntax) for Python-level litmus shapes under each CPython
# implementation scheme. A Python access is expanded to the C11 sequence CPython executes.
import os, itertools

SC, REL, ACQ, RLX = 'memory_order_seq_cst', 'memory_order_release', 'memory_order_acquire', 'memory_order_relaxed'

# scheme: how a Python store/load of a shared slot compiles
SCHEMES = {
 # name: dict(store=..., load=..., unlock=..., owner_rc=bool, na=bool)
 'list-base':  dict(st=REL, ld=SC,  unlock='rmw', rc=False),
 'list-cf':    dict(st=REL, ld=SC,  unlock='rel', rc=False),
 'attr-base':  dict(st=REL, ld=ACQ, unlock='rmw', rc=True),
 'attr-cf':    dict(st=REL, ld=ACQ, unlock='rel', rc=True),
 'attrb-base': dict(st=REL, ld=ACQ, unlock='rmw', rc=False),
 'attrb-cf':   dict(st=REL, ld=ACQ, unlock='rel', rc=False),
 'array-now':  dict(na=True),
 'array-fix':  dict(st=RLX, ld=RLX, unlock=None, rc=False),
 'proposed':   dict(st=SC,  ld=SC,  unlock='rel', rc=False),   # proposed fix, with the WEAKER lock
}

# Python-level litmus shapes: per thread, a list of ('W',loc,val) / ('R',loc,reg)
SHAPES = {
 'SB':   ([('W','x',1),('R','y','r0')], [('W','y',1),('R','x','r0')]),
 'MP':   ([('W','x',1),('W','y',1)],   [('R','y','r0'),('R','x','r1')]),
 'LB':   ([('R','x','r0'),('W','y',1)], [('R','y','r0'),('W','x',1)]),
 'R':    ([('W','x',1),('W','y',1)],   [('W','y',2),('R','x','r0')]),
 '2+2W': ([('W','x',1),('W','y',2)],   [('W','y',1),('W','x',2)]),
 'IRIW': ([('W','x',1)], [('W','y',1)], [('R','x','r0'),('R','y','r1')], [('R','y','r0'),('R','x','r1')]),
 'WRC':  ([('W','x',1)], [('R','x','r0'),('W','y',1)], [('R','y','r0'),('R','x','r1')]),
}
COND = {   # the SC-forbidden outcome
 'SB':   'exists (0:r0=0 /\\ 1:r0=0)',
 'MP':   'exists (1:r0=1 /\\ 1:r1=0)',
 'LB':   'exists (0:r0=1 /\\ 1:r0=1)',
 'R':    'exists ([y]=2 /\\ 1:r0=0)',
 '2+2W': 'exists ([x]=1 /\\ [y]=1)',
 'IRIW': 'exists (2:r0=1 /\\ 2:r1=0 /\\ 3:r0=1 /\\ 3:r1=0)',
 'WRC':  'exists (1:r0=1 /\\ 2:r0=1 /\\ 2:r1=0)',
}

def body(ops, s):
    out = []
    for op in ops:
        kind, loc = op[0], op[1]
        m, o = 'm' + loc, 'o' + loc            # per-object mutex and owner refcount
        if s.get('na'):
            out.append(f'*{loc} = {op[2]};' if kind == 'W' else f'int {op[2]} = *{loc};')
            continue
        if kind == 'W':
            if s['unlock']:
                out.append(f'atomic_exchange_explicit({m}, 1, {SC});')
            out.append(f'atomic_store_explicit({loc}, {op[2]}, {s["st"]});')
            if s['unlock'] == 'rmw':
                out.append(f'atomic_exchange_explicit({m}, 0, {SC});')
            elif s['unlock'] == 'rel':
                out.append(f'atomic_store_explicit({m}, 0, {REL});')
        else:
            out.append(f'int {op[2]} = atomic_load_explicit({loc}, {s["ld"]});')
        if s['rc']:
            out.append(f'atomic_fetch_add_explicit({o}, -1, {SC});')
    return out

def litmus(shape, sname):
    s = SCHEMES[sname]
    locs = ['x', 'y']
    na = s.get('na')
    ty = 'int' if na else 'atomic_int'
    init = '; '.join(f'{v}=0' for v in locs + ([] if na else ['mx','my','ox','oy'])) + ';'
    params = ', '.join(f'{ty}* {v}' for v in locs) + ('' if na else ', atomic_int* mx, atomic_int* my, atomic_int* ox, atomic_int* oy')
    procs = []
    for t, ops in enumerate(SHAPES[shape]):
        lines = '\n  '.join(body(ops, s))
        procs.append(f'P{t} ({params}) {{\n  {lines}\n}}')
    name = f'{shape}+{sname}'
    return f'C {name}\n\n{{ {init} }}\n\n' + '\n\n'.join(procs) + f'\n\n{COND[shape]}\n'

if __name__ == '__main__':
    os.makedirs('c11', exist_ok=True)
    names = []
    for shape in SHAPES:
        for sname in SCHEMES:
            fn = f'c11/{shape}+{sname}.litmus'.replace('+', '_')
            open(fn, 'w').write(litmus(shape, sname)); names.append(fn)
    open('c11/@all', 'w').write('\n'.join(os.path.basename(n) for n in names) + '\n')
    print(len(names), 'tests'); print(open('c11/SB_list-cf.litmus').read())
