# Summarise the pyperformance subset: per arch, each build's mean time per benchmark relative to a
# lock-matched or stock baseline; geometric mean over benchmarks; count of benchmarks whose change is
# significant by pyperf's own t-test (is_significant_benchs, as in `pyperf compare_to`).
#   python3 -I analyze.py   (reads out/<arch>-<build>/all.json)
import sys, pathlib, math
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'lib'))  # pyperf 2.9.0 here, or pip install pyperf==2.9.0
import pyperf
from pyperf._compare import is_significant_benchs
PAIRS = [('sc', 'base'), ('fix', 'cf'), ('cf', 'base'), ('fix', 'base')]
for arch in ('arm', 'x86'):
    S = {b: {bm.get_name(): bm for bm in pyperf.BenchmarkSuite.load(str(HERE / 'out' / f'{arch}-{b}' / 'all.json')).get_benchmarks()}
         for b in ('base', 'sc', 'cf', 'fix')}
    names = sorted(set.intersection(*(set(v) for v in S.values())))
    print(f'## {arch}: {len(names)} benchmarks in all four builds')
    print('benchmark' + ''.join(f'\t{a}/{b}' for a, b in PAIRS))
    logs = {p: [] for p in PAIRS}; sig = {p: [0, 0] for p in PAIRS}
    for n in names:
        row = [n]
        for a, b in PAIRS:
            r = S[a][n].mean() / S[b][n].mean(); logs[(a, b)].append(math.log(r))
            s, _ = is_significant_benchs(S[b][n], S[a][n])
            if s: sig[(a, b)][r < 1] += 1
            row.append(f'{(r-1)*100:+.1f}%{"*" if s else ""}')
        print('\t'.join(row))
    for p in PAIRS:
        rs = sorted(math.exp(x) for x in logs[p])
        print(f'# {arch} {p[0]}/{p[1]}: geomean {(math.exp(sum(logs[p])/len(logs[p]))-1)*100:+.2f}%  '
              f'min {(rs[0]-1)*100:+.1f}% max {(rs[-1]-1)*100:+.1f}%  significant slower {sig[p][0]} faster {sig[p][1]}')
    # if the fix had a real per-benchmark cost, the two lock-matched pairings would agree
    a, b = logs[('sc', 'base')], logs[('fix', 'cf')]
    ma, mb = sum(a) / len(a), sum(b) / len(b)
    cov = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    r = cov / math.sqrt(sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b))
    agree = sum((x > 0) == (y > 0) for x, y in zip(a, b))
    print(f'# {arch} Pearson r(sc/base, fix/cf) over benchmarks = {r:+.2f}; same sign in {agree}/{len(a)}')
    print()
