# MP / SB on module globals. LOAD_GLOBAL_MODULE reads me_value with a relaxed load and, for
# immortal values, never re-reads it (_Py_TryIncrefCompareStackRef -> _Py_TryIncrefFast), so the
# flag load is relaxed. Globals cannot be fresh per iteration, so we reuse two names and write
# the immortal small int v_i = i % 128 at iteration i. The lockstep spin (each thread waits for
# the partner to reach i) bounds what a read can see to v_{i-1} or v_i.
#   MP:  T0: X=v_i; Y=v_i     T1: r0=Y; r1=X    forbidden: r0==v_i and r1==v_{i-1}
#   SB:  T0: X=v_i; r0=Y      T1: Y=v_i; r1=X   forbidden: r0==v_{i-1} and r1==v_{i-1}
#   python3.14t -I litmus_global.py MP|SB <iters> [runs]
import sys, threading, time
SRC = {
 'MP': ("global X, Y\n        X = v\n        Y = v", "r0[i] = Y\n        r1[i] = X"),
 'SB': ("global X\n        X = v\n        r0[i] = Y", "global Y\n        Y = v\n        r1[i] = X"),
}
TEMPLATE = '''
def body{t}(r0, r1, cnt, n):
    other = {o}
    for i in range(n):
        v = i % 128
        while cnt[other] < i:
            pass
        {code}
        cnt[{t}] = i + 1
'''
def run_once(test, n):
    ns = {'X': 127, 'Y': 127}
    for t in (0, 1):
        exec(TEMPLATE.format(t=t, o=1 - t, code=SRC[test][t]), ns)
    r0, r1, cnt = [-1] * n, [-1] * n, [0, 0]
    th = [threading.Thread(target=ns['body0'], args=(r0, r1, cnt, n)),
          threading.Thread(target=ns['body1'], args=(r0, r1, cnt, n))]
    t0 = time.perf_counter()
    for t in th: t.start()
    for t in th: t.join()
    bad = both_new = 0
    for i in range(n):
        cur, prev = i % 128, (i - 1) % 128
        if test == 'MP':
            bad += r0[i] == cur and r1[i] == prev
            both_new += r0[i] == cur and r1[i] == cur
        else:
            bad += r0[i] == prev and r1[i] == prev
            both_new += r0[i] == cur and r1[i] == cur
    return bad, both_new, time.perf_counter() - t0
if __name__ == '__main__':
    test, n = sys.argv[1], int(sys.argv[2]); runs = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    B = N = 0; T = 0.0
    for _ in range(runs):
        b, nn, dt = run_once(test, n); B += b; N += nn; T += dt
    gil = sys._is_gil_enabled() if hasattr(sys, '_is_gil_enabled') else True
    print(f"{sys.version.split()[0]} gil={gil} {test} global n={n*runs} forbidden={B} ({B/(n*runs):.2e}) "
          f"overlap(both new)={N} {T:.1f}s")
