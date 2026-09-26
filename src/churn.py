"""RQ5: can the 2024 inventory's entries be found in the 2025 inventory?

The 2024 consolidated file carries no use case identifier, so matching is by
agency and normalised name. Unmatched is an upper bound on silent
disappearance; a seeded sample of unmatched rows is reviewed by hand against
the agency's full 2025 name list (results/churn_review.json) to estimate the
rename rate and correct the bound.
"""
import csv, json, os, re, sys, random, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from frame import load
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P24 = os.path.join(BASE, "data", "raw", "2024_consolidated_ai_inventory_raw_v2.csv")
SEED = 20260926; N_REVIEW = 60

def norm(s):
    s = (s or "").lower()
    s = re.sub(r"\[.*?\]", " ", s)          # bracketed inventory tags
    s = re.sub(r"\(.*?\)", " ", s)          # parentheticals
    s = re.sub(r"[^a-z0-9]+", " ", s)
    s = re.sub(r"\b(the|a|an|of|for|and|to|in|on|with|using|use|ai|artificial|intelligence|ml|machine|learning|model|models|tool|system|project)\b", " ", s)
    return re.sub(r"\s+", " ", s).strip()

with open(P24, encoding="cp1252", newline="") as f:
    r24 = list(csv.DictReader(f))
r25 = load()
# agency abbreviation alignment: 2024 uses 'Agency Abbreviation'
AG_MAP = {"HHS": "HHS", "DOJ": "DOJ", "VA": "VA", "DHS": "DHS", "DOE": "DOE", "DOI": "DOI", "USDA": "USDA",
          "DOC": "DOC", "TREAS": "TREAS", "TREASURY": "TREAS", "NASA": "NASA", "SSA": "SSA", "STATE": "STATE",
          "DOS": "STATE", "SEC": "SEC", "DOL": "DOL", "ED": "ED", "DOT": "DOT", "EPA": "EPA", "GSA": "GSA",
          "HUD": "HUD", "NSF": "NSF", "OPM": "OPM", "SBA": "SBA", "NRC": "NRC", "FDIC": "FDIC", "FRB": "FRB",
          "FTC": "FTC", "FHFA": "FHFA", "NARA": "NARA", "NCUA": "NCUA", "PBGC": "PBGC", "TVA": "TVA",
          "FCC": "FCC", "FERC": "FERC", "CFTC": "CFTC", "NEA": "NEA", "EAC": "EAC", "OSC": "OSC", "NTSB": "NTSB",
          "NIGC": "NIGC", "FCA": "FCA", "STB": "STB", "OSHRC": "OSHRC", "USITC": "USITC"}
ab24 = collections.Counter(r["Agency Abbreviation"].strip().upper() for r in r24)
ab25 = collections.Counter(r["agency"].strip().upper() for r in r25)
by25 = collections.defaultdict(set); names25 = collections.defaultdict(list)
for r in r25:
    a = r["agency"].strip().upper(); by25[a].add(norm(r["use_case_name"])); names25[a].append(r["use_case_name"])
matched, unmatched, no_agency = [], [], []
for i, r in enumerate(r24):
    a = AG_MAP.get(r["Agency Abbreviation"].strip().upper(), r["Agency Abbreviation"].strip().upper())
    n = norm(r["Use Case Name"])
    if a not in by25:
        no_agency.append(i); continue
    (matched if n in by25[a] else unmatched).append(i)
res = {"n_2024": len(r24), "n_2025": len(r25), "matched": len(matched), "unmatched": len(unmatched),
       "agency_absent_in_2025": len(no_agency), "unmatched_rate_of_matchable": len(unmatched) / (len(matched) + len(unmatched)),
       "agencies_2024_not_in_2025": sorted({r24[i]["Agency Abbreviation"] for i in no_agency}),
       "unmatched_by_agency": dict(collections.Counter(r24[i]["Agency Abbreviation"] for i in unmatched).most_common()),
       "n2024_by_agency": dict(ab24.most_common()),
       "retired_in_2025": sum(1 for r in r25 if r["development_stage"] == "Retired")}
# review sample of unmatched rows
rng = random.Random(SEED)
samp = rng.sample(sorted(unmatched), min(N_REVIEW, len(unmatched)))
review = [{"i": i, "agency": r24[i]["Agency Abbreviation"], "name_2024": r24[i]["Use Case Name"],
           "stage_2024": r24[i]["Stage of Development"],
           "candidates_2025": sorted(names25[AG_MAP.get(r24[i]["Agency Abbreviation"].strip().upper(), r24[i]["Agency Abbreviation"].strip().upper())])}
          for i in samp]
json.dump(res, open(os.path.join(BASE, "results", "churn.json"), "w"), indent=2)
json.dump(review, open(os.path.join(BASE, "data", "calibration", "churn_review_blind.json"), "w"), indent=1)
print(res["n_2024"], "rows in 2024;", res["matched"], "matched by agency+name;", res["unmatched"], "unmatched;", res["agency_absent_in_2025"], "from agencies absent in 2025")
print("unmatched rate among matchable:", round(res["unmatched_rate_of_matchable"], 3))
print("agencies absent:", res["agencies_2024_not_in_2025"]); print("unmatched by agency:", list(res["unmatched_by_agency"].items())[:12])
print("2025 rows marked Retired:", res["retired_in_2025"])
