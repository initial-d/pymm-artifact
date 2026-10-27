# Native-x86 pyperformance (dev05, Xeon E5-2620 v3): 4 builds x 3 rounds, build order rotated per
# (round, benchmark). Per benchmark and round: ratio of means a/b for each pairing. Report per round
# the geometric mean over benchmarks, and per benchmark the median over rounds; a benchmark counts as
# consistently slower/faster only if all three rounds agree in sign.
#   python3 -I analyze_native.py   (reads native/out_native/r<k>-<build>/all.json)
import sys, pathlib, math, statistics as st
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'lib'))  # pyperf 2.9.0 here, or pip install pyperf==2.9.0
import pyperf
PAIRS = [('sc', 'base'), ('fix', 'cf'), ('cf', 'base'), ('fix', 'base')]
ROUNDS = (1, 2, 3)
D = {(r, b): {bm.get_name(): bm.mean() for bm in pyperf.BenchmarkSuite.load(
        str(HERE / 'native' / 'out_native' / f'r{r}-{b}' / 'all.json')).get_benchmarks()}
     for r in ROUNDS for b in ('base', 'sc', 'cf', 'fix')}
names = sorted(set.intersection(*(set(v) for v in D.values())))
gm = lambda xs: math.exp(st.mean(math.log(x) for x in xs))
print(f'## native x86: {len(names)} benchmarks in all builds and rounds')
print('benchmark' + ''.join(f'\t{a}/{b} [r1 r2 r3]' for a, b in PAIRS))
med = {p: {} for p in PAIRS}; rat = {p: {} for p in PAIRS}
for n in names:
    row = [n]
    for a, b in PAIRS:
        rs = [D[(r, a)][n] / D[(r, b)][n] for r in ROUNDS]
        rat[(a, b)][n] = rs; med[(a, b)][n] = st.median(rs)
        row.append(f'{(st.median(rs)-1)*100:+.1f}% [' + ' '.join(f'{(x-1)*100:+.1f}' for x in rs) + ']')
    print('\t'.join(row))
for p in PAIRS:
    per_round = [gm([rat[p][n][k] for n in names]) for k in range(3)]
    slow = [n for n in names if all(x > 1 for x in rat[p][n])]
    fast = [n for n in names if all(x < 1 for x in rat[p][n])]
    ms = sorted(med[p].values())
    print(f'# {p[0]}/{p[1]}: geomean of medians {(gm(ms)-1)*100:+.2f}%  per-round geomeans '
          + ' '.join(f'{(x-1)*100:+.2f}%' for x in per_round)
          + f'  median range {(ms[0]-1)*100:+.1f}%..{(ms[-1]-1)*100:+.1f}%'
          + f'  all-3-rounds slower {len(slow)} faster {len(fast)}')
    big = sorted(((med[p][n], n) for n in slow), reverse=True)[:6]
    print(f'#   consistently slower, largest: ' + ', '.join(f'{n} {(m-1)*100:+.1f}%' for m, n in big))
# agreement between the two lock-matched pairings
a = [math.log(med[('sc', 'base')][n]) for n in names]; b = [math.log(med[('fix', 'cf')][n]) for n in names]
ma, mb = st.mean(a), st.mean(b)
r = sum((x-ma)*(y-mb) for x, y in zip(a, b)) / math.sqrt(sum((x-ma)**2 for x in a) * sum((y-mb)**2 for y in b))
both = [n for n in names if all(x > 1 for x in rat[('sc','base')][n]) and all(x > 1 for x in rat[('fix','cf')][n])]
print(f'# Pearson r(sc/base, fix/cf medians) = {r:+.2f}; slower in all rounds of BOTH pairings: {len(both)}: '
      + ', '.join(f'{n} ({(med[("sc","base")][n]-1)*100:+.1f}/{(med[("fix","cf")][n]-1)*100:+.1f})' for n in both))
