"""Unblind the calibration pass and measure the passes' bias."""
import json, os, collections, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAL = os.path.join(BASE, "data", "calibration"); OUT = os.path.join(BASE, "results")

def reading(d): return d["category"] != "none" and d["decision_role"] != "none"

key1 = {d["did"]: d for d in json.load(open(os.path.join(CAL, "c1_key.json")))}
rev1 = {json.loads(l)["did"]: json.loads(l) for l in open(os.path.join(CAL, "c1_reviewer.jsonl"))}
ratings = json.load(open(os.path.join(BASE, "data/rating/all_ratings.json")))
by = collections.defaultdict(list)
for d in ratings: by[d["rid"]].append(d)
items_key = {k["rid"]: k for k in json.load(open(os.path.join(BASE, "data/rating/items_key.json")))}

# self-consistency
dups = collections.defaultdict(list)
for did, k in key1.items(): dups[k["rid"]].append(did)
pairs = {r: dd for r, dd in dups.items() if len(dd) == 2}
cons = {f: sum(1 for r, dd in pairs.items() if rev1[dd[0]][f] == rev1[dd[1]][f]) for f in ("category", "decision_role", "stage")}
cons["reading"] = sum(1 for r, dd in pairs.items() if reading(rev1[dd[0]]) == reading(rev1[dd[1]]))
rev_by_rid = {}
for r, dd in dups.items():
    js = [rev1[d] for d in dd]
    if len({reading(j) for j in js}) == 1:
        rev_by_rid[r] = js[0]

# survival by prior
surv = {}
for prior in ("high", "not"):
    rids = sorted({k["rid"] for k in key1.values() if k["prior"] == prior and k["rid"] in rev_by_rid})
    kept = sum(1 for r in rids if reading(rev_by_rid[r]) == (prior == "high"))
    surv[prior] = {"n": len(rids), "survived": kept, "rate": kept / len(rids)}
disp = sorted({k["rid"] for k in key1.values() if k["prior"] == "disputed" and k["rid"] in rev_by_rid})
disp_res = collections.Counter("high" if reading(rev_by_rid[r]) else "not" for r in disp)

# category-level agreement with passes on rows where passes agreed on category
cat_agree = 0; cat_n = 0
for r in rev_by_rid:
    c = [d["category"] for d in by[r]]
    if c[0] == c[1]:
        cat_n += 1; cat_agree += (rev_by_rid[r]["category"] == c[0])
# stage: reviewer vs passes
stage_conf = collections.Counter()
for r in rev_by_rid:
    for d in by[r]: stage_conf[(d["stage"], rev_by_rid[r]["stage"])] += 1

# C2
key2 = {d["did"]: d for d in json.load(open(os.path.join(CAL, "c2_key.json")))}
rev2 = {json.loads(l)["did"]: json.loads(l) for l in open(os.path.join(CAL, "c2_reviewer.jsonl"))}
row2rid = {v["row"]: r for r, v in items_key.items()}
q_rows = sorted(key2[d]["row"] for d, v in rev2.items() if v["quantified"])
chk_rows = sorted(key2[d]["row"] for d, v in rev2.items() if v["quantified"] and v["metric_named"] and v["evaluation_described"])
# compare with passes on sampled rows
comp = {"reviewer_q_in_sample": 0, "passes_both_q": 0, "passes_any_q": 0, "agree_both": 0, "missed_by_both": [], "overcalled_by_both": []}
for d, k in key2.items():
    rid = row2rid.get(k["row"])
    if rid is None: continue
    rq = rev2[d]["quantified"]; pq = [x["quantified"] for x in by[rid]]
    comp["reviewer_q_in_sample"] += rq
    comp["passes_both_q"] += all(pq); comp["passes_any_q"] += any(pq)
    if rq and all(pq): comp["agree_both"] += 1
    if rq and not any(pq): comp["missed_by_both"].append(k["row"])
    if (not rq) and all(pq): comp["overcalled_by_both"].append(k["row"])
n_in_sample = sum(1 for k in key2.values() if k["row"] in row2rid)
# passes' quantified on sampled rows NOT in the numeral candidate set (should be impossible)
cand_rows = {k["row"] for k in key2.values()}
outside = [r for r, k in items_key.items() if k["row"] not in cand_rows and all(x["quantified"] for x in by[r])]

res = {"self_consistency": cons, "n_dup_pairs": len(pairs), "c1_survival": surv,
       "c1_disputed_n": len(disp), "c1_disputed_resolution": dict(disp_res),
       "category_agreement_with_agreed_passes": {"n": cat_n, "agree": cat_agree, "rate": cat_agree / cat_n},
       "stage_confusion_pass_vs_reviewer": {f"{a}->{b}": c for (a, b), c in stage_conf.items()},
       "c2_candidates": len(key2), "c2_in_sample": n_in_sample,
       "c2_reviewer_quantified_rows": q_rows, "c2_reviewer_checkable_rows": chk_rows,
       "c2_reviewer_baseline_n": sum(1 for v in rev2.values() if v["baseline_given"]),
       "c2_reviewer_uncertainty_n": sum(1 for v in rev2.values() if v["uncertainty_given"]),
       "c2_vs_passes": comp, "passes_quantified_outside_candidates": outside}
json.dump(res, open(os.path.join(OUT, "calibration.json"), "w"), indent=2)
print("self-consistency:", cons, "of", len(pairs))
print("survival:", surv)
print("disputed ->", dict(disp_res), "of", len(disp))
print(f"category agreement with agreed passes: {cat_agree}/{cat_n}")
print("stage pass->reviewer:", dict(stage_conf))
print(f"C2: {len(key2)} candidates, {n_in_sample} in sample; reviewer quantified {len(q_rows)}, checkable {len(chk_rows)}")
print("C2 vs passes on sampled candidates:", {k: (v if not isinstance(v, list) else len(v)) for k, v in comp.items()})
print("passes quantified outside candidate set:", outside)
