Source of Fig. (execution graphs, paper/main.tex fig:exec).
- SB_list-cf.dot / .herd.txt:  herd7 -model x86tso.cat -show prop -o . ../x86/SB_list-cf.litmus
  -> Allowed, Positive: 1 (the drawn witness: e reads y=0 and j reads x=0 from Init).
- SB_list-base.herd.txt: same for ../x86/SB_list-base.litmus -> Never, Positive: 0.
- SB_list-base.invalid.dot: herd7 -through invalid ... (candidates rejected by `acyclic ghb as tso`).
Edges in the figure: po_ghb = WW(po)|RM(po); implied = MA(WR(po)) | AM(WR(po)) (x86tso.cat).
