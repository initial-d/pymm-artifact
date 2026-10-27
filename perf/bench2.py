# 2x2 cost study: {stock CAS unlock, release-store unlock} x {RA, seq_cst managed accesses}.
# One process = one round: every (loop, threads, sharing) cell once, in a per-round shuffled order.
#   python -I bench2.py <label> <round>      -> TSV rows: label loop threads sharing round ms
import sys, time, threading, random
class A:
    def __init__(self): self.v = 0
class S:
    __slots__ = ('v',)
    def __init__(self): self.v = 0
N = 2_000_000
def attr(n, o):
    for i in range(n): o.v = i; x = o.v
def slot(n, o):
    for i in range(n): o.v = i; x = o.v
def lst(n, l):
    for i in range(n): l[i & 7] = i; x = l[(i + 1) & 7]
def dct(n, d):
    for i in range(n): d['a'] = i; x = d['b']
def mixed(n, objs):
    acc = 0
    for i in range(n // 4):
        o = objs[i & 63]; o.v = o.v + i; acc += o.v
        d = {'k': i}; acc += d['k']
MK = dict(attr=A, slot=S, list=lambda: [0] * 8, dict=lambda: {'a': 0, 'b': 0},
          mixed=lambda: [A() for _ in range(64)])
BENCH = dict(attr=attr, slot=slot, list=lst, dict=dct, mixed=mixed)
def run(name, threads, shared):
    f, mk = BENCH[name], MK[name]
    one = mk()
    args = [one if shared else mk() for _ in range(threads)]
    ts = [threading.Thread(target=f, args=(N // threads, a)) for a in args]
    t0 = time.perf_counter()
    for t in ts: t.start()
    for t in ts: t.join()
    return time.perf_counter() - t0
label, rnd = sys.argv[1], int(sys.argv[2])
cells = [(b, th, sh) for b in BENCH for th in (1, 4) for sh in ((False,) if th == 1 else (False, True))]
random.Random(rnd).shuffle(cells)
for b, th, sh in cells:
    run(b, th, sh)                      # warm-up, discarded
    ms = run(b, th, sh) * 1e3
    print(f'{label}\t{b}\t{th}\t{"shared" if sh else "private"}\t{rnd}\t{ms:.2f}', flush=True)
