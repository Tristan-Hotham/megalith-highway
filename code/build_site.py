"""Step 6: build ../index.html and ../README.md.

Every number in the text is a placeholder like {{coast.groups.all.ratio_random|f1}}
filled from ../data/results.json; the compact map data is embedded as `const D = ...`.
Formats: int (thousands commas), pct0, pct1, f1, f2, yr (a year, no comma), raw, words.
Run: python3 build_site.py
"""
import os, re, json
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
R = json.load(open(os.path.join(ROOT, "data", "results.json")))


def show():
    """Named shortcuts for numbers quoted in the text (all derived from the sections above)."""
    p = R["c14"]["primary"]
    reg = {r["region"]: r for r in p["regions"]}
    rk = p["ranked"]
    lc = R["c14"]["link_check"]["counts"]
    g = R["coast"]["groups"]
    zr = {r["id"]: r for r in R["zones"]["rows"]}
    S = dict(
        first_region=rk[0], second_region=rk[1], third_region=rk[2], last_region=rk[-1], n_ranked=len(rk),
        nwf_p10=reg["North-west France"]["tomb_p10_bc"], nwf_lo=reg["North-west France"]["tomb_p10_ci"][0], nwf_hi=reg["North-west France"]["tomb_p10_ci"][1],
        nwf_n=reg["North-west France"]["dated_tombs"],
        second_p10=reg[rk[1]]["tomb_p10_bc"], second_lo=reg[rk[1]]["tomb_p10_ci"][0], second_hi=reg[rk[1]]["tomb_p10_ci"][1],
        por_p10=reg["Portugal"]["tomb_p10_bc"], por_n=reg["Portugal"]["dated_tombs"],
        eng_p10=reg["England and Man"]["tomb_p10_bc"], lc_p10=reg["Low Countries, north Germany and Poland"]["tomb_p10_bc"],
        lc_n=reg["Low Countries, north Germany and Poland"]["dated_tombs"],
        rof_p10=reg["Rest of France"]["tomb_p10_bc"], ses_p10=reg["Southern and eastern Spain"]["tomb_p10_bc"],
        ire_p10=reg["Ireland"]["tomb_p10_bc"],
        link_ok=lc.get("same monument", 0) + lc.get("same complex", 0), link_same=lc.get("same monument", 0),
        link_unclear=lc.get("unclear", 0), link_wrong=lc.get("wrong", 0),
        link_ok_share=(lc.get("same monument", 0) + lc.get("same complex", 0)) / R["c14"]["link_check"]["n"],
        regions_with_8=len(rk),
        tomb_share_named=R["data"]["tombs"] / R["data"]["megaliths"],
        standing=R["data"]["by_class"]["menhir"] + R["data"]["by_class"]["rows"] + R["data"]["by_class"]["circle"],
        coast_tumuli_gap=g["all"]["observed_near"] - g["all"]["tumuli_near"],
        z_tomb_atl=zr["tombs"]["Atlantic and northern seas"], z_tum_atl=zr["tumuli"]["Atlantic and northern seas"],
        z_rand_atl=zr["random"]["Atlantic and northern seas"], z_all_atl=zr["all"]["Atlantic and northern seas"],
        z_longb_atl=zr["longb"]["Atlantic and northern seas"], z_cpw_atl=zr["cpw"]["Atlantic and northern seas"],
        z_rows_atl=zr["rows"]["Atlantic and northern seas"], z_circle_atl=zr["circle"]["Atlantic and northern seas"],
        z_menhir_atl=zr["menhir"]["Atlantic and northern seas"], z_dolmen_atl=zr["dolmen"]["Atlantic and northern seas"],
        z_dolmen_inland=zr["dolmen"]["Inland"], z_passage_atl=zr["passage"]["Atlantic and northern seas"],
        z_gallery_atl=zr["gallery"]["Atlantic and northern seas"], z_chamber_atl=zr["chamber"]["Atlantic and northern seas"],
        france_ratio=next(c for c in R["coast"]["countries"] if c["country"] == "France")["ratio_random"],
        portugal_near=next(c for c in R["coast"]["countries"] if c["country"] == "Portugal")["near_share"],
        portugal_rand=next(c for c in R["coast"]["countries"] if c["country"] == "Portugal")["random_near_share"],
        denmark_n=R["data"]["by_country"].get("Denmark", 0), sweden_n=R["data"]["by_country"].get("Sweden", 0),
        denmark_tumuli=R["data"]["tumuli_by_country"].get("Denmark", 0),
        netherlands_n=R["data"]["by_country"].get("Netherlands", 0),
        france_n=R["data"]["by_country"]["France"], germany_n=R["data"]["by_country"]["Germany"],
        not_recorded=R["data"]["period_counts"]["Not recorded"],
    )
    R["show"] = S
    json.dump(R, open(os.path.join(ROOT, "data", "results.json"), "w"), indent=1, ensure_ascii=False)



def get(path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f):
    if f == "int": return f"{int(round(v)):,}"
    if f == "pct0": return f"{v * 100:.0f}%"
    if f == "pct1": return f"{v * 100:.1f}%"
    if f == "f1": return f"{v:.1f}"
    if f == "f2": return f"{v:.2f}"
    if f == "f4": return f"{v:.4f}"
    if f == "yr": return f"{int(round(v))}"
    if f == "words":
        w = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen".split()
        return w[int(v)] if int(v) < len(w) else f"{int(v):,}"
    return str(v)


def sub(m):
    path, _, f = m.group(1).partition("|")
    return fmt(get(path.strip()), f.strip() or "raw")


def site_data():
    M = pd.read_csv(os.path.join(ROOT, "data", "megaliths.csv"), keep_default_na=False)
    cls = [c["id"] for c in R["classes"]]
    countries = sorted(M.country.unique())
    periods = ["Neolithic or Copper Age", "Neolithic or Bronze Age", "Bronze Age", "Iron Age", "Nuragic", "Talaiotic",
               "Prehistoric, unspecified", "Later or other tag", "Not recorded"]
    zones = ["Atlantic and northern seas", "Mediterranean and Black Sea", "Inland"]
    S = pd.read_csv(os.path.join(ROOT, "data", "radiocarbon_sites.csv"), keep_default_na=False)
    S = S[(S.primary == True) & (S.dup_of_earlier == False) & (S.start_bc != "")]
    regions = [r["region"] for r in R["c14"]["primary"]["regions"]]
    dated = {r.osm: r for r in S.itertuples() if r.osm}
    pts = []
    for r in M.itertuples():
        o = r.osm.split("/")
        d = dated.get(r.osm)
        pts.append([round(r.lat, 4), round(r.lon, 4), cls.index(r.cls), countries.index(r.country), periods.index(r.period),
                    r.name, o[0][0] + o[1], round(r.coast_km, 1), zones.index(r.zone) if r.zone in zones else 2, r.wikidata,
                    int(float(d.start_bc)) if d is not None else 0])
    rc = []
    for r in S.itertuples():
        rc.append([round(float(r.lat), 4), round(float(r.lon), 4), int(float(r.start_bc)), r.site.replace('ÔøΩ', '?'), regions.index(r.region),
                   cls.index(r.cls) if r.cls in cls else cls.index("unk"), r.rule, r.start_labid, int(float(r.start_age_bp)), int(float(r.start_error)), r.osm_name])
    return dict(R=R, p=pts, countries=countries, periods=periods, zones=zones, regions=regions, rc=rc)


def fill(t):
    return re.sub(r"\{\{(.+?)\}\}", sub, t)


def main():
    show()
    site = json.dumps(site_data(), ensure_ascii=False, separators=(",", ":"))
    site = site.replace("\u2013", "-").replace("\u2014", "-").replace("</", "<\\/")
    t = open(os.path.join(HERE, "page_template.html")).read().replace("<!--PROSE-->", open(os.path.join(HERE, "prose.html")).read())
    t = re.sub(r"\{\{(.+?)\}\}", sub, t)
    t = t.replace("/*DATA*/", "const D = " + site + ";")
    open(os.path.join(ROOT, "index.html"), "w").write(t)
    print("index.html", len(t.encode()) // 1024, "KB")
    md = re.sub(r"\{\{(.+?)\}\}", sub, open(os.path.join(HERE, "README_template.md")).read())
    open(os.path.join(ROOT, "README.md"), "w").write(md)
    print("README.md written")


if __name__ == "__main__":
    main()
