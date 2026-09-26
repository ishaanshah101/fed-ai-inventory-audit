"""RQ1: which required fields are actually filled, by agency.

The OMB reporting instructions mark each field as required for all rows, for
live rows only, or for high-impact deployed rows only. Completeness is
measured against exactly that requirement, so a blank in a field that was not
required for that row does not count against the agency.
"""
import json, os, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from frame import load
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# is_withheld is required on the submission to OMB but is trivially "No" for every
# row in a public inventory, so it is not counted here.
REQ_ALL = ["use_case_name", "agency_bureau", "development_stage", "is_high_impact"]
REQ_ACTIVE = ["topic_area", "classification", "problem_solved", "benefits", "system_outputs"]   # pre-deployment, pilot, deployed
REQ_LIVE = ["operational_date", "contracting_usage", "have_ato", "data_description", "has_pii",
            "demographic_features", "has_custom_code"]                                             # pilot, deployed
REQ_HI_DEPLOYED = ["hi_testing_conducted", "hi_assessment_completed", "hi_potential_impacts",
                   "hi_independent_review", "hi_ongoing_monitoring", "hi_training_established",
                   "hi_failsafe_presence", "hi_appeal_process", "hi_public_consultation"]
EMPTY_LIST = {"", "[]"}

def filled(v):
    return v is not None and v.strip() not in EMPTY_LIST

def required_fields(r):
    f = list(REQ_ALL)
    st = r["development_stage"]
    if st in ("Pre-deployment", "Pilot", "Deployed"):
        f += REQ_ACTIVE
    if st in ("Pilot", "Deployed"):
        f += REQ_LIVE
    if st == "Deployed" and r["is_high_impact"] == "High-impact":
        f += REQ_HI_DEPLOYED
    return f

rows = load()
# columns each agency left out of its public inventory entirely, parsed from
# OMB's data sourcing summary (results/columns_omitted_by_agency.json)
omitted = json.load(open(os.path.join(BASE, "results", "columns_omitted_by_agency.json")))
per_row = []
for r in rows:
    req = required_fields(r)
    n_f = sum(1 for f in req if filled(r[f]))
    miss = [f for f in req if not filled(r[f])]
    om = set(omitted.get(r["agency"], []))
    per_row.append({"row": r["_row"], "agency": r["agency"], "n_required": len(req),
                    "n_filled": n_f, "missing": miss,
                    "missing_column_omitted": [f for f in miss if f in om],
                    "missing_cell_blank": [f for f in miss if f not in om]})
tot_req = sum(p["n_required"] for p in per_row); tot_fill = sum(p["n_filled"] for p in per_row)
by_ag = collections.defaultdict(lambda: [0, 0, 0])
for p in per_row:
    b = by_ag[p["agency"]]; b[0] += 1; b[1] += p["n_required"]; b[2] += p["n_filled"]
field_miss = collections.Counter(f for p in per_row for f in p["missing"])
n_miss_omitted = sum(len(p["missing_column_omitted"]) for p in per_row)
n_miss_blank = sum(len(p["missing_cell_blank"]) for p in per_row)
# rows that are effectively name-only: no stage, no determination, no problem statement
name_only = [p["row"] for p, r in zip(per_row, rows)
             if not filled(r["development_stage"]) and not filled(r["is_high_impact"])
             and not filled(r["problem_solved"]) and not filled(r["system_outputs"])]
res = {"n_rows": len(rows), "required_cells": tot_req, "filled_cells": tot_fill,
       "overall_completeness": tot_fill / tot_req,
       "rows_fully_complete": sum(1 for p in per_row if p["n_filled"] == p["n_required"]),
       "missing_cells": tot_req - tot_fill,
       "missing_because_column_omitted": n_miss_omitted,
       "missing_because_cell_blank": n_miss_blank,
       "agencies_omitting_a_required_column": sorted(a for a in omitted if any(
           c in REQ_ALL + REQ_ACTIVE + REQ_LIVE + REQ_HI_DEPLOYED for c in omitted[a])),
       "rows_missing_stage": sum(1 for r in rows if not filled(r["development_stage"])),
       "rows_missing_determination": sum(1 for r in rows if not filled(r["is_high_impact"])),
       "rows_name_only": len(name_only),
       "name_only_by_agency": dict(collections.Counter(rows[i]["agency"] for i in name_only)),
       "by_agency": {a: {"n": b[0], "required": b[1], "filled": b[2], "completeness": b[2] / b[1]}
                     for a, b in by_ag.items()},
       "missing_by_field": dict(field_miss.most_common())}
json.dump(res, open(os.path.join(BASE, "results", "completeness.json"), "w"), indent=2)
print(f"overall completeness {res['overall_completeness']:.3f} over {tot_req} required cells; "
      f"{res['rows_fully_complete']} of {len(rows)} rows fully complete")
print(f"missing cells {res['missing_cells']}: {n_miss_omitted} because the agency omitted the column, {n_miss_blank} blank within a reported column")
print(f"missing stage {res['rows_missing_stage']}, missing determination {res['rows_missing_determination']}, name-only {len(name_only)} {res['name_only_by_agency']}")
print("lowest agencies:", sorted(((v['completeness'], a, v['n']) for a, v in res['by_agency'].items()))[:8])
print("most-missed fields:", list(field_miss.most_common(8)))
