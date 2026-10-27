"""Step 2, test one: are megaliths closer to the sea than chance, and than other burial mounds?

Baseline A: random points on land in the same country, ten for every megalith in that country.
Baseline B: OpenStreetMap barrows and tumuli without a megalithic tag, in the same countries,
            reweighted so each country counts as much as it does among the megaliths.
Uncertainty: a cluster bootstrap that resamples 50 km grid cells (monuments cluster, so
resampling single monuments would make the intervals far too narrow).
Outputs: ../data/coast_by_country.csv, ../data/coast_bands.csv, results.json section "coast"
Run: python3 02_coast_test.py
"""
import json, os, pickle
import numpy as np, pandas as pd
import shapely
from pyproj import Transformer

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
T = Transformer.from_crs("EPSG:4326", "EPSG:3035", always_xy=True)
rng = np.random.default_rng(20261027)
K = 10            # random points per megalith
NEAR = 10         # "near the sea" threshold, km
BANDS = [0, 2, 5, 10, 25, 50, 100, 1e9]
BAND_LAB = ["Under 2 km", "2 to 5 km", "5 to 10 km", "10 to 25 km", "25 to 50 km", "50 to 100 km", "Over 100 km"]
TOMBS = {"dolmen", "passage", "gallery", "cpw", "chamber", "longb"}
GROUPS = {"all": None, "tombs": TOMBS, "standing": {"menhir", "rows", "circle"}, "tower": {"tower"}, "all_excl_russia": "noru"}

M = pd.read_csv(os.path.join(ROOT, "data", "megaliths.csv"), keep_default_na=False)
U = pd.read_csv(os.path.join(ROOT, "data", "tumuli_baseline.csv"), keep_default_na=False)
G = pickle.load(open(os.path.join(ROOT, "work", "geo.pkl"), "rb"))
tree = shapely.STRtree(G["segs"])


def coast_km(x, y):
    (pi, si), d = tree.query_nearest(shapely.points(x, y), return_distance=True, all_matches=False)
    out = np.full(len(x), np.nan); out[pi] = d / 1000
    return out


def sample(poly, n):
    """n uniform random points inside a projected polygon (rejection sampling)."""
    x0, y0, x1, y1 = poly.bounds
    shapely.prepare(poly)
    xs, ys = [], []
    got = 0
    while got < n:
        m = max(1000, int((n - got) * 3 * (x1 - x0) * (y1 - y0) / max(poly.area, 1)))
        m = min(m, 2_000_000)
        x = rng.uniform(x0, x1, m); y = rng.uniform(y0, y1, m)
        ok = shapely.contains_xy(poly, x, y)
        xs.append(x[ok]); ys.append(y[ok]); got += ok.sum()
    return np.concatenate(xs)[:n], np.concatenate(ys)[:n]


# random points per country
rand = {}
for c, n in M.country.value_counts().items():
    x, y = sample(G["proj"][c], K * n)
    rand[c] = coast_km(x, y)
    if c == "Russia":
        pass
print("random points", sum(len(v) for v in rand.values()))


def band_share(d):
    h, _ = np.histogram(d, BANDS)
    return h / max(len(d), 1)


def expected(sub, ref):
    """Country-weighted expectation from a per-country reference distribution (dict country -> distances)."""
    w = sub.country.value_counts()
    w = w[[c for c in w.index if c in ref and len(ref[c]) >= 30]]
    near = sum(w[c] * np.mean(ref[c] <= NEAR) for c in w.index) / w.sum()
    bands = sum(w[c] * band_share(ref[c]) for c in w.index) / w.sum()
    # weighted median: pool reference points with weight w_c / len(ref_c)
    vals = np.concatenate([ref[c] for c in w.index]); wts = np.concatenate([np.full(len(ref[c]), w[c] / len(ref[c])) for c in w.index])
    o = np.argsort(vals); cw = np.cumsum(wts[o]); med = vals[o][np.searchsorted(cw, cw[-1] / 2)]
    return near, bands, med, int(w.sum())


def boot_near(sub, reps=1000):
    """Cluster bootstrap of the observed share within NEAR km, resampling 50 km cells."""
    X, Y = T.transform(sub.lon.values, sub.lat.values)
    cell = (np.floor(X / 50000).astype(int) * 100000 + np.floor(Y / 50000).astype(int))
    df = pd.DataFrame(dict(cell=cell, near=(sub.coast_km.values <= NEAR)))
    g = df.groupby("cell").near.agg(["sum", "size"])
    s, n = g["sum"].values, g["size"].values
    k = len(g)
    out = []
    for _ in range(reps):
        i = rng.integers(0, k, k)
        out.append(s[i].sum() / n[i].sum())
    return np.percentile(out, [2.5, 97.5]).tolist(), k


tumref = {c: g.coast_km.values for c, g in U.groupby("country")}
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
res = {}
for gname, cls in GROUPS.items():
    sub = M if cls is None else (M[M.country != "Russia"] if cls == "noru" else M[M.cls.isin(cls)])
    obs = float(np.mean(sub.coast_km <= NEAR))
    ci, ncell = boot_near(sub)
    rn, rb, rmed, _ = expected(sub, rand)
    tn, tb, tmed, tw = expected(sub, tumref)
    sub_t = sub[sub.country.isin([c for c in tumref if len(tumref[c]) >= 30])]
    res[gname] = dict(
        n=len(sub), near_km=NEAR, observed_near=obs, observed_near_ci=ci, cells=ncell,
        median_km=float(sub.coast_km.median()),
        random_near=rn, random_median_km=float(rmed), ratio_random=obs / rn,
        tumuli_near=tn, tumuli_median_km=float(tmed), tumuli_countries_n=tw,
        observed_near_tumuli_countries=float(np.mean(sub_t.coast_km <= NEAR)),
        ratio_tumuli=float(np.mean(sub_t.coast_km <= NEAR)) / tn,
        bands_observed=band_share(sub.coast_km.values).tolist(), bands_random=rb.tolist(), bands_tumuli=tb.tolist(),
    )
    print(gname, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in res[gname].items() if not k.startswith("bands")})

# per-country table (countries with at least 50 megaliths)
rows = []
for c, g in M.groupby("country"):
    if len(g) < 50:
        continue
    t = tumref.get(c, np.array([]))
    rows.append(dict(country=c, megaliths=len(g), tumuli=len(t),
                     median_km=round(float(g.coast_km.median()), 1), random_median_km=round(float(np.median(rand[c])), 1),
                     tumuli_median_km=round(float(np.median(t)), 1) if len(t) >= 30 else None,
                     near_share=round(float(np.mean(g.coast_km <= NEAR)), 4), random_near_share=round(float(np.mean(rand[c] <= NEAR)), 4),
                     tumuli_near_share=round(float(np.mean(t <= NEAR)), 4) if len(t) >= 30 else None))
cc = pd.DataFrame(rows).sort_values("megaliths", ascending=False)
cc["ratio_random"] = (cc.near_share / cc.random_near_share).round(2)
cc["ratio_tumuli"] = (cc.near_share / cc.tumuli_near_share).round(2)
cc.to_csv(os.path.join(ROOT, "data", "coast_by_country.csv"), index=False)
print(cc.to_string())
bands = pd.DataFrame(dict(band=BAND_LAB, megaliths=res["all"]["bands_observed"], random_same_country=res["all"]["bands_random"], tumuli_same_country=res["all"]["bands_tumuli"]))
bands.to_csv(os.path.join(ROOT, "data", "coast_bands.csv"), index=False)

R["coast"] = dict(groups=res, band_labels=BAND_LAB, k_random=K,
                  random_points=int(sum(len(v) for v in rand.values())),
                  countries=cc.to_dict("records"),
                  countries_closer_than_random=int((cc.near_share > cc.random_near_share).sum()),
                  countries_closer_than_tumuli=int((cc.ratio_tumuli > 1).sum()),
                  countries_with_tumuli=int(cc.ratio_tumuli.notna().sum()),
                  countries_tested=len(cc),
                  median_country_ratio_random=float(cc.ratio_random.median()),
                  median_country_ratio_tumuli=float(cc.ratio_tumuli.replace([np.inf], np.nan).dropna().median()))
json.dump(R, open(os.path.join(ROOT, "data", "results.json"), "w"), indent=1, ensure_ascii=False)
