# Run all litmus tests through herd7 and print a shape x scheme verdict matrix.
import subprocess, re, sys, os, json
H = os.environ.get('HERD7', 'herd7')  # path to herd7 7.58
from gen_litmus import SHAPES

def verdict(model, fn):
    try:
        p = subprocess.run([H, '-model', model, fn], capture_output=True, text=True, timeout=1500)
    except subprocess.TimeoutExpired:
        return 'TIMEOUT'
    out = p.stdout + p.stderr
    m = re.search(r'^Observation \S+ (Never|Sometimes|Always)', out, re.M)
    ub = 'Undefined' in out or 'undefined' in out.lower() and 'Flag' in out
    flags = re.findall(r'^Flag (\S+)', out, re.M)
    if not m: return 'ERR:' + out.strip().splitlines()[-1][:60] if out.strip() else 'ERR'
    v = {'Never': 'forbid', 'Sometimes': 'ALLOW', 'Always': 'ALWAYS'}[m.group(1)]
    if flags: v += '[' + ','.join(sorted(set(flags))) + ']'
    return v

from concurrent.futures import ThreadPoolExecutor
POOL = ThreadPoolExecutor(max_workers=int(os.environ.get('J', '8')))
def matrix(dirn, model, schemes):
    res = {}
    futs = {(sh, s): POOL.submit(verdict, model, f'{dirn}/{sh}_{s}.litmus')
            for sh in SHAPES for s in schemes if os.path.exists(f'{dirn}/{sh}_{s}.litmus')}
    print(f'\n### {dirn} under {model}')
    print(f"{'shape':6}" + ''.join(f'{s:>14}' for s in schemes))
    for shape in SHAPES:
        line = f'{shape:6}'
        for s in schemes:
            fn = f'{dirn}/{shape}_{s}.litmus'
            v = futs[(shape, s)].result() if (shape, s) in futs else '-'
            res[f'{shape}/{s}'] = v
            line += f'{v:>14}'
        print(line, flush=True)
    return res

if __name__ == '__main__':
    layer = sys.argv[1]
    c11s = ['list-base','list-cf','attr-base','attr-cf','attrb-base','attrb-cf','array-now','array-fix','proposed']
    hw = ['list-base','list-cf','attr-base','attr-cf','attrb-base','attrb-cf','array-now','proposed']
    model = {'c11': 'rc11.cat', 'x86': 'x86tso.cat', 'aarch64': 'aarch64.cat'}[layer]
    res = matrix(layer, model, c11s if layer == 'c11' else hw)
    json.dump(res, open(f'herd_{layer}.json', 'w'), indent=1)
