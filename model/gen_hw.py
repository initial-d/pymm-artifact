# Hardware-level litmus tests (herd7 AArch64 / X86) using the instruction sequences clang emits
# for each CPython scheme (see SCHEMES.md, from disassembly of the 3.14.9 builds).
import os
from gen_litmus import SHAPES, COND

HW = {  # name: store kind, load kind, unlock kind, owner refcount?
 'list-base':  ('rel', 'sc',  'rmw', False),
 'list-cf':    ('rel', 'sc',  'rel', False),
 'attr-base':  ('rel', 'acq', 'rmw', True),
 'attr-cf':    ('rel', 'acq', 'rel', True),
 'attrb-base': ('rel', 'acq', 'rmw', False),
 'attrb-cf':   ('rel', 'acq', 'rel', False),
 'array-now':  ('plain', 'plain', None, False),
 'proposed':   ('sc', 'sc', 'rel', False),
}

def arm_thread(ops, s, t):
    st, ld, unl, rc = s
    regs, out, outregs = {}, [], {}
    # X1=x X2=y X3=mx X4=my X5=ox X6=oy ; W0=1 scratch, W7=0
    base = {'x': 'X1', 'y': 'X2'}; mut = {'x': 'X3', 'y': 'X4'}; own = {'x': 'X5', 'y': 'X6'}
    out += ['MOV W7,#0']
    rn = 10
    for op in ops:
        kind, loc = op[0], op[1]
        if kind == 'W':
            out.append(f'MOV W0,#{op[2]}')
            if unl: out.append(f'MOV W11,#1'); out.append(f'SWPAL W11,W12,[{mut[loc]}]')
            out.append({'rel': f'STLR W0,[{base[loc]}]', 'sc': f'STLR W0,[{base[loc]}]',
                        'plain': f'STR W0,[{base[loc]}]'}[st])
            if unl == 'rmw': out.append(f'SWPAL W7,W12,[{mut[loc]}]')
            elif unl == 'rel': out.append(f'STLR W7,[{mut[loc]}]')
        else:
            r = f'W{rn}'; rn += 3 if rn == 10 else 1
            r = {0: 'W20', 1: 'W21'}[int(op[2][1])]
            out.append({'sc': f'LDAR {r},[{base[loc]}]', 'acq': f'LDAPR {r},[{base[loc]}]',
                        'plain': f'LDR {r},[{base[loc]}]', 'rlx': f'LDR {r},[{base[loc]}]'}[ld])
            outregs[op[2]] = 'X' + r[1:]
        if rc: out.append(f'MOV W8,#-1'); out.append(f'LDADDAL W8,W9,[{own[loc]}]')
    return out, outregs

def x86_thread(ops, s, t):
    st, ld, unl, rc = s
    out, outregs = [], {}
    for op in ops:
        kind, loc = op[0], op[1]
        if kind == 'W':
            if unl: out.append('MOV ESI,$1'); out.append(f'XCHG [m{loc}],ESI')
            out.append(f'XCHG [{loc}],EDI' if st == 'sc' else f'MOV [{loc}],${op[2]}')
            if st == 'sc': out.insert(len(out)-1, f'MOV EDI,${op[2]}')
            if unl == 'rmw': out.append('MOV ESI,$0'); out.append(f'XCHG [m{loc}],ESI')
            elif unl == 'rel': out.append(f'MOV [m{loc}],$0')
        else:
            r = {0: 'EAX', 1: 'EBX'}[int(op[2][1])]
            out.append(f'MOV {r},[{loc}]'); outregs[op[2]] = r
        if rc: out.append('MOV EDX,$0'); out.append(f'XCHG [o{loc}],EDX')
    return out, outregs

def table(cols):
    n = max(len(c) for c in cols); w = [max([len(x) for x in c] + [4]) for c in cols]
    head = ' ' + ' | '.join(f'P{i}'.ljust(w[i]) for i in range(len(cols))) + ' ;'
    rows = [' ' + ' | '.join((c[r] if r < len(c) else '').ljust(w[i]) for i, c in enumerate(cols)) + ' ;'
            for r in range(n)]
    return '\n'.join([head] + rows)

def fix_cond(cond, regmaps, arch):
    import re
    def rep(m):
        t, r = int(m.group(1)), m.group(2)
        return f'{t}:{regmaps[t].get(r, r)}'
    return re.sub(r'(\d+):(r\d)', rep, cond)

def gen(arch):
    os.makedirs(arch, exist_ok=True); names = []
    for shape, threads in SHAPES.items():
        for sname, s in HW.items():
            cols, maps = [], []
            for t, ops in enumerate(threads):
                o, m = (arm_thread if arch == 'aarch64' else x86_thread)(ops, s, t)
                cols.append(o); maps.append(m)
            name = f'{shape}+{sname}'
            if arch == 'aarch64':
                init = ' '.join(f'{t}:X1=x; {t}:X2=y; {t}:X3=mx; {t}:X4=my; {t}:X5=ox; {t}:X6=oy;'
                                for t in range(len(threads)))
                hdr = f'AArch64 {name}\n{{\n{init}\n}}\n'
            else:
                hdr = f'X86 {name}\n{{ x=0; y=0; mx=0; my=0; ox=0; oy=0; }}\n'
            cond = fix_cond(COND[shape], maps, arch)
            fn = f'{arch}/{shape}_{sname}.litmus'
            open(fn, 'w').write(hdr + table(cols) + '\n' + cond + '\n'); names.append(os.path.basename(fn))
    open(f'{arch}/@all', 'w').write('\n'.join(names) + '\n')
    return names

if __name__ == '__main__':
    for a in ('aarch64', 'x86'):
        print(a, len(gen(a)))
    print(open('aarch64/SB_list-cf.litmus').read()); print(open('x86/SB_list-base.litmus').read())
