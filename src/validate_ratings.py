"""Validate the six rater output files against the schema in docs/RATER_PROMPT.md.
Exits non-zero on any problem."""
import json, collections, sys, os
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = os.path.join(BASE, "data", "rating")
CATS = set("abcdefghijklmno") | {"none"}
ROLES = {"principal", "assistive", "none"}
STAGES = {"in_use", "not_yet", "unclear"}
BOOLS = ["quantified", "metric_named", "evaluation_described", "baseline_given", "uncertainty_given"]
KEYS = {"rater", "rid", "category", "decision_role", "stage", *BOOLS}
items = json.load(open(os.path.join(R, "items.json")))
problems, rows = [], []
for r in range(6):
    exp = {it["rid"] for it in json.load(open(os.path.join(R, f"rater_{r}_items.json")))}
    seen, n = set(), 0
    for ln, line in enumerate(open(os.path.join(R, f"rater_{r}.jsonl")), 1):
        line = line.strip()
        if not line: continue
        n += 1
        try: d = json.loads(line)
        except Exception as e: problems.append(f"r{r} L{ln}: bad JSON {e}"); continue
        if set(d) != KEYS: problems.append(f"r{r} L{ln}: keys {sorted(set(d)^KEYS)}")
        if d.get("rater") != r: problems.append(f"r{r} L{ln}: rater={d.get('rater')}")
        rid = d.get("rid")
        if rid not in exp: problems.append(f"r{r} L{ln}: rid {rid} not assigned")
        if rid in seen: problems.append(f"r{r}: duplicate rid {rid}")
        seen.add(rid)
        if d.get("category") not in CATS: problems.append(f"r{r} rid {rid}: category {d.get('category')!r}")
        if d.get("decision_role") not in ROLES: problems.append(f"r{r} rid {rid}: role {d.get('decision_role')!r}")
        if d.get("stage") not in STAGES: problems.append(f"r{r} rid {rid}: stage {d.get('stage')!r}")
        for b in BOOLS:
            if not isinstance(d.get(b), bool): problems.append(f"r{r} rid {rid}: {b}={d.get(b)!r}")
        rows.append(d)
    miss = exp - seen
    if miss: problems.append(f"r{r}: missing {len(miss)} rids e.g. {sorted(miss)[:8]}")
    print(f"rater {r}: {n} rows, {len(exp)} assigned, {len(miss)} missing")
cov = collections.Counter(d["rid"] for d in rows)
bad = {k: v for k, v in cov.items() if v != 2}
print(f"\nrows {len(rows)}  distinct rids {len(cov)}  items {len(items)}  not-exactly-twice {len(bad)}")
if bad: problems.append(f"coverage {list(bad.items())[:8]}")
if len(cov) != len(items): problems.append("coverage count")
json.dump(rows, open(os.path.join(R, "all_ratings.json"), "w"), indent=0)
print("\ncategory  :", dict(collections.Counter(d["category"] for d in rows).most_common()))
print("role      :", dict(collections.Counter(d["decision_role"] for d in rows)))
print("stage     :", dict(collections.Counter(d["stage"] for d in rows)))
for b in BOOLS: print(f"{b:22s} true: {sum(1 for d in rows if d[b])}")
print(f"\nPROBLEMS: {len(problems)}")
for p in problems[:30]: print(" -", p)
sys.exit(1 if problems else 0)
