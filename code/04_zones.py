"""Step 4, test three: Atlantic facade against inland Europe, by type of monument.

Zones (from step 1): a monument is in the "Atlantic and northern seas" zone or the
"Mediterranean and Black Sea" zone if it lies within 50 km of a coastline of that sea
(nearest coast decides), and "Inland" if it is more than 50 km from any coast.
Baselines: random points on land in the same countries (ten per megalith, country-weighted
like the megaliths) and the non-megalithic barrows and tumuli.
Outputs: ../data/zones_by_type.csv, results.json section "zones"
Run: python3 04_zones.py
"""
import json, os, pickle
import numpy as np, pandas as pd
import shapely
from pyproj import Transformer

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
TI = Transformer.from_crs("EPSG:3035", "EPSG:4326", always_xy=True)
rng = np.random.default_rng(4)
ZONES = ["Atlantic and northern seas", "Mediterranean and Black Sea", "Inland"]
M = pd.read_csv(os.path.join(ROOT, "data", "megaliths.csv"), keep_default_na=False)
U = pd.read_csv(os.path.join(ROOT, "data", "tumuli_baseline.csv"), keep_default_na=False)
G = pickle.load(open(os.path.join(ROOT, "work", "geo.pkl"), "rb"))
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
tree = shapely.STRtree(G["segs"])


def sea_zone(lon, lat):  # same rule as 01_prepare.py
    if lon > 46.5 and lat < 48.5:
        return "Caspian"
    if lon > -5.6 and lat < 47.5 and not (lon < -0.9 and lat > 42.5):
        return "Mediterranean and Black Sea"
    return "Atlantic and northern seas"


def zones_for(x, y):
    pts = shapely.points(x, y)
    (pi, si), d = tree.query_nearest(pts, return_distance=True, all_matches=False)
    near = shapely.get_point(shapely.shortest_line(pts[pi], G["segs"][si]), 1)
    lon, lat = TI.transform(shapely.get_x(near), shapely.get_y(near))
    z = np.array([sea_zone(a, b) for a, b in zip(lon, lat)], dtype=object)
    z[d / 1000 > 50] = "Inland"
    return z


def sample(poly, n):
    x0, y0, x1, y1 = poly.bounds
    shapely.prepare(poly)
    xs, ys, got = [], [], 0
    while got < n:
        m = min(2_000_000, max(1000, int((n - got) * 3 * (x1 - x0) * (y1 - y0) / poly.area)))
        x = rng.uniform(x0, x1, m); y = rng.uniform(y0, y1, m)
        ok = shapely.contains_xy(poly, x, y)
        xs.append(x[ok]); ys.append(y[ok]); got += ok.sum()
    return np.concatenate(xs)[:n], np.concatenate(ys)[:n]


rz = []
for c, n in M.country.value_counts().items():
    x, y = sample(G["proj"][c], 10 * n)
    rz.append(zones_for(x, y))
rz = np.concatenate(rz)


def shares(z):
    z = pd.Series(z)
    return {k: float((z == k).mean()) for k in ZONES}


rows = []
lab = {c["id"]: c["label"] for c in R["classes"]}
for c in [c["id"] for c in R["classes"]]:
    g = M[M.cls == c]
    s = shares(g.zone.values)
    rows.append(dict(type=lab[c], id=c, n=len(g), **{k: round(v, 4) for k, v in s.items()},
                     within_10km=round(float((g.coast_km <= 10).mean()), 4), median_coast_km=round(float(g.coast_km.median()), 1)))
tombs = M[M.cls.isin([c["id"] for c in R["classes"] if c["tomb"]])]
for name, idv, z, ck in [("All tombs", "tombs", tombs.zone.values, tombs.coast_km), ("All megalithic monuments", "all", M.zone.values, M.coast_km),
                         ("Random land points, same countries", "random", rz, None)]:
    s = shares(z)
    rows.append(dict(type=name, id=idv, n=len(z), **{k: round(v, 4) for k, v in s.items()},
                     within_10km=round(float((ck <= 10).mean()), 4) if ck is not None else None,
                     median_coast_km=round(float(ck.median()), 1) if ck is not None else None))
# tumuli, reweighted so that each country counts as it does among the megaliths (countries with 30+ tumuli)
w = M.country.value_counts(); tc = U.country.value_counts()
w = w[[c for c in w.index if tc.get(c, 0) >= 30]]
tz = {k: float(sum(w[c] * (U[U.country == c].zone == k).mean() for c in w.index) / w.sum()) for k in ZONES}
t10 = float(sum(w[c] * (U[U.country == c].coast_km <= 10).mean() for c in w.index) / w.sum())
rows.append(dict(type="Barrows and tumuli, same country mix", id="tumuli", n=int(U.country.isin(w.index).sum()), **{k: round(v, 4) for k, v in tz.items()},
                 within_10km=round(t10, 4), median_coast_km=None))
Z = pd.DataFrame(rows)
Z.to_csv(os.path.join(ROOT, "data", "zones_by_type.csv"), index=False)
print(Z.to_string())
# Atlantic facade monuments by country
atl = M[M.zone == "Atlantic and northern seas"]
R["zones"] = dict(rows=Z.where(Z.notna(), None).to_dict("records"), zone_names=ZONES, buffer_km=50,
                  atlantic_total=len(atl), atlantic_share=len(atl) / len(M),
                  atlantic_by_country=atl.country.value_counts().head(10).to_dict(),
                  atlantic_tomb_share=float((tombs.zone == "Atlantic and northern seas").mean()),
                  random_atlantic_share=float((rz == "Atlantic and northern seas").mean()),
                  tumuli_atlantic_share=tz["Atlantic and northern seas"], tumuli_reweight_countries=len(w))
json.dump(R, open(os.path.join(ROOT, "data", "results.json"), "w"), indent=1, ensure_ascii=False)
