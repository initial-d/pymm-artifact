# Summarise the interleaved 2x2 cost study: per (platform, loop, threads, sharing) cell, median
# over rounds of each build's time relative to base, with a bootstrap-free spread measure:
# the inter-quartile range of the per-round paired ratio build/base (same round = adjacent runs).
import sys, statistics as st, collections
rows = collections.defaultdict(dict)   # (plat, loop, th, sh) -> {build: {round: ms}}
for fn in sys.argv[1:]:
    for line in open(fn):
        if line.startswith('#') or not line.strip(): continue
        lab, loop, th, sh, r, ms = line.split('\t')
        plat, b = lab.rsplit('-', 1)
        rows[(plat, loop, int(th), sh)].setdefault(b, {})[int(r)] = float(ms)
def q(xs, p):
    xs = sorted(xs); k = (len(xs) - 1) * p; f = int(k); c = min(f + 1, len(xs) - 1)
    return xs[f] + (xs[c] - xs[f]) * (k - f)
print('# plat loop threads sharing | rounds | median base ms | per build: median paired ratio-1 (%) [IQR]')
summ = collections.defaultdict(list); sig = collections.defaultdict(list)
for key in sorted(rows):
    d = rows[key]; R = sorted(set.intersection(*(set(v) for v in d.values())))
    out = [f'{key[0]:4} {key[1]:6} {key[2]} {key[3]:7} | {len(R):2} | {st.median(d["base"][r] for r in R):8.1f} |']
    for b in ('sc', 'cf', 'fix'):
        rat = [d[b][r] / d['base'][r] - 1 for r in R]
        m = st.median(rat) * 100; summ[(key[0], b)].append(m)
        sig[(key[0], b)].append((q(rat, .25) > 0) - (q(rat, .75) < 0))
        out.append(f' {b}: {m:+5.1f} [{q(rat,.25)*100:+5.1f},{q(rat,.75)*100:+5.1f}]')
    # fix on the release-store lock, paired against CF (same lock, same round)
    rat = [d['fix'][r] / d['cf'][r] - 1 for r in R]
    m = st.median(rat) * 100; summ[(key[0], 'fix/cf')].append(m)
    sig[(key[0], 'fix/cf')].append((q(rat, .25) > 0) - (q(rat, .75) < 0))
    out.append(f' fix/cf: {m:+5.1f} [{q(rat,.25)*100:+5.1f},{q(rat,.75)*100:+5.1f}]')
    print(''.join(out))
print('\n# per platform/build: range of cell medians, and geometric-mean ratio over cells')
import math
for (p, b), ms in sorted(summ.items()):
    gm = math.exp(st.mean(math.log(1 + m / 100) for m in ms)) - 1
    print(f'{p:4} {b:6}: cells={len(ms)} min={min(ms):+.1f}% max={max(ms):+.1f}% geomean={gm*100:+.1f}% IQR>0:{sig[(p,b)].count(1)} IQR<0:{sig[(p,b)].count(-1)}')
