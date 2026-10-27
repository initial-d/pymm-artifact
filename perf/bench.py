# Cost of the PyMM fix: single-thread and 4-thread store/load-heavy loops.
#   python -I bench.py <label>
import sys, time, threading
class A:
    def __init__(self): self.v = 0
class S:
    __slots__ = ('v',)
    def __init__(self): self.v = 0
N = 2_000_000
def attr(n):
    o = A()
    for i in range(n): o.v = i; x = o.v
def slot(n):
    o = S()
    for i in range(n): o.v = i; x = o.v
def lst(n):
    l = [0] * 8
    for i in range(n): l[i & 7] = i; x = l[(i + 1) & 7]
def dct(n):
    d = {'a': 0, 'b': 0}
    for i in range(n): d['a'] = i; x = d['b']
def mixed(n):  # something program-like: build objects, mutate, sum
    acc = 0; objs = [A() for _ in range(64)]
    for i in range(n // 4):
        o = objs[i & 63]; o.v = o.v + i; acc += o.v
        d = {'k': i}; acc += d['k']
    return acc
BENCH = dict(attr=attr, slot=slot, list=lst, dict=dct, mixed=mixed)
def run(f, threads):
    ts = [threading.Thread(target=f, args=(N // threads,)) for _ in range(threads)]
    t0 = time.perf_counter()
    for t in ts: t.start()
    for t in ts: t.join()
    return time.perf_counter() - t0
label = sys.argv[1]
for name, f in BENCH.items():
    for th in (1, 4):
        best = min(run(f, th) for _ in range(7))
        print(f'{label}\t{name}\t{th}\t{best*1e3:.1f}', flush=True)
