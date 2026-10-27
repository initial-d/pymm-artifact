# PyMM: a memory model for free-threaded CPython

Code, models and raw results for the paper *Sequential Consistency by Accident: A Memory Model
for Free-Threaded Python, and Why It Needs One Now* (Yimin Du, Guixing Wu).

Every number in the paper comes from a file in this repository. The paper source is not included.

## Layout

| Path | Contents | Paper |
|---|---|---|
| `model/pymm_patch.diff` | Patch against CPython 3.14.9: `PYMM_RELEASE_UNLOCK` (counterfactual release-store unlock, "CF") and `PYMM_SC_STORE` (the fix: seq_cst managed stores and loads, three macros) | §4, §7 |
| `model/pymm.cat` | The proposed two-tier model in herd7's `cat` language | §6 |
| `model/gen_litmus.py`, `gen_hw.py`, `gen_global.py`, `gen_py.py` | Generators for the C11, x86 and AArch64 litmus tests | §5 |
| `model/{c11,x86,aarch64,global,mixed,py}/` | Generated litmus tests | §5–7 |
| `model/herd_*.txt`, `herd_rerun.txt`, `pymm_results.txt` | herd7 verdicts (Tables 4, 5); `herd_rerun_running.txt` records the C11 2+2W attr-base run stopped after 39.9 h; `herd_c11_2+2W_attr-base_derived.txt` derives that cell (forbid) from the attr_b cell | §5–6 |
| `model/execgraph/` | herd7 witnesses behind Figure 3 | §5 |
| `model/*_disasm_counts.txt`, `native_x86/disasm_counts.txt` | Instruction counts of the builds | §7 |
| `litmus/litmus.py`, `litmus_global.py` | Python litmus harness | §4 |
| `litmus/*.txt` | Raw hardware outcomes (Table 3, Figure 2); `extpatch_window_check.txt` is the two-/three-macro argument | §4, §7 |
| `litmus/sb.c`, `sb2.c` | C store-buffering probes | §4 |
| `native_x86/` | Native Xeon build, litmus and 2×2 scripts and raw outcomes | §4, §7 |
| `perf/bench2.py`, `run2x2.sh`, `analyze2x2.py` | Lock-matched 2×2 cost study; raw `bench2_*.tsv`, summary `bench2_summary.txt` (Figure 4) | §7 |
| `perf/pyperf/` | pyperformance driver, screen, raw pyperf JSON and summary (M5, Rosetta 2) | §7, Table 6 |
| `perf/pyperf/native/` | Three-round pyperformance on native x86 | §7, Table 6 |
| `figs/make_figs.py` | Regenerates Figures 2 and 4 from the files above | |
| `PREREG_*.md` | Predictions written before the counterfactual and native runs | §4 |

## Reproducing

**Builds.** Download Python 3.14.9, apply the patch and build the four configurations
(`base`, `sc`, `cf`, `fix`):

```sh
tar xf Python-3.14.9.tar.xz
(cd Python-3.14.9 && git apply ../model/pymm_patch.diff)
CPY=Python-3.14.9 scripts/build_m5.sh          # macOS: arm64 and x86_64 (Rosetta 2)
```

On Linux, `native_x86/build.sh` builds `base`, `cf` and `fix`; `sc` is
`configure --disable-gil CFLAGS=-DPYMM_SC_STORE`.

**herd7 verdicts.** Install herd7 7.58 (`opam install herd`), then
`cd model && HERD7=$(which herd7) python3 run_herd.py`. Some cells take hours; the 25-minute
timeouts and their unbounded reruns are listed in `herd_rerun.txt`.

**Litmus tests on hardware.** `build-arm-cf/python.exe -I litmus/litmus.py SB attrb 10000000 3`
runs 3×10M iterations of SB on borrowed attributes; the raw files record the exact invocations.

**Cost.** `perf/run2x2.sh` (M5) and `native_x86/run2x2.sh` (Linux) produce the timing TSVs;
`python3 perf/analyze2x2.py perf/bench2_m5.tsv perf/bench2_native.tsv` reproduces
`perf/bench2_summary.txt`. The pyperformance runs need the pyperformance 1.x benchmark sources
(`bm/`, not included) and pyperf 2.9.0; `perf/pyperf/analyze.py` and `analyze_native.py`
reproduce the summaries from the raw JSON.

**Figures.** `python3 figs/make_figs.py` (matplotlib) writes `figs/sb_rates.pdf` and
`figs/perf.pdf`.

Raw result files contain the absolute paths of the machines they were measured on; they are kept
unmodified.

## License

MIT for the code in this repository (see `LICENSE`). `model/pymm_patch.diff` modifies CPython and
is offered under the PSF License, like CPython itself.
