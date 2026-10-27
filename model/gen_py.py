# Python-level litmus tests for PyMM: every shape x {managed, raw}, plus mixed ones.
# PyMM-SC: managed = seq_cst;  PyMM-RA: managed = release stores / acquire loads.
import os
from gen_litmus import SHAPES, COND
ORD = {'sc':  {'W': 'memory_order_seq_cst', 'R': 'memory_order_seq_cst'},
       'ra':  {'W': 'memory_order_release', 'R': 'memory_order_acquire'},
       'raw': {'W': 'memory_order_relaxed', 'R': 'memory_order_relaxed'}}
def lit(shape, mode):
    procs = []
    for t, ops in enumerate(SHAPES[shape]):
        b = []
        for op in ops:
            o = ORD[mode][op[0]]
            b.append(f'atomic_store_explicit({op[1]}, {op[2]}, {o});' if op[0] == 'W'
                     else f'int {op[2]} = atomic_load_explicit({op[1]}, {o});')
        procs.append(f'P{t} (atomic_int* x, atomic_int* y) {{\n  ' + '\n  '.join(b) + '\n}')
    return f'C {shape}+py-{mode}\n\n{{ x=0; y=0; }}\n\n' + '\n\n'.join(procs) + f'\n\n{COND[shape]}\n'
os.makedirs('py', exist_ok=True)
for shape in SHAPES:
    for mode in ORD:
        open(f'py/{shape}_py-{mode}.litmus', 'w').write(lit(shape, mode))
print('ok')
