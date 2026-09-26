"""Blinded calibration materials.

C1: seeded sample stratified over agreed-high-impact, agreed-not, and disputed
    reading, text only, shuffled, with duplicate controls.
C2: every live row that carries a candidate numeral, text only, shuffled.
Keys are written separately and not read until the reviewer's judgements exist.
"""
import json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from frame import load
from build_rating_sets import redact, SHOW
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = os.path.join(BASE, "data", "rating"); OUT = os.path.join(BASE, "data", "calibration")
os.makedirs(OUT, exist_ok=True)
SEED = 20260926; N_TRUE, N_FALSE, N_DISP, N_DUP = 40, 40, 30, 8
rows = load()
items = {it["rid"]: it for it in json.load(open(os.path.join(R, "items.json")))}
split = json.load(open(os.path.join(BASE, "results", "reading_split.json")))
agreed = {int(k): v for k, v in split["agreed"].items()}
disp = split["disputed"]
rng = random.Random(SEED)
c1 = rng.sample(sorted(r for r, v in agreed.items() if v), N_TRUE) \
   + rng.sample(sorted(r for r, v in agreed.items() if not v), N_FALSE) \
   + rng.sample(sorted(disp), N_DISP)
dups = rng.sample(c1, N_DUP)
disp_list = [(r, 0) for r in c1] + [(r, 1) for r in dups]
rng.shuffle(disp_list)
blind, key = [], []
for i, (rid, rep) in enumerate(disp_list, 1):
    did = f"A{i:03d}"
    blind.append({"did": did, **{f: items[rid][f] for f in SHOW}})
    key.append({"did": did, "rid": rid, "rep": rep,
                "prior": "disputed" if rid in disp else ("high" if agreed[rid] else "not")})
json.dump(blind, open(os.path.join(OUT, "c1_blind.json"), "w"), indent=1)
json.dump(key, open(os.path.join(OUT, "c1_key.json"), "w"), indent=1)
# C2
# C2 is built in two blocks so that the display order matches what was reviewed:
# the 208 version-1 candidates first (seed 20260926), then the 97 candidates the
# extended screen added (seed 20260927), see Amendment 1.
allc = json.load(open(os.path.join(BASE, "results", "numeral_screen.json")))
cands = [c for c in allc if c["v1"]]
rng.shuffle(cands)
extra = [c for c in allc if c["v2_only"]]
random.Random(SEED + 1).shuffle(extra)
cands = cands + extra
b2, k2 = [], []
for i, c in enumerate(cands, 1):
    r = rows[c["row"]]
    b2.append({"did": f"B{i:03d}", "numerals": c["numerals"],
               **{f: redact(r[f].strip()) for f in SHOW}})
    k2.append({"did": f"B{i:03d}", "row": c["row"], "id": c["id"]})
json.dump(b2, open(os.path.join(OUT, "c2_blind.json"), "w"), indent=1)
json.dump(k2, open(os.path.join(OUT, "c2_key.json"), "w"), indent=1)
json.dump({"seed": SEED, "c1_units": len(c1), "c1_displays": len(blind), "c1_dup": N_DUP,
           "c2_candidates_v1": sum(1 for c in cands if c["v1"]), "c2_candidates": len(b2)},
          open(os.path.join(OUT, "manifest.json"), "w"), indent=2)
print(f"C1 {len(c1)} units / {len(blind)} displays;  C2 {len(b2)} numeral candidates")
