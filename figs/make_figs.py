"""Figures for the PyMM paper. Reads raw result files; writes PDF figures next to this script.

Usage: python3 make_figs.py   (from any directory)
"""
import re, csv, pathlib
import matplotlib
matplotlib.use("pdf")
import matplotlib.pyplot as plt

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent  # repository root
LIT = ROOT / "litmus"

# Validated categorical slots 1-3 (blue, orange, aqua); identity also carried by marker shape.
COL = {"base": "#2a78d6", "cf": "#eb6834", "fix": "#1baf7a"}
MARK = {"base": "o", "cf": "s", "fix": "D"}
NAME = {"base": "stock", "cf": "CF (release unlock)", "fix": "fix (seq_cst stores)"}
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"

plt.rcParams.update({
    "font.family": "serif", "font.size": 8, "axes.labelsize": 8, "legend.fontsize": 7,
    "xtick.labelsize": 7, "ytick.labelsize": 7, "axes.edgecolor": INK2, "axes.labelcolor": INK,
    "xtick.color": INK2, "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
    "pdf.fonttype": 42, "lines.linewidth": 1.0,
})

LINE = re.compile(r"\[(x86|arm) (\w+)\].*?SB\s+(\w+)\s+n=\s*(\d+)\s+forbidden\(0, 0\)=\s*(\d+)")


def sb_cells(files):
    """(platform, build, kind) -> (forbidden, n), summed over files."""
    out = {}
    for f in files:
        for m in LINE.finditer((LIT / f).read_text()):
            key = (m[1], m[2], m[3])
            k, n = int(m[5]), int(m[4])
            a, b = out.get(key, (0, 0))
            out[key] = (a + k, b + n)
    return out


def native_cells():
    """Native Xeon (dev05) SB counts: build -> kind -> (forbidden, n)."""
    out = {}
    pat = re.compile(r"\[(\w+)\].*?SB\s+(\w+)\s+n=\s*(\d+)\s+forbidden\(0, 0\)=\s*(\d+)")
    for m in pat.finditer((ROOT / "native_x86" / "raw" / "native.txt").read_text()):
        out[("x86", m[1], m[2])] = (int(m[4]), int(m[3]))
    return out


def _sb_panel(ax, cells, kinds, title):
    off = {"base": -0.22, "cf": 0.0, "fix": 0.22}
    for b in ("base", "cf", "fix"):
        for i, (k, _) in enumerate(kinds):
            if ("x86", b, k) not in cells:
                continue
            hit, n = cells[("x86", b, k)]
            x = i + off[b]
            if hit:
                ax.plot(x, hit / n, MARK[b], color=COL[b], ms=5, mec="white", mew=0.6, zorder=3)
            else:  # rule of three: 95% one-sided upper bound
                ub = 3 / n
                ax.plot([x, x], [ub, 3e-9], color=COL[b], lw=1.0, zorder=2)
                ax.plot(x, ub, MARK[b], mfc="white", mec=COL[b], ms=4.5, mew=1.0, zorder=3)
    ax.set_yscale("log"); ax.set_ylim(1e-8, 1e-2)
    ax.set_xticks(range(len(kinds)), [lab for _, lab in kinds])
    ax.set_xlim(-0.5, len(kinds) - 0.5)
    ax.yaxis.grid(True, color=GRID, lw=0.5); ax.set_axisbelow(True)
    ax.set_title(title, fontsize=7.5, color=INK)


def fig_sb():
    """SB rate on x86 per location kind and build, Rosetta 2 and native; zeros drawn as 95% bounds (3/n)."""
    kinds = [("list", "list"), ("attr", "attr\nX[i].v"),
             ("attrb", "attr\nborrowed"), ("slotb", "slot\nborrowed")]
    ros = sb_cells(["cf_x86_sb_big.txt", "borrowed_x86.txt", "fix_x86.txt"])
    # Cells only in the first 6M run (stock attr): fill gaps, never add to the 60M counts.
    for k, v in sb_cells(["cf_x86_sb.txt"]).items():
        ros.setdefault(k, v)
    fig, axes = plt.subplots(1, 2, figsize=(5.6, 2.1), sharey=True)
    _sb_panel(axes[0], ros, kinds, "x86-64 under Rosetta 2 (Apple M5)")
    _sb_panel(axes[1], native_cells(), kinds, "x86-64 native (Xeon E5-2620 v3)")
    axes[0].set_ylabel("SB outcome rate")
    handles = [plt.Line2D([], [], ls="", marker=MARK[b], color=COL[b], mec="white", ms=5, label=NAME[b])
               for b in ("base", "cf", "fix")]
    handles.append(plt.Line2D([], [], ls="", marker="o", mfc="white", mec=INK2, ms=4.5,
                              label="0 observed (95% bound)"))
    fig.legend(handles=handles, loc="upper center", ncol=4, frameon=False,
               handletextpad=0.3, columnspacing=1.2, bbox_to_anchor=(0.5, 1.02))
    fig.tight_layout(pad=0.3, rect=(0, 0, 1, 0.9))
    fig.savefig(HERE / "sb_rates.pdf")


def fig_perf():
    """Cost of the fix from the interleaved 2x2 study (perf/bench2_*.tsv): per cell, median over
    15 rounds of the paired ratio, whiskers = IQR. Two pairings isolate the fix: sc/base (stock
    CAS unlock) and fix/cf (release-store unlock)."""
    import statistics as st
    rows = {}
    for fn in ("bench2_m5.tsv", "bench2_native.tsv"):
        for line in open(ROOT / "perf" / fn):
            if line.startswith("#") or not line.strip():
                continue
            lab, loop, th, sh, r, ms = line.split("\t")
            plat, b = lab.rsplit("-", 1)
            rows.setdefault((plat, loop, int(th), sh), {}).setdefault(b, {})[int(r)] = float(ms)

    def q(xs, p):
        xs = sorted(xs); k = (len(xs) - 1) * p; f = int(k); c = min(f + 1, len(xs) - 1)
        return xs[f] + (xs[c] - xs[f]) * (k - f)
    loops = ["attr", "slot", "list", "dict", "mixed"]
    cells = [(lp, th, sh) for lp in loops for th, sh in ((1, "private"), (4, "private"), (4, "shared"))]
    labels = [f"{lp} {th}{'s' if sh == 'shared' else 'p'}" for lp, th, sh in cells]
    pairs = [("sc", "base", COL["base"], "o", "seq_cst accesses, stock lock (sc / stock)"),
             ("fix", "cf", COL["fix"], "D", "seq_cst accesses, release-store lock (fix / CF)")]
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 3.0), sharey=True)
    for ax, plat, title in zip(axes, ("arm", "x86", "x86n"),
                               ("AArch64, Apple M5", "x86-64, Rosetta 2 on M5", "x86-64 native, Xeon E5-2620 v3")):
        for i, (lp, th, sh) in enumerate(cells):
            d = rows[(plat, lp, th, sh)]
            R = sorted(set.intersection(*(set(v) for v in d.values())))
            for k, (num, den, col, mk, _) in enumerate(pairs):
                rat = [100 * (d[num][r] / d[den][r] - 1) for r in R]
                y = i + (-0.17 if k == 0 else 0.17)
                ax.plot([q(rat, .25), q(rat, .75)], [y, y], color=col, lw=1.0, solid_capstyle="butt")
                ax.plot(st.median(rat), y, mk, color=col, ms=3.6, mec="white", mew=0.4, zorder=3)
        ax.axvline(0, color=INK2, lw=0.6)
        for i in range(2, len(cells) - 1, 3):
            ax.axhline(i + 0.5, color=GRID, lw=0.5)
        ax.set_title(title, fontsize=7.5, color=INK)
        ax.set_xlim(-42, 58); ax.set_xlabel("time change (%)")
        ax.xaxis.grid(True, color=GRID, lw=0.5); ax.set_axisbelow(True)
    axes[0].set_yticks(range(len(cells)), labels); axes[0].invert_yaxis()
    h = [plt.Line2D([], [], color=c, marker=m, ms=4, lw=1.0, label=lab) for _, _, c, m, lab in pairs]
    fig.legend(handles=h, loc="upper center", ncol=2, frameon=False, fontsize=7,
               bbox_to_anchor=(0.5, 1.01), handletextpad=0.4, columnspacing=1.5)
    fig.tight_layout(pad=0.3, rect=(0, 0, 1, 0.93))
    fig.savefig(HERE / "perf.pdf")


if __name__ == "__main__":
    fig_sb(); fig_perf()
    print("wrote", sorted(p.name for p in HERE.glob("*.pdf")))
