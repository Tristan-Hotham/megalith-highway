"""Shared helpers for the static maps and charts (header, paper, blog, collage).

Projection: ETRS89 Lambert azimuthal equal-area (EPSG:3035), in km.
Land: Natural Earth 1:50m countries (public domain), read in place from ../../_data3/ne/geojson/.
"""
import json, os
import numpy as np
import pandas as pd
from matplotlib.patches import Polygon
from pyproj import Transformer

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
NE = os.path.join(HERE, "..", "..", "_data3", "ne", "geojson", "ne_50m_admin_0_countries.geojson")
T = Transformer.from_crs("EPSG:4326", "EPSG:3035", always_xy=True)
FONTS = os.environ.get("FONT_DIR", "/tmp/claude-0/-home-claude/c232619d-81e0-53f3-9de6-41e973630753/scratchpad/fonts/")
R = json.load(open(os.path.join(ROOT, "data", "results.json")))

# house palette (light), matching the page
BG, PANEL, FG, MUT, RULE = "#F4F1EA", "#E9E4D8", "#1B2430", "#5F6875", "#D9D3C5"
SEA, HOT, OCHRE, GREY, LAND, WATER = "#1F4E79", "#B9472A", "#C98A1E", "#8E8A80", "#E4DCCB", "#DCE5EA"
CLS_COL = ["#B5452B", "#D9822B", "#8C5A2B", "#D9A92E", "#7A2E3A", "#C46F8E", "#1F5FA8", "#3B9DC4", "#2E8B6E", "#6D4BA3", "#6B7F3A", "#8E8A80"]
FAMILY = {"dolmen": "tomb", "passage": "tomb", "gallery": "tomb", "cpw": "tomb", "chamber": "tomb", "longb": "tomb",
          "menhir": "stone", "rows": "stone", "circle": "stone", "tower": "tower", "other": "other", "unk": "other"}
FAM_COL = {"tomb": HOT, "stone": SEA, "tower": "#6D4BA3", "other": "#9A9384"}
FAM_LAB = {"tomb": "Tombs", "stone": "Menhirs, rows and circles", "tower": "Nuraghi and talaiots", "other": "Other or type not tagged"}


def fonts():
    from matplotlib import font_manager as fm
    for f in ["FrauncesVar.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf", "SourceSerif4-Regular.ttf",
              "SourceSerif4-Semibold.ttf", "SourceSerif4-It.ttf"]:
        p = os.path.join(FONTS, f)
        if os.path.exists(p):
            fm.fontManager.addfont(p)
    p = os.path.join(FONTS, "FrauncesVar.ttf")
    disp = fm.FontProperties(fname=p, weight=900) if os.path.exists(p) else fm.FontProperties(family="serif", weight="bold")
    return disp, "Source Serif 4", "IBM Plex Mono"


def xy(lon, lat):
    x, y = T.transform(np.asarray(lon, float), np.asarray(lat, float))
    return np.asarray(x) / 1000, np.asarray(y) / 1000


_LAND = None


def land_rings():
    global _LAND
    if _LAND is None:
        g = json.load(open(NE))
        out = []
        for f in g["features"]:
            geom = f["geometry"]
            polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
            for poly in polys:
                ring = np.array(poly[0])
                if ring[:, 0].max() < -35 or ring[:, 0].min() > 70 or ring[:, 1].max() < 25 or ring[:, 1].min() > 80:
                    continue
                ring = ring[(ring[:, 0] > -60) & (ring[:, 0] < 100)] if np.ptp(ring[:, 0]) > 300 else ring
                if len(ring) < 3:
                    continue
                X, Y = xy(ring[:, 0], ring[:, 1])
                out.append(np.c_[X, Y])
        _LAND = out
    return _LAND


def draw_land(ax, fc=LAND, ec="none", lw=0.4, z=1):
    for r in land_rings():
        ax.add_patch(Polygon(r, closed=True, fc=fc, ec=ec, lw=lw, zorder=z))


def extent(ax, lon0=-11, lat0=35, lon1=30, lat1=62):
    lo = np.linspace(lon0, lon1, 30); la = np.linspace(lat0, lat1, 30)
    X1, Y1 = xy(np.r_[lo, lo, np.full(30, lon0), np.full(30, lon1)], np.r_[np.full(30, lat0), np.full(30, lat1), la, la])
    ax.set_xlim(X1.min(), X1.max()); ax.set_ylim(Y1.min(), Y1.max()); ax.set_aspect("equal"); ax.axis("off")


def load_megaliths():
    M = pd.read_csv(os.path.join(ROOT, "data", "megaliths.csv"), keep_default_na=False)
    M["x"], M["y"] = xy(M.lon.values, M.lat.values)
    M["fam"] = M.cls.map(FAMILY)
    return M


def load_dated():
    S = pd.read_csv(os.path.join(ROOT, "data", "radiocarbon_sites.csv"), keep_default_na=False)
    S = S[(S.primary == True) & (S.dup_of_earlier == False) & (S.start_bc != "")].copy()
    S["start_bc"] = S.start_bc.astype(float)
    S["x"], S["y"] = xy(S.lon.astype(float).values, S.lat.astype(float).values)
    return S


def time_cmap():
    from matplotlib.colors import LinearSegmentedColormap
    return LinearSegmentedColormap.from_list("t", ["#A0341C", "#CD9120", "#1F4E79"])
