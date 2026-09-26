"""Main analysis. Produces results/analysis.json, from which the paper is written."""
import json, os, sys, collections
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from frame import load
from stats import wilson, cluster_bootstrap_rate, cluster_bootstrap_diff

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "results")
NBOOT, SEED = 10_000, 20260926
rows = load()
live = [r for r in rows if r["development_stage"] in ("Deployed", "Pilot")]
ratings = json.load(open(os.path.join(BASE, "data/rating/all_ratings.json")))
by = collections.defaultdict(list)
for d in ratings: by[d["rid"]].append(d)
ikey = {k["rid"]: k["row"] for k in json.load(open(os.path.join(BASE, "data/rating/items_key.json")))}
cal = json.load(open(os.path.join(OUT, "calibration.json")))
agree = json.load(open(os.path.join(OUT, "agreement.json")))
screen = {o["row"]: o for o in json.load(open(os.path.join(OUT, "presumption_screen.json")))}
comp = json.load(open(os.path.join(OUT, "completeness.json")))
churn = json.load(open(os.path.join(OUT, "churn.json")))
churn_rev = json.load(open(os.path.join(OUT, "churn_review.json")))
vend = json.load(open(os.path.join(OUT, "vendors.json")))
struct = json.load(open(os.path.join(OUT, "structured.json")))

def reading(d): return d["category"] != "none" and d["decision_role"] != "none"
def strict(d): return d["category"] != "none" and d["decision_role"] == "principal"

res = {"n_rows": len(rows), "n_live": len(live), "n_sampled": len(ikey),
       "agreement": agree}

# ---------------------------------------------------------------- RQ2
HI = "High-impact"; NOT = "Not High-impact"; PRES = "Presumed High-Impact, but Not High-impact"
samp = []
for rid, row in ikey.items():
    r = rows[row]; js = by[rid]
    rd = [reading(j) for j in js]; st = [strict(j) for j in js]
    samp.append({"rid": rid, "row": row, "agency": r["agency"], "self": r["is_high_impact"],
                 "stage": r["development_stage"],
                 "read": rd[0] if rd[0] == rd[1] else None,
                 "read_strict": st[0] if st[0] == st[1] else None,
                 "screen": bool(screen[row]["categories"]),
                 "cats": sorted({j["category"] for j in js if j["category"] != "none"})})
surv_hi = cal["c1_survival"]["high"]["rate"]; surv_not = cal["c1_survival"]["not"]["rate"]
disp_hi_frac = cal["c1_disputed_resolution"].get("high", 0) / cal["c1_disputed_n"]

def block(sub):
    n = len(sub); agreed = [s for s in sub if s["read"] is not None]
    hi = sum(1 for s in agreed if s["read"]); nt = len(agreed) - hi; disp = n - len(agreed)
    # calibrated: agreed-high * surv_hi + agreed-not * (1 - surv_not) + disputed * disp_hi_frac
    cal_hi = hi * surv_hi + nt * (1 - surv_not) + disp * disp_hi_frac
    strict_hi = sum(1 for s in sub if s["read_strict"])
    return {"n": n, "agreed": len(agreed), "read_high": hi, "read_not": nt, "disputed": disp,
            "rate_read_high_agreed": hi / len(agreed) if agreed else None,
            "wilson": wilson(hi, len(agreed))[1:] if agreed else None,
            "bound_lo": hi / n, "bound_hi": (hi + disp) / n,
            "calibrated_high": cal_hi, "calibrated_rate": cal_hi / n,
            "read_high_strict": strict_hi, "rate_strict": strict_hi / n}
res["rq2"] = {"survival": cal["c1_survival"], "disputed_resolution": cal["c1_disputed_resolution"],
              "by_self_determination": {k: block([s for s in samp if s["self"] == k]) for k in (HI, NOT, PRES, "")}}
# calibration bootstrap: resample the calibration units within each prior class
# to put an interval on the calibrated Not-high-impact rate
key1 = {d["did"]: d for d in json.load(open(os.path.join(BASE, "data/calibration/c1_key.json")))}
rev1 = {json.loads(l)["did"]: json.loads(l) for l in open(os.path.join(BASE, "data/calibration/c1_reviewer.jsonl"))}
units = collections.defaultdict(list)
seen = set()
for did, k in key1.items():
    if k["rid"] in seen: continue
    seen.add(k["rid"]); units[k["prior"]].append(reading(rev1[did]))
rng = np.random.default_rng(SEED)
bn = res["rq2"]["by_self_determination"][NOT]
boot = []
for _ in range(NBOOT):
    sh = np.mean(rng.choice(units["high"], len(units["high"])))
    sn = np.mean(rng.choice(units["not"], len(units["not"])))   # flip rate of agreed-not (reader says high)
    sd = np.mean(rng.choice(units["disputed"], len(units["disputed"])))
    boot.append((bn["read_high"] * sh + bn["read_not"] * sn + bn["disputed"] * sd) / bn["n"])
lo, hi = np.percentile(boot, [2.5, 97.5])
res["rq2"]["not_hi_calibrated_boot"] = (bn["calibrated_rate"], float(lo), float(hi))
res["rq2"]["calibration_units"] = {k: len(v) for k, v in units.items()}

# agency bootstrap on the not-high-impact stratum (rows nested in agencies)
not_rows = [s for s in samp if s["self"] == NOT and s["read"] is not None]
ag_cl = collections.defaultdict(lambda: [0, 0])
for s in not_rows:
    ag_cl[s["agency"]][1] += 1; ag_cl[s["agency"]][0] += s["read"]
res["rq2"]["not_hi_read_high_agency_bootstrap"] = cluster_bootstrap_rate([tuple(v) for v in ag_cl.values()], NBOOT, SEED)

# population extrapolation for the Not-high-impact live rows: weight each agency's
# sampled rate by its live Not-high-impact count
pop_not = collections.Counter(r["agency"] for r in live if r["is_high_impact"] == NOT)
est = 0.0; per_ag = {}
for a, (h, n) in ag_cl.items():
    rate = h / n; est += rate * pop_not[a]
    per_ag[a] = {"sampled": n, "read_high": h, "rate": rate, "live_not_hi": pop_not[a],
                 "self_high_live": sum(1 for r in live if r["agency"] == a and r["is_high_impact"] == HI)}
res["rq2"]["population_estimate_not_hi_read_high"] = {
    "estimate": est, "of": sum(pop_not.values()), "rate": est / sum(pop_not.values()),
    "self_reported_high_live": sum(1 for r in live if r["is_high_impact"] == HI),
    "per_agency": per_ag}
# prediction 2: zero-self-reporters vs top self-reporters among agencies with >=30 live rows
live_by_ag = collections.Counter(r["agency"] for r in live)
big = [a for a, n in live_by_ag.items() if n >= 30 and a in per_ag]
zero = [a for a in big if per_ag[a]["self_high_live"] == 0]
top = sorted(big, key=lambda a: -per_ag[a]["self_high_live"])[:3]
def pooled(ags): return (sum(per_ag[a]["read_high"] for a in ags), sum(per_ag[a]["sampled"] for a in ags))
z, t = pooled(zero), pooled(top)
d = cluster_bootstrap_diff([(per_ag[a]["read_high"], per_ag[a]["sampled"]) for a in zero],
                           [(per_ag[a]["read_high"], per_ag[a]["sampled"]) for a in top], NBOOT, SEED) if zero and top else None
res["rq2"]["prediction2"] = {"zero_self_report_agencies": zero, "zero_rate": z[0] / z[1], "zero_n": z,
                             "top_self_report_agencies": top, "top_rate": t[0] / t[1], "top_n": t, "diff_boot": d}
# screen precision
sc = [s for s in samp if s["read"] is not None]
res["rq2"]["screen"] = {"live_matching": sum(1 for r in live if screen[r["_row"]]["categories"]),
                        "live_matching_self_not": sum(1 for r in live if screen[r["_row"]]["categories"] and r["is_high_impact"] == NOT),
                        "precision_in_sample": sum(1 for s in sc if s["screen"] and s["read"]) / max(1, sum(1 for s in sc if s["screen"])),
                        "recall_in_sample": sum(1 for s in sc if s["screen"] and s["read"]) / max(1, sum(1 for s in sc if s["read"]))}
# categories read among high-impact readings
res["rq2"]["categories_among_read_high"] = dict(collections.Counter(c for s in samp if s["read"] for c in s["cats"]).most_common())

# ---------------------------------------------------------------- RQ3 (exact, from C2)
rev2 = [json.loads(l) for l in open(os.path.join(BASE, "data/calibration/c2_reviewer.jsonl"))]
q = [v for v in rev2 if v["quantified"]]
res["rq3"] = {"n_live": len(live), "candidates": len(rev2),
              "quantified": len(q), "rate": len(q) / len(live), "wilson": wilson(len(q), len(live))[1:],
              "metric_named": sum(1 for v in q if v["metric_named"]),
              "evaluation_described": sum(1 for v in q if v["evaluation_described"]),
              "baseline_given": sum(1 for v in q if v["baseline_given"]),
              "uncertainty_given": sum(1 for v in q if v["uncertainty_given"]),
              "checkable": sum(1 for v in q if v["metric_named"] and v["evaluation_described"]),
              "checkable_rate": sum(1 for v in q if v["metric_named"] and v["evaluation_described"]) / len(live),
              "checkable_wilson": wilson(sum(1 for v in q if v["metric_named"] and v["evaluation_described"]), len(live))[1:],
              "passes_vs_reviewer": cal["c2_vs_passes"]}

# ---------------------------------------------------------------- RQ4 (population)
dhi = [r for r in rows if r["development_stage"] == "Deployed" and r["is_high_impact"] == HI]
MP = {"hi_testing_conducted": {"Yes"}, "hi_assessment_completed": {"Yes"},
      "hi_independent_review": {"Internal Independent Review", "Oversight Board Review", "CAIO Review"},
      "hi_ongoing_monitoring": {"Yes - Monitoring Established"},
      "hi_training_established": {"Training Established", "a) Yes, sufficient and periodic training has been established"},
      "hi_failsafe_presence": {"Yes", "Not Applicable"}}
omitted = json.load(open(os.path.join(OUT, "columns_omitted_by_agency.json")))
def done(r, f): return r[f].strip() in MP[f]
rq4 = {"n_deployed_high_impact": len(dhi), "per_practice": {}, "by_agency": {}}
for f in MP:
    rq4["per_practice"][f] = {"complete": sum(1 for r in dhi if done(r, f)),
                              "in_progress": sum(1 for r in dhi if "progress" in r[f].lower()),
                              "blank": sum(1 for r in dhi if not r[f].strip()),
                              "waived": sum(1 for r in dhi if "waived" in r[f].lower())}
rq4["all_six_complete"] = sum(1 for r in dhi if all(done(r, f) for f in MP))
rq4["none_complete_reported"] = sum(1 for r in dhi if all(r[f].strip() for f in MP) and not any(done(r, f) for f in MP))
rq4["all_blank"] = sum(1 for r in dhi if not any(r[f].strip() for f in MP))
for a in sorted({r["agency"] for r in dhi}):
    sub = [r for r in dhi if r["agency"] == a]
    rq4["by_agency"][a] = {"n": len(sub), "all_six": sum(1 for r in sub if all(done(r, f) for f in MP)),
                           "all_blank": sum(1 for r in sub if not any(r[f].strip() for f in MP)),
                           "columns_omitted": any(f in omitted.get(a, []) for f in MP)}
res["rq4"] = rq4

# ---------------------------------------------------------------- RQ1, RQ5, RQ6, structured
res["rq1"] = {k: v for k, v in comp.items() if k != "by_agency"}
res["rq1"]["by_agency_lowest"] = sorted(((v["completeness"], a, v["n"]) for a, v in comp["by_agency"].items()))[:10]
rc = collections.Counter(o["verdict"] for o in churn_rev)
unm = churn["unmatched_rate_of_matchable"]
res["rq5"] = {**churn, "review": dict(rc), "review_n": len(churn_rev),
              "silent_disappearance_upper_incl_cots": unm * (rc["no_successor"] + rc["no_successor_cots_likely"]) / len(churn_rev),
              "silent_disappearance_upper_excl_cots": unm * rc["no_successor"] / len(churn_rev),
              "stage": struct["development_stage"], "deployed_rate": struct["development_stage"]["Deployed"] / len(rows),
              "live_rate": len(live) / len(rows)}
res["rq6"] = {k: v for k, v in vend.items() if k != "mapping"}

# ---------------------------------------------------------------- Part C stage
dep = [s for s in samp if s["stage"] == "Deployed"]
st_pairs = [(tuple(sorted(j["stage"] for j in by[s["rid"]]))) for s in dep]
res["partC"] = {"n_deployed_sampled": len(dep),
                "passes_both_in_use": sum(1 for p in st_pairs if p == ("in_use", "in_use")),
                "passes_both_not_in_use": sum(1 for p in st_pairs if "in_use" not in p),
                "passes_disagree": sum(1 for p in st_pairs if ("in_use" in p) and p != ("in_use", "in_use")),
                "alpha": agree["fields"]["stage"]["alpha"],
                "pass_in_use_survival": cal["stage_confusion_pass_vs_reviewer"]}

# ---------------------------------------------------------------- predictions
b = res["rq2"]["by_self_determination"]
res["predictions"] = {
 "1_not_hi_read_high_ge_15pct": {"value": b[NOT]["rate_read_high_agreed"], "calibrated": b[NOT]["calibrated_rate"], "held": b[NOT]["rate_read_high_agreed"] >= 0.15},
 "2_zero_reporters_higher": {"zero": res["rq2"]["prediction2"]["zero_rate"], "top": res["rq2"]["prediction2"]["top_rate"],
                             "held": res["rq2"]["prediction2"]["zero_rate"] > res["rq2"]["prediction2"]["top_rate"], "diff_boot": d},
 "3_quantified_lt_10_checkable_lt_2": {"quantified": res["rq3"]["rate"], "checkable": res["rq3"]["checkable_rate"],
                                       "held": res["rq3"]["rate"] < 0.10 and res["rq3"]["checkable_rate"] < 0.02},
 "4_unmatched_ge_20pct": {"raw_unmatched": unm, "corrected_upper": res["rq5"]["silent_disappearance_upper_incl_cots"], "held_as_stated": unm >= 0.20},
 "5_top5_gt_half": {"top5_share": vend["share_top5"], "held": vend["share_top5"] > 0.5},
 "6_deployed_read_not_in_use_ge_10pct": {"passes_both_not_in_use_rate": res["partC"]["passes_both_not_in_use"] / len(dep),
                                          "testable": False, "note": "stage rubric did not reproduce (alpha 0.37; pass in_use survived review 22%)"},
}
json.dump(res, open(os.path.join(OUT, "analysis.json"), "w"), indent=2, default=float)

# ---------------------------------------------------------------- print
print("RQ2 by self-determination (agreed-high / agreed / n, calibrated rate):")
for k, v in b.items():
    print(f"  {k or '(blank)':45s} high {v['read_high']:3d} / agreed {v['agreed']:3d} / n {v['n']:3d}  "
          f"rate {v['rate_read_high_agreed'] if v['agreed'] else 0:.3f}  cal {v['calibrated_rate']:.3f}  strict {v['rate_strict']:.3f}")
p = res["rq2"]["population_estimate_not_hi_read_high"]
print(f"  population: est {p['estimate']:.0f} of {p['of']} live Not-HI rows read high ({p['rate']:.3f}); agencies self-report {p['self_reported_high_live']} live HI")
print("  P2:", {k: v for k, v in res["rq2"]["prediction2"].items()})
print("  agency bootstrap on Not-HI read-high:", res["rq2"]["not_hi_read_high_agency_bootstrap"])
print("  calibrated Not-HI rate with calibration bootstrap:", res["rq2"]["not_hi_calibrated_boot"])
print("  screen:", res["rq2"]["screen"])
print("  categories among read-high:", res["rq2"]["categories_among_read_high"])
r3 = res["rq3"]; print(f"RQ3: quantified {r3['quantified']}/{r3['n_live']} = {100*r3['rate']:.2f}%  checkable {r3['checkable']} = {100*r3['checkable_rate']:.2f}%  baseline {r3['baseline_given']} uncertainty {r3['uncertainty_given']}")
print("RQ4:", {f: v["complete"] for f, v in rq4["per_practice"].items()}, "all six", rq4["all_six_complete"], "all blank", rq4["all_blank"], "none complete", rq4["none_complete_reported"])
print("     by agency:", {a: (v["n"], v["all_six"], v["all_blank"]) for a, v in rq4["by_agency"].items()})
print(f"RQ5: unmatched {unm:.3f}; review {dict(rc)}; silent upper incl cots {res['rq5']['silent_disappearance_upper_incl_cots']:.3f} excl {res['rq5']['silent_disappearance_upper_excl_cots']:.3f}")
print("RQ6: top5", round(vend["share_top5"], 3), "top10", round(vend["share_top10"], 3), "MS", round(vend["microsoft_share"], 3))
print("PartC:", res["partC"])
print("predictions:", {k: v.get("held", v.get("held_as_stated", v.get("testable"))) for k, v in res["predictions"].items()})
