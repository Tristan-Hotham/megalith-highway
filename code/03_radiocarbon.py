"""Step 3, test two: where are the earliest radiocarbon dates for megalithic sites?

Dates: p3k14c (Bird et al. 2022), all dates in the Europe box. All p3k14c dates are uncalibrated;
I calibrate each with IntCal20 (Reimer et al. 2020; curve file from the rcarbon package,
https://github.com/ahb108/rcarbon, inst/extdata/intcal20.14c, path in INTCAL below) on a 5-year grid
and use the median of the calibrated distribution. Marine shell dates are dropped (marine reservoir).

Linking a p3k14c site (unique SiteName + coordinates) to megaliths, three documented rules:
  K  keyword: the site name contains a megalithic word (dolmen, passage grave, anta, mamoa, orca,
     hunebed, dysse, Großsteingrab, nuraghe, talaiot, long barrow, stone circle, menhir ...).
  N  name and place: the site name shares a distinctive word (4+ letters, not a generic monument
     word) with the name of an OSM megalith within 1 km.
  P  proximity: the site lies within 150 m of an OSM megalith.
Sites whose names say settlement, hut, house, enclosure, pit or field system are excluded.
A site's start is its earliest calibrated median date between 5500 and 500 cal BC (older dates are
taken as pre-monument activity or old material and counted separately).
Outputs: ../data/radiocarbon_sites.csv, ../data/radiocarbon_regions.csv, results.json section "c14"
Run: python3 03_radiocarbon.py
"""
import json, os, re, unicodedata
import numpy as np, pandas as pd
from scipy.spatial import cKDTree
from pyproj import Transformer

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
P3K = os.path.join(HERE, "..", "..", "_data3", "p3k14c", "inst", "p3k14c_scrubbed_fuzzed.csv")
INTCAL = os.environ.get("INTCAL", "/tmp/claude-0/-home-claude/c232619d-81e0-53f3-9de6-41e973630753/scratchpad/mh/x_rcarbon/inst/extdata/intcal20.14c")
T = Transformer.from_crs("EPSG:4326", "EPSG:3035", always_xy=True)
TOMBS = {"dolmen", "passage", "gallery", "cpw", "chamber", "longb"}
OLDEST, YOUNGEST = 5500, 500   # cal BC window for a site's start
NAME_KM = 1.0                 # rule N search radius

KW = {  # keyword -> class it implies
    r"dolmen|hunebed|hünenbett|dysse|\bdös\b|großsteingrab|grosssteingrab|steinkammer|\banta\b|\bmamoa\b|\borca\b|portal (?:tomb|dolmen)": "dolmen",
    r"passage (?:grave|tomb)|ganggrab|j[æa]e?ttestue|g[åa]nggrift": "passage",
    r"gallery grave|all[ée]e couverte|galer[ií]a cubierta": "gallery",
    r"court (?:tomb|cairn)|wedge tomb": "cpw",
    r"chambered|tholos|megalithic tomb|sepulcro megal|sepulcre megal": "chamber",
    r"long barrow|long cairn|langbett": "longb",
    r"menhir|standing stone": "menhir",
    r"stone row|alignement": "rows",
    r"stone circle|cromlech|steinkreis": "circle",
    r"nurag|\btalai|\btalay|naveta": "tower",
    r"megali": "unk",
}
EXCL = re.compile(r"settlement|habitat|hut\b|huts\b|house|enclosure|field system|\bpit\b|pits\b|village|poblado|asentamiento|siedlung|camp\b|midden|cave|cueva|grotte|grotta|abri\b|rock ?shelter", re.I)
GEN = set("""dolmen dolmens tumulus tumuli grave graves tomb tombs tombe cairn cairns site stone stones standing circle menhir menhirs
megalith megalithic megalitico long barrow barrows passage gallery chamber chambered allee couverte court portal wedge nuraghe nuraghi anta antas orca mamoa
sepulcro sepulcre dysse hunebed ganggrab grosssteingrab north south east west nord upper lower great little high grand petit grande petite
with from near field fields farm hill mound mont mount monte saint sainte santa santo hall house moor castle cove cave wood park lane road church
chapel bridge pont pierre pierres della delle alla alle the and des les van von der den het ring henge camp settlement enclosure fort hillfort
burial cemetery necropolis village valley vale isle island lewis orkney mainland human animal bone""".split())

REGIONS = [  # order matters: first match wins. (name, Atlantic-facing?)
    ("Orkney and Shetland", True), ("Scotland", True), ("Ireland", True), ("Wales", True), ("England and Man", True),
    ("North-west France", True), ("Rest of France", False), ("Portugal", True), ("Galicia and northern Spain", True),
    ("Southern and eastern Spain", False), ("Balearic Islands", False), ("Sardinia and Corsica", False),
    ("Italy, Sicily and Malta", False), ("Low Countries, north Germany and Poland", True), ("Denmark, Sweden and Norway", True),
    ("Central Europe", False), ("South-east Europe and the Black Sea", False),
]


def region(country, lon, lat):
    if country in ("United Kingdom", "Isle of Man", "Ireland", "Guernsey", "Jersey"):
        if country == "Ireland" or (country == "United Kingdom" and lon < -5.4 and 54.0 < lat < 55.4):
            return "Ireland"
        if lat > 58.7:
            return "Orkney and Shetland"
        if lat > 55.3 or (lat > 54.9 and lon < -3.0):
            return "Scotland"
        if lon < -2.65 and 51.35 < lat < 53.45 and not (lon > -3.1 and lat > 53.2):
            return "Wales"
        if country in ("Guernsey", "Jersey"):
            return "North-west France"
        return "England and Man"
    if country == "France":
        if 8.4 < lon < 9.7 and 41.3 < lat < 43.1:
            return "Sardinia and Corsica"
        return "North-west France" if (lon < 0.5 and lat > 46.0) else "Rest of France"
    if country in ("Portugal",):
        return "Portugal"
    if country in ("Spain", "Andorra", "Gibraltar"):
        if lon > 1.0 and 38.5 < lat < 40.2:
            return "Balearic Islands"
        return "Galicia and northern Spain" if lat > 42.0 and lon < -1.5 else "Southern and eastern Spain"
    if country in ("Italy", "Malta", "San Marino", "Vatican"):
        return "Sardinia and Corsica" if (8.0 < lon < 10.0 and 38.8 < lat < 41.4) else "Italy, Sicily and Malta"
    if country in ("Netherlands", "Belgium", "Luxembourg", "Poland") or (country == "Germany" and lat > 52.0):
        return "Low Countries, north Germany and Poland"
    if country in ("Denmark", "Sweden", "Norway", "Finland", "Faroe Islands", "Iceland"):
        return "Denmark, Sweden and Norway"
    if country in ("Germany", "Czechia", "Austria", "Switzerland", "Liechtenstein", "Slovakia", "Hungary", "Slovenia"):
        return "Central Europe"
    return "South-east Europe and the Black Sea"


def toks(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return {t for t in re.findall(r"[a-z]{4,}", s)} - GEN


def calibrate(age, err, curve):
    cal, mu, sig = curve
    s2 = err ** 2 + sig ** 2
    p = np.exp(-(age - mu) ** 2 / (2 * s2)) / np.sqrt(s2)
    if p.sum() == 0:
        return np.nan
    c = np.cumsum(p) / p.sum()
    return float(cal[np.searchsorted(c, 0.5)])


def main():
    raw = np.genfromtxt(INTCAL, delimiter=",", comments="#")
    raw = raw[np.argsort(raw[:, 0])]
    grid = np.arange(0, 50001, 5.0)
    curve = (grid, np.interp(grid, raw[:, 0], raw[:, 1]), np.interp(grid, raw[:, 0], raw[:, 2]))

    d = pd.read_csv(P3K, low_memory=False)
    d = d[d.Long.between(-32, 60) & d.Lat.between(34, 72) & d.Age.notna() & d.Error.notna()].copy()
    n_box = len(d)
    shell = d.Material.fillna("").str.contains("shell|marine", case=False)
    d = d[~shell].copy()
    M = pd.read_csv(os.path.join(ROOT, "data", "megaliths.csv"), keep_default_na=False)
    mx, my = T.transform(M.lon.values, M.lat.values)
    tree = cKDTree(np.c_[mx, my])
    mtok = [toks(n) for n in M.name]

    d["SiteName"] = d.SiteName.fillna("").astype(str)
    sites = d.groupby(["SiteName", "Long", "Lat"]).size().rename("n_dates").reset_index()
    sx, sy = T.transform(sites.Long.values, sites.Lat.values)
    out = []
    for i, s in sites.iterrows():
        name = s.SiteName
        if EXCL.search(name):
            continue
        rule, cls, j_best, dist = "", "", -1, np.nan
        for pat, c in KW.items():
            if re.search(pat, name, re.I):
                rule, cls = "K", c
                break
        st = toks(name)
        nb = tree.query_ball_point([sx[i], sy[i]], NAME_KM * 1000)
        hit = [j for j in nb if st & mtok[j]]
        if hit:
            j_best = min(hit, key=lambda j: (mx[j] - sx[i]) ** 2 + (my[j] - sy[i]) ** 2)
            rule = rule + "N"
        dd, jn = tree.query([sx[i], sy[i]])
        if dd <= 150:
            rule = rule + "P"
            if j_best < 0:
                j_best = jn
        if not rule:
            continue
        if j_best >= 0:
            dist = float(np.hypot(mx[j_best] - sx[i], my[j_best] - sy[i]))
            if not cls or cls == "unk":
                cls = M.cls[j_best]
        out.append(dict(site=name, lon=s.Long, lat=s.Lat, n_dates=int(s.n_dates), rule=rule, cls=cls,
                        osm=M.osm[j_best] if j_best >= 0 else "", osm_name=M.name[j_best] if j_best >= 0 else "",
                        dist_m=round(dist) if dist == dist else None,
                        country=M.country[j_best] if j_best >= 0 else ""))
    S = pd.DataFrame(out)
    # country for keyword-only sites: p3k14c's own country field
    key = d.groupby(["SiteName", "Long", "Lat"]).Country.first()
    S["country"] = [c if c else str(key.get((a, b, e), "")) for c, a, b, e in zip(S.country, S.site, S.lon, S.lat)]
    S["country"] = S.country.replace({"Czech Republic": "Czechia", "Channel Isles": "Jersey"})
    # calibrate every date at linked sites
    dd = d.merge(S[["site", "lon", "lat"]], left_on=["SiteName", "Long", "Lat"], right_on=["site", "lon", "lat"])
    dd["cal_bp"] = [calibrate(a, e, curve) for a, e in zip(dd.Age.values, dd.Error.values)]
    dd["cal_bc"] = dd.cal_bp - 1950   # positive = BC
    win = dd[(dd.cal_bc <= OLDEST) & (dd.cal_bc >= YOUNGEST)]
    first = win.sort_values("cal_bc", ascending=False).groupby(["SiteName", "Long", "Lat"]).first()
    S["start_bc"] = [first.cal_bc.get((a, b, e), np.nan) for a, b, e in zip(S.site, S.lon, S.lat)]
    S["start_labid"] = [first.LabID.get((a, b, e), "") for a, b, e in zip(S.site, S.lon, S.lat)]
    S["start_age_bp"] = [first.Age.get((a, b, e), np.nan) for a, b, e in zip(S.site, S.lon, S.lat)]
    S["start_error"] = [first.Error.get((a, b, e), np.nan) for a, b, e in zip(S.site, S.lon, S.lat)]
    older = dd[dd.cal_bc > OLDEST].groupby(["SiteName", "Long", "Lat"]).size()
    S["n_older_than_window"] = [int(older.get((a, b, e), 0)) for a, b, e in zip(S.site, S.lon, S.lat)]
    S["region"] = [region(c, a, b) for c, a, b in zip(S.country, S.lon, S.lat)]
    S["tomb"] = S.cls.isin(TOMBS)
    S["start_bc"] = S.start_bc.round(0)
    S = S.sort_values("start_bc", ascending=False)
    S["primary"] = S.rule.str.contains("K|N")
    # one row per monument: several p3k14c site names can point at the same OSM megalith
    S["dup_of_earlier"] = False
    pr = S[S.primary]
    S.loc[pr.index, "dup_of_earlier"] = pr.osm.ne("") & pr.duplicated(subset=["osm"], keep="first")
    S["dup_any"] = S.osm.ne("") & S.duplicated(subset=["osm"], keep="first")
    S.to_csv(os.path.join(ROOT, "data", "radiocarbon_sites.csv"), index=False)
    M["region"] = [region(c, a, b) for c, a, b in zip(M.country, M.lon, M.lat)]
    prim = summarise(S[S.primary & ~S.dup_of_earlier], M, "primary")
    sens = summarise(S[~S.dup_any], M, "with_proximity")
    R = json.load(open(os.path.join(ROOT, "data", "results.json")))
    R["c14"] = dict(
        dates_box=int(n_box), shell_dropped=int(shell.sum()), sites_linked=len(S),
        dates_at_linked=int(len(dd)), dates_in_window=int(len(win)),
        rule_counts=S.rule.value_counts().to_dict(),
        rule_k=int(S.rule.str.contains("K").sum()), rule_n=int(S.rule.str.contains("N").sum()), rule_p=int(S.rule.str.contains("P").sum()),
        rule_p_only=int((S.rule == "P").sum()), primary_sites=int((S.primary & ~S.dup_of_earlier).sum()),
        duplicates=int(S.dup_of_earlier.sum()), sensitivity_sites=int((~S.dup_any).sum()),
        window=[OLDEST, YOUNGEST], sites_with_older_dates=int((S.n_older_than_window > 0).sum()),
        primary=prim, with_proximity=sens)
    json.dump(R, open(os.path.join(ROOT, "data", "results.json"), "w"), indent=1, ensure_ascii=False)
    pd.DataFrame(prim["regions"]).to_csv(os.path.join(ROOT, "data", "radiocarbon_regions.csv"), index=False)
    print(pd.DataFrame(prim["regions"]).drop(columns=["mean_lon", "mean_lat"]).to_string())
    print(json.dumps({k: v for k, v in prim.items() if k not in ("regions", "hist_tombs", "earliest20")}, indent=1))
    print(pd.DataFrame(sens["regions"])[["region", "dated_tombs", "tomb_p10_bc", "tomb_p10_ci"]].to_string())


def summarise(S, M, label):
    from scipy.stats import spearmanr, mannwhitneyu
    rng = np.random.default_rng(7)
    D = S[S.start_bc.notna()]
    T5 = D[D.tomb].merge(M[["osm", "coast_km", "coast_sea"]], on="osm", how="left")
    rows = []
    for rname, atl in REGIONS:
        g = D[D.region == rname]; gt = T5[T5.region == rname]
        mm = M[M.region == rname]
        e = gt.sort_values("start_bc", ascending=False)
        p10 = ci = None
        if len(gt) >= 8:
            v = gt.start_bc.values
            p10 = float(np.percentile(v, 90))
            bs = [np.percentile(rng.choice(v, len(v)), 90) for _ in range(2000)]
            ci = [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]
        rows.append(dict(region=rname, atlantic=atl, megaliths=len(mm), tombs=int(mm.cls.isin(TOMBS).sum()),
                         dated_sites=len(g), dated_tombs=len(gt),
                         tomb_earliest_bc=float(e.start_bc.iloc[0]) if len(e) else None,
                         tomb_earliest_site=e.site.iloc[0] if len(e) else "",
                         tomb_p10_bc=p10, tomb_p10_ci=ci,
                         tomb_median_bc=float(gt.start_bc.median()) if len(gt) >= 8 else None,
                         share_megaliths_atlantic_coast=float(((mm.coast_sea == "Atlantic and northern seas") & (mm.coast_km <= 25)).mean()) if len(mm) else None,
                         mean_lon=float(mm.lon.mean()) if len(mm) else None, mean_lat=float(mm.lat.mean()) if len(mm) else None))
    t2 = T5.dropna(subset=["coast_km"])
    rho, p = spearmanr(t2.start_bc, t2.coast_km)
    atl = T5[T5.region.isin([r for r, a in REGIONS if a])]
    oth = T5[~T5.region.isin([r for r, a in REGIONS if a])]
    u = mannwhitneyu(atl.start_bc, oth.start_bc, alternative="greater")
    e20 = T5.sort_values("start_bc", ascending=False).head(20)
    bins = list(range(5500, 499, -250))
    hist = {r: [int(((T5[T5.region == r].start_bc <= b) & (T5[T5.region == r].start_bc > b - 250)).sum()) for b in bins[:-1]] for r, _ in REGIONS}
    ranked = sorted([r for r in rows if r["tomb_p10_bc"]], key=lambda r: -r["tomb_p10_bc"])
    clean = lambda df: [{k: (None if (isinstance(v, float) and v != v) else v) for k, v in r.items()} for r in df.to_dict("records")]
    return dict(label=label, sites_dated=len(D), tombs_dated=len(T5), regions=rows,
                ranked=[r["region"] for r in ranked],
                earliest20=clean(e20[["site", "region", "start_bc", "cls", "coast_km", "start_labid", "start_age_bp", "start_error", "rule"]]),
                earliest20_regions=e20.region.value_counts().to_dict(),
                earliest20_within10km=int((e20.coast_km <= 10).sum()),
                spearman_start_vs_coast=dict(rho=float(rho), p=float(p), n=len(t2)),
                atlantic_vs_other=dict(n_atl=len(atl), n_other=len(oth), median_atl=float(atl.start_bc.median()), median_other=float(oth.start_bc.median()),
                                       p10_atl=float(np.percentile(atl.start_bc, 90)), p10_other=float(np.percentile(oth.start_bc, 90)), p_mannwhitney=float(u.pvalue)),
                hist_bins=bins, hist_tombs=hist)


if __name__ == "__main__":
    main()
