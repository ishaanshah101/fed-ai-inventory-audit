"""Load the OMB-consolidated 2025 inventory, record its provenance, and tabulate
the structured fields.

The inventory is the population, not a sample. Every use case federal agencies
chose to report publicly is in this file, so counts over the structured fields
carry no sampling uncertainty at all; what they carry is whatever the agencies
put in the boxes, which is the subject of the rest of the study.
"""
import csv, json, os, hashlib, collections

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, "data", "raw", "2025_individually_reported_AI_use_cases.csv")
OUT = os.path.join(BASE, "results")
os.makedirs(OUT, exist_ok=True)

PROVENANCE = {
    "source_repo": "https://github.com/ombegov/2025-Federal-Agency-AI-Use-Case-Inventory",
    "source_commit": "06c7ebeef5b376524211042bd9673b2a7fefd3e3",
    "source_commit_date": "2026-05-14",
    "file": "Data/2025_individually_reported_AI_use_cases.csv",
    "sha256": hashlib.sha256(open(RAW, "rb").read()).hexdigest(),
    "prior_year_repo": "https://github.com/ombegov/2024-Federal-AI-Use-Case-Inventory",
    "prior_year_commit": "4a29d132291261d4829b187acd8af618e7295294",
}


def load():
    with open(RAW, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    for i, r in enumerate(rows):
        r["_row"] = i
    return rows


STAGES = ["Deployed", "Pilot", "Pre-deployment", "Retired", ""]
HI = ["High-impact", "Presumed High-Impact, but Not High-impact", "Not High-impact", ""]

if __name__ == "__main__":
    rows = load()
    n = len(rows)
    res = {"provenance": PROVENANCE, "n_use_cases": n,
           "n_agencies": len({r["agency"] for r in rows})}
    for col in ["development_stage", "is_high_impact", "contracting_usage", "have_ato",
                "has_pii", "has_custom_code", "classification", "topic_area", "is_withheld"]:
        res[col] = dict(collections.Counter(r[col] for r in rows))
    live = [r for r in rows if r["development_stage"] in ("Deployed", "Pilot")]
    res["n_deployed_or_pilot"] = len(live)
    res["stage_by_hi"] = {s: dict(collections.Counter(r["is_high_impact"] for r in rows
                                                       if r["development_stage"] == s))
                          for s in STAGES}
    res["hi_by_agency_live"] = {}
    for a in sorted({r["agency"] for r in live}):
        sub = [r for r in live if r["agency"] == a]
        res["hi_by_agency_live"][a] = {"n": len(sub),
                                       **dict(collections.Counter(r["is_high_impact"] for r in sub))}
    # minimum-practice fields on deployed high-impact use cases
    dhi = [r for r in rows if r["development_stage"] == "Deployed"
           and r["is_high_impact"] == "High-impact"]
    res["n_deployed_high_impact"] = len(dhi)
    res["min_practices"] = {}
    for col in ["hi_testing_conducted", "hi_assessment_completed", "hi_independent_review",
                "hi_ongoing_monitoring", "hi_training_established", "hi_failsafe_presence",
                "hi_appeal_process", "hi_public_consultation"]:
        res["min_practices"][col] = dict(collections.Counter(r[col] for r in dhi))
    json.dump(res, open(os.path.join(OUT, "structured.json"), "w"), indent=2)
    print(f"{n} use cases from {res['n_agencies']} agencies; {len(live)} deployed or pilot; "
          f"{len(dhi)} deployed high-impact")
    print("stage:", res["development_stage"])
    print("high-impact:", res["is_high_impact"])
    print("\nlive use cases by agency and self-determination:")
    for a, d in sorted(res["hi_by_agency_live"].items(), key=lambda x: -x[1]["n"])[:20]:
        print(f"  {a:8s} n={d['n']:4d}  HI={d.get('High-impact',0):3d}  "
              f"presumed-not={d.get('Presumed High-Impact, but Not High-impact',0):3d}  "
              f"not={d.get('Not High-impact',0):4d}  blank={d.get('',0)}")
