"""r/dataisbeautiful collage for The Megalith Highway: reddit/megalith_highway.png (2400 x 3000).
Every number comes from ../data/results.json. Run: python3 reddit/collage.py
"""
import os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "code"))
from mapdraw import R, fonts, draw_land, extent, load_megaliths, load_dated, time_cmap  # noqa: E402

DISP, SER, MONO = fonts()
BG, FG, MUT, RULE = "#EEEBE4", "#18222E", "#5D6672", "#D5CFC2"
OCEAN, LAND, BLUE = "#173E63", "#E9E1CF", "#1F4E79"
TOMB, STONE, TOWER, OTHER = "#C4502C", "#D9A030", "#8A5AA8", "#A99E88"
M = load_megaliths(); S = load_dated()
G = R["coast"]["groups"]; SH = R["show"]

fig = plt.figure(figsize=(12, 15), dpi=200, facecolor=BG)
fig.text(0.045, 0.972, "THE MEGALITH HIGHWAY", family=MONO, fontsize=14, color=BG, va="top",
         bbox=dict(boxstyle="square,pad=0.4", fc=BLUE, ec="none"))
fig.text(0.04, 0.948, "Did Europe's great stone\ntombs travel by sea?", fontproperties=DISP, fontsize=46, color=FG, va="top", linespacing=0.95)
fig.text(0.045, 0.842, f"Every megalithic monument mapped in OpenStreetMap: {R['data']['megaliths']:,} dolmens, passage graves,\n"
         "menhirs, stone circles and Sardinian towers, tested three ways against the sea-route story.",
         family=SER, fontsize=14.5, color=FG, va="top", linespacing=1.35)

# hero map: deep blue sea, sand land, monuments as dots
ax = fig.add_axes([0.02, 0.345, 0.6, 0.44], facecolor=OCEAN)
draw_land(ax, fc=LAND)
for fam, c, s, a in [("other", OTHER, 1.6, .7), ("tower", TOWER, 2.6, .9), ("stone", STONE, 2.6, .85), ("tomb", TOMB, 2.8, .85)]:
    g = M[M.fam == fam]
    ax.scatter(g.x, g.y, s=s, c=c, alpha=a, lw=0, zorder=3, rasterized=True)
extent(ax, -11, 36, 21, 61.2)
ax.set_aspect("equal", adjustable="datalim")
ax.axis("on"); ax.set_xticks([]); ax.set_yticks([])
for sp in ax.spines.values():
    sp.set_visible(False)
dc = R["data"]["by_class"]
tombs = R["data"]["tombs"]; stones = SH["standing"]; towers = dc["tower"]; other = R["data"]["megaliths"] - tombs - stones - towers
hs = [Line2D([], [], marker="o", ls="", ms=9, color=c) for c in (TOMB, STONE, TOWER, OTHER)]
ax.legend(hs, [f"Tombs  {tombs:,}", f"Menhirs, rows, circles  {stones:,}", f"Nuraghi, talaiots  {towers:,}", f"Other or untyped  {other:,}"],
          loc="lower left", frameon=True, facecolor=BG, edgecolor="none", framealpha=.93, prop={"family": MONO, "size": 10.5}, borderpad=.8, handletextpad=.3)
from mapdraw import xy
ax.text(*xy(-9.6, 49.3), "ATLANTIC\nOCEAN", family=MONO, fontsize=11, color="#9FB6CF", ha="center", va="center", zorder=5)

# right column: headline numbers
tx = fig.add_axes([0.655, 0.345, 0.32, 0.44]); tx.axis("off")
notes = [
    (f"{G['all']['ratio_random']:.1f}×", HOT := TOMB,
     f"as likely as random land in the\nsame country to stand within\n10 km of the sea ({G['all']['observed_near'] * 100:.0f}% against {G['all']['random_near'] * 100:.0f}%)."),
    (f"{G['all']['ratio_tumuli']:.1f}×", BLUE,
     f"against ordinary barrows in the\nsame countries ({G['all']['tumuli_near'] * 100:.0f}%). The range\nfor megaliths, {G['all']['observed_near_ci'][0] * 100:.0f}% to {G['all']['observed_near_ci'][1] * 100:.0f}%,\nincludes the barrows."),
    (f"{SH['nwf_p10']:.0f} BC", TOMB,
     f"when tombs begin in north-west\nFrance, the earliest of {SH['n_ranked']} regions\n(10th percentile of {SH['nwf_n']} dated tombs)."),
    (f"{SH['z_tomb_atl'] * 100:.0f}% v {SH['z_tum_atl'] * 100:.0f}%", BLUE,
     "of tombs and of barrows within\n50 km of the Atlantic and northern\nseas. Stone rows: " + f"{SH['z_rows_atl'] * 100:.0f}%."),
]
for (big, c, small), y in zip(notes, [1.0, 0.75, 0.47, 0.22]):
    tx.text(0, y, big, fontproperties=DISP, fontsize=31, color=c, va="top", transform=tx.transAxes)
    tx.text(0, y - 0.075, small, family=SER, fontsize=12.2, color=FG, va="top", transform=tx.transAxes, linespacing=1.3)

# bottom left: when the tombs begin
fig.text(0.045, 0.305, "WHEN THE TOMBS BEGIN", family=MONO, fontsize=12, color=MUT)
a1 = fig.add_axes([0.24, 0.135, 0.27, 0.155], facecolor=BG)
rows = sorted([r for r in R["c14"]["primary"]["regions"] if r["tomb_p10_bc"]], key=lambda r: -r["tomb_p10_bc"])
for i, r in enumerate(rows):
    y = len(rows) - 1 - i; c = BLUE if r["atlantic"] else STONE
    a1.plot([-r["tomb_p10_ci"][1], -r["tomb_p10_ci"][0]], [y, y], color=c, lw=3, alpha=.4, solid_capstyle="round")
    a1.scatter(-r["tomb_p10_bc"], y, s=120, color=c, edgecolor=BG, lw=1.5, zorder=3)
short = {"North-west France": "NW France", "Low Countries, north Germany and Poland": "Low Countries, N Germany",
         "England and Man": "England", "Rest of France": "Rest of France", "Southern and eastern Spain": "S and E Spain"}
a1.set_yticks(range(len(rows))); a1.set_yticklabels([f"{short.get(r['region'], r['region'])} ({r['dated_tombs']})" for r in rows[::-1]])
a1.set_xticks([-5000, -4000, -3000, -2000]); a1.set_xticklabels(["5000 BC", "4000", "3000", "2000"])
a1.set_xlim(-5550, -1900)
for t in a1.get_xticklabels() + a1.get_yticklabels():
    t.set_family(MONO); t.set_fontsize(10.5); t.set_color(FG)
a1.tick_params(length=0); a1.xaxis.grid(True, color=RULE); a1.set_axisbelow(True)
for s in a1.spines.values(): s.set_visible(False)
fig.text(0.045, 0.104, "Dot: 10th percentile of tomb start dates, line: 95% range.\nBlue: Atlantic-facing region. Ochre: Mediterranean or inland.",
         family=MONO, fontsize=9.5, color=MUT, va="top", linespacing=1.4)

# bottom right: within 10 km of the sea, by group
fig.text(0.56, 0.305, "WITHIN 10 KM OF THE SEA", family=MONO, fontsize=12, color=MUT)
a2 = fig.add_axes([0.745, 0.135, 0.225, 0.155], facecolor=BG)
grp = [("All megaliths", G["all"]), ("Tombs", G["tombs"]), ("Standing stones", G["standing"]), ("Towers", G["tower"])]
for i, (nm, g) in enumerate(grp):
    y = len(grp) - 1 - i
    a2.plot([v * 100 for v in g["observed_near_ci"]], [y, y], color=TOMB, lw=8, alpha=.2, solid_capstyle="round")
    a2.scatter(g["random_near"] * 100, y, marker="s", s=70, color="#9A9384", zorder=3)
    a2.scatter(g["tumuli_near"] * 100, y, marker="D", s=70, color=BLUE, zorder=3)
    a2.scatter(g["observed_near"] * 100, y, s=130, color=TOMB, edgecolor=BG, lw=1.5, zorder=4)
a2.set_yticks(range(len(grp))); a2.set_yticklabels([g[0] for g in grp[::-1]])
a2.set_xlim(0, 80); a2.set_xticks([0, 20, 40, 60, 80]); a2.set_xticklabels(["0", "20", "40", "60", "80%"])
for t in a2.get_xticklabels() + a2.get_yticklabels():
    t.set_family(MONO); t.set_fontsize(10.5); t.set_color(FG)
a2.tick_params(length=0); a2.xaxis.grid(True, color=RULE); a2.set_axisbelow(True)
for s in a2.spines.values(): s.set_visible(False)
fig.text(0.56, 0.104, "Circle: monuments (shade: 95% range). Diamond: barrows,\nsame countries. Square: random land, same countries.",
         family=MONO, fontsize=9.5, color=MUT, va="top", linespacing=1.4)

fig.add_artist(Line2D([0.045, 0.955], [0.066, 0.066], color=RULE, lw=1, transform=fig.transFigure))
fig.text(0.045, 0.058, "Data: © OpenStreetMap contributors (ODbL 1.0), extract of 27 Oct 2026. Radiocarbon: p3k14c (Bird et al. 2022, CC0),\n"
         "calibrated with IntCal20. Coastlines: Natural Earth. OSM coverage is uneven between countries.\n"
         "Analysis and chart: Tristan Hotham, with Python and matplotlib.", family=MONO, fontsize=9.5, color=MUT, va="top", linespacing=1.45)
fig.savefig(os.path.join(HERE, "megalith_highway.png"), dpi=200, facecolor=BG)
print("megalith_highway.png")
