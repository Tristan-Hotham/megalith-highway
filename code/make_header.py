"""Step 7: ../header.png, the 1200 x 630 social card (matplotlib)."""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mapdraw import ROOT, R, fonts, draw_land, extent, load_megaliths, FAM_COL, BG, FG, MUT, SEA, HOT, LAND, WATER

DISP, SER, MONO = fonts()
M = load_megaliths()
fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor=BG)
ax = fig.add_axes([0.5, 0.0, 0.5, 1.0], facecolor=WATER)
draw_land(ax, fc=LAND)
for fam, s, a in [("other", 2.2, .5), ("tower", 3, .8), ("stone", 3, .75), ("tomb", 3.2, .8)]:
    g = M[M.fam == fam]
    ax.scatter(g.x, g.y, s=s, c=FAM_COL[fam], alpha=a, lw=0, zorder=3)
extent(ax, -11, 35.5, 22, 61)
ax.set_aspect("equal", adjustable="datalim")
ax.axis("on"); ax.set_xticks([]); ax.set_yticks([])
for s in ax.spines.values():
    s.set_visible(False)
fig.text(0.05, 0.88, "DATA STUDY", fontsize=13, family=MONO, color=BG, va="center", bbox=dict(boxstyle="square,pad=0.45", fc=SEA, ec="none"))
fig.text(0.168, 0.88, "EUROPE, 5500 TO 500 BC", fontsize=13, family=MONO, color=MUT, va="center")
fig.text(0.047, 0.80, "The Megalith", fontproperties=DISP, fontsize=50, color=FG, va="top")
fig.text(0.047, 0.66, "Highway", fontproperties=DISP, fontsize=50, color=SEA, va="top")
fig.text(0.05, 0.43, f"{R['data']['megaliths']:,} dolmens, passage graves,\nmenhirs and stone circles. Did the\nidea travel by sea?",
         family=SER, fontsize=20, color=FG, va="top", linespacing=1.25)
fig.text(0.05, 0.085, "Dr Tristan Hotham · Independent researcher", family=MONO, fontsize=12.5, color=MUT)
fig.savefig(os.path.join(ROOT, "header.png"), dpi=100, facecolor=BG)
print("header.png")
