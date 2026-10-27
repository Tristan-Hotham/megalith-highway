"""Step 5: check a random sample of 50 radiocarbon links (rules K or N) by reading the names.

Each sampled link was judged by comparing the p3k14c site name with the OSM monument name:
"same monument", "same complex" (a group of monuments with one name), "unclear" (for example a
village name shared with a tomb nearby) or "wrong". The judgements are listed below so the check
can be repeated. Output: ../data/link_check.csv, results.json c14.link_check
Run after 03_radiocarbon.py: python3 05_link_check.py
"""
import json, os
import pandas as pd

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
S = pd.read_csv(os.path.join(ROOT, "data", "radiocarbon_sites.csv"), keep_default_na=False)
P = S[(S.primary == True) & (S.dup_of_earlier == False)]
x = P.sample(50, random_state=5)[["site", "osm_name", "cls", "dist_m", "rule", "country"]].copy()
UNCLEAR = {"Lough Gur": "large complex with settlements; dated feature may not be the tomb", "Midlaren": "village name only",
           "Pumsaint": "place name; other sites nearby", "Binimaimut": "place name; 639 m from the naveta", "Borger": "village name only",
           "Wulfen": "village name only", "La-Trinité-sur-Mer \u2013 Mané Roularde": "different named monument nearby"}
WRONG = {"Upper Largie": "different monument in the same valley"}
GROUP = {"Brenig site 53": "another monument in the same complex", "Carrowmore 51": "another tomb in the same cemetery",
         "Karleby": "cemetery of several passage graves", "Karleby 71": "another passage grave in the same cemetery",
         "Son Ermitá": "same necropolis", "Voils Le Fort Cazarils": "same necropolis", "NECROPOLE DE LA BOIXE DOLMEN C": "same necropolis"}


def judge(s):
    if s in WRONG: return "wrong", WRONG[s]
    if s in UNCLEAR: return "unclear", UNCLEAR[s]
    if s in GROUP: return "same complex", GROUP[s]
    return "same monument", ""


x["judgement"], x["note"] = zip(*[judge(s) for s in x.site])
x.to_csv(os.path.join(ROOT, "data", "link_check.csv"), index=False)
c = x.judgement.value_counts().to_dict()
print(c)
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
R["c14"]["link_check"] = dict(n=len(x), counts=c, seed=5)
json.dump(R, open(os.path.join(ROOT, "data", "results.json"), "w"), indent=1, ensure_ascii=False)
