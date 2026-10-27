"""Step 1: classify the OpenStreetMap monuments, place them in countries and sea zones,
and measure distance to the coast.

Inputs (read in place, not copied):
  ../../_data3/osm_monuments_europe.json   OpenStreetMap (ODbL 1.0), pulled 27 Oct 2026
  ../../_data3/wikidata_monuments.json     Wikidata (CC0), used only to add period/culture via the OSM wikidata tag
  ../../_data3/ne/geojson/                 Natural Earth 1:10m countries and coastline (public domain)
Outputs:
  ../data/megaliths.csv          one row per megalithic monument (the map and all tests)
  ../data/tumuli_baseline.csv    non-megalithic barrows/tumuli (second baseline for the coast test)
  ../work/geo.pkl                projected country polygons and coastline (for step 2)
  ../data/results.json           section "data"
Run: python3 01_prepare.py
"""
import json, os, re, pickle, collections
import numpy as np, pandas as pd
import shapely
from shapely.geometry import shape, box
from shapely.ops import unary_union
from pyproj import Transformer

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
D3 = os.path.join(HERE, "..", "..", "_data3")
T = Transformer.from_crs("EPSG:4326", "EPSG:3035", always_xy=True)
TI = Transformer.from_crs("EPSG:3035", "EPSG:4326", always_xy=True)
BOX = box(-32, 34, 60, 72)

# ---------------------------------------------------------------- classes
CLASSES = [  # id, label, short label
    ("dolmen", "Dolmens", "Dolmen"),
    ("passage", "Passage graves", "Passage grave"),
    ("gallery", "Gallery graves", "Gallery grave"),
    ("cpw", "Court, portal and wedge tombs", "Court, portal or wedge tomb"),
    ("chamber", "Chamber tombs and chambered cairns", "Chamber tomb"),
    ("longb", "Long barrows", "Long barrow"),
    ("menhir", "Menhirs and standing stones", "Menhir or standing stone"),
    ("rows", "Alignments and stone rows", "Alignment or stone row"),
    ("circle", "Stone circles", "Stone circle"),
    ("tower", "Nuraghi and talaiots", "Nuraghe or talaiot"),
    ("other", "Cists, stone ships and other", "Other megalithic"),
    ("unk", "Megalith, type not tagged", "Megalith (type not tagged)"),
]
TOMBS = {"dolmen", "passage", "gallery", "cpw", "chamber", "longb"}
MT = {
    "dolmen": "dolmen", "portal_stones": "dolmen",
    "passage_grave": "passage",
    "gallery_grave": "gallery",
    "court_tomb": "cpw", "portal_tomb": "cpw", "wedge_tomb": "cpw",
    "chamber": "chamber", "chambered_cairn": "chamber", "tholos": "chamber", "tomb": "chamber",
    "long_barrow": "longb",
    "menhir": "menhir", "standing_stone": "menhir", "lech": "menhir", "zutarria": "menhir", "bigstone": "menhir",
    "alignment": "rows", "stone_row": "rows", "stone_line": "rows",
    "stone_circle": "circle", "cromlech": "circle",
    "nuraghe": "tower", "talaiot": "tower", "talayot": "tower", "taula": "tower", "naveta": "tower", "naveform": "tower",
    "cist": "other", "stone_ship": "other", "stone": "other", "ring_cairn": "other",
}
BARROWISH = {"", "round_barrow", "barrow", "tumuloa", "cairn", "grave_field", "undetermined"}
TOMB_TAG = {"dolmen": "dolmen", "passage_tomb": "passage", "gallery": "gallery"}
HIST_TAG = {"dolmen": "dolmen", "menhir": "menhir", "standing_stone": "menhir", "stone_circle": "circle", "megalith": "unk"}
# name rule for rows that matched only the multilingual name query (q == "E")
CIRCLE_RE = re.compile(r"stone circle|steinkreis|kamienn\w* kr[ąę]g|kr[ąę]g\w* kamienn|cromlech|domarring|stensättning|cercle de pierres|círculo de piedras|kamenný kruh|kivikehä|steinring", re.I)
ROW_RE = re.compile(r"stone row|steinreihe|alignement", re.I)
NOT_RE = re.compile(r"street|road|lane|court|gatan|vägen|ulica|stacja|sąd|okręg|okrąg|kręgiel|pub|inn\b|hotel|farm|house|cottage|school|bus|parking", re.I)


def classify(r):
    mt = (r.get("mt") or "").strip().lower()
    a = (r.get("as") or "").strip().lower()
    tomb = (r.get("tomb") or "").strip().lower()
    hist = (r.get("hist") or "").strip().lower()
    q = r["q"]
    if mt in MT:
        if mt == "stone" and a != "megalith":
            return None
        return MT[mt]
    if a in ("nuraghe", "nu"):
        return "tower"
    if a == "cromlech":
        return "circle"
    if tomb in TOMB_TAG:
        return TOMB_TAG[tomb]
    if hist in HIST_TAG and a in ("", "megalith"):
        return HIST_TAG[hist]
    if a in ("megalith", "tumulus;megalith"):
        return "unk"
    if set(q) <= {"E"} or q == "DE":
        n = r.get("name") or ""
        if hist in ("archaeological_site", "standing_stone", "stone", "ruins", "memorial", "monument", "") and not NOT_RE.search(n):
            if CIRCLE_RE.search(n):
                return "circle"
            if ROW_RE.search(n):
                return "rows"
    return None


def is_tumulus(r):
    mt = (r.get("mt") or "").strip().lower()
    a = (r.get("as") or "").strip().lower()
    tomb = (r.get("tomb") or "").strip().lower()
    return (a == "tumulus" and mt in BARROWISH) or (a == "" and tomb == "tumulus" and mt in BARROWISH)


# ---------------------------------------------------------------- period / culture
def norm_period(*vals):
    s = " ".join(v.lower() for v in vals if v)
    if not s.strip():
        return "Not recorded"
    if "nurag" in s:
        return "Nuragic"
    if "talai" in s or "talay" in s:
        return "Talaiotic"
    neo = re.search(r"neolith|stone.age|stone_age|néolith|funnelbeaker|eneolit|copper|chalcolith|megalith", s)
    bro = re.search(r"bronze", s)
    iro = re.search(r"iron|hallstat|celtic|celts|la tène|etrusc", s)
    if neo and bro:
        return "Neolithic or Bronze Age"
    if neo:
        return "Neolithic or Copper Age"
    if bro:
        return "Bronze Age"
    if iro:
        return "Iron Age"
    if "prehist" in s:
        return "Prehistoric, unspecified"
    return "Later or other tag"


def main():
    osm = json.load(open(os.path.join(D3, "osm_monuments_europe.json")))
    # Wikidata period/culture, joined by the OSM wikidata tag only
    wd = json.load(open(os.path.join(D3, "wikidata_monuments.json")))
    wper = {}
    for k, rows in wd.items():
        for r in rows:
            v = " ".join(x for x in (r.get("perLabel"), r.get("culLabel")) if x and not x.startswith("Q"))
            if v:
                wper[r["i"]] = (wper.get(r["i"], "") + " " + v).strip()

    rows, tum = [], []
    reasons = collections.Counter()
    for r in osm:
        c = classify(r)
        q = (r.get("wd") or "").rsplit("/", 1)[-1]
        if c:
            p = norm_period(r.get("per") or "", r.get("civ") or "", wper.get(q, ""))
            rows.append(dict(osm=r["o"], lat=r["lat"], lon=r["lon"], name=(r.get("name") or "").strip(), cls=c,
                             mt=r.get("mt") or "", as_=r.get("as") or "", period=p, wikidata=q,
                             period_src="wikidata" if (not (r.get("per") or r.get("civ")) and q in wper) else ("osm" if (r.get("per") or r.get("civ")) else "")))
            reasons["megalithic"] += 1
        elif is_tumulus(r):
            tum.append(dict(osm=r["o"], lat=r["lat"], lon=r["lon"]))
            reasons["tumulus"] += 1
        else:
            reasons["dropped"] += 1
    M = pd.DataFrame(rows)
    U = pd.DataFrame(tum)
    print(reasons, len(M), len(U))

    # ------------------------------------------------------------ geography
    ne = json.load(open(os.path.join(D3, "ne", "geojson", "ne_10m_admin_0_countries.geojson")))
    merge = {"Aland": "Finland"}
    cgeo = {}
    for f in ne["features"]:
        p = f["properties"]
        if p["CONTINENT"] != "Europe":
            continue
        g = shape(f["geometry"]).intersection(BOX)
        if g.is_empty:
            continue
        name = merge.get(p["ADMIN"], p["ADMIN"]).replace("Republic of Serbia", "Serbia")
        cgeo[name] = unary_union([cgeo[name], g]) if name in cgeo else g
    names = sorted(cgeo)
    proj = {n: shapely.transform(cgeo[n], lambda a: np.c_[T.transform(a[:, 0], a[:, 1])], include_z=False) for n in names}
    cl = json.load(open(os.path.join(D3, "ne", "geojson", "ne_10m_coastline.geojson")))
    segs = []
    for f in cl["features"]:
        g = shape(f["geometry"])
        if not g.intersects(box(-40, 30, 70, 76)):
            continue
        a = np.asarray(g.coords)
        X, Y = T.transform(a[:, 0], a[:, 1])
        xy = np.c_[X, Y]
        for i in range(0, len(xy) - 1, 20):  # short pieces for a fast spatial index
            segs.append(shapely.linestrings(xy[i:i + 21]))
    segs = np.array([s for s in segs if s.length > 0])
    tree = shapely.STRtree(segs)
    ctree = shapely.STRtree([proj[n] for n in names])
    pickle.dump(dict(names=names, proj=proj, segs=segs), open(os.path.join(ROOT, "work", "geo.pkl"), "wb"))

    def place(df):
        X, Y = T.transform(df.lon.values, df.lat.values)
        pts = shapely.points(X, Y)
        # country: polygon containing the point, else nearest within 5 km (points on small islands or the shoreline)
        idx = np.full(len(pts), -1)
        pi, ci = ctree.query(pts, predicate="within")
        idx[pi] = ci
        miss = np.where(idx < 0)[0]
        if len(miss):
            (pi2, ci2), d2 = ctree.query_nearest(pts[miss], max_distance=5000, return_distance=True)
            idx[miss[pi2]] = ci2
        country = np.where(idx >= 0, np.array(names, dtype=object)[np.maximum(idx, 0)], "")
        (pi3, si3), dist = tree.query_nearest(pts, return_distance=True, all_matches=False)
        dk = np.full(len(pts), np.nan)
        dk[pi3] = dist / 1000
        near = shapely.get_point(shapely.shortest_line(pts[pi3], segs[si3]), 1)
        nlon, nlat = TI.transform(shapely.get_x(near), shapely.get_y(near))
        zone = np.array([sea_zone(a, b) for a, b in zip(nlon, nlat)], dtype=object)
        z = np.full(len(pts), "", dtype=object)
        z[pi3] = zone
        return country, np.round(dk, 3), z, X, Y

    for df in (M, U):
        df["country"], df["coast_km"], df["coast_sea"], df["x"], df["y"] = place(df)
    M = M[M.country != ""].copy()
    U = U[U.country != ""].copy()
    # remove duplicates: same class within 15 m (a node and an outline for one monument)
    M = M.sort_values(["cls", "osm"]).reset_index(drop=True)
    keep = np.ones(len(M), bool)
    for c, g in M.groupby("cls"):
        t = shapely.STRtree(shapely.points(g.x.values, g.y.values))
        a, b = t.query(shapely.points(g.x.values, g.y.values), predicate="dwithin", distance=15)
        ii = g.index.values
        for i, j in zip(a, b):
            if i < j and keep[ii[i]]:
                keep[ii[j]] = False
    ndup = int((~keep).sum())
    M = M[keep].reset_index(drop=True)
    M["zone"] = np.where(M.coast_km > 50, "Inland", M.coast_sea)
    U["zone"] = np.where(U.coast_km > 50, "Inland", U.coast_sea)
    M = M.drop(columns=["x", "y"])
    M.to_csv(os.path.join(ROOT, "data", "megaliths.csv"), index=False)
    U[["osm", "lat", "lon", "country", "coast_km", "coast_sea", "zone"]].to_csv(os.path.join(ROOT, "data", "tumuli_baseline.csv"), index=False)

    R = load_results()
    lab = {c[0]: c[1] for c in CLASSES}
    R["classes"] = [dict(id=c[0], label=c[1], short=c[2], tomb=c[0] in TOMBS) for c in CLASSES]
    R["data"] = dict(
        osm_records=len(osm), megaliths=len(M), duplicates_removed=ndup, tumuli=len(U),
        by_class={c: int((M.cls == c).sum()) for c in lab},
        tombs=int(M.cls.isin(TOMBS).sum()),
        named=int((M.name != "").sum()),
        with_period=int((~M.period.isin(["Not recorded"])).sum()),
        period_counts=M.period.value_counts().to_dict(),
        countries=int(M.country.nunique()),
        by_country=M.country.value_counts().to_dict(),
        tumuli_by_country=U.country.value_counts().to_dict(),
        name_rule_rows=int(sum(1 for r in osm if set(r["q"]) <= {"E"} and classify(r))),
        top_type_country={c: M[M.cls == c].country.value_counts().head(3).to_dict() for c in lab},
    )
    save_results(R)
    print(M.cls.value_counts(), M.country.value_counts().head(20), M.zone.value_counts(), sep="\n")


def sea_zone(lon, lat):
    """Which sea the nearest coastline belongs to (simple, documented box rules)."""
    if lon > 46.5 and lat < 48.5:
        return "Caspian"
    if lon > -5.6 and lat < 47.5 and not (lon < -0.9 and lat > 42.5):
        return "Mediterranean and Black Sea"
    return "Atlantic and northern seas"


def load_results():
    p = os.path.join(ROOT, "data", "results.json")
    return json.load(open(p)) if os.path.exists(p) else {}


def save_results(R):
    json.dump(R, open(os.path.join(ROOT, "data", "results.json"), "w"), indent=1, ensure_ascii=False, default=lambda o: o.item() if hasattr(o, "item") else str(o))


if __name__ == "__main__":
    main()
