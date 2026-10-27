# Litmus tests for the (unspecified) Python memory model, run on free-threaded CPython.
# Each iteration i uses FRESH locations, and both threads spin until the partner has reached
# iteration i before running the test body, so bodies overlap in time (litmus7 style).
#
#   python3.14t -I litmus.py <test> <kind> <iters> [runs]
#   tests: SB MP LB R 2+2W  ;  kinds: list attr slot dict
import sys, threading, time, collections

class A:            # instance __dict__ attribute
    def __init__(self): self.v = 0
class S:            # __slots__ attribute
    __slots__ = ('v',)
    def __init__(self): self.v = 0

def make_locs(kind, n):
    """Return (get, set, cells) for n fresh locations of the given kind."""
    if kind == 'list':
        c = [0] * n
        return c
    if kind in ('attr', 'attrb'):  return [A() for _ in range(n)]
    if kind in ('slot', 'slotb'):  return [S() for _ in range(n)]
    if kind == 'dict':  return [{'v': 0} for _ in range(n)]
    if kind == 'ctypes':
        import ctypes
        return (ctypes.c_int * n)()          # raw C memory, no locks, no barriers in setitem/getitem
    if kind == 'array':
        import array
        return array.array('i', bytes(4 * n))
    raise SystemExit(kind)

# ---- test bodies, one function per (test, kind, thread); written out so the bytecode is
# ---- the obvious one (no helper calls between the two accesses). ----
SRC = {
 # Store buffering: x=1; r0=y || y=1; r1=x.   SC forbids r0=r1=0.
 'SB': ("{X}=1\n        r0[i]={Y}", "{Y}=1\n        r1[i]={X}"),
 # Message passing: x=1; y=1 || r0=y; r1=x.  SC (and RA) forbid r0=1,r1=0.
 'MP': ("{X}=1\n        {Y}=1", "r0[i]={Y}\n        r1[i]={X}"),
 # Load buffering: r0=x; y=1 || r1=y; x=1.   SC/RA forbid r0=r1=1.
 'LB': ("r0[i]={X}\n        {Y}=1", "r1[i]={Y}\n        {X}=1"),
 # R: x=1; y=1 || y=2; r1=x.  SC forbids (y==2 at end and r1==0).
 'R':  ("{X}=1\n        {Y}=1", "{Y}=2\n        r1[i]={X}"),
 # 2+2W: x=1; y=2 || y=1; x=2. SC forbids final x==1 and y==1.
 '2+2W': ("{X}=1\n        {Y}=2", "{Y}=1\n        {X}=2"),
 # Mixed publication: data in array X, flag in list F.  r0=F (flag), r1=X (data).
 'MPmix': ("{X}=1\n        F[i]=1", "r0[i]=F[i]\n        r1[i]={X}"),
}

ACCESS = {'list': ('X[i]', 'Y[i]'), 'attr': ('X[i].v', 'Y[i].v'),
          'slot': ('X[i].v', 'Y[i].v'), 'dict': ("X[i]['v']", "Y[i]['v']"),
          'ctypes': ('X[i]', 'Y[i]'), 'array': ('X[i]', 'Y[i]'),
          # borrowed owners: fetch both objects BEFORE the window, so no refcount RMW
          # sits between the store and the load
          'attrb': ('xo.v', 'yo.v'), 'slotb': ('xo.v', 'yo.v')}
PRE = {'attrb': 'xo = X[i]; yo = Y[i]', 'slotb': 'xo = X[i]; yo = Y[i]'}

TEMPLATE = '''
def body{t}(X, Y, r0, r1, cnt, n, F=None):
    other = {o}
    for i in range(n):
        {pre}
        while cnt[other] < i:
            pass
        {code}
        cnt[{t}] = i + 1
'''

def build(test, kind):
    xa, ya = ACCESS[kind]
    ns = {}
    for t in (0, 1):
        code = SRC[test][t].format(X=xa, Y=ya)
        exec(TEMPLATE.format(t=t, o=1 - t, code=code, pre=PRE.get(kind, 'pass')), ns)
    return ns['body0'], ns['body1']

def read(kind, cell):
    if kind == 'list': return cell
    if kind == 'dict': return cell['v']
    return cell.v

def run_once(test, kind, n):
    b0, b1 = build(test, kind)
    X, Y = make_locs(kind, n), make_locs(kind, n)
    r0, r1 = [-1] * n, [-1] * n
    cnt = [0, 0]
    F = [0] * n
    th = [threading.Thread(target=b0, args=(X, Y, r0, r1, cnt, n, F)),
          threading.Thread(target=b1, args=(X, Y, r0, r1, cnt, n, F))]
    t0 = time.perf_counter()
    for t in th: t.start()
    for t in th: t.join()
    dt = time.perf_counter() - t0
    hist = collections.Counter()
    for i in range(n):
        x = X[i] if kind in ('list', 'ctypes', 'array') else read(kind, X[i])
        y = Y[i] if kind in ('list', 'ctypes', 'array') else read(kind, Y[i])
        if test == 'SB':   key = (r0[i], r1[i])
        elif test in ('MP', 'MPmix'): key = (r0[i], r1[i])
        elif test == 'LB': key = (r0[i], r1[i])
        elif test == 'R':  key = (y, r1[i])
        else:              key = (x, y)
        hist[key] += 1
    return hist, dt

FORBIDDEN = {'SB': (0, 0), 'MP': (1, 0), 'MPmix': (1, 0), 'LB': (1, 1), 'R': (2, 0), '2+2W': (1, 1)}

if __name__ == '__main__':
    test, kind, n = sys.argv[1], sys.argv[2], int(sys.argv[3])
    runs = int(sys.argv[4]) if len(sys.argv) > 4 else 1
    import os
    if os.environ.get('PYMM_SWITCH'):   # GIL control: default 5 ms switch interval makes spin-sync crawl
        sys.setswitchinterval(float(os.environ['PYMM_SWITCH']))
    gil = sys._is_gil_enabled() if hasattr(sys, '_is_gil_enabled') else True
    tot = collections.Counter(); T = 0.0
    for _ in range(runs):
        h, dt = run_once(test, kind, n); tot += h; T += dt
    bad = tot[FORBIDDEN[test]]
    print(f"{sys.version.split()[0]} gil={gil} {test:5} {kind:5} n={n*runs:>9} "
          f"forbidden{FORBIDDEN[test]}={bad:>7}  ({bad/(n*runs):.2e})  {dict(sorted(tot.items()))}  {T:.1f}s")
